# gui/mainpage.py
from __future__ import annotations

import os
import json
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt, Signal, QTimer, QThread, QObject, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout, QSizePolicy, QDialog
)

# FIX: richtiger Import + richtiger Dateiname
# Deine Datei heißt gui/widgets/segmentedtabs.py
from gui.widgets.segmentedtabs import SegmentedTabs


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


def build_qss(p: Palette) -> str:
    return f"""
    QWidget {{
        background: {p.bg0};
        color: {p.text0};
        font-family: "Segoe UI", "Inter", "Helvetica", "Arial";
    }}

    #Root {{
        background: qradialgradient(cx:0.15, cy:0.10, radius:1.1,
                                   fx:0.15, fy:0.10,
                                   stop:0 rgba(109,146,155,30),
                                   stop:1 rgba(11,13,16,255));
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
    #SegmentedTabs {{
        background: rgba(255,255,255,10);
        border: 1px solid rgba(39,48,59,170);
        border-radius: 999px; /* komplett rund */
        padding: 0px;
    }}

    #SegmentedIndicator {{
        background: rgba(230,234,240,235);
        border: 1px solid rgba(39,48,59,110);
        border-radius: 999px; /* komplett rund */
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

    /* News (FIX: multi-line titles, no clipping) */
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
# External link confirmation dialog
# --------------------------
class ExternalLinkDialog(QDialog):
    def __init__(self, url: str, palette: Palette, parent: QWidget | None = None):
        super().__init__(parent)

        self._url = (url or "").strip()

        self.setWindowTitle("Externe Ressource öffnen")
        self.setModal(True)
        self.setObjectName("Root")
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.setStyleSheet(build_qss(palette))
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
# Background fetch worker
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
            for n in j[:30]:
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
            "maxrecords": "30",
            "sort": "hybridrel",
            "formatdatetime": "0",
        }
        url = f"{base}?{urllib.parse.urlencode(params)}"

        j = self._read_json(url, headers={"User-Agent": "Aurelic/1.0 (Desktop App)"})

        arts = j.get("articles", [])
        if isinstance(arts, list):
            for a in arts[:30]:
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
# Main Page
# --------------------------
class MainPage(QWidget):
    tab_changed = Signal(str)   # "brokerage" | "analyse"
    avatar_clicked = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setObjectName("Root")
        self._palette = Palette()
        self.setStyleSheet(build_qss(self._palette))
        self.setAttribute(Qt.WA_StyledBackground, True)

        self._news_items: list[NewsItem] = []
        self._news_page: int = 0
        self._news_page_size: int = 6

        self._news_cards: list[ClickableNewsCard] = []
        self._news_title_labels: list[QLabel] = []
        self._news_meta_labels: list[QLabel] = []
        self._news_loading_label: QLabel | None = None

        self._news_refresh_timer = QTimer(self)
        self._news_refresh_timer.setInterval(180_000)
        self._news_refresh_timer.timeout.connect(self._refresh_news)

        self._news_rotate_timer = QTimer(self)
        self._news_rotate_timer.setInterval(180_000)
        self._news_rotate_timer.timeout.connect(self._rotate_news_page)

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

        # FIX: also set segmented control to brokerage on init (keeps UI in sync)
        self._set_active_tab("brokerage", sync_tabs=True)

        self._refresh_news()
        self._news_refresh_timer.start()
        self._news_rotate_timer.start()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)

        m = 40
        avail_w = max(300, self.width() - 2 * m)
        avail_h = max(300, self.height() - 2 * m)

        ratio = 1.568
        w = min(avail_w, int(avail_h * ratio))
        h = min(avail_h, int(w / ratio))
        self._shell.setFixedSize(w, h)

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

        # FIX: when user clicks, we switch pages AND keep UI state in sync
        self._seg_tabs.changed.connect(lambda which: self._set_active_tab(which, sync_tabs=False))

        avatar = QPushButton("N")
        avatar.setObjectName("Avatar")
        avatar.setFixedSize(44, 44)
        avatar.clicked.connect(self.avatar_clicked.emit)

        h.addWidget(self._seg_tabs, 0, Qt.AlignLeft)
        h.addStretch(1)
        h.addWidget(avatar, 0, Qt.AlignRight)
        return bar

    def _set_active_tab(self, which: str, sync_tabs: bool = True) -> None:
        which = "analyse" if which == "analyse" else "brokerage"

        # keep segmented tabs visual state in sync even when page changes externally
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

        center = self._panel(
            title="",
            placeholder="Linienchart oder\nKerzenchart",
            min_w=860
        )
        center.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        right = QWidget()
        right.setAttribute(Qt.WA_StyledBackground, True)
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(14)

        right_top = self._panel(
            title="Overall\nTop Mover",
            placeholder="+\n-",
            min_w=320
        )
        right_bottom = self._panel(
            title="Favoriten-Kategorie\nTop Mover",
            placeholder="+\n-",
            min_w=320
        )

        right_top.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        right_bottom.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        rv.addWidget(right_top, 1)
        rv.addWidget(right_bottom, 1)

        h.addWidget(left, 0)
        h.addWidget(center, 1)
        h.addWidget(right, 0)
        return w

    # ... Rest bleibt identisch bei dir (News Panel / Refresh / Render / Investments / Panel Helper)

    def _build_news_panel(self, min_w: int = 360) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        panel.setAttribute(Qt.WA_StyledBackground, True)
        panel.setMinimumWidth(min_w)

        v = QVBoxLayout(panel)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(10)

        title = QLabel("Favoriten-Kategorie\nNews")
        title.setObjectName("PanelTitle")
        title.setWordWrap(True)
        v.addWidget(title, 0, Qt.AlignLeft)

        self._news_loading_label = QLabel("Lade News …")
        self._news_loading_label.setObjectName("FinePrint")
        self._news_loading_label.setWordWrap(True)
        v.addWidget(self._news_loading_label)

        # cards with wrap-capable QLabel titles
        self._news_cards.clear()
        self._news_title_labels.clear()
        self._news_meta_labels.clear()

        for _ in range(self._news_page_size):
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
            v.addWidget(card)

            self._news_cards.append(card)
            self._news_title_labels.append(t)
            self._news_meta_labels.append(meta)

        v.addStretch(1)

        footer = QLabel("Aktualisiert alle 3 Minuten (Finnhub + GDELT).")
        footer.setObjectName("FinePrint")
        footer.setWordWrap(True)
        v.addWidget(footer)

        return panel

    # --------------------------
    # External open confirm
    # --------------------------
    def _open_news_url_confirmed(self, url: str) -> None:
        url = (url or "").strip()
        if not url:
            return

        dlg = ExternalLinkDialog(url=url, palette=self._palette, parent=self)
        if dlg.exec() == QDialog.Accepted:
            QDesktopServices.openUrl(QUrl(dlg.url))

    # --------------------------
    # Investments area
    # --------------------------
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

    # --------------------------
    # Generic panel helper
    # --------------------------
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

    # --------------------------
    # News: refresh + rotate
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

        self._render_news()

    def _rotate_news_page(self) -> None:
        if not self._news_items:
            return
        pages = max(1, (len(self._news_items) + self._news_page_size - 1) // self._news_page_size)
        self._news_page = (self._news_page + 1) % pages
        self._render_news()

    def _render_news(self) -> None:
        items = self._news_items
        start = self._news_page * self._news_page_size
        chunk = items[start:start + self._news_page_size]

        for i in range(self._news_page_size):
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
