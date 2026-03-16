from __future__ import annotations

import os
import json
import urllib.parse
import re
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import Optional, Any

from PySide6.QtCore import Qt, Signal, QTimer, QThread, QObject, QUrl, QSize, QDateTime, QMargins, QSettings
from PySide6.QtGui import QDesktopServices, QIcon, QPainter, QColor, QPen

from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout, QSizePolicy, QDialog,
    QScrollArea, QButtonGroup
)

from gui.widgets.segmentedtabs import SegmentedTabs
from gui.utils.guided_tour import GuidedTourOverlay, TourStep

# Optional: QtCharts (Portfolio-Chart)
try:
    from PySide6.QtCharts import QChart, QChartView, QLineSeries, QDateTimeAxis, QValueAxis
    _HAS_QTCHARTS = True
except Exception:
    QChart = QChartView = QLineSeries = QDateTimeAxis = QValueAxis = object  # type: ignore
    _HAS_QTCHARTS = False


# --------------------------
# Theme
# --------------------------
@dataclass(frozen=True)
class Palette:
    bg0: str = "#0F1318"
    bg1: str = "#0F1318"
    bg2: str = "#0F1318"
    line: str = "#27303B"
    line2: str = "#313C4A"
    text0: str = "#E6EAF0"
    text1: str = "#AEB7C2"
    text2: str = "#7E8896"
    accent: str = "#6D929B"
    accent2: str = "#6D929B"


def _qss_url(path: str) -> str:
    p = (path or "").replace("\\", "/")
    return f'url("{p}")' if p else ""


def build_qss(p: Palette, background_image_path: str = "images/Backgroundimage.png") -> str:
    bg_url = _qss_url(background_image_path)

    return f"""
    QWidget {{
        color: {p.text0};
        font-family: -apple-system, "SF Pro Display", "SF Pro Text", "Inter", "Helvetica Neue", "Arial";
        background-color: {p.bg0};
    }}

    #Root {{
        background-color: {p.bg0};
        border-image: {bg_url} 0 0 0 0 stretch stretch;
    }}

    #Card {{
        background: {p.bg1};
        border: 1px solid rgba(39,48,59,170);
        border-radius: 22px;
    }}

    #Shell {{
        background: {p.bg1};
        border: 1px solid rgba(39,48,59,170);
        border-radius: 44px;
    }}

    #Panel {{
        background: {p.bg2};
        border: 1px solid rgba(39,48,59,170);
        border-radius: 22px;
    }}

    #PanelTitle {{
        font-size: 14px;
        font-weight: 900;
        letter-spacing: -0.2px;
        color: {p.text0};
    }}

    #FinePrint {{
        color: rgba(174,183,194,150);
        font-size: 12px;
    }}

    /* ---- Segmented Tabs ---- */
    QFrame#SegmentedTabs {{
        background: rgba(255,255,255,10);
        border: 1px solid rgba(39,48,59,170);
        border-radius: 999px;
        padding: 2px;
    }}

    QFrame#SegmentedIndicator {{
        background: rgba(230,234,240,235);
        border: 1px solid rgba(39,48,59,110);
        border-radius: 999px;
    }}

    QPushButton#SegmentedButton {{
        background: transparent;
        border: 0px;
        padding: 10px 16px;
        border-radius: 999px;
        font-weight: 900;
        color: rgba(230,234,240,170);
    }}

    QPushButton#SegmentedButton[active="true"] {{
        color: rgba(15,19,24,235);
    }}

    QPushButton#Avatar {{
        background: rgba(109,146,155,25);
        border: 1px solid rgba(39,48,59,170);
        border-radius: 22px;
        padding: 0px;
        font-weight: 900;
        color: {p.text0};
    }}
    QPushButton#Avatar:hover {{
        background: rgba(109,146,155,35);
        border: 1px solid rgba(109,146,155,90);
    }}

    QPushButton#CalendarBtn {{
        background: rgba(109,146,155,18);
        border: 1px solid rgba(39,48,59,170);
        border-radius: 22px;
        padding: 0px;
        font-weight: 900;
        color: rgba(230,234,240,210);
    }}
    QPushButton#CalendarBtn:hover {{
        background: rgba(109,146,155,30);
        border: 1px solid rgba(109,146,155,90);
    }}

    /* Investment circle button (invest.png) */
    QPushButton#InvestBtn {{
        background: rgba(109,146,155,18);
        border: 1px solid rgba(39,48,59,170);
        border-radius: 22px;
        padding: 0px;
    }}
    QPushButton#InvestBtn:hover {{
        background: rgba(109,146,155,30);
        border: 1px solid rgba(109,146,155,90);
    }}

    /* Small filter chips */
    QPushButton#Chip {{
        background: rgba(255,255,255,6);
        border: 1px solid rgba(39,48,59,170);
        border-radius: 999px;
        padding: 6px 10px;
        font-weight: 850;
        color: rgba(230,234,240,190);
        font-size: 11px;
    }}
    QPushButton#Chip:checked {{
        background: rgba(109,146,155,35);
        border: 1px solid rgba(109,146,155,110);
        color: rgba(230,234,240,235);
    }}

    /* News */
    #NewsCard {{
        background: transparent;
        border: 0px;
        border-radius: 12px;
    }}
    #NewsCard:hover {{
        background: rgba(109,146,155,18);
    }}
    #NewsTitle {{
        color: rgba(230,234,240,210);
        font-size: 13px;
        font-weight: 850;
    }}
    #NewsMeta {{
        color: rgba(174,183,194,150);
        font-size: 11px;
    }}

    /* ScrollArea */
    QScrollArea {{
        border: 0px;
        background: transparent;
    }}
    QScrollBar:vertical {{
        border: 0px;
        background: transparent;
        width: 10px;
        margin: 6px 2px 6px 2px;
    }}
    QScrollBar::handle:vertical {{
        background: rgba(230,234,240,60);
        border-radius: 5px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: rgba(230,234,240,90);
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
        width: 0px;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
    }}

    #Placeholder {{
        color: rgba(174,183,194,180);
        font-size: 13px;
        padding: 2px 0px;
    }}

    /* -----------------------------
       Investments (CLEANER LOOK)
       ----------------------------- */
    QFrame#InvPanel {{
        background: rgba(255,255,255,4);
        border: 1px solid rgba(39,48,59,130);
        border-radius: 18px;
    }}

    QFrame#InvRow {{
        background: rgba(255,255,255,4);
        border: 1px solid rgba(39,48,59,120);
        border-radius: 16px;
    }}
    QFrame#InvRow:hover {{
        background: rgba(109,146,155,12);
        border: 1px solid rgba(109,146,155,80);
    }}

    QLabel#InvTitle {{
        font-weight: 950;
        font-size: 12px;
        color: rgba(230,234,240,235);
    }}

    QLabel#InvMeta {{
        font-size: 10.5px;
        color: rgba(174,183,194,155);
    }}

    QLabel#InvValue {{
        font-weight: 950;
        font-size: 12px;
        color: rgba(230,234,240,235);
    }}

    QLabel#InvBadge {{
        background: rgba(109,146,155,18);
        border: 1px solid rgba(109,146,155,55);
        border-radius: 999px;
        padding: 6px 10px;
        font-weight: 950;
        font-size: 11px;
        color: rgba(230,234,240,220);
    }}

    /* Chart header labels */
    QLabel#ChartValue {{
        font-size: 20px;
        font-weight: 950;
        letter-spacing: -0.3px;
        color: rgba(230,234,240,235);
    }}
    QLabel#ChartPct {{
        font-size: 12px;
        font-weight: 900;
        color: rgba(174,183,194,200);
    }}
    """


# --------------------------
# Models
# --------------------------
@dataclass(frozen=True)
class NewsItem:
    title: str
    source: str
    published_ts: int
    url: str
    tag: str


@dataclass(frozen=True)
class MoverItem:
    symbol: str
    name: str
    change_pct: float
    price: float


@dataclass(frozen=True)
class FavQuoteItem:
    symbol: str
    name: str
    change_pct: float
    price: float


@dataclass(frozen=True)
class InvestmentSummaryItem:
    asset_id: int
    symbol: str
    name: str
    category: str
    quantity: float
    last_price: float
    value: float
    pct: float


@dataclass(frozen=True)
class PortfolioPoint:
    d: date
    value: float
    missing_assets: int = 0


def _safe_int(x, default=0) -> int:
    try:
        return int(x)
    except Exception:
        return default


def _fmt_time(ts: int) -> str:
    try:
        return datetime.fromtimestamp(ts).strftime("%H:%M")
    except Exception:
        return ""


def _fmt_num(x: float, decimals: int = 2) -> str:
    try:
        return f"{float(x):.{decimals}f}"
    except Exception:
        return "0.00"


def _fmt_eur(x: float, decimals: int = 2) -> str:
    try:
        v = float(x)
    except Exception:
        v = 0.0
    s = f"{v:,.{decimals}f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} €"


def _fmt_qty(x: float) -> str:
    try:
        xx = float(x)
        if abs(xx) >= 1000:
            return f"{xx:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        if abs(xx) >= 10:
            return f"{xx:.2f}"
        return f"{xx:.6f}".rstrip("0").rstrip(".")
    except Exception:
        return "0"


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


_PCT_RE = re.compile(r"[-+]?\d+(?:[.,]\d+)?")


def _parse_change_pct(v: Any) -> float:
    if v is None:
        return 0.0

    if isinstance(v, (int, float)):
        try:
            return float(v)
        except Exception:
            return 0.0

    s = str(v).strip()
    if not s:
        return 0.0

    s = s.replace("(", "").replace(")", "").replace("%", "").strip()

    m = _PCT_RE.search(s)
    if not m:
        return 0.0

    num = m.group(0).replace(",", ".")
    try:
        return float(num)
    except Exception:
        return 0.0


