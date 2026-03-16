# gui/widgets/quant_analysis.py
from __future__ import annotations

import os
import json
import math
import time
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import Qt, QTimer, Signal, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout,
    QSizePolicy, QPushButton
)

# ----------------------------
# Helpers: formatting
# ----------------------------
def _fmt_num(x: float | None, digits: int = 2) -> str:
    if x is None:
        return "—"
    try:
        return f"{float(x):.{digits}f}"
    except Exception:
        return "—"


def _fmt_pct(x: float | None, digits: int = 2) -> str:
    if x is None:
        return "—"
    try:
        return f"{float(x):.{digits}f}%"
    except Exception:
        return "—"


def _fmt_money_mcap(x: float | None) -> str:
    if x is None:
        return "—"
    try:
        v = float(x)
    except Exception:
        return "—"
    usd = v * 1_000_000.0 if v < 1_000_000_000 else v
    if usd >= 1_000_000_000_000:
        return f"{usd / 1_000_000_000_000:.2f} T$"
    if usd >= 1_000_000_000:
        return f"{usd / 1_000_000_000:.2f} B$"
    if usd >= 1_000_000:
        return f"{usd / 1_000_000:.2f} M$"
    return f"{usd:.0f} $"


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _safe_float(x: Any) -> float | None:
    try:
        if x is None:
            return None
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except Exception:
        return None


# ----------------------------
# Technical indicators
# ----------------------------
def _sma(values: list[float], period: int) -> float | None:
    if period <= 0 or len(values) < period:
        return None
    return sum(values[-period:]) / period


def _rsi(closes: list[float], period: int = 14) -> float | None:
    if len(closes) < period + 1:
        return None
    gains = 0.0
    losses = 0.0
    for i in range(-period, 0):
        diff = closes[i] - closes[i - 1]
        if diff >= 0:
            gains += diff
        else:
            losses += -diff
    if losses == 0 and gains == 0:
        return 50.0
    if losses == 0:
        return 100.0
    rs = gains / losses
    return 100.0 - (100.0 / (1.0 + rs))


