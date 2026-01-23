# gui/brokerage.py
from __future__ import annotations

import os
import json
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from datetime import date


from PySide6.QtCore import Qt, Signal, QTimer, QThread, QObject, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout, QSizePolicy, QDialog,
    QScrollArea
)

from gui.widgets.segmentedtabs import SegmentedTabs
from PySide6.QtWidgets import QComboBox

from controller.stock_view import StockViewController
from src.stocks.db_calls import get_all_assets
from src.stocks.timeframes import TIMEFRAMES

from PySide6.QtGui import QPen, QColor
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import QDateTime, Qt




# --------------------------
# Theme (same as StartPage)
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

    /* App background image */
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

    /* ---- Segmented Tabs (Analyse/Brokerage) ---- */
    QFrame#SegmentedTabs {{
        background: rgba(255,255,255,10);
        border: 1px solid rgba(39,48,59,170);
        border-radius: 999px;
        padding: 2px; /* entspricht pad=2 im SegmentedTabs-Code */
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
    /* ------------------------------------------- */

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

    /* ScrollArea: modern und unauffällig */
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

    /* External Link Dialog */
    #SectionTitle {{
        font-size: 20px;
        font-weight: 900;
        letter-spacing: -0.3px;
        color: {p.text0};
    }}

    #UrlBox {{
        background: rgba(255,255,255,6);
        border: 1px solid rgba(39,48,59,170);
        border-radius: 14px;
        padding: 10px 12px;
        color: rgba(230,234,240,220);
        font-size: 12px;
    }}

    QPushButton#Ghost {{
        background: transparent;
        border: 1px solid rgba(39,48,59,170);
        border-radius: 16px;
        padding: 10px 14px;
        font-weight: 850;
        color: rgba(230,234,240,180);
    }}
    QPushButton#Ghost:hover {{
        border: 1px solid rgba(109,146,155,90);
        color: {p.text0};
    }}

    QPushButton#Primary {{
        background: rgba(109,146,155,55);
        border: 1px solid rgba(109,146,155,110);
        border-radius: 16px;
        padding: 10px 14px;
        font-weight: 900;
        color: {p.text0};
    }}
    QPushButton#Primary:hover {{
        background: rgba(109,146,155,70);
        border: 1px solid rgba(109,146,155,160);
    }}
    """


# --------------------------
# News models
# --------------------------
@dataclass(frozen=True)
class NewsItem:
    title: str
    source: str
    published_ts: int  # unix ts seconds
    url: str
    tag: str           # "stocks" | "politics"


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


# --------------------------
# Movers models (FMP)
# --------------------------
@dataclass(frozen=True)
class MoverItem:
    symbol: str
    name: str
    change_pct: float
    price: float


# --------------------------
# External link confirmation dialog
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


# --------------------------
# Clickable news card
# --------------------------
class ClickableNewsCard(QFrame):
    clicked = Signal(str)  # url

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
# Background fetch worker (News)
# --------------------------
class NewsFetcherWorker(QObject):
    finished = Signal(list)      # list[NewsItem]
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


# --------------------------
# Background fetch worker (FMP Movers)
# --------------------------
class MoversFetcherWorker(QObject):
    finished = Signal(list, list)  # gainers, losers
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
        stable_map = {
            "gainers": "biggest-gainers",
            "losers": "biggest-losers",
        }
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


# --------------------------
# Main Page
# --------------------------
class MainPage(QWidget):
    tab_changed = Signal(str)   # "brokerage" | "analyse"
    avatar_clicked = Signal()
    calendar_clicked = Signal()

    def __init__(self, background_path: str = "images/Backgroundimage.png", parent: QWidget | None = None):
        super().__init__(parent)

        self.setObjectName("Root")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)

        self._palette = Palette()
        self._background_path = background_path
        self.setStyleSheet(build_qss(self._palette, self._background_path))

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

        # FMP rate limit
        self._fmp_calls_today: int = 0
        self._fmp_calls_date: str = datetime.now().strftime("%Y-%m-%d")
        self._fmp_daily_limit: int = 200

        # Timers
        self._news_refresh_timer = QTimer(self)
        self._news_refresh_timer.setInterval(180_000)
        self._news_refresh_timer.timeout.connect(self._refresh_news)

        self._news_rotate_timer = QTimer(self)
        self._news_rotate_timer.setInterval(180_000)
        self._news_rotate_timer.timeout.connect(self._rotate_news_page)

        self._movers_refresh_timer = QTimer(self)
        self._movers_refresh_timer.setInterval(1_200_000)  # 20 Minuten
        self._movers_refresh_timer.timeout.connect(self._refresh_movers)

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
        shell_v.addWidget(self._build_middle_area(), 1)
        shell_v.addWidget(self._build_investments_area(), 0)

        self._root.addWidget(self._shell, 0, Qt.AlignCenter)

        self._set_active_tab("brokerage", sync_tabs=True)

        self._refresh_news()
        self._news_refresh_timer.start()
        self._news_rotate_timer.start()

        self._refresh_movers()
        self._movers_refresh_timer.start()

        QTimer.singleShot(0, self._update_news_capacity)

        # --- Stock chart state ---
        self._token: str | None = None
        self._stock_ctrl = StockViewController()
        self._stock_ctrl.series_ready.connect(self._on_series_ready)
        self._stock_ctrl.series_failed.connect(self._on_series_failed)

        self._symbol_box: QComboBox | None = None
        self._tf_box: QComboBox | None = None
        self._chart: QChart | None = None
        self._series: QLineSeries | None = None
        self._chart_view: QChartView | None = None
        self._x_axis: QValueAxis | None = None
        self._y_axis: QValueAxis | None = None

        self._x_axis = None
        self._y_axis = None

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)

        m = 40
        avail_w = max(300, self.width() - 2 * m)
        avail_h = max(300, self.height() - 2 * m)

        ratio = 1.568
        w = min(avail_w, int(avail_h * ratio))
        h = min(avail_h, int(w / ratio))
        self._shell.setFixedSize(w, h)

        self._update_news_capacity()

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

        cal_btn = QPushButton("◯")
        cal_btn.setObjectName("CalendarBtn")
        cal_btn.setFixedSize(44, 44)
        cal_btn.clicked.connect(self.calendar_clicked.emit)

        avatar = QPushButton("N")
        avatar.setObjectName("Avatar")
        avatar.setFixedSize(44, 44)
        avatar.clicked.connect(self.avatar_clicked.emit)

        h.addWidget(self._seg_tabs, 0, Qt.AlignLeft)
        h.addStretch(1)
        h.addWidget(cal_btn, 0, Qt.AlignRight)
        h.addWidget(avatar, 0, Qt.AlignRight)
        return bar

    def _set_active_tab(self, which: str, sync_tabs: bool = True) -> None:
        which = "analyse" if which == "analyse" else "brokerage"
        if sync_tabs and hasattr(self, "_seg_tabs") and self._seg_tabs is not None:
            self._seg_tabs.set_active(which, animate=True, emit=False)
        self.tab_changed.emit(which)

    # --------------------------
    # Middle area
    # --------------------------
    def _build_middle_area(self) -> QWidget:
        w = QWidget()
        w.setAttribute(Qt.WA_StyledBackground, True)

        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(14)

        left = self._build_news_panel(min_w=360)
        left.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        center = self._build_chart_panel(min_w=860)
        center.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        center.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        right = QWidget()
        right.setAttribute(Qt.WA_StyledBackground, True)
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(14)

        right_top, self._overall_movers_label = self._panel_with_body(
            title="Top Mover:",
            placeholder="Lade Movers …",
            min_w=320
        )

        if self._overall_movers_label is not None:
            self._overall_movers_label.setTextFormat(Qt.RichText)
            self._overall_movers_label.setTextInteractionFlags(Qt.NoTextInteraction)
            self._overall_movers_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        right_bottom = self._build_favorites_panel(min_w=320)

        right_top.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        right_bottom.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        rv.addWidget(right_top, 1)
        rv.addWidget(right_bottom, 1)

        h.addWidget(left, 0)
        h.addWidget(center, 1)
        h.addWidget(right, 0)
        return w

    def _build_favorites_panel(self, min_w: int = 320) -> QFrame:

        panel = QFrame()
        panel.setObjectName("Panel")
        panel.setAttribute(Qt.WA_StyledBackground, True)
        panel.setMinimumWidth(min_w)

        v = QVBoxLayout(panel)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(10)

        t = QLabel("Favoriten-Kategorie\nTop Mover")
        t.setObjectName("PanelTitle")
        t.setWordWrap(True)
        v.addWidget(t, 0, Qt.AlignLeft)

        # Apple Button (Test)
        btn = QPushButton("AAPL · Apple (Polygon 7D)")
        btn.setObjectName("Ghost")
        btn.clicked.connect(self._load_apple_test_range)
        self._fav_apple_btn = btn
        v.addWidget(btn, 0)

        v.addStretch(1)
        return panel

#    --------------------------------------TESTER FOR CHARTS-------------------------------------------

    def _load_apple_test_range(self) -> None:
        if not self._token:
            return

        if hasattr(self, "_fav_apple_btn") and self._fav_apple_btn:
            self._fav_apple_btn.setEnabled(False)

        self._stock_ctrl.load_polygon_7d_async(self._token, "AAPL")

    # --------------------------------------------END TESTER------------------------------------------------

    # --------------------------
    # Chart area
    # --------------------------

    def _build_chart_panel(self, min_w: int = 860) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        panel.setAttribute(Qt.WA_StyledBackground, True)
        panel.setMinimumWidth(min_w)

        v = QVBoxLayout(panel)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(10)

        # header row (controls)
        header = QWidget()
        hh = QHBoxLayout(header)
        hh.setContentsMargins(0, 0, 0, 0)
        hh.setSpacing(10)

        title = QLabel("Chart")
        title.setObjectName("PanelTitle")

        self._symbol_box = QComboBox()
        self._tf_box = QComboBox()

        hh.addWidget(title, 0, Qt.AlignLeft)
        hh.addStretch(1)
        hh.addWidget(self._symbol_box, 0)
        hh.addWidget(self._tf_box, 0)

        # chart
        self._chart = QChart()
        self._chart.legend().hide()

        self._series = QLineSeries()
        self._chart.addSeries(self._series)

        self._x_axis = QValueAxis()
        self._chart.addAxis(self._x_axis, Qt.AlignBottom)
        self._series.attachAxis(self._x_axis)

        self._y_axis = QValueAxis()
        self._chart.addAxis(self._y_axis, Qt.AlignLeft)
        self._series.attachAxis(self._y_axis)

        self._chart_view = QChartView(self._chart)
        self._chart_view.setRenderHint(QPainter.Antialiasing, True)
        self._chart_view.setStyleSheet("background: transparent;")

        v.addWidget(header, 0)
        v.addWidget(self._chart_view, 1)

        # wire changes
        self._symbol_box.currentIndexChanged.connect(self._reload_series_if_ready)
        self._tf_box.currentIndexChanged.connect(self._reload_series_if_ready)

        self._chart.setPlotAreaBackgroundVisible(True)
        self._chart.setPlotAreaBackgroundBrush(QColor(self._palette.bg0))

        self._chart.setBackgroundVisible(True)
        self._chart.setBackgroundBrush(QColor(self._palette.bg1))

        # if token already known, init
        QTimer.singleShot(0, self._init_stock_controls)
        return panel

    def _parse_dt_to_ms(self, x_str: str) -> float | None:
        s = str(x_str).strip()

        # Daily: "YYYY-MM-DD"
        if len(s) == 10 and s[4] == "-" and s[7] == "-":
            s = s + "T00:00:00"

        # Intraday often: "YYYY-MM-DD HH:MM:SS.ffffff"
        s = s.replace(" ", "T")

        # Qt ISODate is happiest with milliseconds (3 digits), not microseconds (6)
        if "." in s:
            head, frac = s.split(".", 1)
            frac = "".join(ch for ch in frac if ch.isdigit())
            if len(frac) >= 3:
                frac = frac[:3]
                s = f"{head}.{frac}"
            else:
                # no usable millis -> drop fraction
                s = head

        dt = QDateTime.fromString(s, Qt.ISODate)
        if not dt.isValid():
            return None

        return float(dt.toMSecsSinceEpoch())

    def _init_stock_controls(self) -> None:
        if not self._token:
            return
        if not self._symbol_box or not self._tf_box:
            return
        if self._symbol_box.count() > 0 and self._tf_box.count() > 0:
            return  # already initialized

        # load assets
        assets = get_all_assets(self._token)  # [(sym,name,cat),...]
        self._symbol_box.clear()
        for sym, name, cat in assets:
            self._symbol_box.addItem(f"{sym} · {name}", sym)

        # timeframes
        self._tf_box.clear()
        for tf in TIMEFRAMES:
            self._tf_box.addItem(tf.label, tf.key)

        # defaults
        if self._symbol_box.count() > 0:
            self._symbol_box.setCurrentIndex(0)
        # default to 1Y if present
        for i in range(self._tf_box.count()):
            if self._tf_box.itemData(i) == "1y":
                self._tf_box.setCurrentIndex(i)
                break

        self._reload_series_if_ready()

    def _reload_series_if_ready(self) -> None:
        if not self._token or not self._symbol_box or not self._tf_box:
            return
        if self._symbol_box.count() == 0 or self._tf_box.count() == 0:
            return

        sym = self._symbol_box.currentData()
        tf = self._tf_box.currentData()
        if not sym or not tf:
            return

        self._stock_ctrl.load_series_async(self._token, sym, tf)

    def _on_series_ready(self, payload: dict) -> None:
        if not self._chart_view:
            return

        pts = payload.get("points") or []
        print("SERIES:", payload.get("symbol"), payload.get("timeframe"), "points=", len(pts))

        # Build a brand-new chart every time (robust against axis/attach issues)
        chart = QChart()
        chart.legend().hide()

        # Backgrounds (dark)
        chart.setBackgroundVisible(True)
        chart.setBackgroundBrush(QColor(self._palette.bg1))
        chart.setPlotAreaBackgroundVisible(True)
        chart.setPlotAreaBackgroundBrush(QColor(self._palette.bg0))

        series = QLineSeries()

        # Visible styling on dark bg
        pen = QPen(QColor(self._palette.accent2))
        pen.setWidth(2)
        series.setPen(pen)
        series.setPointsVisible(True)

        ymin = ymax = None
        xmin = xmax = None
        appended = 0

        for x_str, y in pts:
            try:
                x_ms = self._parse_dt_to_ms(x_str)
                if x_ms is None:
                    print("BAD DT:", x_str)
                    continue

                y_f = float(y)
                series.append(x_ms, y_f)
                appended += 1

                ymin = y_f if ymin is None else min(ymin, y_f)
                ymax = y_f if ymax is None else max(ymax, y_f)
                xmin = x_ms if xmin is None else min(xmin, x_ms)
                xmax = x_ms if xmax is None else max(xmax, x_ms)
            except Exception as e:
                print("SKIP:", x_str, y, e)
                continue

        print("APPENDED:", appended, "xmin:", xmin, "xmax:", xmax, "ymin:", ymin, "ymax:", ymax)

        if appended == 0 or xmin is None or xmax is None or ymin is None or ymax is None:
            # show empty chart anyway
            self._chart_view.setChart(chart)
            self._chart = chart
            return

        chart.addSeries(series)

        x_axis = QValueAxis()
        y_axis = QValueAxis()

        chart.addAxis(x_axis, Qt.AlignBottom)
        chart.addAxis(y_axis, Qt.AlignLeft)

        series.attachAxis(x_axis)
        series.attachAxis(y_axis)

        x_axis.setRange(xmin, xmax)
        pad = (ymax - ymin) * 0.05 if ymax > ymin else max(1.0, abs(ymax) * 0.01, 1.0)
        y_axis.setRange(ymin - pad, ymax + pad)

        # Swap chart into the view (THIS is the key)
        self._chart_view.setChart(chart)
        self._chart = chart

        if hasattr(self, "_fav_apple_btn") and self._fav_apple_btn:
            self._fav_apple_btn.setEnabled(True)

    def _on_series_failed(self, msg: str) -> None:
        if hasattr(self, "_fav_apple_btn") and self._fav_apple_btn:
            self._fav_apple_btn.setEnabled(True)
        # simple: clear series (keeps UI responsive)
        if self._series is not None:
            self._series.clear()

    def set_token(self, token: str) -> None:
        self._token = (token or "").strip() or None
        if not self._token:
            return

        # populate symbol/timeframe dropdowns and load initial series
        self._init_stock_controls()


    # --------------------------
    # News Panel (scrollbar + dynamische "Page Size" fürs Feeling)
    # --------------------------
    def _build_news_panel(self, min_w: int = 360) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        panel.setAttribute(Qt.WA_StyledBackground, True)
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

        self._ensure_news_cards(10)
        return panel

    def _ensure_news_cards(self, count: int) -> None:
        if self._news_cards_layout is None:
            return

        count = max(1, int(count))

        while len(self._news_cards) > count:
            card = self._news_cards.pop()
            title = self._news_title_labels.pop()
            meta = self._news_meta_labels.pop()
            self._news_cards_layout.removeWidget(card)
            card.deleteLater()
            title.deleteLater()
            meta.deleteLater()

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
        visible_cards = max(6, min(14, int(usable_h // est_card_h)))

        desired_total_cards = max(visible_cards, min(40, visible_cards * 3))
        if desired_total_cards != len(self._news_cards):
            self._ensure_news_cards(desired_total_cards)

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

    def _build_investments_area(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card.setAttribute(Qt.WA_StyledBackground, True)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        v = QVBoxLayout(card)
        v.setContentsMargins(18, 14, 18, 14)
        v.setSpacing(10)

        title = QLabel("Investments")
        title.setObjectName("PanelTitle")

        hint = QLabel("Hier kommt später z. B. eine Tabelle/Scrollable Liste deiner Investments hin.")
        hint.setObjectName("FinePrint")
        hint.setWordWrap(True)

        placeholder = QFrame()
        placeholder.setObjectName("Panel")
        placeholder.setAttribute(Qt.WA_StyledBackground, True)
        placeholder.setFixedHeight(160)

        ph = QVBoxLayout(placeholder)
        ph.setContentsMargins(14, 14, 14, 14)
        ph.setSpacing(6)

        txt = QLabel("Investment-Liste (Placeholder)")
        txt.setObjectName("Placeholder")
        txt.setAlignment(Qt.AlignCenter)
        txt.setWordWrap(True)
        txt.setMinimumHeight(28)
        txt.setTextInteractionFlags(Qt.NoTextInteraction)

        ph.addWidget(txt, 0, Qt.AlignCenter)

        v.addWidget(title)
        v.addWidget(hint)
        v.addWidget(placeholder)
        return card

    def _panel(self, title: str, placeholder: str, min_w: int = 260) -> QFrame:
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
        body.setAlignment(Qt.AlignCenter)

        v.addStretch(1)
        v.addWidget(body, 0, Qt.AlignCenter)
        v.addStretch(1)
        return panel

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

    def _format_movers_block(self, gainers: list[MoverItem], losers: list[MoverItem], n: int = 3) -> str:
        def clamp_name(s: str, max_len: int = 26) -> str:
            s = (s or "").strip()
            if len(s) <= max_len:
                return s
            return s[:max_len - 1] + "…"

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
        pages = max(1, (len(self._news_items) + self._news_page_size - 1) // self._news_page_size)
        self._news_page = (self._news_page + 1) % pages
        if self._news_scroll is not None:
            self._news_scroll.verticalScrollBar().setValue(0)
        self._render_news()

    def _render_news(self) -> None:
        chunk = self._news_items[:len(self._news_cards)]

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
