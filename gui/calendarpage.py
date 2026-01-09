# gui/calendarpage.py
from __future__ import annotations

import os
import json
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional

from PySide6.QtCore import Qt, Signal, QTimer, QThread, QObject
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout, QSizePolicy, QScrollArea
)

# Theme/QSS aus deiner MainPage nutzen
from gui.mainpage import Palette, build_qss


# -----------------------------
# Data Models
# -----------------------------

@dataclass(frozen=True)
class DividendEvent:
    symbol: str
    company: str
    ex_date: str
    pay_date: str
    record_date: str
    amount: str
    currency: str


@dataclass(frozen=True)
class GlobalEvent:
    date: str            # YYYY-MM-DD
    title: str           # e.g. "New Year's Day" / "German federal election"
    country: str         # ISO-2 (DE, US, ...)
    category: str        # "HOLIDAY" | "ELECTION"
    source: str          # "NAGER" | "WIKIDATA"


# -----------------------------
# Dividend Calendar Worker
# -----------------------------

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
        Additionally:
        - Enrich missing company names via FMP profile endpoint + local cache
        """
        try:
            events = self._fetch_from_nasdaq_month()
            if events:
                events = self._enrich_company_names(events)
                self.finished.emit(events, "NASDAQ")
                return
        except Exception:
            # Nasdaq is best-effort
            pass

        try:
            events = self._fetch_from_fmp_month()
            if events:
                events = self._enrich_company_names(events)
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

    # ---------- Company name enrichment (FMP profile + cache) ----------

    def _company_cache_path(self) -> str:
        p = os.getenv("AURELIC_COMPANY_CACHE", "cache/company_names.json").strip()
        return p or "cache/company_names.json"

    def _load_company_cache(self) -> dict:
        path = self._company_cache_path()
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    j = json.load(f)
                    return j if isinstance(j, dict) else {}
        except Exception:
            pass
        return {}

    def _save_company_cache(self, cache: dict) -> None:
        path = self._company_cache_path()
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
        except Exception:
            # Cache ist best-effort – UI soll nicht scheitern, nur weil Speichern nicht geht
            pass

    def _needs_company_name(self, e: DividendEvent) -> bool:
        c = (e.company or "").strip()
        s = (e.symbol or "").strip()
        if not s:
            return False
        return (not c) or (c.upper() == s.upper())

    def _fetch_company_names_fmp_profile(self, symbols: list[str]) -> dict[str, str]:
        """
        Holt firmennamen via FMP stable profile endpoint:
          https://financialmodelingprep.com/stable/profile?symbol=AAPL&apikey=KEY
        Rückgabe: { "AAPL": "Apple Inc.", ... }
        """
        fmp_key = os.getenv("FMP_API_KEY", "").strip()
        if not fmp_key:
            return {}

        base = "https://financialmodelingprep.com/stable/profile"
        headers = {
            "User-Agent": "Aurelic/1.0 (Desktop App)",
            "Accept": "application/json, text/plain, */*",
        }

        out: dict[str, str] = {}
        for sym in symbols:
            sym = sym.strip().upper()
            if not sym:
                continue
            url = f"{base}?{urllib.parse.urlencode({'symbol': sym, 'apikey': fmp_key})}"
            j = self._read_json(url, headers=headers, timeout=12)

            if isinstance(j, list) and j:
                first = j[0]
                if isinstance(first, dict):
                    name = str(first.get("companyName") or first.get("name") or "").strip()
                    if name:
                        out[sym] = name

        return out

    def _enrich_company_names(self, events: list[DividendEvent]) -> list[DividendEvent]:
        """
        Ergänzt fehlende Klarnamen. Nutzt Cache und FMP Profile.
        """
        if not events:
            return events

        cache = self._load_company_cache()

        needed_syms = []
        for e in events:
            if self._needs_company_name(e):
                sym = (e.symbol or "").strip().upper()
                if sym and sym not in cache:
                    needed_syms.append(sym)

        needed_syms = sorted(set(needed_syms))

        fetched = {}
        try:
            if needed_syms:
                fetched = self._fetch_company_names_fmp_profile(needed_syms)
        except Exception:
            fetched = {}

        if fetched:
            cache.update(fetched)
            self._save_company_cache(cache)

        enriched: list[DividendEvent] = []
        for e in events:
            sym = (e.symbol or "").strip().upper()
            if self._needs_company_name(e) and sym in cache:
                enriched.append(
                    DividendEvent(
                        symbol=e.symbol,
                        company=cache[sym],
                        ex_date=e.ex_date,
                        pay_date=e.pay_date,
                        record_date=e.record_date,
                        amount=e.amount,
                        currency=e.currency,
                    )
                )
            else:
                enriched.append(e)

        return enriched

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
            company = str(r.get("companyName") or r.get("name") or sym).strip() or sym

            ex_date = str(r.get("date") or "").strip()
            record_date = str(r.get("recordDate") or "").strip()
            pay_date = str(r.get("paymentDate") or "").strip()

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


# -----------------------------
# Global Events Worker (G20 + EU)
# -----------------------------

class GlobalEventsWorker(QObject):
    finished = Signal(list, str)  # (list[GlobalEvent], source_label)
    failed = Signal(str)

    def __init__(self, year: int, month: int, parent: QObject | None = None):
        super().__init__(parent)
        self._year = int(year)
        self._month = int(month)

        self._countries = self._build_g20_eu_country_codes()

    def run(self) -> None:
        """
        Loads global events (G20 + EU) for a given month:
        - Public holidays via Nager.Date (no key) -> only current month
        - Elections via Wikidata SPARQL (best-effort) -> whole year
        Uses JSON cache (best-effort) to reduce calls.
        """
        try:
            events: list[GlobalEvent] = []
            srcs: list[str] = []

            # Holidays (month)
            try:
                hol = self._fetch_holidays_month()
                events.extend(hol)
                if hol:
                    srcs.append("NAGER")
                else:
                    srcs.append("NAGER(0)")
            except Exception as e:
                err = str(e)[:120].replace("\n", " ")
                srcs.append(f"NAGER(ERR:{err})")

            # Elections (year)
            try:
                elec = self._fetch_elections_year()
                events.extend(elec)
                if elec:
                    srcs.append("WIKIDATA")
                else:
                    srcs.append("WIKIDATA(0)")
            except Exception as e:
                err = str(e)[:120].replace("\n", " ")
                srcs.append(f"WIKIDATA(ERR:{err})")

            # Deduplicate
            seen = set()
            uniq: list[GlobalEvent] = []
            for e in events:
                key = (e.date, e.title, e.country, e.category, e.source)
                if key in seen:
                    continue
                seen.add(key)
                uniq.append(e)

            uniq.sort(key=lambda x: (x.date, x.category, x.country, x.title))
            label = "+".join(srcs) if srcs else "NAGER+WIKIDATA"
            self.finished.emit(uniq, label)

        except Exception as e:
            self.failed.emit(str(e)[:500])

    # ---------- Countries ----------

    def _build_g20_eu_country_codes(self) -> list[str]:
        g20 = [
            "AR", "AU", "BR", "CA", "CN", "FR", "DE", "IN", "ID", "IT",
            "JP", "MX", "RU", "SA", "ZA", "KR", "TR", "UK", "US"
        ]
        eu27 = [
            "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE",
            "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT",
            "RO", "SK", "SI", "ES", "SE"
        ]
        return sorted(set(g20 + eu27))

    # ---------- Cache helpers ----------

    def _cache_path(self) -> str:
        p = os.getenv("AURELIC_GLOBALEVENTS_CACHE", "cache/global_events_cache.json").strip()
        return p or "cache/global_events_cache.json"

    def _load_cache(self) -> dict:
        path = self._cache_path()
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    j = json.load(f)
                    return j if isinstance(j, dict) else {}
        except Exception:
            pass
        return {}

    def _save_cache(self, cache: dict) -> None:
        path = self._cache_path()
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
        except Exception:
            pass

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
                raw = resp.read().decode("utf-8", errors="replace").strip()
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

    def _post_sparql_json(self, endpoint: str, query: str, timeout: int = 18) -> dict:
        import urllib.request
        import urllib.error
        import ssl
        import certifi

        data = urllib.parse.urlencode({"query": query}).encode("utf-8")
        headers = {
            "User-Agent": "Aurelic/1.0 (Desktop App)",
            "Accept": "application/sparql+json",
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        }

        req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")
        ctx = ssl.create_default_context(cafile=certifi.where())

        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                raw = resp.read().decode("utf-8", errors="replace").strip()
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

        if raw[0] != "{":
            raise RuntimeError(f"Non-JSON response: {raw[:200]}")

        try:
            return json.loads(raw)
        except Exception as e:
            raise RuntimeError(f"JSON parse error: {e}. Body head: {raw[:200]}")

    # ---------- Nager.Date holidays ----------

    def _fetch_holidays_year_country(self, year: int, country: str) -> list[dict]:
        """
        Returns list of Nager.Date holiday dicts.
        Cached per (year,country).
        """
        cache = self._load_cache()
        key = f"nager:{year}:{country}"
        if key in cache and isinstance(cache[key], list):
            return cache[key]

        url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country}"
        headers = {"User-Agent": "Aurelic/1.0 (Desktop App)", "Accept": "application/json, text/plain, */*"}
        j = self._read_json(url, headers=headers, timeout=14)

        if not isinstance(j, list):
            j = []

        cache[key] = j
        self._save_cache(cache)
        return j

    def _fetch_holidays_month(self) -> list[GlobalEvent]:
        out: list[GlobalEvent] = []
        month_prefix = f"{self._year:04d}-{self._month:02d}-"

        for cc in self._countries:
            try:
                rows = self._fetch_holidays_year_country(self._year, cc)
            except Exception:
                continue

            for r in rows:
                if not isinstance(r, dict):
                    continue
                date = str(r.get("date") or "").strip()
                if not date.startswith(month_prefix):
                    continue

                name = str(r.get("name") or r.get("localName") or "").strip()
                if not name:
                    continue

                out.append(
                    GlobalEvent(
                        date=date,
                        title=name,
                        country=cc,
                        category="HOLIDAY",
                        source="NAGER",
                    )
                )

        return out

    # ---------- Wikidata elections (whole year) ----------

    def _fetch_elections_year(self) -> list[GlobalEvent]:
        """
        Best-effort Wikidata SPARQL query for elections with ISO2 country code (P297) and date (P585).
        Robust version:
        - Includes subclasses of election via wdt:P31/wdt:P279*
        - Filters YEAR in SPARQL (reduces payload, fewer local filters)
        - Caches per year (prevents "empty forever" due to old cache)
        """
        endpoint = "https://query.wikidata.org/sparql"
        year = self._year

        query = f"""
