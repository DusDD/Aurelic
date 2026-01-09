# gui/widgets/worldbank_feed.py
from __future__ import annotations

import json
import time
import socket
import urllib.request
from urllib.error import URLError, HTTPError
from dataclasses import dataclass
from typing import Any, Callable

# --- SSL fix (macOS robust) ---
# Requires: pip install certifi
import ssl
import certifi

from PySide6.QtCore import (
    QObject, QRunnable, QThreadPool, Signal, Slot, Qt,
    QEvent, QTimer
)
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout,
    QComboBox, QListWidget, QListWidgetItem, QPushButton,
    QSizePolicy
)


# ----------------------------
# Minimal async worker (QRunnable)
# ----------------------------
class _WorkerSignals(QObject):
    ok = Signal(object)
    err = Signal(str)


class _Worker(QRunnable):
    def __init__(self, fn: Callable[[], Any]):
        super().__init__()
        self.fn = fn
        self.signals = _WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            self.signals.ok.emit(self.fn())
        except Exception as e:
            self.signals.err.emit(str(e))


# ----------------------------
# Robust HTTP JSON fetch with:
# - certifi SSL
# - retries + exponential backoff
# - in-memory cache (TTL)
# ----------------------------
_CACHE: dict[str, tuple[float, Any]] = {}
_CACHE_TTL_SEC = 600  # 10 minutes


def _http_get_json(url: str, timeout: int = 12, retries: int = 3) -> Any:
    now = time.time()
    cached = _CACHE.get(url)
    if cached is not None:
        ts, data = cached
        if now - ts < _CACHE_TTL_SEC:
            return data

    ctx = ssl.create_default_context(cafile=certifi.where())

    last_err: Exception | None = None
    backoff = 0.6

    for _attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PySide6-App"})
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                raw = r.read().decode("utf-8")
            data = json.loads(raw)
            _CACHE[url] = (time.time(), data)
            return data

        except (socket.timeout, TimeoutError) as e:
            last_err = e
        except (HTTPError, URLError) as e:
            last_err = e
        except Exception as e:
            last_err = e
            break

        time.sleep(backoff)
        backoff *= 1.8

    raise RuntimeError(f"Request failed after {retries} retries: {last_err}")


# ----------------------------
# World Bank API helpers
# ----------------------------
WB_BASE = "https://api.worldbank.org/v2"

# "Voll" + sinnvoll strukturiert. None = Abschnittsüberschrift
INDICATORS: dict[str, str | None] = {
    "— Growth & Economy —": None,
    "GDP growth (annual %)": "NY.GDP.MKTP.KD.ZG",
    "GDP per capita growth (%)": "NY.GDP.PCAP.KD.ZG",
    "GDP per capita (current US$)": "NY.GDP.PCAP.CD",
    "Investment / Capital formation (% of GDP)": "NE.GDI.TOTL.ZS",
    "Industry value added (% of GDP)": "NV.IND.TOTL.ZS",
    "Services value added (% of GDP)": "NV.SRV.TOTL.ZS",

    "— Inflation & Prices —": None,
    "Inflation (CPI, %)": "FP.CPI.TOTL.ZG",
    "Inflation (GDP deflator, %)": "NY.GDP.DEFL.KD.ZG",
    "Food inflation (%)": "FP.CPI.FOOD.ZG",

    "— Labour Market & Demographics —": None,
    "Unemployment (%)": "SL.UEM.TOTL.ZS",
    "Youth unemployment (%)": "SL.UEM.1524.ZS",
    "Labor force participation (%)": "SL.TLF.CACT.ZS",
    "Population growth (%)": "SP.POP.GROW",
    "Urban population (%)": "SP.URB.TOTL.IN.ZS",

    "— State & Debt —": None,
    "Gov debt (% of GDP)": "GC.DOD.TOTL.GD.ZS",
    "Fiscal balance (% of GDP)": "GC.BAL.CASH.GD.ZS",
    "Tax revenue (% of GDP)": "GC.TAX.TOTL.GD.ZS",
    "Interest payments (% of revenue)": "GC.XPN.INTP.RV.ZS",

    "— External & Trade —": None,
    "Exports (% of GDP)": "NE.EXP.GNFS.ZS",
    "Imports (% of GDP)": "NE.IMP.GNFS.ZS",
    "Current account balance (% GDP)": "BN.CAB.XOKA.GD.ZS",
    "FDI net inflows (% of GDP)": "BX.KLT.DINV.WD.GD.ZS",
}

# Some indicators are not percentages.
SUFFIX: dict[str, str] = {
    "NY.GDP.PCAP.CD": " $",
}


@dataclass(frozen=True)
class Country:
    code: str
    name: str


