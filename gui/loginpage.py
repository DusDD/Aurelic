# gui/benutzerpage_settings.py
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QLineEdit, QSizePolicy
)


# --------------------------
# Theme (identisch zu MainPage)
# --------------------------
@dataclass(frozen=True)
class Palette:
    bg0: str = "#0F1318"
    bg1: str = "#0F1318"
    bg2: str = "#0F1318"
    line: str = "#27303B"
    text0: str = "#E6EAF0"
    text1: str = "#AEB7C2"
    accent: str = "#6D929B"


def build_qss(p: Palette) -> str:
    return f"""
    QWidget {{
        background: {p.bg0};
        color: {p.text0};
        font-family: "Segoe UI", "Inter", "Helvetica", "Arial";
    }}

    #Card {{
        background: {p.bg1};
        border: 1px solid rgba(39,48,59,170);
        border-radius: 22px;
    }}

    #SectionTitle {{
        font-size: 20px;
        font-weight: 900;
        letter-spacing: -0.3px;
    }}

    QLabel {{
        font-size: 13px;
        color: {p.text1};
    }}

    QLineEdit {{
        background: rgba(255,255,255,6);
        border: 1px solid rgba(39,48,59,170);
        border-radius: 14px;
        padding: 10px 12px;
        color: {p.text0};
        font-size: 13px;
    }}

    QLineEdit:focus {{
        border: 1px solid rgba(109,146,155,140);
    }}

    QPushButton#Ghost {{
        background: transparent;
        border: 1px solid rgba(39,48,59,170);
        border-radius: 16px;
        padding: 10px 16px;
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
        padding: 10px 18px;
        font-weight: 900;
        color: {p.text0};
    }}
    QPushButton#Primary:hover {{
        background: rgba(109,146,155,70);
    }}
    """


# --------------------------
# Settings / Benutzer Page
# --------------------------
class SettingsPage(QWidget):
    back_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._palette = Palette()
        self.setStyleSheet(build_qss(self._palette))

        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(20)

        # Card Container
        card = QFrame()
        card.setObjectName("Card")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        cv = QVBoxLayout(card)
        cv.setContentsMargins(26, 24, 26, 26)
        cv.setSpacing(18)

        title = QLabel("Benutzer-Einstellungen")
        title.setObjectName("SectionTitle")

        cv.addWidget(title)

        # ---- Persönliche Daten ----
        cv.addWidget(self._field("Vorname", "Nathan"))
        cv.addWidget(self._field("Nachname", "Becker"))
        cv.addWidget(self._field("Adresse", "Musterstraße 1, 12345 Musterstadt"))

        # ---- Passwort ändern ----
        pw_title = QLabel("Passwort ändern")
        pw_title.setObjectName("SectionTitle")
        pw_title.setContentsMargins(0, 10, 0, 0)

        cv.addWidget(pw_title)
        cv.addWidget(self._field("Aktuelles Passwort", "", password=True))
        cv.addWidget(self._field("Neues Passwort", "", password=True))
        cv.addWidget(self._field("Neues Passwort bestätigen", "", password=True))

        # ---- Buttons ----
        btn_row = QWidget()
        bh = QHBoxLayout(btn_row)
        bh.setContentsMargins(0, 10, 0, 0)
        bh.setSpacing(12)

        back = QPushButton("Zurück")
        back.setObjectName("Ghost")
        back.clicked.connect(self.back_requested.emit)

        save = QPushButton("Änderungen speichern")
        save.setObjectName("Primary")

        bh.addStretch(1)
        bh.addWidget(back)
        bh.addWidget(save)

        cv.addWidget(btn_row)

        root.addWidget(card, 0, Qt.AlignHCenter)
        root.addStretch(1)

    # --------------------------
    # Helpers
    # --------------------------
    def _field(self, label: str, value: str, password: bool = False) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)

        l = QLabel(label)
        e = QLineEdit()
        e.setText(value)
        if password:
            e.setEchoMode(QLineEdit.Password)

        v.addWidget(l)
        v.addWidget(e)
        return w
