# gui/widgets/portfolio_risk_heatmap.py
from __future__ import annotations

import math
import os
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import Qt, QObject, Signal, QThread, QTimer, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout,
    QSizePolicy, QScrollArea, QPushButton, QButtonGroup
)


# --------------------------
# Model
# --------------------------
@dataclass(frozen=True)
class RiskHeatmapItem:
    asset_id: int
    symbol: str
    name: str
    category: str
    volatility_daily: float
    volatility_annual: float
    observations: int


# --------------------------
# Helpers
# --------------------------
def _norm_category(cat: str) -> str:
    c = (cat or "").strip().lower()
    if not c:
        return "stock"
    if c.startswith("etf"):
        return "etf"
    if c in {"stock", "stocks", "equity", "shares"}:
        return "stock"
    if c in {"crypto", "cryptocurrency", "coin", "coins"}:
        return "crypto"
    if c in {"commodity", "commodities", "com"}:
        return "commodity"
    if c in {"index", "indices"}:
        return "index"
    return c


def _clamp(x: float, lo: float, hi: float) -> float:
    try:
        return max(lo, min(hi, float(x)))
    except Exception:
        return lo


def _heat_rgb_for_vol(vol: float) -> tuple[int, int, int]:
    pct = float(vol) * 100.0
    if pct < 10:
        return 74, 222, 128
    if pct < 25:
        return 250, 204, 21
    if pct < 50:
        return 251, 146, 60
    return 251, 113, 133


def _absolute_heat_score(vol_annual: float) -> int:
    pct = float(vol_annual) * 100.0

    if pct <= 0:
        return 0
    if pct < 5:
        return 10
    if pct < 10:
        return 20
    if pct < 15:
        return 30
    if pct < 20:
        return 40
    if pct < 25:
        return 50
    if pct < 35:
        return 65
    if pct < 50:
        return 80
    if pct < 70:
        return 90
    return 100


def _absolute_bar_ratio(vol_annual: float) -> float:
    return _clamp(float(vol_annual) / 0.80, 0.02, 1.0)