def wb_list_countries() -> list[Country]:
    out: list[Country] = []
    page = 1
    while True:
        url = f"{WB_BASE}/country?format=json&per_page=300&page={page}"
        data = _http_get_json(url)
        if not isinstance(data, list) or len(data) < 2:
            break

        meta, rows = data[0], data[1]
        for c in rows:
            code = c.get("id")
            name = c.get("name")
            if code and name:
                out.append(Country(code=code, name=name))

        pages = int(meta.get("pages", 1) or 1)
        if page >= pages:
            break
        page += 1

    out.sort(key=lambda x: x.name.lower())
    return out


def wb_two_latest(country_code: str, indicator: str) -> list[tuple[int, float]]:
    # Keep range not too wide to reduce payload / timeouts
    url = f"{WB_BASE}/country/{country_code}/indicator/{indicator}?format=json&per_page=60&date=2012:2030"
    data = _http_get_json(url)

    if not isinstance(data, list) or len(data) < 2 or not isinstance(data[1], list):
        return []

    out: list[tuple[int, float]] = []
    for row in data[1]:
        val = row.get("value")
        year = row.get("date")
        if val is None or year is None:
            continue
        try:
            out.append((int(year), float(val)))
        except Exception:
            continue
        if len(out) >= 2:
            break
    return out


def _fmt(v: float | None, suffix: str = "") -> str:
    if v is None:
        return "n/a"
    if suffix.strip() == "$":
        return f"{v:,.0f}{suffix}"
    if abs(v) >= 100:
        return f"{v:,.1f}{suffix}"
    return f"{v:.2f}{suffix}"


def _score_color_class(score_0_100: float) -> str:
    """
    Discrete classes for macro score.
    70+   => green
    45-69 => orange
    <45   => red
    """
    if score_0_100 >= 70:
        return "ScoreGood"
    if score_0_100 >= 45:
        return "ScoreMid"
    return "ScoreBad"


def _value_color_class(value: float) -> str:
    """
    For main value coloring:
    >0 => green, <0 => red, ==0 => neutral
    """
    if value > 0:
        return "Pos"
    if value < 0:
        return "Neg"
    return ""


