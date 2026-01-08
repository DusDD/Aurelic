# gui/loginandregisterpage.py
from __future__ import annotations

import re
import os
import json
import random
from dataclasses import dataclass
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from PySide6.QtCore import Qt, Signal, QEvent, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QLineEdit,
    QHBoxLayout, QVBoxLayout, QStackedWidget, QSizePolicy,
    QMessageBox
)


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
    # QSS expects forward slashes; also tolerate relative paths.
    p = (path or "").replace("\\", "/")
    return f'url("{p}")' if p else ""


def build_qss(p: Palette, background_image_path: str = "images/Backgroundimage.png") -> str:
    bg_url = _qss_url(background_image_path)

    return f"""
    QWidget {{
        color: {p.text0};
        font-family: "Segoe UI", "Inter", "Helvetica", "Arial";
        background-color: {p.bg0};
    }}

    /* App background image (Root widget) */
    #Root {{
        background-color: {p.bg0};
        border-image: {bg_url} 0 0 0 0 stretch stretch;
    }}

    #Card {{
        background: {p.bg1};
        border: 1px solid rgba(39,48,59,170);
        border-radius: 22px;
    }}

    #LogoBox {{
        background: transparent;
        border: 0px;
        border-radius: 0px;
    }}

    #BrandTitle {{
        font-size: 28px;
        font-weight: 900;
        letter-spacing: -0.6px;
        color: {p.text0};
    }}

    #BrandSub {{
        font-size: 13px;
        color: {p.text1};
    }}

    #SectionTitle {{
        font-size: 22px;
        font-weight: 900;
        letter-spacing: -0.3px;
        color: {p.text0};
    }}

    #TabBar {{
        background: {p.bg2};
        border: 1px solid rgba(39,48,59,170);
        border-radius: 999px;
        padding: 6px;
    }}

    QPushButton#TabButton {{
        background: transparent;
        border: 0px;
        padding: 10px 12px;
        border-radius: 999px;
        font-weight: 850;
        color: rgba(230,234,240,160);
    }}
    QPushButton#TabButton[active="true"] {{
        background: rgba(109,146,155,40);
        color: {p.text0};
    }}
    QPushButton#TabButton:hover {{
        color: {p.text0};
    }}

    QLineEdit {{
        background: {p.bg2};
        border: 1px solid rgba(39,48,59,200);
        padding: 10px 12px;
        border-radius: 14px;
        font-size: 13px;
        color: {p.text0};
        selection-background-color: rgba(109,146,155,70);
    }}
    QLineEdit:focus {{
        border: 1px solid {p.accent};
    }}

    QPushButton#Primary {{
        background-color: {p.accent};
        color: rgba(11,13,16,255);
        border: 0px;
        border-radius: 16px;
        padding: 11px 14px;
        font-weight: 900;
        letter-spacing: 0.2px;
    }}
    QPushButton#Primary:hover {{
        background-color: rgba(109,146,155,235);
    }}
    QPushButton#Primary:pressed {{
        background-color: rgba(109,146,155,210);
    }}
    QPushButton#Primary:disabled {{
        background-color: rgba(109,146,155,80);
        color: rgba(11,13,16,120);
    }}

    QPushButton#Link {{
        background: transparent;
        border: 0px;
        color: {p.accent};
        font-weight: 850;
        padding: 4px 0px;
        text-align: left;
    }}
    QPushButton#Link:hover {{
        text-decoration: underline;
        color: {p.accent};
    }}

    QPushButton#Eye {{
        background: transparent;
        border: 0px;
        color: {p.accent};
        font-weight: 850;
        padding: 4px 10px;
    }}
    QPushButton#Eye:hover {{
        text-decoration: underline;
        color: {p.accent};
    }}

    #FinePrint {{
        color: rgba(174,183,194,150);
        font-size: 12px;
    }}
    """


