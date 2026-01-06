# gui/startpage.py  (paste the full file; key change: fixed equal widths for both cards)
from __future__ import annotations

import os
from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QLineEdit,
    QHBoxLayout, QVBoxLayout, QStackedWidget, QSizePolicy
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
    accent: str = "#8AD4C8"
    accent2: str = "#66BFB1"


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
                                   stop:0 rgba(138,212,200,30),
                                   stop:1 rgba(11,13,16,255));
    }}

    #Card {{
        background: {p.bg1};
        border: 1px solid rgba(39,48,59,170);
        border-radius: 22px;
    }}

    #LogoBox {{
        background: rgba(138,212,200,10);
        border: 1px solid rgba(39,48,59,170);
        border-radius: 26px;
        color: {p.text1};
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
        background: rgba(138,212,200,22);
        color: {p.text0};
    }}
    QPushButton#TabButton:hover {{
        color: {p.text0};
    }}

    QLineEdit {{
        background: 0B0D10;
        border: 1px solid rgba(39,48,59,200);
        padding: 10px 12px;
        border-radius: 14px;
        font-size: 13px;
        color: {p.text0};
        selection-background-color: rgba(138,212,200,70);
    }}
    QLineEdit:focus {{
        border: 1px solid rgba(138,212,200,170);
    }}

    QPushButton#Primary {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                   stop:0 rgba(138,212,200,245),
                                   stop:1 rgba(102,191,177,235));
        color: rgba(11,13,16,255);
        border: 0px;
        border-radius: 16px;
        padding: 11px 14px;
        font-weight: 900;
        letter-spacing: 0.2px;
    }}
    QPushButton#Primary:hover {{
        background: rgba(138,212,200,245);
    }}
    QPushButton#Primary:pressed {{
        background: rgba(102,191,177,240);
    }}

    QPushButton#Link {{
        background: transparent;
        border: 0px;
        color: rgba(138,212,200,220);
        font-weight: 850;
        padding: 4px 0px;
        text-align: left;
    }}
    QPushButton#Link:hover {{
        text-decoration: underline;
        color: rgba(138,212,200,255);
    }}

    #FinePrint {{
        color: rgba(174,183,194,150);
        font-size: 12px;
    }}
    """


class StartPage(QWidget):
    login_requested = Signal(str, str)
    register_requested = Signal(str, str, str, str)
    forgot_password_requested = Signal()

    def __init__(self, logo_path: str = "logo", parent: QWidget | None = None):
        super().__init__(parent)

        self.setObjectName("Root")
        self._palette = Palette()
        self.setStyleSheet(build_qss(self._palette))

        self._tabs_login: QPushButton | None = None
        self._tabs_register: QPushButton | None = None
        self._stack: QStackedWidget | None = None

        self._login_email: QLineEdit | None = None
        self._login_pw: QLineEdit | None = None

        self._reg_name: QLineEdit | None = None
        self._reg_email: QLineEdit | None = None
        self._reg_pw1: QLineEdit | None = None
        self._reg_pw2: QLineEdit | None = None

        root = QHBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(18)

        brand = self._build_brand_panel(logo_path)
        auth = self._build_auth_card()

        # Make both cards exactly the same width:
        # Choose a width that fits common screens but still feels wide.
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
        logo.setFixedSize(160, 160)
        logo.setAlignment(Qt.AlignCenter)

        pm = QPixmap(logo_path) if os.path.exists(logo_path) else QPixmap()
        if not pm.isNull():
            pm = pm.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo.setPixmap(pm)
        else:
            logo.setText("LOGO")

        title = QLabel("Aurelic")
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
        self._stack.addWidget(self._build_login_page())
        self._stack.addWidget(self._build_register_page())

        self._tabs_login.clicked.connect(lambda: self._set_active_tab(0))
        self._tabs_register.clicked.connect(lambda: self._set_active_tab(1))

        v.addWidget(tabbar, 0)
        v.addWidget(self._stack, 1)

        return card

    def _build_login_page(self) -> QWidget:
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 8, 0, 0)
        v.setSpacing(10)

        title = QLabel("Welcome back")
        title.setObjectName("SectionTitle")

        self._login_email = QLineEdit()
        self._login_email.setPlaceholderText("Email")

        self._login_pw = QLineEdit()
        self._login_pw.setPlaceholderText("Password")
        self._login_pw.setEchoMode(QLineEdit.Password)

        btn_login = QPushButton("Sign in")
        btn_login.setObjectName("Primary")
        btn_login.clicked.connect(self._emit_login)

        btn_forgot = QPushButton("Forgot password?")
        btn_forgot.setObjectName("Link")
        btn_forgot.clicked.connect(self.forgot_password_requested.emit)

        v.addWidget(title)
        v.addWidget(self._login_email)
        v.addWidget(self._login_pw)
        v.addWidget(btn_login)
        v.addWidget(btn_forgot, 0, Qt.AlignLeft)
        v.addStretch(1)

        fine = QLabel("By signing in, you agree to the Terms of Service.")
        fine.setObjectName("FinePrint")
        fine.setWordWrap(True)
        v.addWidget(fine)

        return page

    def _build_register_page(self) -> QWidget:
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 8, 0, 0)
        v.setSpacing(10)

        title = QLabel("Create your account")
        title.setObjectName("SectionTitle")

        self._reg_name = QLineEdit()
        self._reg_name.setPlaceholderText("Full name")

        self._reg_email = QLineEdit()
        self._reg_email.setPlaceholderText("Email")

        self._reg_pw1 = QLineEdit()
        self._reg_pw1.setPlaceholderText("Password")
        self._reg_pw1.setEchoMode(QLineEdit.Password)

        self._reg_pw2 = QLineEdit()
        self._reg_pw2.setPlaceholderText("Confirm password")
        self._reg_pw2.setEchoMode(QLineEdit.Password)

        btn_register = QPushButton("Create account")
        btn_register.setObjectName("Primary")
        btn_register.clicked.connect(self._emit_register)

        v.addWidget(title)
        v.addWidget(self._reg_name)
        v.addWidget(self._reg_email)
        v.addWidget(self._reg_pw1)
        v.addWidget(self._reg_pw2)
        v.addWidget(btn_register)
        v.addStretch(1)

        fine = QLabel("Use a strong password and a valid email address.")
        fine.setObjectName("FinePrint")
        fine.setWordWrap(True)
        v.addWidget(fine)

        return page

    def _set_active_tab(self, index: int) -> None:
        if self._stack is None or self._tabs_login is None or self._tabs_register is None:
            return

        self._stack.setCurrentIndex(index)

        self._tabs_login.setProperty("active", index == 0)
        self._tabs_register.setProperty("active", index == 1)

        self._tabs_login.style().unpolish(self._tabs_login)
        self._tabs_login.style().polish(self._tabs_login)
        self._tabs_register.style().unpolish(self._tabs_register)
        self._tabs_register.style().polish(self._tabs_register)

    def _emit_login(self) -> None:
        email = (self._login_email.text() if self._login_email else "").strip()
        pw = self._login_pw.text() if self._login_pw else ""
        self.login_requested.emit(email, pw)

    def _emit_register(self) -> None:
        name = (self._reg_name.text() if self._reg_name else "").strip()
        email = (self._reg_email.text() if self._reg_email else "").strip()
        pw1 = self._reg_pw1.text() if self._reg_pw1 else ""
        pw2 = self._reg_pw2.text() if self._reg_pw2 else ""
        self.register_requested.emit(name, email, pw1, pw2)
