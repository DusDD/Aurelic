# gui/calendarpage.py
from __future__ import annotations

import os
import json
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt, Signal, QTimer, QThread, QObject
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout, QSizePolicy, QScrollArea
)

# Theme/QSS aus deiner MainPage nutzen
from gui.mainpage import Palette, build_qss


@dataclass(frozen=True)
class DividendEvent:
    symbol: str
    company: str
    ex_date: str
    pay_date: str
    record_date: str
    amount: str
    currency: str


class NasdaqCalendarWorker(QObject):
    finished = Signal(list, str)  # (list[DividendEvent], source_label)
    failed = Signal(str)

    def __init__(self, year: int, month: int, parent: QObject | None = None):
        super().__init__(parent)
        self._year = int(year)
        self._month = int(month)

    def run(self) -> None:
        """
        Strategy:
        1) Try NASDAQ (no key) -> if returns events: use it
        2) Else fallback to FMP dividends-calendar (requires FMP_API_KEY)
        """
        try:
            events = self._fetch_from_nasdaq_month()
            if events:
                self.finished.emit(events, "NASDAQ")
                return
        except Exception:
            # Nasdaq is best-effort
            pass

        try:
            events = self._fetch_from_fmp_month()
            if events:
                self.finished.emit(events, "FMP")
                return
            # If FMP returns empty, treat it as a real "no events" case
            self.finished.emit([], "FMP")
        except Exception as e:
            self.failed.emit(str(e)[:500])

    # ---------- HTTP helpers ----------

    def _read_json(self, url: str, headers: Optional[dict] = None, timeout: int = 12):
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

    # ---------- NASDAQ (best-effort) ----------

    def _fetch_from_nasdaq_month(self) -> list[DividendEvent]:
        """
        Nasdaq calendar dividends is typically per-day:
          https://api.nasdaq.com/api/calendar/dividends?date=YYYY-MM-DD
        We aggregate days in the month.
        Note: This endpoint can be flaky / blocked; we treat it as best-effort.
        """
        import calendar as _cal

        base = os.getenv(
            "AURELIC_NASDAQ_CAL_URL",
            "https://api.nasdaq.com/api/calendar/dividends"
        ).strip()

        headers = {
            "User-Agent": "Mozilla/5.0 (Aurelic/1.0)",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.nasdaq.com/",
            "Origin": "https://www.nasdaq.com",
        }

        last_day = _cal.monthrange(self._year, self._month)[1]
        out: list[DividendEvent] = []
        seen = set()

        for day in range(1, last_day + 1):
            date_str = f"{self._year:04d}-{self._month:02d}-{day:02d}"
            url = f"{base}?{urllib.parse.urlencode({'date': date_str})}"

            j = self._read_json(url, headers=headers, timeout=10)

            rows = None
            if isinstance(j, dict):
                data = j.get("data")
                if isinstance(data, dict):
                    cal = data.get("calendar") or data.get("dividends") or data.get("rows")
                    if isinstance(cal, dict):
                        rows = cal.get("rows") or cal.get("data") or cal.get("table", {}).get("rows")
                    elif isinstance(cal, list):
                        rows = cal

            if not isinstance(rows, list):
                continue

            for r in rows:
                if not isinstance(r, dict):
                    continue

                sym = (r.get("symbol") or r.get("ticker") or "").strip()
                company = (r.get("company") or r.get("companyName") or r.get("name") or "").strip()
                ex_date = (r.get("exOrEffDate") or r.get("exDate") or r.get("ex_date") or r.get("ex") or "").strip()
                pay_date = (r.get("paymentDate") or r.get("payDate") or r.get("pay_date") or "").strip()
                record_date = (r.get("recordDate") or r.get("record_date") or "").strip()
                amount = (r.get("cashAmount") or r.get("amount") or r.get("dividend") or "").strip()
                currency = (r.get("currency") or "USD").strip() or "USD"

                if not sym or not ex_date:
                    continue

                key = (sym, ex_date, amount, currency)
                if key in seen:
                    continue
                seen.add(key)

                out.append(
                    DividendEvent(
                        symbol=sym,
                        company=company or sym,
                        ex_date=ex_date,
                        pay_date=pay_date,
                        record_date=record_date,
                        amount=amount,
                        currency=currency,
                    )
                )

        out.sort(key=lambda e: (e.ex_date or "", e.symbol))
        return out

    # ---------- FMP (reliable fallback) ----------

    def _fetch_from_fmp_month(self) -> list[DividendEvent]:
        """
        FMP stable Dividends Calendar API:
          https://financialmodelingprep.com/stable/dividends-calendar?from=YYYY-MM-DD&to=YYYY-MM-DD&apikey=KEY
        Docs: stable/dividends-calendar :contentReference[oaicite:2]{index=2}
        """
        import calendar as _cal

        fmp_key = os.getenv("FMP_API_KEY", "").strip()
        if not fmp_key:
            raise RuntimeError("FMP_API_KEY fehlt – FMP-Fallback kann nicht genutzt werden.")

        first = f"{self._year:04d}-{self._month:02d}-01"
        last_day = _cal.monthrange(self._year, self._month)[1]
        last = f"{self._year:04d}-{self._month:02d}-{last_day:02d}"

        base = "https://financialmodelingprep.com/stable/dividends-calendar"
        url = f"{base}?{urllib.parse.urlencode({'from': first, 'to': last, 'apikey': fmp_key})}"

        headers = {
            "User-Agent": "Aurelic/1.0 (Desktop App)",
            "Accept": "application/json, text/plain, */*",
        }

        j = self._read_json(url, headers=headers, timeout=12)

        out: list[DividendEvent] = []
        if not isinstance(j, list):
            return out

        for r in j:
            if not isinstance(r, dict):
                continue

            sym = str(r.get("symbol") or "").strip()
            # FMP liefert oft keine Company-Name im Calendar; wir setzen symbol als fallback
            company = str(r.get("companyName") or r.get("name") or sym).strip() or sym

            # In FMP calendar ist "date" typischerweise Ex-Dividend-Date
            ex_date = str(r.get("date") or "").strip()
            record_date = str(r.get("recordDate") or "").strip()
            pay_date = str(r.get("paymentDate") or "").strip()

            # dividend / adjDividend können floats sein
            div_val = r.get("dividend")
            adj_val = r.get("adjDividend")
            amount = ""
            if div_val is not None:
                try:
                    amount = f"{float(div_val):.6g}"
                except Exception:
                    amount = str(div_val)
            elif adj_val is not None:
                try:
                    amount = f"{float(adj_val):.6g}"
                except Exception:
                    amount = str(adj_val)

            # Currency ist im FMP Calendar oft nicht enthalten; default USD
            currency = str(r.get("currency") or "USD").strip() or "USD"

            if sym and ex_date:
                out.append(
                    DividendEvent(
                        symbol=sym,
                        company=company,
                        ex_date=ex_date,
                        pay_date=pay_date,
                        record_date=record_date,
                        amount=amount,
                        currency=currency,
                    )
                )

        out.sort(key=lambda e: (e.ex_date or "", e.symbol))
        return out