# --------------------------
# External link dialog
# --------------------------
class ExternalLinkDialog(QDialog):
    def __init__(
        self,
        url: str,
        palette: Palette,
        background_path: str = "images/Backgroundimage.png",
        parent: QWidget | None = None
    ):
        super().__init__(parent)

        self._url = (url or "").strip()

        self.setWindowTitle("Externe Ressource öffnen")
        self.setModal(True)

        self.setObjectName("Root")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)

        self.setStyleSheet(build_qss(palette, background_path))
        self.setFixedSize(560, 240)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        card = QFrame()
        card.setObjectName("Card")
        card.setAttribute(Qt.WA_StyledBackground, True)

        cv = QVBoxLayout(card)
        cv.setContentsMargins(18, 16, 18, 16)
        cv.setSpacing(10)

        title = QLabel("Externe Ressource öffnen?")
        title.setObjectName("SectionTitle")
        title.setWordWrap(True)

        hint = QLabel(
            "Du bist dabei, einen Link im Standard-Browser zu öffnen.\n"
            "Öffne nur Quellen, denen du vertraust."
        )
        hint.setObjectName("FinePrint")
        hint.setWordWrap(True)

        url_label = QLabel(self._url)
        url_label.setObjectName("UrlBox")
        url_label.setWordWrap(True)
        url_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        cv.addWidget(title)
        cv.addWidget(hint)
        cv.addWidget(url_label)

        btn_row = QWidget()
        bh = QHBoxLayout(btn_row)
        bh.setContentsMargins(0, 0, 0, 0)
        bh.setSpacing(10)

        cancel = QPushButton("Abbrechen")
        cancel.setObjectName("Ghost")
        cancel.clicked.connect(self.reject)

        open_btn = QPushButton("Öffnen")
        open_btn.setObjectName("Primary")
        open_btn.clicked.connect(self.accept)

        bh.addStretch(1)
        bh.addWidget(cancel)
        bh.addWidget(open_btn)

        root.addWidget(card)
        root.addWidget(btn_row)

    @property
    def url(self) -> str:
        return self._url


class ClickableNewsCard(QFrame):
    clicked = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("NewsCard")
        self.setCursor(Qt.PointingHandCursor)
        self._url: str = ""

    def set_url(self, url: str) -> None:
        self._url = (url or "").strip()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton and self._url:
            self.clicked.emit(self._url)
        super().mousePressEvent(event)


# --------------------------
# Workers
# --------------------------
class NewsFetcherWorker(QObject):
    finished = Signal(list)
    failed = Signal(str)

    def __init__(self, finnhub_key: str, gdelt_query: str, parent: QObject | None = None):
        super().__init__(parent)
        self._finnhub_key = (finnhub_key or "").strip()
        self._gdelt_query = gdelt_query

    def run(self) -> None:
        items: list[NewsItem] = []
        errors: list[str] = []

        try:
            items.extend(self._fetch_finnhub_general())
        except Exception as e:
            errors.append(f"Finnhub: {e}")

        try:
            items.extend(self._fetch_gdelt())
        except Exception as e:
            errors.append(f"GDELT: {e}")

        seen = set()
        deduped: list[NewsItem] = []
        for it in sorted(items, key=lambda x: x.published_ts, reverse=True):
            if not it.url:
                continue
            if it.url in seen:
                continue
            seen.add(it.url)
            deduped.append(it)

        if not deduped and errors:
            self.failed.emit(" | ".join(errors)[:220])
            return

        self.finished.emit(deduped)

    def _read_json(self, url: str, headers: Optional[dict] = None, timeout: int = 10):
        import urllib.request
        import urllib.error
        import ssl
        import certifi

        req = urllib.request.Request(url, headers=headers or {}, method="GET")
        ctx = ssl.create_default_context(cafile=certifi.where())

        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                raw_bytes = resp.read()
                raw = raw_bytes.decode("utf-8", errors="replace").strip()

        except urllib.error.HTTPError as e:
            try:
                raw = (e.read() or b"").decode("utf-8", errors="replace").strip()
            except Exception:
                raw = ""
            raise RuntimeError(f"HTTP {e.code} — {raw[:200]}")

        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error: {e}")

        if not raw:
            raise RuntimeError("Empty response")

        if raw[0] not in "{[":
            raise RuntimeError(f"Non-JSON response: {raw[:200]}")

        try:
            return json.loads(raw)
        except Exception as e:
            raise RuntimeError(f"JSON parse error: {e}. Body head: {raw[:200]}")

    def _fetch_finnhub_general(self) -> list[NewsItem]:
        if not self._finnhub_key:
            return []

        out: list[NewsItem] = []
        base = "https://finnhub.io/api/v1/news"
        url = f"{base}?{urllib.parse.urlencode({'category': 'general', 'token': self._finnhub_key})}"

        j = self._read_json(url, headers={"User-Agent": "Aurelic/1.0 (Desktop App)"})
        if isinstance(j, list):
            for n in j[:60]:
                title = (n.get("headline") or "").strip()
                link = (n.get("url") or "").strip()
                ts = _safe_int(n.get("datetime"), 0)
                src = (n.get("source") or "Finnhub").strip()
                if title and link and ts:
                    out.append(NewsItem(title=title, source=src, published_ts=ts, url=link, tag="stocks"))
        return out

    def _fetch_gdelt(self) -> list[NewsItem]:
        out: list[NewsItem] = []
        base = "https://api.gdeltproject.org/api/v2/doc/doc"
        params = {
            "query": self._gdelt_query,
            "mode": "ArtList",
            "format": "json",
            "maxrecords": "80",
            "sort": "hybridrel",
            "formatdatetime": "0",
        }
        url = f"{base}?{urllib.parse.urlencode(params)}"

        j = self._read_json(url, headers={"User-Agent": "Aurelic/1.0 (Desktop App)"})
        arts = j.get("articles", [])
        if isinstance(arts, list):
            for a in arts[:80]:
                title = (a.get("title") or "").strip()
                link = (a.get("url") or "").strip()
                src = (a.get("sourceCommonName") or a.get("sourceCountry") or "GDELT").strip()

                seendate = (a.get("seendate") or "").strip()
                ts = 0
                if seendate and len(seendate) >= 14 and seendate.isdigit():
                    try:
                        dt = datetime.strptime(seendate[:14], "%Y%m%d%H%M%S")
                        ts = int(dt.timestamp())
                    except Exception:
                        ts = 0

                if title and link and ts:
                    out.append(NewsItem(title=title, source=src, published_ts=ts, url=link, tag="politics"))
        return out