# ----------------------------
# UI item widgets
# ----------------------------
class SectionItem(QFrame):
    def __init__(self, title: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("WBSection")
        self.setAttribute(Qt.WA_StyledBackground, True)

        h = QHBoxLayout(self)
        h.setContentsMargins(10, 6, 10, 6)

        lab = QLabel(title.replace("—", "").strip())
        lab.setObjectName("WBSectionTitle")
        lab.setAlignment(Qt.AlignCenter)
        lab.setWordWrap(False)

        h.addStretch(1)
        h.addWidget(lab, 0)
        h.addStretch(1)


class SignalItem(QFrame):
    def __init__(
        self,
        label: str,
        value_text: str,
        meta_text: str,
        value_class: str = "",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("WBRow")
        self.setAttribute(Qt.WA_StyledBackground, True)

        h = QHBoxLayout(self)
        h.setContentsMargins(10, 8, 10, 8)
        h.setSpacing(10)

        left = QLabel(label)
        left.setObjectName("WBLabel")
        left.setWordWrap(False)
        left.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        right_box = QVBoxLayout()
        right_box.setContentsMargins(0, 0, 0, 0)
        right_box.setSpacing(2)

        val = QLabel(value_text)
        val.setObjectName("WBValue" + (f"_{value_class}" if value_class else ""))
        val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        meta = QLabel(meta_text)
        meta.setObjectName("WBMeta")
        meta.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        right_box.addWidget(val)
        right_box.addWidget(meta)

        h.addWidget(left, 1)
        h.addLayout(right_box, 0)


# ----------------------------
# The main widget
# ----------------------------
class WorldBankFeedWidget(QFrame):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Panel")
        self.setAttribute(Qt.WA_StyledBackground, True)

        self._pool = QThreadPool.globalInstance()
        self._countries: list[Country] = []

        # --- Type-to-jump state ---
        self._type_buffer = ""
        self._type_timer = QTimer(self)
        self._type_timer.setSingleShot(True)
        self._type_timer.timeout.connect(self._clear_type_buffer)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        title = QLabel("Analyse\nSignale (World Bank)")
        title.setObjectName("PanelTitle")
        title.setWordWrap(True)

        controls = QWidget()
        ch = QHBoxLayout(controls)
        ch.setContentsMargins(0, 0, 0, 0)
        ch.setSpacing(8)

        self.country_box = QComboBox()
        self.country_box.setMinimumHeight(34)
        self.country_box.setFocusPolicy(Qt.StrongFocus)
        self.country_box.installEventFilter(self)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setObjectName("GhostButton")
        self.refresh_btn.setMinimumHeight(34)

        ch.addWidget(self.country_box, 1)
        ch.addWidget(self.refresh_btn, 0)

        self.status = QLabel("Lade Länder …")
        self.status.setObjectName("FinePrint")
        self.status.setWordWrap(True)

        self.list = QListWidget()
        self.list.setObjectName("List")
        self.list.setMinimumHeight(260)

        self.macro_score = QLabel("Macro-Score: n/a")
        self.macro_score.setObjectName("FinePrint")
        self.macro_score.setWordWrap(True)

        root.addWidget(title)
        root.addWidget(controls)
        root.addWidget(self.status)
        root.addWidget(self.list, 1)
        root.addWidget(self.macro_score)

        # Local polish:
        # - only colors the VALUES (decently)
        # - macro score colored via classes
        self.setStyleSheet(self.styleSheet() + """
QFrame#WBSection { border-radius: 10px; }
QLabel#WBSectionTitle { font-weight: 700; letter-spacing: 0.5px; }

QFrame#WBRow { border-radius: 10px; }
QLabel#WBLabel { font-size: 12px; }

QLabel#WBValue { font-size: 13px; font-weight: 700; }
QLabel#WBMeta { font-size: 11px; }

/* --- subtle value coloring --- */
QLabel#WBValue_Pos { font-size: 13px; font-weight: 700; color: rgba(80, 200, 140, 0.95); }
QLabel#WBValue_Neg { font-size: 13px; font-weight: 700; color: rgba(255, 110, 110, 0.95); }

/* --- macro score coloring --- */
QLabel#MacroScore_ScoreGood { color: rgba(80, 200, 140, 0.95); font-weight: 700; }
QLabel#MacroScore_ScoreMid  { color: rgba(255, 185, 90, 0.95); font-weight: 700; }
QLabel#MacroScore_ScoreBad  { color: rgba(255, 110, 110, 0.95); font-weight: 700; }
""")

        self.refresh_btn.clicked.connect(self.refresh_current)
        self.country_box.currentIndexChanged.connect(lambda _: self.refresh_current())

        self._load_countries()

    # ---------- type-to-jump ----------
    def _clear_type_buffer(self) -> None:
        self._type_buffer = ""

    def eventFilter(self, obj, event) -> bool:
        if obj is self.country_box and event.type() == QEvent.KeyPress:
            key = event.key()
            text = event.text()

            if key in (Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt, Qt.Key_Meta):
                return False

            if key == Qt.Key_Backspace:
                self._type_buffer = self._type_buffer[:-1]
                self._type_timer.start(900)
                self._jump_to_country(self._type_buffer)
                return True

            if text and text.isprintable() and not event.modifiers():
                self._type_buffer += text
                self._type_timer.start(900)
                self._jump_to_country(self._type_buffer)
                return True

        return super().eventFilter(obj, event)

    def _jump_to_country(self, prefix: str) -> None:
        prefix = (prefix or "").strip().lower()
        if not prefix:
            return

        for i in range(self.country_box.count()):
            name = self.country_box.itemText(i).lower()
            if name.startswith(prefix):
                self.country_box.blockSignals(True)
                self.country_box.setCurrentIndex(i)
                self.country_box.blockSignals(False)
                self.refresh_current()
                return

    # ---------- loading ----------
    def _load_countries(self) -> None:
        w = _Worker(wb_list_countries)
        w.signals.ok.connect(self._on_countries_ok)
        w.signals.err.connect(self._on_err)
        self._pool.start(w)

    @Slot(object)
    def _on_countries_ok(self, countries: list[Country]) -> None:
        self._countries = countries
        self.country_box.blockSignals(True)
        self.country_box.clear()

        preferred = ["DEU", "USA", "GBR", "FRA", "JPN", "CHN", "IND"]
        pref_objs = [c for c in countries if c.code in preferred]
        rest = [c for c in countries if c.code not in preferred]

        for c in pref_objs + rest:
            self.country_box.addItem(c.name, c.code)

        idx = self.country_box.findData("DEU")
        if idx >= 0:
            self.country_box.setCurrentIndex(idx)

        self.country_box.blockSignals(False)
        self.status.setText("Bereit. Wähle ein Land, um Signale zu laden.")
        self.refresh_current()

    @Slot(str)
    def _on_err(self, msg: str) -> None:
        self.status.setText(f"Fehler: {msg}")

    def refresh_current(self) -> None:
        code = self.country_box.currentData()
        if not code:
            return

        self.status.setText(f"Lade Indikatoren für {code} …")
        self.list.clear()
        self.macro_score.setText("Macro-Score: n/a")
        self.macro_score.setObjectName("FinePrint")  # reset class
        self.macro_score.style().unpolish(self.macro_score)
        self.macro_score.style().polish(self.macro_score)

        def job() -> dict[str, Any]:
            rows: list[dict[str, Any]] = []
            score_parts: list[float] = []

            for label, ind in INDICATORS.items():
                if ind is None:
                    rows.append({"section": label})
                    continue

                pts = wb_two_latest(code, ind)
                if len(pts) == 0:
                    rows.append({"label": label, "ind": ind, "latest": None, "year": None, "delta": None})
                    continue

                (y1, v1) = pts[0]
                delta = None
                if len(pts) >= 2:
                    (_, v2) = pts[1]
                    delta = v1 - v2

                rows.append({"label": label, "ind": ind, "latest": v1, "year": y1, "delta": delta})

                # Macro score (heuristic): stable core indicators
                if ind == "NY.GDP.MKTP.KD.ZG":
                    score_parts.append(max(-5.0, min(10.0, v1)))
                elif ind == "FP.CPI.TOTL.ZG":
                    score_parts.append(max(-10.0, min(5.0, -v1 / 2.0)))
                elif ind == "SL.UEM.TOTL.ZS":
                    score_parts.append(max(-10.0, min(5.0, -v1 / 2.0)))
                elif ind == "GC.DOD.TOTL.GD.ZS":
                    score_parts.append(max(-10.0, min(5.0, -v1 / 25.0)))
                elif ind == "BN.CAB.XOKA.GD.ZS":
                    score_parts.append(max(-5.0, min(5.0, v1 / 2.0)))

                time.sleep(0.03)

            raw = sum(score_parts) if score_parts else 0.0
            score = (raw + 45.0) / 75.0 * 100.0
            score = max(0.0, min(100.0, score))

            return {"rows": rows, "score": score}

        w = _Worker(job)
        w.signals.ok.connect(self._on_feed_ok)
        w.signals.err.connect(self._on_err)
        self._pool.start(w)

    @Slot(object)
    def _on_feed_ok(self, payload: dict[str, Any]) -> None:
        self.status.setText("Aktualisiert (World Bank Open Data).")
        self.list.clear()

        rows = payload.get("rows", [])
        for r in rows:
            if "section" in r:
                w = SectionItem(r["section"])
                item = QListWidgetItem()
                item.setFlags(Qt.ItemIsEnabled)
                item.setSizeHint(w.sizeHint())
                self.list.addItem(item)
                self.list.setItemWidget(item, w)
                continue

            label = r.get("label", "")
            ind = r.get("ind", "")
            latest = r.get("latest")
            year = r.get("year")
            delta = r.get("delta")

            suffix = SUFFIX.get(ind, "")
            is_money = (suffix.strip() == "$")

            value_class = ""
            if isinstance(latest, (int, float)) and not is_money:
                # Only color percent-type values; money values stay neutral
                value_class = _value_color_class(float(latest))

            if latest is None or year is None:
                value_text = "n/a"
                meta_text = ""
            else:
                value_text = _fmt(latest, suffix) if is_money else f"{_fmt(latest)}%"

                arrow = ""
                delta_txt = ""
                if delta is not None:
                    if abs(delta) < (0.05 if not is_money else 1.0):
                        arrow = "≈"
                    elif delta > 0:
                        arrow = "↑"
                    else:
                        arrow = "↓"

                    delta_txt = f"{delta:+,.0f}{suffix}" if is_money else f"{delta:+.2f} pp"

                meta_text = f"{year}" if not delta_txt else f"{year}   {delta_txt}   {arrow}"

            w = SignalItem(label=label, value_text=value_text, meta_text=meta_text, value_class=value_class)
            item = QListWidgetItem()
            item.setFlags(Qt.ItemIsEnabled)
            item.setSizeHint(w.sizeHint())
            self.list.addItem(item)
            self.list.setItemWidget(item, w)

        score = payload.get("score")
        if isinstance(score, (int, float)):
            cls = _score_color_class(float(score))
            self.macro_score.setObjectName(f"MacroScore_{cls}")
            self.macro_score.setText(f"Macro-Score (heuristisch): {float(score):.0f}/100")

            # force re-style after objectName change
            self.macro_score.style().unpolish(self.macro_score)
            self.macro_score.style().polish(self.macro_score)
        else:
            self.macro_score.setObjectName("FinePrint")
            self.macro_score.setText("Macro-Score: n/a")
            self.macro_score.style().unpolish(self.macro_score)
            self.macro_score.style().polish(self.macro_score)