# --------------------------
# Worker
# --------------------------
class PortfolioRiskHeatmapWorker(QObject):
    finished = Signal(list)
    failed = Signal(str)

    def __init__(self, user_id: int, lookback_days: int | None = 90, parent: QObject | None = None):
        super().__init__(parent)
        self._user_id = int(user_id)
        self._lookback_days = None if lookback_days is None else max(30, int(lookback_days))

    def run(self) -> None:
        try:
            import psycopg2
        except Exception as e:
            self.failed.emit(f"psycopg2 fehlt: {e}")
            return

        host = os.getenv("POSTGRES_HOST", "127.0.0.1")
        port = int(os.getenv("POSTGRES_PORT", "5432"))
        db = os.getenv("POSTGRES_DB", "stocks")
        user = os.getenv("POSTGRES_USER", "stock_user")
        pw = os.getenv("POSTGRES_PASSWORD", "stock_pass")

        if self._lookback_days is None:
            sql = """
            WITH user_assets AS (
                SELECT DISTINCT i.asset_id
                FROM stocks.investments i
                WHERE i.user_id = %s
            ),
            daily_prices AS (
                SELECT DISTINCT ON (p.asset_id, p.date::date)
                    p.asset_id,
                    p.date::date AS d,
                    p.close::float8 AS close
                FROM stocks.prices p
                JOIN user_assets ua
                    ON ua.asset_id = p.asset_id
                WHERE p.close IS NOT NULL
                  AND p.close::float8 > 0
                ORDER BY
                    p.asset_id,
                    p.date::date,
                    COALESCE(p.source, '') ASC,
                    p.date DESC
            )
            SELECT
                a.asset_id,
                a.canonical_symbol AS symbol,
                COALESCE(a.name, a.canonical_symbol) AS name,
                LOWER(COALESCE(a.category, 'stock')) AS category,
                dp.d,
                dp.close
            FROM daily_prices dp
            JOIN stocks.assets a
                ON a.asset_id = dp.asset_id
            ORDER BY a.asset_id ASC, dp.d ASC;
            """
            params = [self._user_id]
        else:
            sql = """
            WITH user_assets AS (
                SELECT DISTINCT i.asset_id
                FROM stocks.investments i
                WHERE i.user_id = %s
            ),
            daily_prices AS (
                SELECT DISTINCT ON (p.asset_id, p.date::date)
                    p.asset_id,
                    p.date::date AS d,
                    p.close::float8 AS close
                FROM stocks.prices p
                JOIN user_assets ua
                    ON ua.asset_id = p.asset_id
                WHERE p.date >= CURRENT_DATE - (%s * INTERVAL '1 day')
                  AND p.close IS NOT NULL
                  AND p.close::float8 > 0
                ORDER BY
                    p.asset_id,
                    p.date::date,
                    COALESCE(p.source, '') ASC,
                    p.date DESC
            )
            SELECT
                a.asset_id,
                a.canonical_symbol AS symbol,
                COALESCE(a.name, a.canonical_symbol) AS name,
                LOWER(COALESCE(a.category, 'stock')) AS category,
                dp.d,
                dp.close
            FROM daily_prices dp
            JOIN stocks.assets a
                ON a.asset_id = dp.asset_id
            ORDER BY a.asset_id ASC, dp.d ASC;
            """
            params = [self._user_id, self._lookback_days + 14]

        try:
            conn = psycopg2.connect(host=host, port=port, dbname=db, user=user, password=pw)
            try:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    rows = cur.fetchall()
            finally:
                conn.close()
        except Exception as e:
            self.failed.emit(str(e)[:240])
            return

        if not rows:
            self.finished.emit([])
            return

        grouped: dict[int, dict[str, Any]] = {}

        for r in rows:
            try:
                asset_id = int(r[0])
                symbol = str(r[1] or "").strip().upper()
                name = str(r[2] or "").strip() or symbol
                category = _norm_category(str(r[3] or "stock"))
                d = r[4]
                close = float(r[5] or 0.0)

                if close <= 0:
                    continue

                if asset_id not in grouped:
                    grouped[asset_id] = {
                        "asset_id": asset_id,
                        "symbol": symbol,
                        "name": name,
                        "category": category,
                        "prices": []
                    }

                grouped[asset_id]["prices"].append((d, close))
            except Exception:
                continue

        out: list[RiskHeatmapItem] = []

        for _, payload in grouped.items():
            prices = payload["prices"]
            if len(prices) < 3:
                continue

            category = str(payload["category"])
            returns: list[float] = []
            prev_close = None

            for _, close in prices:
                if prev_close is not None and prev_close > 0 and close > 0:
                    r = (close / prev_close) - 1.0

                    if category in {"stock", "etf", "index", "commodity"}:
                        if -0.35 <= r <= 0.35:
                            returns.append(r)
                    elif category == "crypto":
                        if -0.60 <= r <= 0.60:
                            returns.append(r)
                    else:
                        if -0.40 <= r <= 0.40:
                            returns.append(r)

                prev_close = close

            if self._lookback_days is not None and len(returns) > self._lookback_days:
                returns = returns[-self._lookback_days:]

            n = len(returns)
            if n < 2:
                continue

            mean_r = sum(returns) / n
            var = sum((x - mean_r) ** 2 for x in returns) / (n - 1)
            vol_daily = math.sqrt(max(var, 0.0))
            vol_annual = vol_daily * math.sqrt(252)

            out.append(
                RiskHeatmapItem(
                    asset_id=int(payload["asset_id"]),
                    symbol=str(payload["symbol"]),
                    name=str(payload["name"]),
                    category=str(payload["category"]),
                    volatility_daily=float(vol_daily),
                    volatility_annual=float(vol_annual),
                    observations=int(n),
                )
            )

        out.sort(key=lambda x: x.volatility_annual, reverse=True)
        self.finished.emit(out)