class MoversFetcherWorker(QObject):
    finished = Signal(list, list)
    failed = Signal(str)

    def __init__(self, fmp_key: str, parent: QObject | None = None):
        super().__init__(parent)
        self._fmp_key = (fmp_key or "").strip()

    def run(self) -> None:
        if not self._fmp_key:
            self.failed.emit("FMP_API_KEY fehlt.")
            return
        try:
            gainers = self._fetch_overall("gainers")
            losers = self._fetch_overall("losers")
            self.finished.emit(gainers, losers)
        except Exception as e:
            self.failed.emit(str(e)[:220])

    def _read_json(self, url: str, headers: Optional[dict] = None, timeout: int = 10):
        import urllib.request
        import urllib.error
        import ssl
        import certifi

        req = urllib.request.Request(url, headers=headers or {}, method="GET")
        ctx = ssl.create_default_context(cafile=certifi.where())

        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                raw_bytes = resp.read()
                raw = raw_bytes.decode("utf-8", errors="replace").strip()
        except urllib.error.HTTPError as e:
            try:
                raw = (e.read() or b"").decode("utf-8", errors="replace").strip()
            except Exception:
                raw = ""
            raise RuntimeError(f"FMP HTTP {e.code} — {raw[:200]}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"FMP Network error: {e}")

        if not raw:
            raise RuntimeError("FMP: Empty response")
        if raw[0] not in "{[":
            raise RuntimeError(f"FMP: Non-JSON response: {raw[:200]}")
        try:
            return json.loads(raw)
        except Exception as e:
            raise RuntimeError(f"FMP JSON parse error: {e}. Body head: {raw[:200]}")

    def _fetch_overall(self, which: str) -> list[MoverItem]:
        stable_map = {"gainers": "biggest-gainers", "losers": "biggest-losers"}
        base = f"https://financialmodelingprep.com/stable/{stable_map[which]}"
        url = f"{base}?{urllib.parse.urlencode({'apikey': self._fmp_key})}"
        j = self._read_json(url, headers={"User-Agent": "Aurelic/1.0 (Desktop App)"})

        out: list[MoverItem] = []
        if isinstance(j, list):
            for row in j[:25]:
                sym = (row.get("symbol") or "").strip()
                name = (row.get("name") or row.get("companyName") or "").strip() or sym
                price = float(row.get("price") or 0.0)
                cp = float(row.get("changesPercentage") or 0.0)
                if sym:
                    out.append(MoverItem(symbol=sym, name=name, change_pct=cp, price=price))
        return out


class FavoritesMoversWorker(QObject):
    finished = Signal(list)
    failed = Signal(str)

    def __init__(self, fmp_key: str, symbols: list[str], parent: QObject | None = None):
        super().__init__(parent)
        self._fmp_key = (fmp_key or "").strip()
        self._symbols = [s.strip().upper() for s in (symbols or []) if (s or "").strip()]

    def run(self) -> None:
        if not self._fmp_key:
            self.failed.emit("FMP_API_KEY fehlt.")
            return
        if not self._symbols:
            self.finished.emit([])
            return

        try:
            items = self._fetch_quotes_single(self._symbols[:6])
            self.finished.emit(items)
        except Exception as e:
            self.failed.emit(str(e)[:220])

    def _read_json(self, url: str, headers: Optional[dict] = None, timeout: int = 10):
        import urllib.request
        import urllib.error
        import ssl
        import certifi

        req = urllib.request.Request(url, headers=headers or {}, method="GET")
        ctx = ssl.create_default_context(cafile=certifi.where())

        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                raw_bytes = resp.read()
                raw = raw_bytes.decode("utf-8", errors="replace").strip()
        except urllib.error.HTTPError as e:
            try:
                raw = (e.read() or b"").decode("utf-8", errors="replace").strip()
            except Exception:
                raw = ""
            raise RuntimeError(f"FMP HTTP {e.code} — {raw[:200]}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"FMP Network error: {e}")

        if not raw:
            raise RuntimeError("FMP: Empty response")
        if raw[0] not in "{[":
            raise RuntimeError(f"FMP: Non-JSON response: {raw[:200]}")
        try:
            return json.loads(raw)
        except Exception as e:
            raise RuntimeError(f"FMP JSON parse error: {e}. Body head: {raw[:200]}")

    def _fetch_quotes_single(self, symbols: list[str]) -> list[FavQuoteItem]:
        base = "https://financialmodelingprep.com/stable/quote"

        out: list[FavQuoteItem] = []
        for sym in symbols:
            url = f"{base}?{urllib.parse.urlencode({'symbol': sym, 'apikey': self._fmp_key})}"
            j = self._read_json(url, headers={"User-Agent": "Aurelic/1.0 (Desktop App)"})

            if not isinstance(j, list) or not j:
                continue

            row = j[0] if isinstance(j[0], dict) else {}
            rsym = (row.get("symbol") or sym).strip().upper()
            name = (row.get("name") or row.get("companyName") or "").strip() or rsym

            try:
                price = float(row.get("price") or 0.0)
            except Exception:
                price = 0.0

            cp = row.get("changesPercentage", None)
            if cp is None:
                cp = row.get("changePercent", None)
            if cp is None:
                cp = row.get("changePercentage", None)

            cp_f = _parse_change_pct(cp)

            if abs(cp_f) < 1e-12:
                chg = row.get("change", None)
                prev = row.get("previousClose", None)
                try:
                    chg_f = float(chg) if chg is not None else 0.0
                    prev_f = float(prev) if prev is not None else 0.0
                    if prev_f and abs(chg_f) > 0:
                        cp_f = (chg_f / prev_f) * 100.0
                except Exception:
                    pass

            out.append(FavQuoteItem(symbol=rsym, name=name, change_pct=float(cp_f or 0.0), price=price))

        out.sort(key=lambda x: x.change_pct, reverse=True)
        return out


class InvestmentsSummaryWorker(QObject):
    finished = Signal(list)
    failed = Signal(str)

    def __init__(self, user_id: int, category: str = "all", parent: QObject | None = None):
        super().__init__(parent)
        self._user_id = int(user_id)
        self._category = (category or "all").strip().lower()

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

        cat_filter_sql = ""
        params: list[Any] = [self._user_id]

        if self._category and self._category != "all":
            cat_filter_sql = "AND LOWER(COALESCE(a.category,'stock')) = %s"
            params.append(self._category)

        sql = f"""
        WITH last_prices AS (
            SELECT DISTINCT ON (p.asset_id)
                p.asset_id,
                COALESCE(p.close, 0)::float8 AS last_close,
                p.date AS last_date
            FROM stocks.prices p
            ORDER BY
                p.asset_id,
                p.date DESC,
                COALESCE(p.source,'') ASC
        ),
        base AS (
            SELECT
                i.asset_id,
                a.canonical_symbol AS symbol,
                COALESCE(a.name, a.canonical_symbol) AS name,
                LOWER(COALESCE(a.category, 'stock')) AS category,
                i.quantity::float8 AS quantity,
                COALESCE(lp.last_close, 0)::float8 AS last_price,
                (i.quantity::float8 * COALESCE(lp.last_close, 0)::float8) AS value,
                (lp.last_date IS NOT NULL AND COALESCE(lp.last_close, 0) > 0) AS has_price
            FROM stocks.investments i
            JOIN stocks.assets a ON a.asset_id = i.asset_id
            LEFT JOIN last_prices lp ON lp.asset_id = i.asset_id
            WHERE i.user_id = %s
            {cat_filter_sql}
        ),
        totals AS (
            SELECT
                SUM(value) FILTER (WHERE has_price) AS total_value,
                COUNT(*) FILTER (WHERE NOT has_price) AS missing_price_count
            FROM base
        )
        SELECT
            b.asset_id,
            b.symbol,
            b.name,
            b.category,
            b.quantity,
            b.last_price,
            b.value,
            CASE
                WHEN (SELECT total_value FROM totals) > 0 AND b.has_price
                    THEN (b.value / (SELECT total_value FROM totals)) * 100
                ELSE 0
            END AS pct
        FROM base b
        ORDER BY
            b.has_price DESC,
            b.value DESC NULLS LAST,
            b.quantity DESC,
            b.symbol ASC;
        """

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

        out: list[InvestmentSummaryItem] = []
        for r in rows:
            try:
                cat = _norm_category(str(r[3] or "stock"))
                out.append(
                    InvestmentSummaryItem(
                        asset_id=int(r[0]),
                        symbol=str(r[1] or "").strip(),
                        name=str(r[2] or "").strip(),
                        category=cat,
                        quantity=float(r[4] or 0),
                        last_price=float(r[5] or 0),
                        value=float(r[6] or 0),
                        pct=float(r[7] or 0),
                    )
                )
            except Exception:
                continue

        self.finished.emit(out)


class PortfolioHistoryWorker(QObject):
    finished = Signal(list)
    failed = Signal(str)

    def __init__(self, user_id: int, parent: QObject | None = None):
        super().__init__(parent)
        self._user_id = int(user_id)

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

        sql = """
        WITH inv AS (
            SELECT i.asset_id, i.quantity::float8 AS qty
            FROM stocks.investments i
            WHERE i.user_id = %s
        ),
        bounds AS (
            SELECT
                MIN(p.date)::date AS mind,
                MAX(p.date)::date AS maxd
            FROM stocks.prices p
            JOIN inv i ON i.asset_id = p.asset_id
            WHERE p.date IS NOT NULL
        ),
        clipped AS (
            SELECT
                CASE
                    WHEN mind IS NULL OR maxd IS NULL THEN NULL::date
                    ELSE GREATEST(mind, (maxd - interval '20 years')::date)
                END AS startd,
                maxd
            FROM bounds
        ),
        dates AS (
            SELECT generate_series(
                (SELECT startd FROM clipped),
                (SELECT maxd FROM clipped),
                interval '1 day'
            )::date AS d
            WHERE (SELECT startd FROM clipped) IS NOT NULL
              AND (SELECT maxd FROM clipped) IS NOT NULL
        ),
        last_price AS (
            SELECT
                dt.d,
                i.asset_id,
                i.qty,
                (
                    SELECT p.close::float8
                    FROM stocks.prices p
                    WHERE p.asset_id = i.asset_id
                      AND p.date::date <= dt.d
                      AND p.close IS NOT NULL
                      AND p.close::float8 > 0
                    ORDER BY p.date DESC, COALESCE(p.source,'') ASC
                    LIMIT 1
                ) AS close
            FROM dates dt
            CROSS JOIN inv i
        ),
        portfolio AS (
            SELECT
                d AS date,
                SUM(qty * COALESCE(close, 0))::float8 AS value,
                SUM(CASE WHEN close IS NULL THEN 1 ELSE 0 END)::int AS missing_assets
            FROM last_price
            GROUP BY d
        )
        SELECT date, value, missing_assets
        FROM portfolio
        ORDER BY date ASC;
        """

        try:
            conn = psycopg2.connect(host=host, port=port, dbname=db, user=user, password=pw)
            try:
                with conn.cursor() as cur:
                    cur.execute(sql, [self._user_id])
                    rows = cur.fetchall()
            finally:
                conn.close()
        except Exception as e:
            self.failed.emit(str(e)[:240])
            return

        out: list[PortfolioPoint] = []
        for r in rows or []:
            try:
                d0 = r[0]
                if isinstance(d0, datetime):
                    dd = d0.date()
                elif isinstance(d0, date):
                    dd = d0
                else:
                    dd = datetime.fromisoformat(str(d0)).date()
                out.append(PortfolioPoint(d=dd, value=float(r[1] or 0.0), missing_assets=int(r[2] or 0)))
            except Exception:
                continue

        self.finished.emit(out)


# --------------------------
# Main Page
# --------------------------
class MainPage(QWidget):
    tab_changed = Signal(str)
    avatar_clicked = Signal()
    calendar_clicked = Signal()
    investments_clicked = Signal()

    def __init__(self, background_path: str = "images/Backgroundimage.png", parent: QWidget | None = None):
        super().__init__(parent)

        self.setObjectName("Root")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)

        self._palette = Palette()
        self._background_path = background_path
        self.setStyleSheet(build_qss(self._palette, self._background_path))

        self._avatar_btn: QPushButton | None = None
        self._current_user_id: int | None = None

        # Onboarding / Product Tour
        self._tour_overlay: GuidedTourOverlay | None = None
        self._onboarding_pending: bool = False

        self._tour_target_investments: QWidget | None = None
        self._tour_target_chart: QWidget | None = None
        self._tour_target_news: QWidget | None = None
        self._tour_target_movers: QWidget | None = None
        self._tour_target_favorites: QWidget | None = None

        # Favorites movers state
        self._favorite_symbols: list[str] = []
        self._fav_movers_label: QLabel | None = None
        self._fav_thread: QThread | None = None
        self._fav_worker: FavoritesMoversWorker | None = None

        # Favorites cache
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cache_dir = os.path.abspath(os.path.join(base_dir, "..", "cache"))
        os.makedirs(cache_dir, exist_ok=True)
        self._fav_cache_path = os.path.join(cache_dir, "favorite_movers_cache.json")
        self._fav_cached_items: list[FavQuoteItem] = []
        self._fav_cache_ts: int = 0

        # Favorites refresh throttle
        self._fav_last_fetch_ts: int = 0
        self._fav_min_fetch_interval_s: int = 90

        # NEWS state
        self._news_items: list[NewsItem] = []
        self._news_page: int = 0
        self._news_page_size: int = 6

        self._news_panel: QFrame | None = None
        self._news_scroll: QScrollArea | None = None
        self._news_scroll_content: QWidget | None = None
        self._news_cards_layout: QVBoxLayout | None = None
        self._news_title_label: QLabel | None = None
        self._news_footer_label: QLabel | None = None

        self._news_cards: list[ClickableNewsCard] = []
        self._news_title_labels: list[QLabel] = []
        self._news_meta_labels: list[QLabel] = []
        self._news_loading_label: QLabel | None = None

        # Movers
        self._overall_gainers: list[MoverItem] = []
        self._overall_losers: list[MoverItem] = []
        self._overall_movers_label: QLabel | None = None

        # Investments summary
        self._inv_thread: QThread | None = None
        self._inv_worker: InvestmentsSummaryWorker | None = None
        self._inv_items: list[InvestmentSummaryItem] = []
        self._inv_filter: str = "all"

        self._inv_cards_layout: QVBoxLayout | None = None
        self._inv_scroll: QScrollArea | None = None
        self._inv_scroll_content: QWidget | None = None

        self._inv_status: QLabel | None = None
        self._inv_total_label: QLabel | None = None

        # Portfolio Chart state
        self._pf_thread: QThread | None = None
        self._pf_worker: PortfolioHistoryWorker | None = None
        self._pf_points: list[PortfolioPoint] = []
        self._pf_range_key: str = "1M"
        self._chart_value_label: QLabel | None = None
        self._chart_pct_label: QLabel | None = None
        self._chart_error_label: QLabel | None = None
        self._chart_view: Any = None
        self._chart: Any = None
        self._chart_series: Any = None
        self._chart_axis_x: Any = None
        self._chart_axis_y: Any = None

        # FMP rate limit
        self._fmp_calls_today: int = 0
        self._fmp_calls_date: str = datetime.now().strftime("%Y-%m-%d")
        self._fmp_daily_limit: int = 200

        # Threads
        self._news_thread: QThread | None = None
        self._news_worker: NewsFetcherWorker | None = None

        self._movers_thread: QThread | None = None
        self._movers_worker: MoversFetcherWorker | None = None

        # Timers
        self._news_refresh_timer = QTimer(self)
        self._news_refresh_timer.setInterval(180_000)
        self._news_refresh_timer.timeout.connect(self._refresh_news)

        self._news_rotate_timer = QTimer(self)
        self._news_rotate_timer.setInterval(180_000)
        self._news_rotate_timer.timeout.connect(self._rotate_news_page)

        self._movers_refresh_timer = QTimer(self)
        self._movers_refresh_timer.setInterval(1_200_000)
        self._movers_refresh_timer.timeout.connect(self._refresh_movers)

        self._fav_movers_timer = QTimer(self)
        self._fav_movers_timer.setInterval(300_000)
        self._fav_movers_timer.timeout.connect(self._refresh_favorite_movers)

        self._inv_refresh_timer = QTimer(self)
        self._inv_refresh_timer.setInterval(120_000)
        self._inv_refresh_timer.timeout.connect(self._refresh_investments_summary)

        self._pf_refresh_timer = QTimer(self)
        self._pf_refresh_timer.setInterval(120_000)
        self._pf_refresh_timer.timeout.connect(self._refresh_portfolio_history)

        # Resize debounce
        self._resize_debounce = QTimer(self)
        self._resize_debounce.setSingleShot(True)
        self._resize_debounce.setInterval(60)
        self._resize_debounce.timeout.connect(self._on_resized_debounced)
        self._last_shell_size: tuple[int, int] | None = None

        # Layout root
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(40, 40, 40, 40)
        self._root.setSpacing(0)

        self._shell = QFrame()
        self._shell.setObjectName("Shell")
        self._shell.setAttribute(Qt.WA_StyledBackground, True)
        self._shell.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        shell_v = QVBoxLayout(self._shell)
        shell_v.setContentsMargins(22, 18, 22, 18)
        shell_v.setSpacing(14)

        shell_v.addWidget(self._build_topbar(), 0)
        shell_v.addWidget(self._build_main_area(), 1)

        self._root.addWidget(self._shell, 0, Qt.AlignCenter)

        self._set_active_tab("brokerage", sync_tabs=True)

        self._load_fav_cache()
        self._show_cached_favs_if_any()

        self._refresh_news()
        self._news_refresh_timer.start()
        self._news_rotate_timer.start()

        self._refresh_movers()
        self._movers_refresh_timer.start()

        self._fav_movers_timer.start()
        self._inv_refresh_timer.start()
        self._pf_refresh_timer.start()

        QTimer.singleShot(0, self._update_news_capacity)
        QTimer.singleShot(0, self._refresh_investments_summary)
        QTimer.singleShot(0, self._refresh_portfolio_history)

    # --------------------------
    # Favorites Cache helpers
    # --------------------------
    def _fav_cache_key(self) -> str:
        return ",".join(sorted(self._favorite_symbols))

    def _load_fav_cache(self) -> None:
        self._fav_cached_items = []
        self._fav_cache_ts = 0
        try:
            if not os.path.exists(self._fav_cache_path):
                return
            with open(self._fav_cache_path, "r", encoding="utf-8") as f:
                j = json.load(f)
            if not isinstance(j, dict):
                return

            ts = int(j.get("ts") or 0)
            items = j.get("items") or []
            if not isinstance(items, list):
                return

            out: list[FavQuoteItem] = []
            for it in items:
                if not isinstance(it, dict):
                    continue
                sym = str(it.get("symbol") or "").strip().upper()
                if not sym:
                    continue
                out.append(
                    FavQuoteItem(
                        symbol=sym,
                        name=str(it.get("name") or "").strip() or sym,
                        change_pct=float(it.get("change_pct") or 0.0),
                        price=float(it.get("price") or 0.0),
                    )
                )

            self._fav_cached_items = out
            self._fav_cache_ts = ts
        except Exception:
            self._fav_cached_items = []
            self._fav_cache_ts = 0

    def _save_fav_cache(self, items: list[FavQuoteItem]) -> None:
        try:
            payload = {
                "key": self._fav_cache_key(),
                "ts": int(datetime.now().timestamp()),
                "items": [
                    {"symbol": x.symbol, "name": x.name, "change_pct": x.change_pct, "price": x.price}
                    for x in items
                ],
            }
            tmp = self._fav_cache_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)
            os.replace(tmp, self._fav_cache_path)
        except Exception:
            pass

    def _show_cached_favs_if_any(self) -> None:
        if self._fav_movers_label is None:
            return
        if self._fav_cached_items:
            self._fav_movers_label.setText(self._format_favorites_movers_block(self._fav_cached_items, n=6))

    # --------------------------
    # Public API
    # --------------------------
    def set_current_user(self, user: dict | None) -> None:
        uid = None
        if isinstance(user, dict):
            try:
                uid = int(user.get("id")) if user.get("id") is not None else None
            except Exception:
                uid = None
        self._current_user_id = uid
        self._refresh_investments_summary()
        self._refresh_portfolio_history()
        self.maybe_start_onboarding()

    def _tour_settings_key(self) -> str:
        uid = self._current_user_id if self._current_user_id is not None else "guest"
        return f"onboarding/mainpage/v3/user/{uid}"

    def maybe_start_onboarding(self) -> None:
        if self._current_user_id is None:
            return

        settings = QSettings("Aurelic", "DesktopApp")
        done = settings.value(self._tour_settings_key(), False, bool)
        if done:
            return

        if self._tour_overlay is not None:
            return

        QTimer.singleShot(450, self._start_onboarding)

    def _build_intro_tour_steps(self) -> list[TourStep]:
        return [
            TourStep(
                target=None,
                title="Willkommen",
                text="Bevor wir die Oberfläche ansehen, bekommst du eine kurze Einführung in die wichtigsten Grundlagen rund um Markt, Risiko und Analyse.",
                placement="center",
            ),
            TourStep(
                target=None,
                title="Was ist ein Markt?",
                text="Ein Markt ist der Ort, an dem Käufer und Verkäufer aufeinandertreffen. Dort entstehen Preise für Aktien, ETFs, Rohstoffe, Kryptowährungen und andere Anlageklassen.",
                placement="center",
            ),
            TourStep(
                target=None,
                title="Was ist ein Asset?",
                text="Ein Asset ist ein handelbarer Vermögenswert. Dazu zählen zum Beispiel Aktien, ETFs, Indizes, Rohstoffe oder Kryptowährungen.",
                placement="center",
            ),
            TourStep(
                target=None,
                title="Rendite und Risiko",
                text="Höhere Gewinnchancen gehen oft mit höheren Schwankungen einher. Gute Anlageentscheidungen betrachten deshalb nie nur mögliche Rendite, sondern immer auch das Risiko.",
                placement="center",
            ),
            TourStep(
                target=None,
                title="Volatilität",
                text="Volatilität beschreibt, wie stark ein Preis schwankt. Hohe Volatilität bedeutet meist mehr Unsicherheit, aber oft auch größere Chancen und Risiken.",
                placement="center",
            ),
            TourStep(
                target=None,
                title="Diversifikation",
                text="Diversifikation bedeutet, Kapital auf verschiedene Assets, Sektoren oder Regionen zu verteilen. Das kann helfen, Klumpenrisiken zu reduzieren.",
                placement="center",
            ),
            TourStep(
                target=None,
                title="Korrelation",
                text="Korrelation beschreibt, wie ähnlich sich zwei Assets bewegen. Wenn viele Positionen stark miteinander korrelieren, ist ein Portfolio oft weniger breit gestreut, als es auf den ersten Blick wirkt.",
                placement="center",
            ),
            TourStep(
                target=None,
                title="Zeithorizont",
                text="Kurzfristiges Trading und langfristiges Investieren folgen unterschiedlichen Logiken. Analysen sollten deshalb immer im Kontext des eigenen Zeithorizonts gelesen werden.",
                placement="center",
            ),
            TourStep(
                target=None,
                title="Makrodaten und News",
                text="Zinsen, Inflation, Konjunkturdaten und Unternehmensnachrichten können Märkte stark beeinflussen. Kurse reagieren nicht nur auf Fakten, sondern oft auch auf Erwartungen.",
                placement="center",
            ),
            TourStep(
                target=None,
                title="Was dir diese App zeigt",
                text="Diese Anwendung hilft dir, Märkte strukturierter zu beobachten: mit Portfolio-Ansichten, Preisverläufen, Movers, News und späteren Analyse-Tools.",
                placement="center",
            ),
        ]

    def _build_ui_tour_steps(self) -> list[TourStep]:
        steps: list[TourStep] = []

        if hasattr(self, "_seg_tabs") and self._seg_tabs is not None:
            steps.append(TourStep(
                target=self._seg_tabs,
                title="Navigation",
                text="Hier wechselst du zwischen Brokerage und Analyse. So springst du schnell zwischen Portfolio-Ansicht und Analyse-Tools.",
                placement="bottom",
            ))

        if self._tour_target_investments is not None:
            steps.append(TourStep(
                target=self._tour_target_investments,
                title="Investments",
                text="Hier siehst du deine gehaltenen Positionen, den aktuellen Wert und die Portfolio-Gewichtung. Über den Button oben rechts kommst du in die Detailansicht.",
                placement="right",
            ))

        if self._tour_target_chart is not None:
            steps.append(TourStep(
                target=self._tour_target_chart,
                title="Portfolio-Chart",
                text="Dieser Chart zeigt die historische Entwicklung deines Portfolios. Über die Chips oben wechselst du den Betrachtungszeitraum.",
                placement="left",
            ))

        if self._tour_target_news is not None:
            steps.append(TourStep(
                target=self._tour_target_news,
                title="News",
                text="Hier erscheinen relevante Markt- und Politik-News. Ein Klick auf einen Eintrag öffnet die Quelle im Browser.",
                placement="top",
            ))

        if self._tour_target_movers is not None:
            steps.append(TourStep(
                target=self._tour_target_movers,
                title="Top Mover",
                text="Hier siehst du die stärksten Gewinner und Verlierer im Markt. So erkennst du aktuelle Bewegungen sofort.",
                placement="left",
            ))

        if self._tour_target_favorites is not None:
            steps.append(TourStep(
                target=self._tour_target_favorites,
                title="Favoriten",
                text="Hier werden deine Favoriten mit ihren aktuellen Bewegungen angezeigt. So hast du deine wichtigsten Assets direkt im Blick.",
                placement="left",
            ))

        return steps

    def _start_onboarding(self) -> None:
        if self._current_user_id is None:
            return

        if not self.isVisible():
            self._onboarding_pending = True
            return

        settings = QSettings("Aurelic", "DesktopApp")
        done = settings.value(self._tour_settings_key(), False, bool)
        if done:
            return

        steps = self._build_intro_tour_steps() + self._build_ui_tour_steps()

        if not steps:
            settings.setValue(self._tour_settings_key(), True)
            return

        def _mark_done() -> None:
            settings.setValue(self._tour_settings_key(), True)
            self._tour_overlay = None

        self._tour_overlay = GuidedTourOverlay(
            host=self,
            steps=steps,
            on_finished=_mark_done,
            parent=self,
        )
        self._tour_overlay.start()

    def set_favorite_symbols(self, symbols: list[str] | None) -> None:
        uniq: list[str] = []
        seen = set()
        for s in (symbols or []):
            ss = (s or "").strip().upper()
            if not ss or ss in seen:
                continue
            seen.add(ss)
            uniq.append(ss)

        self._favorite_symbols = uniq[:6]

        if self._fav_movers_label is not None and not self._favorite_symbols:
            self._fav_movers_label.setText("Keine Favoriten")
            return

        self._load_fav_cache()
        self._show_cached_favs_if_any()

        self._refresh_favorite_movers(force=False)

    # --------------------------
    # Avatar helpers
    # --------------------------
    def set_avatar_letter(self, letter: str) -> None:
        if self._avatar_btn is None:
            return
        ch = (letter or "").strip()
        self._avatar_btn.setText(ch[:1].upper() if ch else "N")

    def set_avatar_from_user(self, user: dict | None) -> None:
        letter = ""
        if user:
            first = (user.get("first_name") or "").strip()
            email = (user.get("email") or "").strip()
            if first:
                letter = first[0]
            elif email:
                letter = email[0]
        self.set_avatar_letter(letter or "N")
        self.set_current_user(user)

    def _on_resized_debounced(self) -> None:
        self._update_news_capacity()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)

        m = 40
        avail_w = max(300, self.width() - 2 * m)
        avail_h = max(300, self.height() - 2 * m)

        ratio = 1.568
        w = min(avail_w, int(avail_h * ratio))
        h = min(avail_h, int(w / ratio))

        new_size = (w, h)
        if new_size != self._last_shell_size:
            self._shell.setFixedSize(w, h)
            self._last_shell_size = new_size

        self._resize_debounce.start()

    # --------------------------
    # Topbar
    # --------------------------
    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setAttribute(Qt.WA_StyledBackground, True)

        h = QHBoxLayout(bar)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(12)

        self._seg_tabs = SegmentedTabs()
        self._seg_tabs.setObjectName("SegmentedTabs")
        self._seg_tabs.set_active("brokerage", animate=False, emit=False)
        self._seg_tabs.changed.connect(lambda which: self._set_active_tab(which, sync_tabs=False))

        cal_btn = QPushButton()
        cal_btn.setObjectName("CalendarBtn")
        cal_btn.setFixedSize(44, 44)
        cal_btn.clicked.connect(self.calendar_clicked.emit)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.abspath(os.path.join(base_dir, "..", "images", "icons8-kalender-30.png"))
        cal_btn.setIcon(QIcon(icon_path))
        cal_btn.setIconSize(QSize(24, 24))

        self._avatar_btn = QPushButton("N")
        self._avatar_btn.setObjectName("Avatar")
        self._avatar_btn.setFixedSize(44, 44)
        self._avatar_btn.clicked.connect(self.avatar_clicked.emit)

        h.addWidget(self._seg_tabs, 0, Qt.AlignLeft)
        h.addStretch(1)
        h.addWidget(cal_btn, 0, Qt.AlignRight)
        h.addWidget(self._avatar_btn, 0, Qt.AlignRight)
        return bar

    def _set_active_tab(self, which: str, sync_tabs: bool = True) -> None:
        which = "analyse" if which == "analyse" else "brokerage"
        if sync_tabs and hasattr(self, "_seg_tabs") and self._seg_tabs is not None:
            self._seg_tabs.set_active(which, animate=True, emit=False)
        self.tab_changed.emit(which)

    # --------------------------
    # Main Area
    # --------------------------
    def _build_main_area(self) -> QWidget:
        root = QWidget()
        root.setAttribute(Qt.WA_StyledBackground, True)

        h = QHBoxLayout(root)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(14)

        # LEFT COLUMN
        left_col = QWidget()
        left_col.setAttribute(Qt.WA_StyledBackground, True)
        lv = QVBoxLayout(left_col)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.setSpacing(14)

        upper = QWidget()
        upper.setAttribute(Qt.WA_StyledBackground, True)
        uh = QHBoxLayout(upper)
        uh.setContentsMargins(0, 0, 0, 0)
        uh.setSpacing(14)

        investments = self._build_investments_area()
        investments.setMinimumWidth(360)
        investments.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self._tour_target_investments = investments

        chart = self._build_portfolio_chart_panel()
        chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._tour_target_chart = chart

        uh.addWidget(investments, 0)
        uh.addWidget(chart, 1)

        news = self._build_news_panel(min_w=0)
        news.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        news.setFixedHeight(270)
        self._tour_target_news = news

        lv.addWidget(upper, 1)
        lv.addWidget(news, 0)

        # RIGHT COLUMN
        right_col = QWidget()
        right_col.setAttribute(Qt.WA_StyledBackground, True)
        rv = QVBoxLayout(right_col)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(14)

        right_top, self._overall_movers_label = self._panel_with_body(
            title="Top Mover:",
            placeholder="Lade Movers …",
            min_w=320
        )
        self._tour_target_movers = right_top
        if self._overall_movers_label is not None:
            self._overall_movers_label.setTextFormat(Qt.RichText)
            self._overall_movers_label.setTextInteractionFlags(Qt.NoTextInteraction)
            self._overall_movers_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        right_bottom, self._fav_movers_label = self._panel_with_body(
            title="Favoriten Top Mover:",
            placeholder="Keine Favoriten",
            min_w=320
        )
        self._tour_target_favorites = right_bottom
        if self._fav_movers_label is not None:
            self._fav_movers_label.setTextFormat(Qt.RichText)
            self._fav_movers_label.setTextInteractionFlags(Qt.NoTextInteraction)
            self._fav_movers_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        right_top.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        right_bottom.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        rv.addWidget(right_top, 1)
        rv.addWidget(right_bottom, 1)

        h.addWidget(left_col, 1)
        h.addWidget(right_col, 0)

        return root

    # --------------------------
    # Portfolio Chart Panel
    # --------------------------
    def _build_portfolio_chart_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        panel.setAttribute(Qt.WA_StyledBackground, True)

        v = QVBoxLayout(panel)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(10)

        header = QWidget()
        header.setAttribute(Qt.WA_StyledBackground, True)
        hh = QHBoxLayout(header)
        hh.setContentsMargins(0, 0, 0, 0)
        hh.setSpacing(10)

        left = QWidget()
        left.setAttribute(Qt.WA_StyledBackground, True)
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.setSpacing(2)

        self._chart_value_label = QLabel("—")
        self._chart_value_label.setObjectName("ChartValue")
        self._chart_value_label.setWordWrap(False)

        self._chart_pct_label = QLabel("")
        self._chart_pct_label.setObjectName("ChartPct")
        self._chart_pct_label.setWordWrap(False)

        lv.addWidget(self._chart_value_label)
        lv.addWidget(self._chart_pct_label)

        hh.addWidget(left, 0, Qt.AlignLeft)

        chips = QWidget()
        chips.setAttribute(Qt.WA_StyledBackground, True)
        ch = QHBoxLayout(chips)
        ch.setContentsMargins(0, 0, 0, 0)
        ch.setSpacing(8)

        self._pf_chip_group = QButtonGroup(self)
        self._pf_chip_group.setExclusive(True)

        def _mk_chip(text: str, key: str, checked: bool = False) -> QPushButton:
            b = QPushButton(text)
            b.setObjectName("Chip")
            b.setCheckable(True)
            b.setChecked(checked)
            b.clicked.connect(lambda: self._set_portfolio_range(key))
            self._pf_chip_group.addButton(b)
            return b

        ch.addWidget(_mk_chip("1T", "1T", False))
        ch.addWidget(_mk_chip("1W", "1W", False))
        ch.addWidget(_mk_chip("1M", "1M", True))
        ch.addWidget(_mk_chip("1J", "1J", False))
        ch.addWidget(_mk_chip("Max", "MAX", False))

        hh.addStretch(1)
        hh.addWidget(chips, 0, Qt.AlignRight)

        v.addWidget(header, 0)

        if not _HAS_QTCHARTS:
            self._chart_error_label = QLabel("QtCharts nicht verfügbar. Installiere PySide6-Addons/QtCharts.")
            self._chart_error_label.setObjectName("Placeholder")
            self._chart_error_label.setAlignment(Qt.AlignCenter)
            self._chart_error_label.setWordWrap(True)
            v.addStretch(1)
            v.addWidget(self._chart_error_label, 0, Qt.AlignCenter)
            v.addStretch(1)
            return panel

        self._chart = QChart()
        self._chart.setBackgroundVisible(False)
        self._chart.setPlotAreaBackgroundVisible(False)
        self._chart.legend().hide()
        self._chart.setMargins(QMargins(0, 0, 0, 0))

        self._chart_series = QLineSeries()
        self._chart.addSeries(self._chart_series)

        self._chart_axis_x = QDateTimeAxis()
        self._chart_axis_x.setFormat("dd.MM")
        self._chart_axis_x.setTickCount(6)
        self._chart_axis_x.setLabelsColor(Qt.gray)
        self._chart_axis_x.setGridLineVisible(True)

        self._chart_axis_y = QValueAxis()
        self._chart_axis_y.setLabelsColor(Qt.gray)
        self._chart_axis_y.setGridLineVisible(True)

        self._chart.addAxis(self._chart_axis_x, Qt.AlignBottom)
        self._chart.addAxis(self._chart_axis_y, Qt.AlignLeft)
        self._chart_series.attachAxis(self._chart_axis_x)
        self._chart_series.attachAxis(self._chart_axis_y)

        self._chart_view = QChartView(self._chart)
        self._chart_view.setRenderHint(QPainter.Antialiasing, True)
        self._chart_view.setStyleSheet("background: transparent;")
        self._chart_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        v.addWidget(self._chart_view, 1)
        return panel

    def _set_portfolio_range(self, key: str) -> None:
        k = (key or "1M").strip().upper()
        if k not in {"1T", "1W", "1M", "1J", "MAX"}:
            k = "1M"
        self._pf_range_key = k
        self._render_portfolio_chart()

    def _refresh_portfolio_history(self) -> None:
        if not _HAS_QTCHARTS:
            return

        if self._current_user_id is None:
            self._pf_points = []
            self._render_portfolio_chart()
            return

        try:
            if self._pf_thread is not None and self._pf_thread.isRunning():
                return
        except RuntimeError:
            self._pf_thread = None
            self._pf_worker = None

        if self._chart_pct_label is not None:
            self._chart_pct_label.setText("Lade Verlauf …")
        if self._chart_value_label is not None:
            self._chart_value_label.setText("—")

        thread = QThread(self)
        worker = PortfolioHistoryWorker(user_id=int(self._current_user_id))
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(self._on_portfolio_history)
        worker.failed.connect(self._on_portfolio_history_failed)

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
            if self._pf_thread is thread:
                self._pf_thread = None
            if self._pf_worker is worker:
                self._pf_worker = None

        thread.finished.connect(_cleanup)

        self._pf_thread = thread
        self._pf_worker = worker
        thread.start()

    def _on_portfolio_history_failed(self, msg: str) -> None:
        self._pf_points = []
        if self._chart_pct_label is not None:
            self._chart_pct_label.setText(f"Chart konnte nicht geladen werden: {msg}")
        self._render_portfolio_chart()

    def _on_portfolio_history(self, points: list) -> None:
        self._pf_points = [p for p in points if isinstance(p, PortfolioPoint)]
        self._render_portfolio_chart()

    def _slice_points_by_range(self, pts: list[PortfolioPoint]) -> list[PortfolioPoint]:
        if not pts:
            return []
        pts = sorted(pts, key=lambda x: x.d)
        end = pts[-1].d
        k = (self._pf_range_key or "1M").upper()

        if k == "MAX":
            start = end - timedelta(days=365 * 20)
            return [p for p in pts if p.d >= start]

        days_map = {"1T": 1, "1W": 7, "1M": 30, "1J": 365}
        days = days_map.get(k, 30)
        start = end - timedelta(days=days)
        return [p for p in pts if p.d >= start]

    def _downsample_points(self, pts: list[PortfolioPoint], max_points: int = 1800) -> list[PortfolioPoint]:
        if not pts or len(pts) <= max_points:
            return pts
        step = max(1, len(pts) // max_points)
        sampled = pts[::step]
        if sampled[-1].d != pts[-1].d:
            sampled.append(pts[-1])
        return sampled

    def _render_portfolio_chart(self) -> None:
        if not _HAS_QTCHARTS:
            return
        if self._chart_series is None or self._chart_axis_x is None or self._chart_axis_y is None:
            return

        pts = self._slice_points_by_range(self._pf_points)
        pts = self._downsample_points(pts, max_points=1800)

        try:
            self._chart_series.clear()
        except Exception:
            pass

        if self._current_user_id is None:
            if self._chart_value_label is not None:
                self._chart_value_label.setText("Bitte einloggen")
            if self._chart_pct_label is not None:
                self._chart_pct_label.setText("")
            return

        if not pts or len(pts) < 2:
            if self._chart_value_label is not None:
                self._chart_value_label.setText("—")
            if self._chart_pct_label is not None:
                self._chart_pct_label.setText("Keine Verlaufdaten")
            return

        rounded_vals: list[float] = []
        for p in pts:
            try:
                rounded_vals.append(round(float(p.value), 2))
            except Exception:
                rounded_vals.append(0.0)

        for p, v in zip(pts, rounded_vals):
            dt = datetime.combine(p.d, datetime.min.time())
            qdt = QDateTime(dt)
            self._chart_series.append(qdt.toMSecsSinceEpoch(), float(v))

        min_dt = datetime.combine(pts[0].d, datetime.min.time())
        max_dt = datetime.combine(pts[-1].d, datetime.min.time())
        self._chart_axis_x.setRange(QDateTime(min_dt), QDateTime(max_dt))

        vmin = min(rounded_vals)
        vmax = max(rounded_vals)
        if vmin == vmax:
            eps = max(1.0, abs(vmin) * 0.001)
            vmin -= eps
            vmax += eps
        pad = (vmax - vmin) * 0.08
        self._chart_axis_y.setRange(vmin - pad, vmax + pad)

        first = float(rounded_vals[0])
        last = float(rounded_vals[-1])

        if self._chart_value_label is not None:
            self._chart_value_label.setText(_fmt_eur(last, 2))

        pct_raw = 0.0
        if abs(first) > 1e-9:
            pct_raw = ((last - first) / first) * 100.0
        pct_disp = round(pct_raw, 2)

        green = QColor("#4ADE80")
        red = QColor("#FB7185")
        neutral = QColor("#AEB7C2")

        if pct_disp > 0:
            self._chart_series.setPen(QPen(green, 2.2))
        elif pct_disp < 0:
            self._chart_series.setPen(QPen(red, 2.2))
        else:
            self._chart_series.setPen(QPen(neutral, 2.2))

        if self._chart_pct_label is not None:
            sign = "+" if pct_disp > 0 else ""
            self._chart_pct_label.setText(f"{sign}{pct_disp:.2f}%  ·  {self._pf_range_key}")

            if pct_disp > 0:
                self._chart_pct_label.setStyleSheet("color: rgba(74,222,128,235); font-weight: 900;")
            elif pct_disp < 0:
                self._chart_pct_label.setStyleSheet("color: rgba(251,113,133,235); font-weight: 900;")
            else:
                self._chart_pct_label.setStyleSheet("color: rgba(174,183,194,210); font-weight: 900;")

    # --------------------------
    # News Panel
    # --------------------------
    def _build_news_panel(self, min_w: int = 360) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        panel.setAttribute(Qt.WA_StyledBackground, True)
        if min_w > 0:
            panel.setMinimumWidth(min_w)
        self._news_panel = panel

        v = QVBoxLayout(panel)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(10)

        self._news_title_label = QLabel("News:")
        self._news_title_label.setObjectName("PanelTitle")
        self._news_title_label.setWordWrap(True)
        v.addWidget(self._news_title_label, 0, Qt.AlignLeft)

        self._news_loading_label = QLabel("Lade News …")
        self._news_loading_label.setObjectName("FinePrint")
        self._news_loading_label.setWordWrap(True)
        v.addWidget(self._news_loading_label, 0, Qt.AlignLeft)

        self._news_scroll = QScrollArea()
        self._news_scroll.setWidgetResizable(True)
        self._news_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._news_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self._news_scroll_content = QWidget()
        self._news_scroll_content.setAttribute(Qt.WA_StyledBackground, True)
        self._news_scroll_content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._news_cards_layout = QVBoxLayout(self._news_scroll_content)
        self._news_cards_layout.setContentsMargins(0, 0, 0, 0)
        self._news_cards_layout.setSpacing(6)

        self._news_scroll.setWidget(self._news_scroll_content)
        v.addWidget(self._news_scroll, 1)

        self._news_footer_label = QLabel("")
        self._news_footer_label.setObjectName("FinePrint")
        self._news_footer_label.setWordWrap(True)
        v.addWidget(self._news_footer_label, 0, Qt.AlignLeft)

        self._ensure_news_cards(40)
        return panel

    def _ensure_news_cards(self, count: int) -> None:
        if self._news_cards_layout is None:
            return

        count = max(1, int(count))
        while len(self._news_cards) < count:
            card = ClickableNewsCard()
            cv = QVBoxLayout(card)
            cv.setContentsMargins(10, 10, 10, 10)
            cv.setSpacing(4)

            t = QLabel("")
            t.setObjectName("NewsTitle")
            t.setWordWrap(True)
            t.setTextInteractionFlags(Qt.NoTextInteraction)

            meta = QLabel("")
            meta.setObjectName("NewsMeta")
            meta.setWordWrap(True)

            card.clicked.connect(self._open_news_url_confirmed)

            cv.addWidget(t)
            cv.addWidget(meta)

            card.setVisible(False)
            self._news_cards_layout.addWidget(card)

            self._news_cards.append(card)
            self._news_title_labels.append(t)
            self._news_meta_labels.append(meta)

        self._render_news()

    def _update_news_capacity(self) -> None:
        if self._news_panel is None or self._news_scroll is None:
            return

        panel_h = self._news_panel.height()
        if panel_h <= 0:
            return

        title_h = self._news_title_label.sizeHint().height() if self._news_title_label else 0
        loading_h = self._news_loading_label.sizeHint().height() if (
            self._news_loading_label and self._news_loading_label.isVisible()
        ) else 0
        footer_h = self._news_footer_label.sizeHint().height() if self._news_footer_label else 0

        inner_h = panel_h - (14 * 2)
        usable_h = max(0, inner_h - title_h - loading_h - footer_h - 24)

        est_card_h = 82
        visible_cards = max(4, min(10, int(usable_h // est_card_h)))

        self._news_page_size = visible_cards
        self._render_news()

    def _open_news_url_confirmed(self, url: str) -> None:
        url = (url or "").strip()
        if not url:
            return

        dlg = ExternalLinkDialog(
            url=url,
            palette=self._palette,
            background_path=self._background_path,
            parent=self
        )
        if dlg.exec() == QDialog.Accepted:
            QDesktopServices.openUrl(QUrl(dlg.url))

    # --------------------------
    # Investments
    # --------------------------
    def _build_investments_area(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card.setAttribute(Qt.WA_StyledBackground, True)

        v = QVBoxLayout(card)
        v.setContentsMargins(18, 12, 18, 12)
        v.setSpacing(8)

        header = QWidget()
        header.setAttribute(Qt.WA_StyledBackground, True)
        hh = QHBoxLayout(header)
        hh.setContentsMargins(0, 0, 0, 0)
        hh.setSpacing(10)

        title = QLabel("Investments")
        title.setObjectName("PanelTitle")

        invest_btn = QPushButton()
        invest_btn.setObjectName("InvestBtn")
        invest_btn.setFixedSize(44, 44)
        invest_btn.setToolTip("Zu Investments")
        invest_btn.clicked.connect(self.investments_clicked.emit)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        invest_icon_path = os.path.abspath(os.path.join(base_dir, "..", "images", "invest.png"))
        if os.path.exists(invest_icon_path):
            invest_btn.setIcon(QIcon(invest_icon_path))
            invest_btn.setIconSize(QSize(24, 24))
        else:
            invest_btn.setText("↗")

        hh.addWidget(title, 0, Qt.AlignLeft)
        hh.addStretch(1)
        hh.addWidget(invest_btn, 0, Qt.AlignRight)
        v.addWidget(header)

        chips = QWidget()
        chips.setAttribute(Qt.WA_StyledBackground, True)
        ch = QHBoxLayout(chips)
        ch.setContentsMargins(0, 0, 0, 0)
        ch.setSpacing(8)

        self._inv_chip_group = QButtonGroup(self)
        self._inv_chip_group.setExclusive(True)

        def _mk_chip(text: str, key: str, checked: bool = False) -> QPushButton:
            b = QPushButton(text)
            b.setObjectName("Chip")
            b.setCheckable(True)
            b.setChecked(checked)
            b.clicked.connect(lambda: self._set_investment_filter(key))
            self._inv_chip_group.addButton(b)
            return b

        ch.addWidget(_mk_chip("ALL", "all", True))
        ch.addWidget(_mk_chip("STOCK", "stock"))
        ch.addWidget(_mk_chip("ETF", "etf"))
        ch.addWidget(_mk_chip("CRYPTO", "crypto"))
        ch.addWidget(_mk_chip("COM", "commodity"))
        ch.addWidget(_mk_chip("INDEX", "index"))
        ch.addStretch(1)
        v.addWidget(chips)

        panel = QFrame()
        panel.setObjectName("InvPanel")
        panel.setAttribute(Qt.WA_StyledBackground, True)
        panel.setMinimumHeight(280)
        panel.setMaximumHeight(360)

        pv = QVBoxLayout(panel)
        pv.setContentsMargins(14, 12, 14, 12)
        pv.setSpacing(10)

        topmeta = QWidget()
        topmeta.setAttribute(Qt.WA_StyledBackground, True)
        tmh = QHBoxLayout(topmeta)
        tmh.setContentsMargins(0, 0, 0, 0)
        tmh.setSpacing(10)

        self._inv_status = QLabel("")
        self._inv_status.setObjectName("FinePrint")
        self._inv_status.setWordWrap(True)

        self._inv_total_label = QLabel("")
        self._inv_total_label.setObjectName("FinePrint")

        tmh.addWidget(self._inv_status, 1, Qt.AlignLeft)
        tmh.addWidget(self._inv_total_label, 0, Qt.AlignRight)
        pv.addWidget(topmeta)

        self._inv_scroll = QScrollArea()
        self._inv_scroll.setWidgetResizable(True)
        self._inv_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._inv_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._inv_scroll_content = QWidget()
        self._inv_scroll_content.setAttribute(Qt.WA_StyledBackground, True)

        self._inv_cards_layout = QVBoxLayout(self._inv_scroll_content)
        self._inv_cards_layout.setContentsMargins(0, 0, 0, 0)
        self._inv_cards_layout.setSpacing(10)
        self._inv_cards_layout.setAlignment(Qt.AlignTop)

        self._inv_scroll.setWidget(self._inv_scroll_content)
        pv.addWidget(self._inv_scroll, 1)

        v.addWidget(panel)
        return card

    def _set_investment_filter(self, key: str) -> None:
        self._inv_filter = (key or "all").strip().lower()
        self._refresh_investments_summary()

    def _clear_layout(self, layout: QVBoxLayout | None) -> None:
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

    def _render_investments_summary(self) -> None:
        if self._inv_cards_layout is None:
            return

        self._clear_layout(self._inv_cards_layout)

        if self._current_user_id is None:
            if self._inv_status is not None:
                self._inv_status.setText("Bitte einloggen, um dein Portfolio zu sehen.")
            if self._inv_total_label is not None:
                self._inv_total_label.setText("")
            if self._inv_scroll is not None:
                self._inv_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self._inv_scroll.setFixedHeight(4 * 64 + 3 * 10)
            return

        if not self._inv_items:
            if self._inv_status is not None:
                self._inv_status.setText("Keine Investments vorhanden.")
            if self._inv_total_label is not None:
                self._inv_total_label.setText("")
            if self._inv_scroll is not None:
                self._inv_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self._inv_scroll.setFixedHeight(4 * 64 + 3 * 10)
            return

        total_val = sum(x.value for x in self._inv_items if x.value > 0)
        missing = sum(1 for x in self._inv_items if x.value <= 0)

        if self._inv_total_label is not None:
            if total_val > 0:
                self._inv_total_label.setText(f"Total: {_fmt_num(total_val, 2)}")
            else:
                self._inv_total_label.setText("Total: —")

        if self._inv_status is not None:
            self._inv_status.setText(f"{missing} Asset(s) ohne Kursdaten." if missing > 0 else "")

        row_h = 64
        spacing = 10
        count = len(self._inv_items)
        visible_n = min(4, count)
        viewport_h = visible_n * row_h + max(0, visible_n - 1) * spacing

        if self._inv_scroll is not None:
            self._inv_scroll.setFixedHeight(viewport_h)
            if count > 4:
                self._inv_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            else:
                self._inv_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self._inv_scroll.verticalScrollBar().setValue(0)

        def _primary_name(it: InvestmentSummaryItem) -> str:
            nm = (it.name or "").strip()
            sym = (it.symbol or "").strip().upper()
            if not nm or nm.upper() == sym:
                return sym
            return f"{nm} ({sym})"

        for it in self._inv_items:
            cat = _norm_category(it.category)

            row = QFrame()
            row.setObjectName("InvRow")
            row.setAttribute(Qt.WA_StyledBackground, True)
            row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            row.setFixedHeight(row_h)

            rh = QHBoxLayout(row)
            rh.setContentsMargins(14, 10, 14, 10)
            rh.setSpacing(10)

            left = QWidget()
            left.setAttribute(Qt.WA_StyledBackground, True)
            lv = QVBoxLayout(left)
            lv.setContentsMargins(0, 0, 0, 0)
            lv.setSpacing(3)

            title = QLabel(_primary_name(it))
            title.setObjectName("InvTitle")
            title.setWordWrap(False)
            title.setTextInteractionFlags(Qt.NoTextInteraction)

            last_txt = _fmt_num(it.last_price, 2) if it.last_price > 0 else "—"
            meta = QLabel(f"{cat.upper()} · qty {_fmt_qty(it.quantity)} · last {last_txt}")
            meta.setObjectName("InvMeta")
            meta.setWordWrap(False)

            lv.addWidget(title)
            lv.addWidget(meta)

            right = QWidget()
            right.setAttribute(Qt.WA_StyledBackground, True)
            rv = QVBoxLayout(right)
            rv.setContentsMargins(0, 0, 0, 0)
            rv.setSpacing(4)
            rv.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            value_txt = _fmt_num(it.value, 2) if it.value > 0 else "—"
            value = QLabel(value_txt)
            value.setObjectName("InvValue")
            value.setAlignment(Qt.AlignRight)

            badge_txt = f"{it.pct:.1f}%" if it.value > 0 else "—"
            badge = QLabel(badge_txt)
            badge.setObjectName("InvBadge")
            badge.setAlignment(Qt.AlignCenter)
            badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

            rv.addWidget(value, 0, Qt.AlignRight)
            rv.addWidget(badge, 0, Qt.AlignRight)

            rh.addWidget(left, 1)
            rh.addWidget(right, 0, Qt.AlignRight | Qt.AlignVCenter)

            self._inv_cards_layout.addWidget(row)

        pad = QWidget()
        pad.setFixedHeight(2)
        pad.setStyleSheet("background: transparent; border: 0px;")
        self._inv_cards_layout.addWidget(pad)

    def _refresh_investments_summary(self) -> None:
        if self._current_user_id is None:
            self._inv_items = []
            if self._inv_status is not None:
                self._inv_status.setText("Bitte einloggen, um dein Portfolio zu sehen.")
            self._render_investments_summary()
            return

        try:
            if self._inv_thread is not None and self._inv_thread.isRunning():
                return
        except RuntimeError:
            self._inv_thread = None
            self._inv_worker = None

        if self._inv_status is not None:
            self._inv_status.setText("Lade Portfolio …")

        thread = QThread(self)
        worker = InvestmentsSummaryWorker(user_id=int(self._current_user_id), category=self._inv_filter)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(self._on_investments_summary)
        worker.failed.connect(self._on_investments_summary_failed)

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
            if self._inv_thread is thread:
                self._inv_thread = None
            if self._inv_worker is worker:
                self._inv_worker = None

        thread.finished.connect(_cleanup)

        self._inv_thread = thread
        self._inv_worker = worker

        thread.start()

    def _on_investments_summary_failed(self, msg: str) -> None:
        self._inv_items = []
        if self._inv_status is not None:
            self._inv_status.setText(f"Portfolio konnte nicht geladen werden: {msg}")
        self._render_investments_summary()

    def _on_investments_summary(self, items: list) -> None:
        self._inv_items = [x for x in items if isinstance(x, InvestmentSummaryItem)]
        self._render_investments_summary()

    # --------------------------
    # Panels
    # --------------------------
    def _panel_with_body(self, title: str, placeholder: str, min_w: int = 260) -> tuple[QFrame, QLabel]:
        panel = QFrame()
        panel.setObjectName("Panel")
        panel.setAttribute(Qt.WA_StyledBackground, True)
        panel.setMinimumWidth(min_w)
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        v = QVBoxLayout(panel)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(10)

        if title.strip():
            t = QLabel(title)
            t.setObjectName("PanelTitle")
            t.setWordWrap(True)
            v.addWidget(t, 0, Qt.AlignLeft)

        body = QLabel(placeholder)
        body.setObjectName("Placeholder")
        body.setWordWrap(True)
        body.setTextFormat(Qt.RichText)

        v.addStretch(1)
        v.addWidget(body, 0, Qt.AlignHCenter | Qt.AlignVCenter)
        v.addStretch(1)
        return panel, body

    # --------------------------
    # Movers (overall)
    # --------------------------
    def _refresh_movers(self) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self._fmp_calls_date:
            self._fmp_calls_date = today
            self._fmp_calls_today = 0

        calls_needed = 2
        if self._fmp_calls_today + calls_needed > self._fmp_daily_limit:
            if self._overall_movers_label is not None:
                self._overall_movers_label.setText(
                    f"FMP Tageslimit erreicht ({self._fmp_calls_today}/{self._fmp_daily_limit}).<br>"
                    "Keine weiteren Movers-Updates heute."
                )
            return

        if self._overall_movers_label is not None:
            self._overall_movers_label.setText("Lade Movers …")

        fmp_key = os.getenv("FMP_API_KEY", "").strip()

        self._movers_thread = QThread(self)
        self._movers_worker = MoversFetcherWorker(fmp_key=fmp_key)
        self._movers_worker.moveToThread(self._movers_thread)

        self._movers_thread.started.connect(self._movers_worker.run)
        self._movers_worker.finished.connect(self._on_movers_fetched)
        self._movers_worker.failed.connect(self._on_movers_failed)

        self._movers_worker.finished.connect(self._movers_thread.quit)
        self._movers_worker.failed.connect(self._movers_thread.quit)
        self._movers_thread.finished.connect(self._movers_worker.deleteLater)
        self._movers_thread.finished.connect(self._movers_thread.deleteLater)

        self._fmp_calls_today += calls_needed
        self._movers_thread.start()

    def _on_movers_failed(self, msg: str) -> None:
        if self._overall_movers_label is not None:
            safe = (msg or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
            self._overall_movers_label.setText(f"Movers konnten nicht geladen werden:<br>{safe}")

    def _on_movers_fetched(self, gainers: list, losers: list) -> None:
        self._overall_gainers = [x for x in gainers if isinstance(x, MoverItem)]
        self._overall_losers = [x for x in losers if isinstance(x, MoverItem)]

        if self._overall_movers_label is not None:
            self._overall_movers_label.setText(
                self._format_movers_block(self._overall_gainers, self._overall_losers, n=3)
            )

    # --------------------------
    # Favorites movers
    # --------------------------
    def _refresh_favorite_movers(self, force: bool = False) -> None:
        if self._fav_movers_label is None:
            return
        if not self._favorite_symbols:
            self._fav_movers_label.setText("Keine Favoriten")
            return

        now_ts = int(datetime.now().timestamp())

        if not force and self._fav_last_fetch_ts and (now_ts - self._fav_last_fetch_ts) < self._fav_min_fetch_interval_s:
            if not self._fav_cached_items:
                self._fav_movers_label.setText("Lade Favoriten Movers …")
            return

        if not self._fav_cached_items:
            self._fav_movers_label.setText("Lade Favoriten Movers …")

        if self._fav_thread is not None and self._fav_thread.isRunning():
            return

        self._fav_last_fetch_ts = now_ts

        fmp_key = os.getenv("FMP_API_KEY", "").strip()

        self._fav_thread = QThread(self)
        self._fav_worker = FavoritesMoversWorker(fmp_key=fmp_key, symbols=self._favorite_symbols)
        self._fav_worker.moveToThread(self._fav_thread)

        self._fav_thread.started.connect(self._fav_worker.run)
        self._fav_worker.finished.connect(self._on_fav_movers_fetched)
        self._fav_worker.failed.connect(self._on_fav_movers_failed)

        self._fav_worker.finished.connect(self._fav_thread.quit)
        self._fav_worker.failed.connect(self._fav_thread.quit)
        self._fav_thread.finished.connect(self._fav_worker.deleteLater)
        self._fav_thread.finished.connect(self._fav_thread.deleteLater)

        self._fav_thread.start()

    def _on_fav_movers_failed(self, msg: str) -> None:
        if self._fav_movers_label is None:
            return

        if self._fav_cached_items:
            return

        safe = (msg or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        self._fav_movers_label.setText(f"Favoriten Movers konnten nicht geladen werden:<br>{safe}")

    def _on_fav_movers_fetched(self, items: list) -> None:
        if self._fav_movers_label is None:
            return

        favs: list[FavQuoteItem] = [x for x in items if isinstance(x, FavQuoteItem)]
        if not favs:
            if self._fav_cached_items:
                return
            self._fav_movers_label.setText("Keine Favoriten-Daten gefunden.")
            return

        self._fav_cached_items = favs[:]
        self._save_fav_cache(self._fav_cached_items)

        self._fav_movers_label.setText(self._format_favorites_movers_block(favs, n=6))

    def _format_favorites_movers_block(self, items: list[FavQuoteItem], n: int = 6) -> str:
        def clamp_name(s: str, max_len: int = 26) -> str:
            s = (s or "").strip()
            return s if len(s) <= max_len else s[:max_len - 1] + "…"

        def esc(s: str) -> str:
            return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        green = "#4ADE80"
        red = "#FB7185"

        def row_html(it: FavQuoteItem) -> str:
            positive = it.change_pct >= 0
            num_color = green if positive else red
            sign = "+" if positive else ""
            name = clamp_name(it.name, 26)
            return (
                "<div style='margin: 8px 0 10px 0;'>"
                f"  <div><span style='font-weight:900;'>{esc(it.symbol)}</span> &nbsp;·&nbsp; {esc(name)}</div>"
                f"  <div style='color:{num_color}; font-weight:850;'>{sign}{it.change_pct:.2f}% &nbsp;·&nbsp; {it.price:.2f}</div>"
                "</div>"
            )

        top = items[:max(1, int(n))]
        block = "".join(row_html(x) for x in top) if top else "<div>—</div>"

        return f"""
        <div style="font-size: 12px; line-height: 1.25; color: rgba(230,234,240,235); text-align:center;">
          {block}
        </div>
        """.strip()

    def _format_movers_block(self, gainers: list[MoverItem], losers: list[MoverItem], n: int = 3) -> str:
        def clamp_name(s: str, max_len: int = 26) -> str:
            s = (s or "").strip()
            return s if len(s) <= max_len else s[:max_len - 1] + "…"

        def esc(s: str) -> str:
            return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        green = "#4ADE80"
        red = "#FB7185"

        def item_html(it: MoverItem, positive: bool) -> str:
            num_color = green if positive else red
            sign = "+" if positive else ""
            name = clamp_name(it.name, 26)
            return (
                "<div style='margin: 8px 0 10px 0;'>"
                f"  <div><span style='font-weight:900;'>{esc(it.symbol)}</span> &nbsp;·&nbsp; {esc(name)}</div>"
                f"  <div style='color:{num_color}; font-weight:850;'>{sign}{it.change_pct:.2f}% &nbsp;·&nbsp; {it.price:.2f}</div>"
                "</div>"
            )

        top_g = gainers[:n]
        top_l = losers[:n]

        g_block = "".join(item_html(it, True) for it in top_g) if top_g else "<div>—</div>"
        l_block = "".join(item_html(it, False) for it in top_l) if top_l else "<div>—</div>"

        return f"""
        <div style="font-size: 12px; line-height: 1.25; color: rgba(230,234,240,235); text-align:center;">
          <div style="color:{green}; font-weight:900; margin-bottom:6px;">Positiv</div>
          {g_block}
          <div style="height:22px;"></div>
          <div style="color:{red}; font-weight:900; margin-bottom:6px;">Negativ</div>
          {l_block}
        </div>
        """.strip()

    # --------------------------
    # News
    # --------------------------
    def _refresh_news(self) -> None:
        if self._news_loading_label is not None:
            self._news_loading_label.setText("Lade News …")
            self._news_loading_label.setVisible(True)

        finnhub_key = os.getenv("FINNHUB_API_KEY", "").strip()
        gdelt_query = os.getenv(
            "AURELIC_GDELT_QUERY",
            "politics OR election OR government OR parliament OR sanctions OR war OR inflation OR central bank OR interest rates"
        ).strip()

        self._news_thread = QThread(self)
        self._news_worker = NewsFetcherWorker(finnhub_key=finnhub_key, gdelt_query=gdelt_query)
        self._news_worker.moveToThread(self._news_thread)

        self._news_thread.started.connect(self._news_worker.run)
        self._news_worker.finished.connect(self._on_news_fetched)
        self._news_worker.failed.connect(self._on_news_failed)

        self._news_worker.finished.connect(self._news_thread.quit)
        self._news_worker.failed.connect(self._news_thread.quit)
        self._news_thread.finished.connect(self._news_worker.deleteLater)
        self._news_thread.finished.connect(self._news_thread.deleteLater)

        self._news_thread.start()

    def _on_news_failed(self, msg: str) -> None:
        if self._news_loading_label is not None:
            self._news_loading_label.setText(f"News konnten nicht geladen werden: {msg}")
            self._news_loading_label.setVisible(True)
        self._render_news()

    def _on_news_fetched(self, items: list) -> None:
        self._news_items = [it for it in items if isinstance(it, NewsItem)]
        self._news_page = 0

        if self._news_loading_label is not None:
            if not self._news_items:
                self._news_loading_label.setText("Keine News gefunden (Filter/Key prüfen).")
                self._news_loading_label.setVisible(True)
            else:
                self._news_loading_label.setVisible(False)

        self._update_news_capacity()
        self._render_news()

    def _rotate_news_page(self) -> None:
        if not self._news_items:
            return
        page_size = max(1, int(self._news_page_size))
        pages = max(1, (len(self._news_items) + page_size - 1) // page_size)
        self._news_page = (self._news_page + 1) % pages
        if self._news_scroll is not None:
            self._news_scroll.verticalScrollBar().setValue(0)
        self._render_news()

    def _render_news(self) -> None:
        if not self._news_cards:
            return

        total = len(self._news_items)
        page_size = max(1, int(self._news_page_size))
        pages = max(1, (total + page_size - 1) // page_size)

        if self._news_page < 0:
            self._news_page = 0
        if self._news_page > pages - 1:
            self._news_page = pages - 1

        start = self._news_page * page_size
        end = min(total, start + page_size)
        chunk = self._news_items[start:end]

        if self._news_footer_label is not None:
            if total > 0:
                self._news_footer_label.setText("")
            else:
                self._news_footer_label.setText("")

        for i in range(len(self._news_cards)):
            card = self._news_cards[i]
            title = self._news_title_labels[i]
            meta = self._news_meta_labels[i]

            if i < len(chunk):
                it = chunk[i]
                title.setText(it.title)
                meta.setText(f"{_fmt_time(it.published_ts)} · {it.source} · {it.tag.upper()}")
                card.set_url(it.url)
                card.setVisible(True)
            else:
                card.set_url("")
                card.setVisible(False)
                title.setText("")
                meta.setText("")

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._onboarding_pending:
            self._onboarding_pending = False
            self.maybe_start_onboarding()