def _atr(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> float | None:
    if len(closes) < period + 1 or len(highs) != len(lows) or len(lows) != len(closes):
        return None
    trs: list[float] = []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        trs.append(tr)
    if len(trs) < period:
        return None
    return sum(trs[-period:]) / period


# ----------------------------
# Data model
# ----------------------------
@dataclass
class QuantRow:
    symbol: str

    # quote
    last_price: float | None = None
    change_pct: float | None = None

    # valuation + base metrics
    pe_ttm: float | None = None
    pb: float | None = None
    ps_ttm: float | None = None
    dividend_yield: float | None = None
    market_cap: float | None = None
    beta: float | None = None
    eps_ttm: float | None = None
    week52_high: float | None = None
    week52_low: float | None = None

    # quality inputs
    roe_ttm: float | None = None
    roic_ttm: float | None = None
    gross_margin_ttm: float | None = None
    net_margin_ttm: float | None = None
    revenue_growth_3y: float | None = None
    eps_growth_3y: float | None = None
    debt_to_equity: float | None = None

    # valuation interpretation
    peers_pe_avg: float | None = None
    pe_5y_avg: float | None = None
    pe_5y_std: float | None = None
    pe_zscore: float | None = None
    peg: float | None = None
    valuation_label: str = "—"

    # technicals
    rsi14: float | None = None
    sma50: float | None = None
    sma200: float | None = None
    atr14: float | None = None
    trend_label: str = "—"
    cross_label: str = "—"
    dist_52w_high_pct: float | None = None

    # quality score
    quality_score: int | None = None
    quality_profitability: str = "—"
    quality_growth: str = "—"
    quality_leverage: str = "—"


class QuantAnalysisWidget(QFrame):
    """
    Big Wrapper (no list scroll):
      - shows ONE selected symbol at a time (full analysis)
      - top symbol selector to switch between favorites
    """
    error = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Panel")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._api_key = (os.getenv("FINNHUB_API_KEY") or "").strip()
        self._net = QNetworkAccessManager(self)

        self._symbols: list[str] = []
        self._rows: dict[str, QuantRow] = {}
        self._pending: dict[str, int] = {}

        self._selected: str | None = None

        # debounce refresh
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(250)
        self._debounce.timeout.connect(self.refresh_now)

        # caches
        self._cache_peers: dict[str, tuple[float, list[str]]] = {}
        self._cache_peer_pe: dict[str, tuple[float, float | None]] = {}

        # ---- UI ----
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)  # slightly bigger than before
        root.setSpacing(12)

        # Header row
        header = QWidget()
        hh = QHBoxLayout(header)
        hh.setContentsMargins(0, 0, 0, 0)
        hh.setSpacing(10)

        title = QLabel("Quantitative Analyse")
        title.setObjectName("PanelTitle")
        title.setWordWrap(False)

        self._status = QLabel("")
        self._status.setObjectName("FinePrint")
        self._status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        hh.addWidget(title, 1, Qt.AlignLeft)
        hh.addWidget(self._status, 0, Qt.AlignRight)

        # Symbol selector bar
        self._symbar = QWidget()
        sb = QHBoxLayout(self._symbar)
        sb.setContentsMargins(0, 0, 0, 0)
        sb.setSpacing(8)

        self._sym_buttons: dict[str, QPushButton] = {}

        # Content card (one symbol)
        self._content = QFrame()
        self._content.setObjectName("Card")
        self._content.setAttribute(Qt.WA_StyledBackground, True)
        self._content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(16, 14, 16, 14)
        self._content_layout.setSpacing(12)

        root.addWidget(header, 0)
        root.addWidget(self._symbar, 0)
        root.addWidget(self._content, 1)

        self._render_empty()

    # -------------------------
    # Public API
    # -------------------------
    def set_symbols(self, symbols: list[str] | None) -> None:
        syms: list[str] = []
        for s in (symbols or []):
            s = (s or "").strip().upper()
            if s and s not in syms:
                syms.append(s)
        self._symbols = syms[:6]

        # select first if needed
        if self._selected not in self._symbols:
            self._selected = self._symbols[0] if self._symbols else None

        # keep rows only for existing
        self._rows = {k: v for k, v in self._rows.items() if k in self._symbols}

        self._rebuild_symbar()
        self._render_selected()
        self._debounce.start()

    def refresh_now(self) -> None:
        if not self._symbols:
            self._status.setText("Keine Favoriten ausgewählt.")
            return
        if not self._api_key:
            self._status.setText("FINNHUB_API_KEY fehlt (ENV).")
            self.error.emit("FINNHUB_API_KEY fehlt (ENV).")
            return

        self._status.setText("Lade…")
        for sym in self._symbols:
            if sym not in self._rows:
                self._rows[sym] = QuantRow(symbol=sym)
            self._fetch_symbol(sym)

    # -------------------------
    # UI: selector bar
    # -------------------------
    def _rebuild_symbar(self) -> None:
        layout = self._symbar.layout()
        if layout is None:
            return

        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._sym_buttons.clear()

        if not self._symbols:
            self._symbar.setVisible(False)
            return

        self._symbar.setVisible(True)

        for sym in self._symbols:
            btn = QPushButton(sym)
            # Use existing QSS buttons if present; fallback is ok
            btn.setObjectName("Ghost" if sym != self._selected else "Primary")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _=False, s=sym: self._select_symbol(s))
            btn.setMinimumHeight(36)
            self._sym_buttons[sym] = btn
            layout.addWidget(btn, 0)

        layout.addStretch(1)

    def _select_symbol(self, sym: str) -> None:
        if sym not in self._symbols:
            return
        self._selected = sym
        # update styles quickly
        for s, b in self._sym_buttons.items():
            b.setObjectName("Primary" if s == sym else "Ghost")
            b.style().unpolish(b)
            b.style().polish(b)
        self._render_selected()

    # -------------------------
    # Networking
    # -------------------------
    def _fetch_symbol(self, symbol: str) -> None:
        # quote + metric + peers + candles
        self._pending[symbol] = self._pending.get(symbol, 0) + 4

        self._get_json(
            f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={self._api_key}",
            ("quote", symbol),
        )
        self._get_json(
            f"https://finnhub.io/api/v1/stock/metric?symbol={symbol}&metric=all&token={self._api_key}",
            ("metric", symbol),
        )
        self._get_json(
            f"https://finnhub.io/api/v1/stock/peers?symbol={symbol}&token={self._api_key}",
            ("peers", symbol),
        )

        now = int(time.time())
        frm = now - 370 * 24 * 3600
        self._get_json(
            f"https://finnhub.io/api/v1/stock/candle?symbol={symbol}&resolution=D&from={frm}&to={now}&token={self._api_key}",
            ("candles", symbol),
        )

    def _get_json(self, url: str, tag: tuple[str, str]) -> None:
        req = QNetworkRequest(QUrl(url))
        req.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        reply = self._net.get(req)
        reply.finished.connect(lambda r=reply, t=tag: self._on_reply(r, t))

    def _on_reply(self, reply: QNetworkReply, tag: tuple[str, str]) -> None:
        kind, symbol = tag
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                self.error.emit(f"{symbol}: {reply.errorString()}")
                self._dec_pending(symbol)
                return
            data = bytes(reply.readAll()).decode("utf-8", errors="replace").strip()
            payload: Any = json.loads(data) if data else {}
        except Exception as e:
            self.error.emit(f"{symbol}: JSON parse error ({kind}): {e}")
            self._dec_pending(symbol)
            return
        finally:
            reply.deleteLater()

        # peer metric special callback path
        if isinstance(kind, str) and kind.startswith("peer_metric:"):
            peer_sym = kind.split("peer_metric:", 1)[1].strip().upper()
            metric = payload.get("metric", {}) if isinstance(payload, dict) else {}
            pe = _safe_float(metric.get("peTTM"))
            self._cache_peer_pe[peer_sym] = (time.time(), pe)
            self._recalc_peers_avg(symbol)
            self._dec_pending(symbol)
            self._render_selected()
            return

        row = self._rows.get(symbol) or QuantRow(symbol=symbol)
        self._rows[symbol] = row

        if kind == "quote":
            row.last_price = _safe_float(payload.get("c"))
            row.change_pct = _safe_float(payload.get("dp"))

        elif kind == "metric":
            metric = payload.get("metric", {}) if isinstance(payload, dict) else {}
            series = payload.get("series", {}) if isinstance(payload, dict) else {}

            row.pe_ttm = _safe_float(metric.get("peTTM"))
            row.pb = _safe_float(metric.get("pbAnnual"))
            row.ps_ttm = _safe_float(metric.get("psTTM"))
            row.dividend_yield = _safe_float(metric.get("dividendYieldIndicatedAnnual"))
            row.market_cap = _safe_float(metric.get("marketCapitalization"))
            row.beta = _safe_float(metric.get("beta"))
            row.eps_ttm = _safe_float(metric.get("epsTTM"))
            row.week52_high = _safe_float(metric.get("52WeekHigh"))
            row.week52_low = _safe_float(metric.get("52WeekLow"))

            row.roe_ttm = _safe_float(metric.get("roeTTM") or metric.get("roeAnnual"))
            row.roic_ttm = _safe_float(metric.get("roicTTM") or metric.get("roicAnnual"))
            row.gross_margin_ttm = _safe_float(metric.get("grossMarginTTM") or metric.get("grossMarginAnnual"))
            row.net_margin_ttm = _safe_float(metric.get("netMarginTTM") or metric.get("netMarginAnnual"))
            row.revenue_growth_3y = _safe_float(metric.get("revenueGrowth3Y") or metric.get("revenueGrowthAnnual"))
            row.eps_growth_3y = _safe_float(metric.get("epsGrowth3Y") or metric.get("epsGrowthAnnual"))
            row.debt_to_equity = _safe_float(metric.get("debtToEquityAnnual") or metric.get("debtToEquityTTM"))

            # 5Y PE stats best-effort
            pe_vals = self._extract_pe_series(series)
            if pe_vals:
                last5 = pe_vals[-5:] if len(pe_vals) >= 5 else pe_vals
                mean = sum(last5) / len(last5)
                var = sum((x - mean) ** 2 for x in last5) / max(1, (len(last5) - 1))
                std = math.sqrt(var) if var > 0 else 0.0
                row.pe_5y_avg = mean
                row.pe_5y_std = std if std > 0 else None
                row.pe_zscore = (row.pe_ttm - mean) / std if row.pe_ttm is not None and std > 0 else None
            else:
                row.pe_5y_avg = None
                row.pe_5y_std = None
                row.pe_zscore = None

            # PEG
            if row.pe_ttm is not None and row.eps_growth_3y not in (None, 0):
                row.peg = row.pe_ttm / row.eps_growth_3y
            else:
                row.peg = None

            self._compute_quality(row)
            self._compute_valuation_label(row)

        elif kind == "peers":
            peers = payload if isinstance(payload, list) else []
            peers = [str(p).strip().upper() for p in peers if str(p).strip()]
            peers = [p for p in peers if p != symbol][:8]
            self._compute_peers_avg_pe(symbol, peers)

        elif kind == "candles":
            if not isinstance(payload, dict) or payload.get("s") != "ok":
                self._compute_technicals(symbol, None)
            else:
                self._compute_technicals(symbol, payload)

        self._dec_pending(symbol)
        self._render_selected()

    def _dec_pending(self, symbol: str) -> None:
        self._pending[symbol] = max(0, self._pending.get(symbol, 1) - 1)
        total = sum(self._pending.values()) if self._pending else 0
        self._status.setText("Aktualisiert." if total <= 0 else f"Lade… ({total})")

    # -------------------------
    # Valuation series extraction (best-effort)
    # -------------------------
    def _extract_pe_series(self, series: Any) -> list[float]:
        if not isinstance(series, dict):
            return []
        candidates = []
        for k, v in series.items():
            if isinstance(k, str) and "pe" in k.lower():
                candidates.append(v)
        if "annual" in series and isinstance(series["annual"], dict):
            for k, v in series["annual"].items():
                if isinstance(k, str) and "pe" in k.lower():
                    candidates.append(v)

        def pull(obj: Any) -> list[float]:
            vals: list[float] = []
            if isinstance(obj, dict):
                for key in ("v", "value", "values"):
                    if key in obj and isinstance(obj[key], list):
                        for x in obj[key]:
                            fx = _safe_float(x)
                            if fx is not None and fx > 0:
                                vals.append(fx)
                        return vals
                for _, vv in obj.items():
                    fx = _safe_float(vv)
                    if fx is not None and fx > 0:
                        vals.append(fx)
                return vals
            if isinstance(obj, list):
                for x in obj:
                    fx = _safe_float(x)
                    if fx is not None and fx > 0:
                        vals.append(fx)
            return vals

        for v in candidates:
            out = pull(v)
            if out:
                return out
        return []

    # -------------------------
    # Peers avg PE (industry proxy)
    # -------------------------
    def _compute_peers_avg_pe(self, symbol: str, peers: list[str]) -> None:
        row = self._rows.get(symbol)
        if row is None:
            return
        if not peers:
            row.peers_pe_avg = None
            self._compute_valuation_label(row)
            return

        self._cache_peers[symbol] = (time.time(), peers)

        now = time.time()
        need = []
        for p in peers[:8]:
            cached = self._cache_peer_pe.get(p)
            if cached and (now - cached[0]) < 30 * 60:
                continue
            need.append(p)

        to_fetch = need[:6]
        if to_fetch:
            self._pending[symbol] = self._pending.get(symbol, 0) + len(to_fetch)

        for peer_sym in to_fetch:
            self._get_json(
                f"https://finnhub.io/api/v1/stock/metric?symbol={peer_sym}&metric=all&token={self._api_key}",
                (f"peer_metric:{peer_sym}", symbol),
            )

        self._recalc_peers_avg(symbol)

    def _recalc_peers_avg(self, symbol: str) -> None:
        row = self._rows.get(symbol)
        if row is None:
            return
        entry = self._cache_peers.get(symbol)
        if not entry:
            row.peers_pe_avg = None
            return
        peers = entry[1]
        now = time.time()
        vals: list[float] = []
        for p in peers:
            cached = self._cache_peer_pe.get(p)
            if cached and (now - cached[0]) < 30 * 60:
                pe = cached[1]
                if pe is not None and pe > 0:
                    vals.append(pe)
        row.peers_pe_avg = (sum(vals) / len(vals)) if vals else None
        self._compute_valuation_label(row)

    def _compute_valuation_label(self, row: QuantRow) -> None:
        z = row.pe_zscore
        if z is None:
            row.valuation_label = "—"
            return
        if z >= 1.5:
            row.valuation_label = f"deutlich überbewertet (+{_fmt_num(z,1)}σ)"
        elif z >= 0.6:
            row.valuation_label = f"leicht überbewertet (+{_fmt_num(z,1)}σ)"
        elif z <= -1.5:
            row.valuation_label = f"deutlich unterbewertet ({_fmt_num(z,1)}σ)"
        elif z <= -0.6:
            row.valuation_label = f"leicht unterbewertet ({_fmt_num(z,1)}σ)"
        else:
            row.valuation_label = f"fair ({_fmt_num(z,1)}σ)"

    # -------------------------
    # Quality score
    # -------------------------
    def _compute_quality(self, row: QuantRow) -> None:
        prof_scores: list[float] = []
        if row.roe_ttm is not None:
            prof_scores.append(_clamp((row.roe_ttm / 35.0) * 100.0, 0, 100))
        if row.roic_ttm is not None:
            prof_scores.append(_clamp((row.roic_ttm / 25.0) * 100.0, 0, 100))
        if row.gross_margin_ttm is not None:
            prof_scores.append(_clamp((row.gross_margin_ttm / 60.0) * 100.0, 0, 100))
        if row.net_margin_ttm is not None:
            prof_scores.append(_clamp((row.net_margin_ttm / 30.0) * 100.0, 0, 100))
        profitability = sum(prof_scores) / len(prof_scores) if prof_scores else None

        growth_scores: list[float] = []
        if row.revenue_growth_3y is not None:
            growth_scores.append(_clamp((row.revenue_growth_3y / 25.0) * 100.0, 0, 100))
        if row.eps_growth_3y is not None:
            growth_scores.append(_clamp((row.eps_growth_3y / 30.0) * 100.0, 0, 100))
        growth = sum(growth_scores) / len(growth_scores) if growth_scores else None

        leverage = None
        if row.debt_to_equity is not None:
            dte = row.debt_to_equity
            leverage = _clamp(100.0 - (dte / 4.0) * 100.0, 0, 100)

        parts: list[tuple[float, float]] = []
        if profitability is not None:
            parts.append((profitability, 0.45))
        if growth is not None:
            parts.append((growth, 0.35))
        if leverage is not None:
            parts.append((leverage, 0.20))

        if not parts:
            row.quality_score = None
            row.quality_profitability = "—"
            row.quality_growth = "—"
            row.quality_leverage = "—"
            return

        total_w = sum(w for _, w in parts)
        score = sum(s * w for s, w in parts) / max(1e-9, total_w)
        row.quality_score = int(round(score))

        def bucket(v: float | None, kind: str) -> str:
            if v is None:
                return "—"
            if v >= 75:
                return "Hoch" if kind != "lev" else "Niedrig"
            if v >= 50:
                return "Moderat"
            return "Schwach" if kind != "lev" else "Hoch"

        row.quality_profitability = bucket(profitability, "prof")
        row.quality_growth = bucket(growth, "growth")
        row.quality_leverage = bucket(leverage, "lev")

    # -------------------------
    # Technische Indikatoren
    # -------------------------
    def _compute_technicals(self, symbol: str, payload: dict[str, Any] | None) -> None:
        row = self._rows.get(symbol)
        if row is None:
            return
        if not payload:
            row.rsi14 = None
            row.sma50 = None
            row.sma200 = None
            row.atr14 = None
            row.trend_label = "—"
            row.cross_label = "—"
            row.dist_52w_high_pct = None
            return

        closes = payload.get("c") or []
        highs = payload.get("h") or []
        lows = payload.get("l") or []
        try:
            closes_f = [float(x) for x in closes]
            highs_f = [float(x) for x in highs]
            lows_f = [float(x) for x in lows]
        except Exception:
            return

        if len(closes_f) < 60:
            return

        row.rsi14 = _rsi(closes_f, 14)
        row.sma50 = _sma(closes_f, 50)
        row.sma200 = _sma(closes_f, 200)
        row.atr14 = _atr(highs_f, lows_f, closes_f, 14)

        last = closes_f[-1]
        if row.sma200 is not None:
            row.trend_label = "über 200 MA" if last >= row.sma200 else "unter 200 MA"
        else:
            row.trend_label = "—"

        if row.sma50 is not None and row.sma200 is not None:
            if row.sma50 > row.sma200:
                row.cross_label = "Golden Cross"
            elif row.sma50 < row.sma200:
                row.cross_label = "Death Cross"
            else:
                row.cross_label = "Neutral"
        else:
            row.cross_label = "—"

        hi_52 = max(closes_f[-252:]) if len(closes_f) >= 252 else max(closes_f)
        row.dist_52w_high_pct = (last / hi_52 - 1.0) * 100.0 if hi_52 > 0 else None

    # -------------------------
    # Render selected symbol
    # -------------------------
    def _clear_content(self) -> None:
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _render_empty(self) -> None:
        self._clear_content()
        lbl = QLabel("Wähle Favoriten (UserPage) – dann erscheint hier die komplette Aktienanalyse.")
        lbl.setObjectName("Placeholder")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        self._content_layout.addStretch(1)
        self._content_layout.addWidget(lbl, 0, Qt.AlignCenter)
        self._content_layout.addStretch(1)

    def _render_selected(self) -> None:
        if not self._symbols or not self._selected:
            self._render_empty()
            return

        row = self._rows.get(self._selected) or QuantRow(symbol=self._selected)
        self._rows[self._selected] = row

        self._clear_content()

        # Header: symbol + price
        header = QWidget()
        hh = QHBoxLayout(header)
        hh.setContentsMargins(0, 0, 0, 0)
        hh.setSpacing(10)

        sym = QLabel(row.symbol)
        sym.setObjectName("PanelTitle")

        px = QLabel(f"{_fmt_num(row.last_price, 2)}   ({_fmt_pct(row.change_pct, 2)})")
        px.setObjectName("FinePrint")
        px.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        hh.addWidget(sym, 1)
        hh.addWidget(px, 0)
        self._content_layout.addWidget(header)

        # --- Bewertungs-Interpretation ---
        self._content_layout.addWidget(self._section("Bewertungs-Interpretation"))
        self._content_layout.addWidget(self._kv_row(
            ("KGV (TTM)", _fmt_num(row.pe_ttm, 2)),
            ("Peers Ø", _fmt_num(row.peers_pe_avg, 2)),
            ("5Y Ø", _fmt_num(row.pe_5y_avg, 2)),
        ))
        self._content_layout.addWidget(self._kv_row(
            ("PEG", _fmt_num(row.peg, 2)),
            ("Z-Score", _fmt_num(row.pe_zscore, 2) if row.pe_zscore is not None else "—"),
            ("Bewertung", row.valuation_label),
        ))

        # --- Fundamentale Qualität ---
        self._content_layout.addWidget(self._section("Fundamentale Qualität"))
        qs = f"{row.quality_score} / 100" if row.quality_score is not None else "—"
        self._content_layout.addWidget(self._kv_row(
            ("Quality Score", qs),
            ("Profitabilität", row.quality_profitability),
            ("Wachstum", row.quality_growth),
        ))
        self._content_layout.addWidget(self._kv_row(
            ("Verschuldung", row.quality_leverage),
            ("ROE", _fmt_pct(row.roe_ttm, 2)),
            ("ROIC", _fmt_pct(row.roic_ttm, 2)),
        ))
        self._content_layout.addWidget(self._kv_row(
            ("Gross Margin", _fmt_pct(row.gross_margin_ttm, 2)),
            ("Net Margin", _fmt_pct(row.net_margin_ttm, 2)),
            ("Debt/Equity", _fmt_num(row.debt_to_equity, 2)),
        ))
        self._content_layout.addWidget(self._kv_row(
            ("Revenue Growth 3Y", _fmt_pct(row.revenue_growth_3y, 2)),
            ("EPS Growth 3Y", _fmt_pct(row.eps_growth_3y, 2)),
            ("Market Cap", _fmt_money_mcap(row.market_cap)),
        ))

        # --- Momentum & Technische Indikatoren ---
        self._content_layout.addWidget(self._section("Momentum & Technische Indikatoren"))
        self._content_layout.addWidget(self._kv_row(
            ("RSI(14)", _fmt_num(row.rsi14, 1)),
            ("Trend", row.trend_label),
            ("Cross", row.cross_label),
        ))
        self._content_layout.addWidget(self._kv_row(
            ("SMA50", _fmt_num(row.sma50, 2)),
            ("SMA200", _fmt_num(row.sma200, 2)),
            ("ATR(14)", _fmt_num(row.atr14, 2)),
        ))
        self._content_layout.addWidget(self._kv_row(
            ("52W Dist.", _fmt_pct(row.dist_52w_high_pct, 2)),
            ("Beta", _fmt_num(row.beta, 2)),
            ("52W High", _fmt_num(row.week52_high, 2)),
        ))

        # keep it “full” without forcing scroll: add stretch at end
        self._content_layout.addStretch(1)

    # -------------------------
    # UI small helpers
    # -------------------------
    def _section(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("FinePrint")
        lbl.setWordWrap(False)
        return lbl

    def _kv_row(self, a: tuple[str, str], b: tuple[str, str], c: tuple[str, str]) -> QWidget:
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(10)
        h.addWidget(self._kv(a[0], a[1]), 1)
        h.addWidget(self._kv(b[0], b[1]), 1)
        h.addWidget(self._kv(c[0], c[1]), 1)
        return row

    def _kv(self, k: str, v_: str) -> QWidget:
        w = QWidget()
        vv = QVBoxLayout(w)
        vv.setContentsMargins(0, 0, 0, 0)
        vv.setSpacing(2)

        lk = QLabel(k)
        lk.setObjectName("FinePrint")
        lk.setWordWrap(False)

        lv = QLabel(v_)
        lv.setObjectName("PanelTitle")
        lv.setWordWrap(False)

        vv.addWidget(lk)
        vv.addWidget(lv)
        return w