# --------------------------
# Painted heat bar
# --------------------------
class HeatBar(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._ratio: float = 0.0
        self._color = QColor(250, 204, 21)
        self.setMinimumHeight(12)
        self.setMaximumHeight(12)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_value(self, ratio: float, color: QColor) -> None:
        self._ratio = _clamp(ratio, 0.0, 1.0)
        self._color = QColor(color)
        self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        r = self.rect().adjusted(0, 1, 0, -1)
        rr = 6.0

        track = QColor(255, 255, 255, 10)
        track_border = QColor(39, 48, 59, 110)

        p.setPen(QPen(track_border, 1))
        p.setBrush(QBrush(track))
        p.drawRoundedRect(QRectF(r), rr, rr)

        fill_w = max(0.0, r.width() * self._ratio)
        if fill_w > 0:
            fill_rect = QRectF(r.x(), r.y(), fill_w, r.height())
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(self._color))
            p.drawRoundedRect(fill_rect, rr, rr)

        p.end()


# --------------------------
# UI Row
# --------------------------
class RiskHeatRow(QFrame):
    def __init__(self, item: RiskHeatmapItem, parent: QWidget | None = None):
        super().__init__(parent)

        r, g, b = _heat_rgb_for_vol(item.volatility_annual)
        bg = f"rgba({r},{g},{b},18)"

        self.setObjectName("RiskHeatRow")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(84)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(f"""
            QFrame#RiskHeatRow {{
                background: {bg};
                border: 1px solid rgba(39,48,59,120);
                border-radius: 18px;
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(8)

        top = QWidget()
        th = QHBoxLayout(top)
        th.setContentsMargins(0, 0, 0, 0)
        th.setSpacing(10)

        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.setSpacing(3)

        title = QLabel(item.symbol)
        title.setObjectName("InvTitle")

        meta = QLabel(f"{item.category.upper()} · {item.observations} Returns")
        meta.setObjectName("InvMeta")
        meta.setWordWrap(False)

        lv.addWidget(title)
        lv.addWidget(meta)

        right = QWidget()
        right.setMinimumWidth(92)
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(4)

        value = QLabel(f"{item.volatility_annual * 100:.1f}%")
        value.setObjectName("InvValue")
        value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        heat_score = _absolute_heat_score(item.volatility_annual)
        badge = QLabel(f"Heat {heat_score}")
        badge.setObjectName("InvBadge")
        badge.setAlignment(Qt.AlignCenter)
        badge.setFixedWidth(78)

        rv.addWidget(value, 0, Qt.AlignRight)
        rv.addWidget(badge, 0, Qt.AlignRight)

        th.addWidget(left, 1)
        th.addWidget(right, 0)

        color = QColor(r, g, b, 230)
        ratio = _absolute_bar_ratio(item.volatility_annual)

        bar = HeatBar()
        bar.set_value(ratio, color)

        root.addWidget(top)
        root.addWidget(bar)


# --------------------------
# Widget
# --------------------------
class PortfolioRiskHeatmapWidget(QFrame):
    error = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setObjectName("Panel")
        self.setAttribute(Qt.WA_StyledBackground, True)

        self._user_id: int | None = None
        self._lookback_days: int | None = 90

        self._thread: QThread | None = None
        self._worker: PortfolioRiskHeatmapWorker | None = None
        self._items: list[RiskHeatmapItem] = []

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(180_000)
        self._refresh_timer.timeout.connect(self.refresh)
        self._refresh_timer.start()

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        title = QLabel("Portfolio\nRisiko")
        title.setObjectName("PanelTitle")
        title.setWordWrap(True)
        root.addWidget(title, 0, Qt.AlignLeft)

        controls = QWidget()
        controls.setAttribute(Qt.WA_StyledBackground, True)
        ch = QHBoxLayout(controls)
        ch.setContentsMargins(0, 0, 0, 0)
        ch.setSpacing(8)

        self._chip_group = QButtonGroup(self)
        self._chip_group.setExclusive(True)

        def _mk_chip(text: str, value: int | None, checked: bool = False) -> QPushButton:
            b = QPushButton(text)
            b.setObjectName("Chip")
            b.setCheckable(True)
            b.setChecked(checked)
            b.clicked.connect(lambda: self.set_lookback_days(value))
            self._chip_group.addButton(b)
            return b

        ch.addWidget(_mk_chip("90T", 90, True))
        ch.addWidget(_mk_chip("252T", 252, False))
        ch.addWidget(_mk_chip("MAX", None, False))
        ch.addStretch(1)

        root.addWidget(controls, 0)

        self._meta = QLabel("90 Tage · annualisiert")
        self._meta.setObjectName("FinePrint")
        self._meta.setWordWrap(True)
        root.addWidget(self._meta, 0, Qt.AlignLeft)

        self._status = QLabel("Bitte einloggen")
        self._status.setObjectName("Placeholder")
        self._status.setWordWrap(True)
        self._status.setAlignment(Qt.AlignCenter)
        root.addWidget(self._status, 0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.setFrameShape(QFrame.NoFrame)

        self._content = QWidget()
        self._content.setAttribute(Qt.WA_StyledBackground, True)

        self._rows = QVBoxLayout(self._content)
        self._rows.setContentsMargins(0, 0, 0, 0)
        self._rows.setSpacing(10)
        self._rows.setAlignment(Qt.AlignTop)

        self._scroll.setWidget(self._content)
        root.addWidget(self._scroll, 1)

    def set_user_id(self, user_id: int | None) -> None:
        self._user_id = int(user_id) if user_id is not None else None
        self.refresh()

    def set_lookback_days(self, days: int | None) -> None:
        self._lookback_days = None if days is None else max(30, int(days))
        if self._lookback_days is None:
            self._meta.setText("Max · annualisiert")
        else:
            self._meta.setText(f"{self._lookback_days} Tage · annualisiert")
        self.refresh()

    def refresh(self) -> None:
        if self._user_id is None:
            self._items = []
            self._status.setText("Bitte einloggen")
            self._status.show()
            self._render()
            return

        try:
            if self._thread is not None and self._thread.isRunning():
                return
        except RuntimeError:
            self._thread = None
            self._worker = None

        self._status.setText("Lade Risiko-Daten …")
        self._status.show()

        thread = QThread(self)
        worker = PortfolioRiskHeatmapWorker(
            user_id=int(self._user_id),
            lookback_days=self._lookback_days
        )
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(self._on_finished)
        worker.failed.connect(self._on_failed)

        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)

        def _cleanup():
            try:
                worker.deleteLater()
            except Exception:
                pass
            try:
                thread.deleteLater()
            except Exception:
                pass
            if self._thread is thread:
                self._thread = None
            if self._worker is worker:
                self._worker = None

        thread.finished.connect(_cleanup)

        self._thread = thread
        self._worker = worker
        thread.start()

    def _on_finished(self, items: list) -> None:
        self._items = [x for x in items if isinstance(x, RiskHeatmapItem)]
        if self._items:
            self._status.hide()
        else:
            self._status.setText("Keine Risiko-Daten gefunden.")
            self._status.show()
        self._render()

    def _on_failed(self, msg: str) -> None:
        self._items = []
        self._status.setText(f"Fehler beim Laden: {msg}")
        self._status.show()
        self.error.emit(msg)
        self._render()

    def _clear_rows(self) -> None:
        while self._rows.count():
            item = self._rows.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

    def _render(self) -> None:
        self._clear_rows()

        if not self._items:
            return

        for it in self._items:
            row = RiskHeatRow(item=it)
            self._rows.addWidget(row)

        spacer = QWidget()
        spacer.setFixedHeight(2)
        spacer.setStyleSheet("background: transparent; border: 0px;")
        self._rows.addWidget(spacer)