class StartPage(QWidget):
    login_requested = Signal(str, str)

    # Existing signal (kept for backwards compatibility)
    register_requested = Signal(str, str, str, str)  # name, email, pw1, pw2

    # New signal including address data
    register_requested_v2 = Signal(
        str, str, str, str, str, str, str, str, str
    )  # first_name, last_name, email, pw1, pw2, street, postal_code, city, country

    # Frontend-only forgot password flow signals
    forgot_password_email_submitted = Signal(str)            # email
    forgot_password_reset_submitted = Signal(str, str, str)  # email, code, new_password

    _EMAIL_RE = re.compile(
        r"^(?=.{3,254}$)(?=.{1,64}@)"
        r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
        r"@"
        r"[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$"
    )

    def __init__(
        self,
        logo_path: str = "images/Aurelic Logo mit Clar Leitmotiv.png",
        background_path: str = "images/Backgroundimage.png",
        parent: QWidget | None = None
    ):
        super().__init__(parent)

        # IMPORTANT: ensure the widget paints the styled background (prevents white showing through)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)

        self.setObjectName("Root")
        self._palette = Palette()
        self.setStyleSheet(build_qss(self._palette, background_path))

        self._tabs_login: QPushButton | None = None
        self._tabs_register: QPushButton | None = None
        self._stack: QStackedWidget | None = None

        # Login widgets
        self._login_email: QLineEdit | None = None
        self._login_pw: QLineEdit | None = None
        self._btn_login: QPushButton | None = None
        self._login_email_hint: QLabel | None = None
        self._login_caps_hint: QLabel | None = None
        self._btn_login_eye: QPushButton | None = None

        # Register widgets
        self._reg_first_name: QLineEdit | None = None
        self._reg_last_name: QLineEdit | None = None
        self._reg_email: QLineEdit | None = None
        self._reg_pw1: QLineEdit | None = None
        self._reg_pw2: QLineEdit | None = None
        self._reg_street: QLineEdit | None = None
        self._reg_postal: QLineEdit | None = None
        self._reg_city: QLineEdit | None = None
        self._reg_country: QLineEdit | None = None

        self._reg_email_hint: QLabel | None = None
        self._reg_caps_hint: QLabel | None = None
        self._btn_reg_eye1: QPushButton | None = None
        self._btn_reg_eye2: QPushButton | None = None
        self._reg_address_hint: QLabel | None = None

        # Forgot password widgets
        self._reset_email: QLineEdit | None = None
        self._btn_send_code: QPushButton | None = None
        self._reset_email_hint: QLabel | None = None

        self._reset_confirm_email: QLineEdit | None = None
        self._reset_code: QLineEdit | None = None
        self._reset_new_pw: QLineEdit | None = None
        self._reset_new_pw2: QLineEdit | None = None
        self._reset_confirm_email_hint: QLabel | None = None
        self._reset_caps_hint: QLabel | None = None
        self._btn_reset_eye1: QPushButton | None = None
        self._btn_reset_eye2: QPushButton | None = None

        # Password strength UI
        self._reg_strength_label: QLabel | None = None
        self._reg_match_label: QLabel | None = None
        self._btn_register: QPushButton | None = None

        self._reset_strength_label: QLabel | None = None
        self._reset_match_label: QLabel | None = None
        self._btn_reset: QPushButton | None = None

        # Quote UI (login page)
        self._quote_label: QLabel | None = None
        self._quotes = [
  "Trading ist der einzige Beruf, bei dem man vor dem Bildschirm sitzt und trotzdem Herzrasen bekommt.",
  "Ich trade nicht aus Gier – ich sammle nur sehr ambitioniert Verluste.",
  "Buy the dip – und dann noch einen – und noch einen. Irgendwann passt es.",
  "Mein Risikomanagement besteht aus Hoffnung und Kaffee.",
  "Daytrading: Heute Millionär, morgen realistischer Mensch.",
  "Der Markt ist irrational – und ich bin es manchmal auch.",
  "Stop-Loss ist das, was immer genau dort liegt, wo der Markt kurz hinläuft.",
  "Ich liebe Volatilität. Sie liebt mich leider nicht.",
  "Chartanalyse: Linien zeichnen, bis es logisch aussieht.",
  "Trading lehrt Demut – meistens sehr schnell.",
  "Der Markt hat immer recht. Leider.",
  "Ich wollte investieren. Jetzt habe ich eine Lebenserfahrung.",
  "Emotionen haben an der Börse nichts verloren – außer Panik.",
  "Mein Portfolio ist gut diversifiziert: Verluste in allen Sektoren.",
  "Trading ist einfach. Gewinne machen ist der schwierige Teil.",
  "Hebelprodukte: Kleine Entscheidung, große Gefühle.",
  "Ich trade langfristig – bis morgen.",
  "Der Markt schuldet dir nichts. Nicht mal eine Erklärung.",
  "Wenn es einfach wäre, würden es alle können. Oh, Moment …",
  "Börse ist wie Schach – nur ohne Regeln und mit weniger Kontrolle.",
  "Ich trade datenbasiert – meine Daten sagen mir, dass es weh tut.",
  "Der Markt macht keine Fehler. Meine Orders schon.",
  "Trading ist Geduld haben, bis man sie verliert.",
  "Gewinne sind temporär, Screenshots sind für immer.",
  "Backtesting: In der Vergangenheit war ich extrem erfolgreich.",
  "Der Markt öffnet – meine Disziplin schließt.",
  "Ich habe einen Plan. Der Markt hat einen besseren.",
  "Trading ist 10 % Strategie und 90 % Selbstbeherrschung. Ungefähr.",
  "Der Chart sah eindeutig aus – bis er es nicht mehr war.",
  "Ich folge dem Trend. Meistens dem falschen.",
  "Meine größte Position ist Hoffnung.",
  "Trading ist Stress, aber mit Kerzen.",
  "Ich handle nicht gegen den Markt. Ich werde nur regelmäßig belehrt.",
  "Gewinnmitnahmen sind schwierig. Verluste laufen lassen geht erstaunlich leicht.",
  "Wenn alle euphorisch sind, werde ich nervös. Wenn alle panisch sind, auch.",
  "Trading ist wie Wettervorhersage – nur mit echtem Geld.",
  "Der Markt testet nicht nur Levels, sondern auch Charakter.",
  "Ich bin nicht schlecht im Trading. Der Markt ist nur sehr konsequent.",
  "Trading hat mir beigebracht, dass ‚sicher‘ ein sehr flexibler Begriff ist.",
  "Man lernt nie aus – vor allem nicht aus dem letzten Trade."
]

        self._quote_timer = QTimer(self)
        self._quote_timer.setInterval(10_000)
        self._quote_timer.timeout.connect(self._rotate_quote)

        # Page refs
        self._page_login: QWidget | None = None
        self._page_register: QWidget | None = None
        self._page_reset_request: QWidget | None = None
        self._page_reset_confirm: QWidget | None = None

        root = QHBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(18)

        brand = self._build_brand_panel(logo_path)
        auth = self._build_auth_card()

        card_width = 720
        brand.setFixedWidth(card_width)
        auth.setFixedWidth(card_width)

        root.addStretch(1)
        root.addWidget(brand, 0)
        root.addWidget(auth, 0)
        root.addStretch(1)

        self._set_active_tab(0)

    def _build_brand_panel(self, logo_path: str) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Card")
        panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        v = QVBoxLayout(panel)
        v.setContentsMargins(26, 26, 26, 22)
        v.setSpacing(12)

        logo = QLabel()
        logo.setObjectName("LogoBox")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(480, 480)

        pm = QPixmap(logo_path) if os.path.exists(logo_path) else QPixmap()
        if not pm.isNull():
            pm = pm.scaled(420, 420, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo.setPixmap(pm)
        else:
            logo.setText("LOGO")

        title = QLabel("Aurelic.")
        title.setObjectName("BrandTitle")

        sub = QLabel("Secure access to your portfolio. Log in to continue or create a new account.")
        sub.setObjectName("BrandSub")
        sub.setWordWrap(True)

        hint = QLabel("For security reasons, only the password defined by you for this application may be used.")
        hint.setObjectName("FinePrint")
        hint.setWordWrap(True)

        v.addWidget(logo, 0, Qt.AlignHCenter)
        v.addStretch(1)
        v.addWidget(title, 0, Qt.AlignLeft)
        v.addWidget(sub)
        v.addWidget(hint)

        return panel

    def _build_auth_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        v = QVBoxLayout(card)
        v.setContentsMargins(26, 26, 26, 22)
        v.setSpacing(14)

        tabbar = QFrame()
        tabbar.setObjectName("TabBar")
        th = QHBoxLayout(tabbar)
        th.setContentsMargins(6, 6, 6, 6)
        th.setSpacing(6)

        self._tabs_login = QPushButton("Login")
        self._tabs_login.setObjectName("TabButton")
        self._tabs_login.setProperty("active", True)

        self._tabs_register = QPushButton("Create account")
        self._tabs_register.setObjectName("TabButton")
        self._tabs_register.setProperty("active", False)

        th.addWidget(self._tabs_login)
        th.addWidget(self._tabs_register)

        self._stack = QStackedWidget()

        self._page_login = self._build_login_page()
        self._page_register = self._build_register_page()
        self._page_reset_request = self._build_reset_request_page()
        self._page_reset_confirm = self._build_reset_confirm_page()

        self._stack.addWidget(self._page_login)          # 0
        self._stack.addWidget(self._page_register)       # 1
        self._stack.addWidget(self._page_reset_request)  # 2
        self._stack.addWidget(self._page_reset_confirm)  # 3

        self._tabs_login.clicked.connect(lambda: self._set_active_tab(0))
        self._tabs_register.clicked.connect(lambda: self._set_active_tab(1))

        v.addWidget(tabbar, 0)
        v.addWidget(self._stack, 1)

        return card

    # -----------------------------
    # UI helpers: password row + eye toggle + caps lock
    # -----------------------------
    def _make_password_row(self, line_edit: QLineEdit, eye_button: QPushButton) -> QWidget:
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)
        h.addWidget(line_edit, 1)
        h.addWidget(eye_button, 0)
        return row

    def _toggle_password_visibility(self, line_edit: QLineEdit, btn: QPushButton) -> None:
        if line_edit.echoMode() == QLineEdit.Password:
            line_edit.setEchoMode(QLineEdit.Normal)
            btn.setText("Hide")
        else:
            line_edit.setEchoMode(QLineEdit.Password)
            btn.setText("Show")

    def _caps_on(self, modifiers: Qt.KeyboardModifiers) -> bool:
        try:
            return bool(modifiers & Qt.KeyboardModifier.CapsLockModifier)
        except Exception:
            return False

    def _set_caps_label(self, label: QLabel | None, caps_on: bool) -> None:
        if label is None:
            return
        label.setText("Caps Lock is ON." if caps_on else "")

    def eventFilter(self, obj, event) -> bool:
        if event.type() in (QEvent.KeyPress, QEvent.KeyRelease):
            if obj in (
                self._login_pw,
                self._reg_pw1,
                self._reg_pw2,
                self._reset_new_pw,
                self._reset_new_pw2
            ):
                caps = self._caps_on(event.modifiers())

                if obj == self._login_pw:
                    self._set_caps_label(self._login_caps_hint, caps)
                elif obj in (self._reg_pw1, self._reg_pw2):
                    self._set_caps_label(self._reg_caps_hint, caps)
                elif obj in (self._reset_new_pw, self._reset_new_pw2):
                    self._set_caps_label(self._reset_caps_hint, caps)

        return super().eventFilter(obj, event)

    # -----------------------------
    # Validation: email + address
    # -----------------------------
    def _is_valid_email(self, email: str) -> bool:
        email = (email or "").strip()
        if not email or " " in email:
            return False
        return bool(self._EMAIL_RE.match(email))

    def _set_email_hint(self, label: QLabel | None, email: str) -> bool:
        ok = self._is_valid_email(email)
        if label is not None:
            if not email.strip():
                label.setText("")
            else:
                label.setText("Email looks valid." if ok else "Please enter a valid email address.")
        return ok

    def _is_reasonable_text(self, s: str, min_len: int = 2, max_len: int = 120) -> bool:
        s = (s or "").strip()
        if not (min_len <= len(s) <= max_len):
            return False
        return bool(re.match(r"^[A-Za-zÀ-ÖØ-öø-ÿ0-9 .,'’\\-/#]+$", s))

    def _is_valid_postal_code(self, postal: str, country: str) -> bool:
        """
        Enforces: postal code must be digits-only (as requested).
        For Germany (default): exactly 5 digits.
        For other countries: digits-only length 3..10.
        """
        postal = (postal or "").strip()
        country = (country or "").strip().lower()

        if not postal:
            return False

        # digits-only requirement
        if not postal.isdigit():
            return False

        if country in ("", "germany", "de", "deutschland"):
            return len(postal) == 5

        return 3 <= len(postal) <= 10

    def _build_address_string(self) -> tuple[str, str, str, str]:
        street = (self._reg_street.text() if self._reg_street else "").strip()
        postal = (self._reg_postal.text() if self._reg_postal else "").strip()
        city = (self._reg_city.text() if self._reg_city else "").strip()
        country = (self._reg_country.text() if self._reg_country else "").strip()
        return street, postal, city, country

    def _address_format_ok(self) -> tuple[bool, str]:
        street, postal, city, country = self._build_address_string()

        if not self._is_reasonable_text(street, 5, 120):
            return False, "Please enter a valid street address."
        if not self._is_valid_postal_code(postal, country):
            return False, "Postal code must contain digits only (e.g., 68159)."
        if not self._is_reasonable_text(city, 2, 80):
            return False, "Please enter a valid city."
        if not self._is_reasonable_text(country, 2, 80):
            return False, "Please enter a valid country (e.g., Germany)."
        return True, "Address format looks valid."

    def _google_validate_address(self, street: str, postal: str, city: str, country: str) -> tuple[bool, str]:
        api_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
        if not api_key:
            return True, "No API key set; using format validation only."

        endpoint = f"https://addressvalidation.googleapis.com/v1:validateAddress?key={api_key}"
        body = {"address": {"addressLines": [street, f"{postal} {city}", country]}}
        data = json.dumps(body).encode("utf-8")
        req = Request(endpoint, data=data, headers={"Content-Type": "application/json"}, method="POST")

        try:
            with urlopen(req, timeout=8) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                j = json.loads(raw)

            verdict = (j.get("result", {}).get("verdict", {}) if isinstance(j, dict) else {})
            is_complete = bool(verdict.get("addressComplete"))
            has_unconfirmed = bool(verdict.get("hasUnconfirmedComponents"))

            if is_complete and not has_unconfirmed:
                return True, "Address validated successfully."
            if is_complete and has_unconfirmed:
                return True, "Address seems valid, but some parts are unconfirmed."
            return False, "Address could not be confirmed."

        except HTTPError as e:
            return False, f"Address validation failed (HTTP {e.code})."
        except URLError:
            return False, "Address validation failed (network error)."
        except Exception:
            return False, "Address validation failed (unexpected error)."

    # -----------------------------
    # Password strength
    # -----------------------------
    def _password_strength(self, pw: str) -> tuple[str, bool]:
        pw = pw or ""
        if len(pw) < 10:
            return ("Password too short (min. 10 characters).", False)

        has_lower = bool(re.search(r"[a-z]", pw))
        has_upper = bool(re.search(r"[A-Z]", pw))
        has_digit = bool(re.search(r"\\d", pw))
        has_special = bool(re.search(r"[^A-Za-z0-9]", pw))

        missing = []
        if not has_lower:
            missing.append("lowercase")
        if not has_upper:
            missing.append("uppercase")
        if not has_digit:
            missing.append("number")
        if not has_special:
            missing.append("special character")

        if missing:
            return (f"Add: {', '.join(missing)}.", False)

        lowered = pw.lower()
        common = {"password", "passwort", "123456", "qwerty", "letmein", "admin", "welcome"}
        if any(c in lowered for c in common):
            return ("Password looks too common. Choose something less predictable.", False)

        if re.search(r"(0123|1234|2345|3456|4567|5678|6789|abcd|bcde|cdef|qwer)", lowered):
            return ("Avoid simple sequences (e.g., 1234, abcd).", False)

        if re.search(r"(.)\\1\\1\\1", pw):
            return ("Avoid repeated characters (e.g., aaaa).", False)

        return ("Strong password.", True)

    # -----------------------------
    # UI state updates
    # -----------------------------
    def _update_login_ui(self) -> None:
        email = self._login_email.text() if self._login_email else ""
        pw = self._login_pw.text() if self._login_pw else ""
        email_ok = self._set_email_hint(self._login_email_hint, email)

        if self._btn_login is not None:
            self._btn_login.setEnabled(email_ok and bool(pw))

    def _update_register_ui(self) -> None:
        email = self._reg_email.text() if self._reg_email else ""
        email_ok = self._set_email_hint(self._reg_email_hint, email)

        fn = (self._reg_first_name.text() if self._reg_first_name else "").strip()
        ln = (self._reg_last_name.text() if self._reg_last_name else "").strip()
        fn_ok = self._is_reasonable_text(fn, 2, 60)
        ln_ok = self._is_reasonable_text(ln, 2, 60)

        pw1 = self._reg_pw1.text() if self._reg_pw1 else ""
        pw2 = self._reg_pw2.text() if self._reg_pw2 else ""
        msg, pw_ok = self._password_strength(pw1)

        if self._reg_strength_label is not None:
            self._reg_strength_label.setText(msg)

        match_ok = (pw1 == pw2) and (len(pw2) > 0)
        if self._reg_match_label is not None:
            if len(pw2) == 0:
                self._reg_match_label.setText("")
            else:
                self._reg_match_label.setText("Passwords match." if match_ok else "Passwords do not match.")

        addr_ok, addr_msg = self._address_format_ok()
        if self._reg_address_hint is not None:
            if any((self._reg_street.text(), self._reg_postal.text(), self._reg_city.text(), self._reg_country.text())):
                self._reg_address_hint.setText(addr_msg)
            else:
                self._reg_address_hint.setText("")

        if self._btn_register is not None:
            self._btn_register.setEnabled(email_ok and fn_ok and ln_ok and pw_ok and match_ok and addr_ok)

    def _update_reset_request_ui(self) -> None:
        email = self._reset_email.text() if self._reset_email else ""
        email_ok = self._set_email_hint(self._reset_email_hint, email)
        if self._btn_send_code is not None:
            self._btn_send_code.setEnabled(email_ok)

    def _update_reset_confirm_ui(self) -> None:
        email = self._reset_confirm_email.text() if self._reset_confirm_email else ""
        email_ok = self._set_email_hint(self._reset_confirm_email_hint, email)

        code = (self._reset_code.text() if self._reset_code else "").strip()
        pw1 = self._reset_new_pw.text() if self._reset_new_pw else ""
        pw2 = self._reset_new_pw2.text() if self._reset_new_pw2 else ""

        msg, pw_ok = self._password_strength(pw1)
        if self._reset_strength_label is not None:
            self._reset_strength_label.setText(msg)

        match_ok = (pw1 == pw2) and (len(pw2) > 0)
        if self._reset_match_label is not None:
            if len(pw2) == 0:
                self._reset_match_label.setText("")
            else:
                self._reset_match_label.setText("Passwords match." if match_ok else "Passwords do not match.")

        if self._btn_reset is not None:
            self._btn_reset.setEnabled(email_ok and bool(code) and pw_ok and match_ok)

    # -----------------------------
    # Pages
    # -----------------------------
    def _build_login_page(self) -> QWidget:
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 8, 0, 0)
        v.setSpacing(10)

        title = QLabel("Welcome back")
        title.setObjectName("SectionTitle")

        subtitle = QLabel("Sign in with your email and password to continue.")
        subtitle.setObjectName("FinePrint")
        subtitle.setWordWrap(True)

        self._login_email = QLineEdit()
        self._login_email.setPlaceholderText("Email")

        self._login_email_hint = QLabel("")
        self._login_email_hint.setObjectName("FinePrint")
        self._login_email_hint.setWordWrap(True)

        self._login_pw = QLineEdit()
        self._login_pw.setPlaceholderText("Password")
        self._login_pw.setEchoMode(QLineEdit.Password)
        self._login_pw.installEventFilter(self)

        self._btn_login_eye = QPushButton("Show")
        self._btn_login_eye.setObjectName("Eye")
        self._btn_login_eye.clicked.connect(
            lambda: self._toggle_password_visibility(self._login_pw, self._btn_login_eye)
        )

        self._login_caps_hint = QLabel("")
        self._login_caps_hint.setObjectName("FinePrint")
        self._login_caps_hint.setWordWrap(True)

        self._btn_login = QPushButton("Sign in")
        self._btn_login.setObjectName("Primary")
        self._btn_login.setEnabled(False)
        self._btn_login.clicked.connect(self._emit_login)

        self._login_pw.returnPressed.connect(self._btn_login.click)

        btn_forgot = QPushButton("Forgot password?")
        btn_forgot.setObjectName("Link")
        btn_forgot.clicked.connect(self._open_reset_request)

        self._login_email.textChanged.connect(self._update_login_ui)
        self._login_pw.textChanged.connect(self._update_login_ui)

        v.addWidget(title)
        v.addWidget(subtitle)
        v.addWidget(self._login_email)
        v.addWidget(self._login_email_hint)
        v.addWidget(self._make_password_row(self._login_pw, self._btn_login_eye))
        v.addWidget(self._login_caps_hint)
        v.addWidget(self._btn_login)
        v.addWidget(btn_forgot, 0, Qt.AlignLeft)
        v.addStretch(1)

        # Rotating quote (above fine print)
        self._quote_label = QLabel("")
        self._quote_label.setObjectName("BrandSub")
        self._quote_label.setWordWrap(True)
        self._quote_label.setAlignment(Qt.AlignLeft)
        v.addWidget(self._quote_label)

        fine = QLabel("By signing in, you agree to the Terms of Service.")
        fine.setObjectName("FinePrint")
        fine.setWordWrap(True)
        v.addWidget(fine)

        # start rotating quotes
        self._rotate_quote()
        if not self._quote_timer.isActive():
            self._quote_timer.start()

        return page

    def _build_register_page(self) -> QWidget:
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 8, 0, 0)
        v.setSpacing(10)

        title = QLabel("Create your account")
        title.setObjectName("SectionTitle")

        subtitle = QLabel("Create an account using a valid email address, a strong password, and your address details.")
        subtitle.setObjectName("FinePrint")
        subtitle.setWordWrap(True)

        self._reg_first_name = QLineEdit()
        self._reg_first_name.setPlaceholderText("First name")

        self._reg_last_name = QLineEdit()
        self._reg_last_name.setPlaceholderText("Last name")

        self._reg_email = QLineEdit()
        self._reg_email.setPlaceholderText("Email")

        self._reg_email_hint = QLabel("By creating an account, you agree to the Terms of Service.")
        self._reg_email_hint.setObjectName("FinePrint")
        self._reg_email_hint.setWordWrap(True)

        self._reg_pw1 = QLineEdit()
        self._reg_pw1.setPlaceholderText("Password")
        self._reg_pw1.setEchoMode(QLineEdit.Password)
        self._reg_pw1.installEventFilter(self)

        self._btn_reg_eye1 = QPushButton("Show")
        self._btn_reg_eye1.setObjectName("Eye")
        self._btn_reg_eye1.clicked.connect(
            lambda: self._toggle_password_visibility(self._reg_pw1, self._btn_reg_eye1)
        )

        self._reg_pw2 = QLineEdit()
        self._reg_pw2.setPlaceholderText("Confirm password")
        self._reg_pw2.setEchoMode(QLineEdit.Password)
        self._reg_pw2.installEventFilter(self)

        self._btn_reg_eye2 = QPushButton("Show")
        self._btn_reg_eye2.setObjectName("Eye")
        self._btn_reg_eye2.clicked.connect(
            lambda: self._toggle_password_visibility(self._reg_pw2, self._btn_reg_eye2)
        )

        self._reg_caps_hint = QLabel("")
        self._reg_caps_hint.setObjectName("FinePrint")
        self._reg_caps_hint.setWordWrap(True)

        self._reg_strength_label = QLabel("")
        self._reg_strength_label.setObjectName("FinePrint")
        self._reg_strength_label.setWordWrap(True)

        self._reg_match_label = QLabel("")
        self._reg_match_label.setObjectName("FinePrint")
        self._reg_match_label.setWordWrap(True)

        # Address fields
        self._reg_street = QLineEdit()
        self._reg_street.setPlaceholderText("Street address")

        self._reg_postal = QLineEdit()
        self._reg_postal.setPlaceholderText("Postal code (digits only)")

        self._reg_city = QLineEdit()
        self._reg_city.setPlaceholderText("City")

        self._reg_country = QLineEdit()
        self._reg_country.setPlaceholderText("Country (e.g., Germany)")

        self._reg_address_hint = QLabel("")
        self._reg_address_hint.setObjectName("FinePrint")
        self._reg_address_hint.setWordWrap(True)

        self._btn_register = QPushButton("Create account")
        self._btn_register.setObjectName("Primary")
        self._btn_register.setEnabled(False)
        self._btn_register.clicked.connect(self._emit_register)

        self._reg_pw2.returnPressed.connect(self._btn_register.click)

        # Live validation
        self._reg_first_name.textChanged.connect(self._update_register_ui)
        self._reg_last_name.textChanged.connect(self._update_register_ui)
        self._reg_email.textChanged.connect(self._update_register_ui)
        self._reg_pw1.textChanged.connect(self._update_register_ui)
        self._reg_pw2.textChanged.connect(self._update_register_ui)
        self._reg_street.textChanged.connect(self._update_register_ui)
        self._reg_postal.textChanged.connect(self._update_register_ui)
        self._reg_city.textChanged.connect(self._update_register_ui)
        self._reg_country.textChanged.connect(self._update_register_ui)

        v.addWidget(title)
        v.addWidget(subtitle)
        v.addWidget(self._reg_first_name)
        v.addWidget(self._reg_last_name)
        v.addWidget(self._reg_email)
        v.addWidget(self._reg_email_hint)
        v.addWidget(self._make_password_row(self._reg_pw1, self._btn_reg_eye1))
        v.addWidget(self._make_password_row(self._reg_pw2, self._btn_reg_eye2))
        v.addWidget(self._reg_caps_hint)
        v.addWidget(self._reg_strength_label)
        v.addWidget(self._reg_match_label)

        v.addWidget(self._reg_street)
        v.addWidget(self._reg_postal)
        v.addWidget(self._reg_city)
        v.addWidget(self._reg_country)
        v.addWidget(self._reg_address_hint)

        v.addWidget(self._btn_register)
        v.addStretch(1)

        fine = QLabel("")
        fine.setObjectName("FinePrint")
        fine.setWordWrap(True)
        v.addWidget(fine)

        self._update_register_ui()
        return page

    def _build_reset_request_page(self) -> QWidget:
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 8, 0, 0)
        v.setSpacing(10)

        title = QLabel("Reset your password")
        title.setObjectName("SectionTitle")

        info = QLabel("Enter your email address. We will send you a one-time code.")
        info.setObjectName("FinePrint")
        info.setWordWrap(True)

        self._reset_email = QLineEdit()
        self._reset_email.setPlaceholderText("Email address")

        self._reset_email_hint = QLabel("")
        self._reset_email_hint.setObjectName("FinePrint")
        self._reset_email_hint.setWordWrap(True)

        self._btn_send_code = QPushButton("Send code")
        self._btn_send_code.setObjectName("Primary")
        self._btn_send_code.setEnabled(False)
        self._btn_send_code.clicked.connect(self._on_reset_send_code)

        btn_back = QPushButton("Back to sign in")
        btn_back.setObjectName("Link")
        btn_back.clicked.connect(self._back_to_login)

        self._reset_email.textChanged.connect(self._update_reset_request_ui)

        v.addWidget(title)
        v.addWidget(info)
        v.addWidget(self._reset_email)
        v.addWidget(self._reset_email_hint)
        v.addWidget(self._btn_send_code)
        v.addWidget(btn_back, 0, Qt.AlignLeft)
        v.addStretch(1)

        return page

    def _build_reset_confirm_page(self) -> QWidget:
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 8, 0, 0)
        v.setSpacing(10)

        title = QLabel("Enter code and set a new password")
        title.setObjectName("SectionTitle")

        info = QLabel("We sent a one-time code to this email:")
        info.setObjectName("FinePrint")
        info.setWordWrap(True)

        self._reset_confirm_email = QLineEdit()
        self._reset_confirm_email.setReadOnly(True)

        self._reset_confirm_email_hint = QLabel("")
        self._reset_confirm_email_hint.setObjectName("FinePrint")
        self._reset_confirm_email_hint.setWordWrap(True)

        self._reset_code = QLineEdit()
        self._reset_code.setPlaceholderText("6-digit code")

        self._reset_new_pw = QLineEdit()
        self._reset_new_pw.setPlaceholderText("New password")
        self._reset_new_pw.setEchoMode(QLineEdit.Password)
        self._reset_new_pw.installEventFilter(self)

        self._btn_reset_eye1 = QPushButton("Show")
        self._btn_reset_eye1.setObjectName("Eye")
        self._btn_reset_eye1.clicked.connect(
            lambda: self._toggle_password_visibility(self._reset_new_pw, self._btn_reset_eye1)
        )

        self._reset_new_pw2 = QLineEdit()
        self._reset_new_pw2.setPlaceholderText("Repeat new password")
        self._reset_new_pw2.setEchoMode(QLineEdit.Password)
        self._reset_new_pw2.installEventFilter(self)

        self._btn_reset_eye2 = QPushButton("Show")
        self._btn_reset_eye2.setObjectName("Eye")
        self._btn_reset_eye2.clicked.connect(
            lambda: self._toggle_password_visibility(self._reset_new_pw2, self._btn_reset_eye2)
        )

        self._reset_caps_hint = QLabel("")
        self._reset_caps_hint.setObjectName("FinePrint")
        self._reset_caps_hint.setWordWrap(True)

        self._btn_reset = QPushButton("Reset password")
        self._btn_reset.setObjectName("Primary")
        self._btn_reset.setEnabled(False)
        self._btn_reset.clicked.connect(self._on_reset_submit)

        self._reset_new_pw2.returnPressed.connect(self._btn_reset.click)

        self._reset_strength_label = QLabel("")
        self._reset_strength_label.setObjectName("FinePrint")
        self._reset_strength_label.setWordWrap(True)

        self._reset_match_label = QLabel("")
        self._reset_match_label.setObjectName("FinePrint")
        self._reset_match_label.setWordWrap(True)

        self._reset_code.textChanged.connect(self._update_reset_confirm_ui)
        self._reset_new_pw.textChanged.connect(self._update_reset_confirm_ui)
        self._reset_new_pw2.textChanged.connect(self._update_reset_confirm_ui)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        btn_resend = QPushButton("Resend code")
        btn_resend.setObjectName("Link")
        btn_resend.clicked.connect(self._on_reset_resend)

        btn_back = QPushButton("Back")
        btn_back.setObjectName("Link")
        btn_back.clicked.connect(self._back_to_reset_request)

        row.addWidget(btn_resend, 0, Qt.AlignLeft)
        row.addStretch(1)
        row.addWidget(btn_back, 0, Qt.AlignRight)

        v.addWidget(title)
        v.addWidget(info)
        v.addWidget(self._reset_confirm_email)
        v.addWidget(self._reset_confirm_email_hint)
        v.addWidget(self._reset_code)
        v.addWidget(self._make_password_row(self._reset_new_pw, self._btn_reset_eye1))
        v.addWidget(self._make_password_row(self._reset_new_pw2, self._btn_reset_eye2))
        v.addWidget(self._reset_caps_hint)
        v.addWidget(self._reset_strength_label)
        v.addWidget(self._reset_match_label)
        v.addWidget(self._btn_reset)
        v.addLayout(row)
        v.addStretch(1)

        fine = QLabel("For security, the code is one-time and typically expires quickly.")
        fine.setObjectName("FinePrint")
        fine.setWordWrap(True)
        v.addWidget(fine)

        return page

    # -----------------------------
    # Quote rotation
    # -----------------------------
    def _rotate_quote(self) -> None:
        if self._quote_label is None or not self._quotes:
            return

        current = self._quote_label.text()
        candidates = [q for q in self._quotes if q != current]
        self._quote_label.setText(random.choice(candidates) if candidates else random.choice(self._quotes))

    # -----------------------------
    # Navigation / actions
    # -----------------------------
    def _open_reset_request(self) -> None:
        if self._stack is None or self._page_reset_request is None:
            return

        prefill = (self._login_email.text() if self._login_email else "").strip()
        if self._reset_email is not None:
            self._reset_email.setText(prefill)

        self._update_reset_request_ui()
        self._set_tabs_active(False, False)
        self._stack.setCurrentWidget(self._page_reset_request)

    def _back_to_login(self) -> None:
        self._set_active_tab(0)

    def _back_to_reset_request(self) -> None:
        if self._stack is None or self._page_reset_request is None:
            return
        self._set_tabs_active(False, False)
        self._stack.setCurrentWidget(self._page_reset_request)

    def _on_reset_send_code(self) -> None:
        email = (self._reset_email.text() if self._reset_email else "").strip()

        if not self._is_valid_email(email):
            QMessageBox.warning(self, "Invalid email", "Please enter a valid email address.")
            return

        self.forgot_password_email_submitted.emit(email)

        if self._reset_confirm_email is not None:
            self._reset_confirm_email.setText(email)

        if self._reset_code is not None:
            self._reset_code.clear()
        if self._reset_new_pw is not None:
            self._reset_new_pw.clear()
        if self._reset_new_pw2 is not None:
            self._reset_new_pw2.clear()

        if self._btn_reset is not None:
            self._btn_reset.setEnabled(False)

        if self._reset_new_pw is not None and self._btn_reset_eye1 is not None:
            self._reset_new_pw.setEchoMode(QLineEdit.Password)
            self._btn_reset_eye1.setText("Show")
        if self._reset_new_pw2 is not None and self._btn_reset_eye2 is not None:
            self._reset_new_pw2.setEchoMode(QLineEdit.Password)
            self._btn_reset_eye2.setText("Show")

        if self._stack is not None and self._page_reset_confirm is not None:
            self._set_tabs_active(False, False)
            self._stack.setCurrentWidget(self._page_reset_confirm)

        self._update_reset_confirm_ui()

        QMessageBox.information(
            self,
            "Check your inbox",
            "If the email exists, you will receive a one-time code shortly."
        )

    def _on_reset_resend(self) -> None:
        email = (self._reset_confirm_email.text() if self._reset_confirm_email else "").strip()
        if self._is_valid_email(email):
            self.forgot_password_email_submitted.emit(email)
            QMessageBox.information(self, "Sent", "If the email exists, a new code will be sent shortly.")
        else:
            QMessageBox.warning(self, "Invalid email", "Email is invalid.")

    def _on_reset_submit(self) -> None:
        email = (self._reset_confirm_email.text() if self._reset_confirm_email else "").strip()
        code = (self._reset_code.text() if self._reset_code else "").strip()
        pw1 = self._reset_new_pw.text() if self._reset_new_pw else ""
        pw2 = self._reset_new_pw2.text() if self._reset_new_pw2 else ""

        if not self._is_valid_email(email):
            QMessageBox.warning(self, "Invalid email", "Email is invalid.")
            return
        if not code:
            QMessageBox.warning(self, "Invalid code", "Please enter the code from the email.")
            return

        msg, ok = self._password_strength(pw1)
        if not ok:
            QMessageBox.warning(self, "Weak password", msg)
            return
        if pw1 != pw2:
            QMessageBox.warning(self, "Mismatch", "Passwords do not match.")
            return

        self.forgot_password_reset_submitted.emit(email, code, pw1)

        QMessageBox.information(self, "Submitted", "Your password reset was submitted.")
        self._set_active_tab(0)

    # -----------------------------
    # Tabs / Stack control
    # -----------------------------
    def _set_tabs_active(self, login_active: bool, register_active: bool) -> None:
        if self._tabs_login is None or self._tabs_register is None:
            return

        self._tabs_login.setProperty("active", login_active)
        self._tabs_register.setProperty("active", register_active)

        self._tabs_login.style().unpolish(self._tabs_login)
        self._tabs_login.style().polish(self._tabs_login)
        self._tabs_register.style().unpolish(self._tabs_register)
        self._tabs_register.style().polish(self._tabs_register)

    def _set_active_tab(self, index: int) -> None:
        if self._stack is None or self._tabs_login is None or self._tabs_register is None:
            return

        self._stack.setCurrentIndex(index)
        self._set_tabs_active(index == 0, index == 1)

        if index == 0:
            self._update_login_ui()
        elif index == 1:
            self._update_register_ui()

    # -----------------------------
    # Emit login/register
    # -----------------------------
    def _emit_login(self) -> None:
        email = (self._login_email.text() if self._login_email else "").strip()
        pw = self._login_pw.text() if self._login_pw else ""

        if not self._is_valid_email(email):
            QMessageBox.warning(self, "Invalid email", "Please enter a valid email address.")
            return
        if not pw:
            QMessageBox.warning(self, "Missing password", "Please enter your password.")
            return

        self.login_requested.emit(email, pw)

    def _emit_register(self) -> None:
        first_name = (self._reg_first_name.text() if self._reg_first_name else "").strip()
        last_name = (self._reg_last_name.text() if self._reg_last_name else "").strip()
        email = (self._reg_email.text() if self._reg_email else "").strip()
        pw1 = self._reg_pw1.text() if self._reg_pw1 else ""
        pw2 = self._reg_pw2.text() if self._reg_pw2 else ""

        if not self._is_reasonable_text(first_name, 2, 60):
            QMessageBox.warning(self, "Invalid first name", "Please enter a valid first name.")
            return
        if not self._is_reasonable_text(last_name, 2, 60):
            QMessageBox.warning(self, "Invalid last name", "Please enter a valid last name.")
            return
        if not self._is_valid_email(email):
            QMessageBox.warning(self, "Invalid email", "Please enter a valid email address.")
            return

        msg, ok = self._password_strength(pw1)
        if not ok:
            QMessageBox.warning(self, "Weak password", msg)
            return
        if pw1 != pw2:
            QMessageBox.warning(self, "Mismatch", "Passwords do not match.")
            return

        addr_ok, addr_msg = self._address_format_ok()
        if not addr_ok:
            QMessageBox.warning(self, "Invalid address", addr_msg)
            return

        street, postal, city, country = self._build_address_string()
        real_ok, real_msg = self._google_validate_address(street, postal, city, country)
        if not real_ok:
            QMessageBox.warning(self, "Address not confirmed", real_msg)
            return

        self.register_requested_v2.emit(first_name, last_name, email, pw1, pw2, street, postal, city, country)

        full_name = f"{first_name} {last_name}".strip()
        self.register_requested.emit(full_name, email, pw1, pw2)