class CalendarPage(QWidget):
    back_clicked = Signal()

    def __init__(self, palette: Palette | None = None, background_path: str = "images/Backgroundimage.png", parent=None):
        super().__init__(parent)

        self.setObjectName("Root")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)

        self._palette = palette or Palette()
        self._background_path = background_path
        self.setStyleSheet(build_qss(self._palette, self._background_path))

        today = datetime.now()
        self._year = today.year
        self._month = today.month
        self._events: list[DividendEvent] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(0)

        self._shell = QFrame()
        self._shell.setObjectName("Shell")
        self._shell.setAttribute(Qt.WA_StyledBackground, True)
        self._shell.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        sv = QVBoxLayout(self._shell)
        sv.setContentsMargins(22, 18, 22, 18)
        sv.setSpacing(14)

        sv.addWidget(self._build_topbar(), 0)
        sv.addWidget(self._build_body(), 1)

        root.addWidget(self._shell, 0, Qt.AlignCenter)

        QTimer.singleShot(0, self._refresh)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)

        m = 40
        avail_w = max(300, self.width() - 2 * m)
        avail_h = max(300, self.height() - 2 * m)

        ratio = 1.568
        w = min(avail_w, int(avail_h * ratio))
        h = min(avail_h, int(w / ratio))
        self._shell.setFixedSize(w, h)

    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setAttribute(Qt.WA_StyledBackground, True)

        h = QHBoxLayout(bar)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(12)

        title = QLabel("Financial Calendar — Dividends")
        title.setObjectName("PanelTitle")
        title.setWordWrap(True)

        back = QPushButton("Zurück")
        back.setObjectName("Ghost")
        back.clicked.connect(self.back_clicked.emit)

        h.addWidget(title, 0, Qt.AlignLeft)
        h.addStretch(1)
        h.addWidget(back, 0, Qt.AlignRight)
        return bar

    def _build_body(self) -> QWidget:
        w = QWidget()
        w.setAttribute(Qt.WA_StyledBackground, True)

        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(14)

        left = QFrame()
        left.setObjectName("Panel")
        left.setAttribute(Qt.WA_StyledBackground, True)
        left.setMinimumWidth(520)
        left.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        lv = QVBoxLayout(left)
        lv.setContentsMargins(16, 14, 16, 14)
        lv.setSpacing(10)

        header = QWidget()
        hh = QHBoxLayout(header)
        hh.setContentsMargins(0, 0, 0, 0)
        hh.setSpacing(8)

        self._month_label = QLabel("")
        self._month_label.setObjectName("PanelTitle")

        prev_btn = QPushButton("‹")
        prev_btn.setObjectName("Ghost")
        prev_btn.setFixedWidth(44)
        prev_btn.clicked.connect(self._prev_month)

        next_btn = QPushButton("›")
        next_btn.setObjectName("Ghost")
        next_btn.setFixedWidth(44)
        next_btn.clicked.connect(self._next_month)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("Primary")
        refresh_btn.clicked.connect(self._refresh)

        hh.addWidget(self._month_label, 1, Qt.AlignLeft)
        hh.addWidget(prev_btn, 0)
        hh.addWidget(next_btn, 0)
        hh.addWidget(refresh_btn, 0)

        self._status = QLabel("Lade Kalender …")
        self._status.setObjectName("FinePrint")
        self._status.setWordWrap(True)

        self._list_scroll = QScrollArea()
        self._list_scroll.setWidgetResizable(True)
        self._list_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._list_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self._list_content = QWidget()
        self._list_content.setAttribute(Qt.WA_StyledBackground, True)
        self._list_layout = QVBoxLayout(self._list_content)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(6)
        self._list_scroll.setWidget(self._list_content)

        lv.addWidget(header)
        lv.addWidget(self._status)
        lv.addWidget(self._list_scroll, 1)

        right = QFrame()
        right.setObjectName("Panel")
        right.setAttribute(Qt.WA_StyledBackground, True)
        rv = QVBoxLayout(right)
        rv.setContentsMargins(16, 14, 16, 14)

        ph = QLabel()
        ph.setObjectName("Placeholder")
        ph.setAlignment(Qt.AlignCenter)
        ph.setWordWrap(True)

        rv.addStretch(1)
        rv.addWidget(ph, 0, Qt.AlignCenter)
        rv.addStretch(1)

        h.addWidget(left, 0)
        h.addWidget(right, 1)
        return w

    def _prev_month(self) -> None:
        self._month -= 1
        if self._month <= 0:
            self._month = 12
            self._year -= 1
        self._refresh()

    def _next_month(self) -> None:
        self._month += 1
        if self._month >= 13:
            self._month = 1
            self._year += 1
        self._refresh()

    def _refresh(self) -> None:
        self._month_label.setText(f"{self._year:04d}-{self._month:02d}")
        self._status.setText("Lade Kalender …")

        while self._list_layout.count():
            it = self._list_layout.takeAt(0)
            ww = it.widget()
            if ww is not None:
                ww.deleteLater()

        self._cal_thread = QThread(self)
        self._cal_worker = NasdaqCalendarWorker(year=self._year, month=self._month)
        self._cal_worker.moveToThread(self._cal_thread)

        self._cal_thread.started.connect(self._cal_worker.run)
        self._cal_worker.finished.connect(self._on_calendar_loaded)
        self._cal_worker.failed.connect(self._on_calendar_failed)

        self._cal_worker.finished.connect(self._cal_thread.quit)
        self._cal_worker.failed.connect(self._cal_thread.quit)
        self._cal_thread.finished.connect(self._cal_worker.deleteLater)
        self._cal_thread.finished.connect(self._cal_thread.deleteLater)

        self._cal_thread.start()

    def _on_calendar_failed(self, msg: str) -> None:
        self._events = []
        self._status.setText(f"Kalender konnte nicht geladen werden: {msg}")

    def _on_calendar_loaded(self, events: list, source: str) -> None:
        self._events = [e for e in events if isinstance(e, DividendEvent)]

        if not self._events:
            self._status.setText(f"Keine Dividend-Events gefunden. Quelle: {source}.")
            self._list_layout.addStretch(1)
            return

        self._status.setText(f"{len(self._events)} Dividend-Events geladen. Quelle: {source}.")

        for e in self._events[:250]:
            card = QFrame()
            card.setObjectName("NewsCard")
            card.setAttribute(Qt.WA_StyledBackground, True)

            cv = QVBoxLayout(card)
            cv.setContentsMargins(10, 10, 10, 10)
            cv.setSpacing(4)

            title = QLabel(f"{e.symbol} · {e.company}")
            title.setObjectName("NewsTitle")
            title.setWordWrap(True)

            meta_parts = [
                f"Ex-Date: {e.ex_date}",
                f"Pay: {e.pay_date}" if e.pay_date else None,
                f"Record: {e.record_date}" if e.record_date else None,
                f"Amount: {e.amount} {e.currency}" if e.amount else None,
            ]
            meta_txt = " · ".join([p for p in meta_parts if p])

            meta = QLabel(meta_txt)
            meta.setObjectName("NewsMeta")
            meta.setWordWrap(True)

            cv.addWidget(title)
            cv.addWidget(meta)

            self._list_layout.addWidget(card)

        self._list_layout.addStretch(1)