SELECT ?countryCode ?electionLabel ?date WHERE {{
  ?election wdt:P31/wdt:P279* wd:Q40231 ;
            wdt:P17 ?country ;
            wdt:P585 ?date .
  ?country wdt:P297 ?countryCode .
  FILTER(YEAR(?date) = {year})
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
ORDER BY ?date
""".strip()

        cache = self._load_cache()
        key = f"wikidata:elections:year:{year}"
        data = None

        if key in cache and isinstance(cache[key], dict):
            data = cache[key]
        else:
            data = self._post_sparql_json(endpoint, query, timeout=25)
            cache[key] = data
            self._save_cache(cache)

        out: list[GlobalEvent] = []
        bindings = (
            (((data or {}).get("results") or {}).get("bindings") or [])
            if isinstance(data, dict) else []
        )

        allowed = set(self._countries)

        for b in bindings:
            if not isinstance(b, dict):
                continue

            cc = str(((b.get("countryCode") or {}).get("value")) or "").strip().upper()
            if cc not in allowed:
                continue

            dt_raw = str(((b.get("date") or {}).get("value")) or "").strip()
            date_str = dt_raw[:10] if len(dt_raw) >= 10 else ""
            if not date_str.startswith(f"{year:04d}-"):
                continue

            title = str(((b.get("electionLabel") or {}).get("value")) or "").strip()
            if not title:
                title = "Election"

            out.append(
                GlobalEvent(
                    date=date_str,
                    title=title,
                    country=cc,
                    category="ELECTION",
                    source="WIKIDATA",
                )
            )

        return out


# -----------------------------
# UI Page
# -----------------------------

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
        self._global_events: list[GlobalEvent] = []
        self._global_filter: str = "ALL"  # ALL | HOLIDAY | ELECTION

        # ISO2 -> display name (only for those we use)
        self._country_names: dict[str, str] = {
            "AR": "Argentina",
            "AU": "Australia",
            "AT": "Austria",
            "BE": "Belgium",
            "BR": "Brazil",
            "BG": "Bulgaria",
            "CA": "Canada",
            "CN": "China",
            "HR": "Croatia",
            "CY": "Cyprus",
            "CZ": "Czechia",
            "DK": "Denmark",
            "EE": "Estonia",
            "FI": "Finland",
            "FR": "France",
            "DE": "Germany",
            "GR": "Greece",
            "HU": "Hungary",
            "ID": "Indonesia",
            "IN": "India",
            "IE": "Ireland",
            "IT": "Italy",
            "JP": "Japan",
            "KR": "South Korea",
            "LV": "Latvia",
            "LT": "Lithuania",
            "LU": "Luxembourg",
            "MT": "Malta",
            "MX": "Mexico",
            "NL": "Netherlands",
            "PL": "Poland",
            "PT": "Portugal",
            "RO": "Romania",
            "RU": "Russia",
            "SA": "Saudi Arabia",
            "SK": "Slovakia",
            "SI": "Slovenia",
            "ZA": "South Africa",
            "ES": "Spain",
            "SE": "Sweden",
            "TR": "Türkiye",
            "UK": "United Kingdom",
            "US": "United States",
        }

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

    # -----------------------------
    # Date helpers: show only upcoming events
    # -----------------------------

    def _today_date(self) -> date:
        return datetime.now().date()

    def _parse_ymd_date(self, s: str) -> Optional[date]:
        s = (s or "").strip()
        if not s:
            return None
        # Expect "YYYY-MM-DD" or ISO-like "YYYY-MM-DDTHH:MM:SS..."
        try:
            return datetime.fromisoformat(s[:10]).date()
        except Exception:
            return None

    def _is_upcoming(self, date_str: str) -> bool:
        d = self._parse_ymd_date(date_str)
        if d is None:
            # If we can't parse safely, do not show it
            return False
        return d >= self._today_date()

    def _format_countries(self, codes: list[str], limit: int = 18) -> str:
        """
        Render countries as "DE (Germany), US (United States), ..."
        Unknown codes are shown as-is.
        """
        out = []
        for cc in codes:
            cc = (cc or "").strip().upper()
            if not cc:
                continue
            name = self._country_names.get(cc, "")
            out.append(f"{cc} ({name})" if name else cc)

        if len(out) > limit:
            return ", ".join(out[:limit]) + f", +{len(out) - limit} more"
        return ", ".join(out)

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

        # ---------------- Left (Dividends) ----------------
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

        # ---------------- Right (Global Events: G20 + EU) ----------------
        right = QFrame()
        right.setObjectName("Panel")
        right.setAttribute(Qt.WA_StyledBackground, True)
        right.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        rv = QVBoxLayout(right)
        rv.setContentsMargins(16, 14, 16, 14)
        rv.setSpacing(10)

        gheader = QWidget()
        gh = QHBoxLayout(gheader)
        gh.setContentsMargins(0, 0, 0, 0)
        gh.setSpacing(8)

        self._global_title = QLabel("Global Events — G20 + EU")
        self._global_title.setObjectName("PanelTitle")
        self._global_title.setWordWrap(True)

        self._global_all_btn = QPushButton("All")
        self._global_all_btn.setObjectName("Ghost")
        self._global_all_btn.clicked.connect(lambda: self._set_global_filter("ALL"))

        self._global_hol_btn = QPushButton("Holidays")
        self._global_hol_btn.setObjectName("Ghost")
        self._global_hol_btn.clicked.connect(lambda: self._set_global_filter("HOLIDAY"))

        self._global_ele_btn = QPushButton("Elections")
        self._global_ele_btn.setObjectName("Ghost")
        self._global_ele_btn.clicked.connect(lambda: self._set_global_filter("ELECTION"))

        self._global_refresh_btn = QPushButton("Refresh")
        self._global_refresh_btn.setObjectName("Ghost")
        self._global_refresh_btn.clicked.connect(self._refresh_global)

        gh.addWidget(self._global_title, 1, Qt.AlignLeft)
        gh.addWidget(self._global_all_btn, 0)
        gh.addWidget(self._global_hol_btn, 0)
        gh.addWidget(self._global_ele_btn, 0)
        gh.addWidget(self._global_refresh_btn, 0)

        self._global_status = QLabel("Lade globale Events …")
        self._global_status.setObjectName("FinePrint")
        self._global_status.setWordWrap(True)

        self._global_scroll = QScrollArea()
        self._global_scroll.setWidgetResizable(True)
        self._global_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._global_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self._global_content = QWidget()
        self._global_content.setAttribute(Qt.WA_StyledBackground, True)
        self._global_layout = QVBoxLayout(self._global_content)
        self._global_layout.setContentsMargins(0, 0, 0, 0)
        self._global_layout.setSpacing(6)
        self._global_scroll.setWidget(self._global_content)

        rv.addWidget(gheader)
        rv.addWidget(self._global_status)
        rv.addWidget(self._global_scroll, 1)

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

    # -----------------------------
    # Refresh (both panels)
    # -----------------------------

    def _refresh(self) -> None:
        self._month_label.setText(f"{self._year:04d}-{self._month:02d}")

        # Refresh dividends
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

        # Refresh global events (right panel)
        self._refresh_global()

    def _refresh_global(self) -> None:
        self._global_status.setText("Lade globale Events …")

        while self._global_layout.count():
            it = self._global_layout.takeAt(0)
            ww = it.widget()
            if ww is not None:
                ww.deleteLater()

        self._global_thread = QThread(self)
        self._global_worker = GlobalEventsWorker(year=self._year, month=self._month)
        self._global_worker.moveToThread(self._global_thread)

        self._global_thread.started.connect(self._global_worker.run)
        self._global_worker.finished.connect(self._on_global_loaded)
        self._global_worker.failed.connect(self._on_global_failed)

        self._global_worker.finished.connect(self._global_thread.quit)
        self._global_worker.failed.connect(self._global_thread.quit)
        self._global_thread.finished.connect(self._global_worker.deleteLater)
        self._global_thread.finished.connect(self._global_thread.deleteLater)

        self._global_thread.start()

    # -----------------------------
    # Dividends callbacks
    # -----------------------------

    def _on_calendar_failed(self, msg: str) -> None:
        self._events = []
        self._status.setText(f"Kalender konnte nicht geladen werden: {msg}")

    def _on_calendar_loaded(self, events: list, source: str) -> None:
        # Nur valide DividendEvent
        all_events = [e for e in events if isinstance(e, DividendEvent)]

        # Nur kommende Events (>= heute) nach ex_date
        self._events = [e for e in all_events if self._is_upcoming(e.ex_date)]

        if not self._events:
            self._status.setText(f"Keine kommenden Dividend-Events gefunden. Quelle: {source}.")
            self._list_layout.addStretch(1)
            return

        self._status.setText(f"{len(self._events)} kommende Dividend-Events geladen. Quelle: {source}.")

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

    # -----------------------------
    # Global events (right panel)
    # -----------------------------

    def _set_global_filter(self, mode: str) -> None:
        self._global_filter = (mode or "ALL").upper()
        self._render_global_events()

    def _on_global_failed(self, msg: str) -> None:
        self._global_events = []
        self._global_status.setText(f"Global Events konnten nicht geladen werden: {msg}")
        self._global_layout.addStretch(1)

    def _on_global_loaded(self, events: list, source: str) -> None:
        self._global_events = [e for e in events if isinstance(e, GlobalEvent)]

        if not self._global_events:
            self._global_status.setText(f"Keine globalen Events gefunden. Quelle: {source}.")
            self._global_layout.addStretch(1)
            return

        self._global_status.setText(f"{len(self._global_events)} globale Events geladen. Quelle: {source}.")
        self._render_global_events()

    def _render_global_events(self) -> None:
        # Clear UI list
        while self._global_layout.count():
            it = self._global_layout.takeAt(0)
            ww = it.widget()
            if ww is not None:
                ww.deleteLater()

        if not self._global_events:
            self._global_layout.addStretch(1)
            return

        mode = self._global_filter  # ALL | HOLIDAY | ELECTION
        month_prefix = f"{self._year:04d}-{self._month:02d}-"
        today = self._today_date()

        # ---- Aggregate duplicates: group by (date, title, category, source) -> set[countries] ----
        grouped: dict[tuple[str, str, str, str], set[str]] = {}

        for e in self._global_events:
            if mode != "ALL" and e.category != mode:
                continue

            # Nur kommende/aktuelle Events (>= heute)
            d = self._parse_ymd_date(e.date)
            if d is None or d < today:
                continue

            # Keep "ALL" clean: elections only for current month
            if mode == "ALL" and e.category == "ELECTION" and not e.date.startswith(month_prefix):
                continue

            key = (e.date, e.title, e.category, e.source)
            if key not in grouped:
                grouped[key] = set()
            grouped[key].add((e.country or "").strip().upper())

        if not grouped:
            empty = QLabel("Keine Events für diesen Filter.")
            empty.setObjectName("FinePrint")
            empty.setWordWrap(True)
            self._global_layout.addWidget(empty)
            self._global_layout.addStretch(1)
            return

        keys = sorted(grouped.keys(), key=lambda k: (k[0], k[2], k[1], k[3]))

        shown = 0
        for (date_str, title, category, source) in keys:
            codes = sorted([c for c in grouped[(date_str, title, category, source)] if c])
            country_txt = self._format_countries(codes, limit=18)

            card = QFrame()
            card.setObjectName("NewsCard")
            card.setAttribute(Qt.WA_StyledBackground, True)

            cv = QVBoxLayout(card)
            cv.setContentsMargins(10, 10, 10, 10)
            cv.setSpacing(4)

            head = QLabel(title)
            head.setObjectName("NewsTitle")
            head.setWordWrap(True)

            meta = QLabel(f"{date_str} · {category.title()} · {source}")
            meta.setObjectName("NewsMeta")
            meta.setWordWrap(True)

            countries_lbl = QLabel(f"Countries: {country_txt}" if country_txt else "Countries: —")
            countries_lbl.setObjectName("NewsMeta")
            countries_lbl.setWordWrap(True)

            cv.addWidget(head)
            cv.addWidget(meta)
            cv.addWidget(countries_lbl)

            self._global_layout.addWidget(card)

            shown += 1
            if shown >= 250:
                break

        self._global_layout.addStretch(1)
