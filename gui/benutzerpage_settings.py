# gui/userpage.py
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QLineEdit, QTextEdit,
    QHBoxLayout, QVBoxLayout, QSizePolicy
)


# --------------------------
# Theme (same palette)
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

    #Shell {{
        background: {p.bg1};
        border: 1px solid rgba(39,48,59,170);
        border-radius: 44px;
    }}

    #Card {{
        background: {p.bg1};
        border: 1px solid rgba(39,48,59,170);
        border-radius: 22px;
    }}

    #Panel {{
        background: {p.bg2};
        border: 1px solid rgba(39,48,59,170);
        border-radius: 22px;
    }}

    #SectionTitle {{
        font-size: 22px;
        font-weight: 900;
        letter-spacing: -0.3px;
        color: {p.text0};
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

    #FieldLabel {{
        color: rgba(230,234,240,200);
        font-size: 12px;
        font-weight: 850;
        margin-bottom: 4px;
    }}

    QLineEdit, QTextEdit {{
        background: rgba(255,255,255,6);
        border: 1px solid rgba(39,48,59,170);
        border-radius: 14px;
        padding: 10px 12px;
        color: rgba(230,234,240,230);
        font-size: 13px;
        selection-background-color: rgba(109,146,155,70);
    }}

    QLineEdit:focus, QTextEdit:focus {{
        border: 1px solid rgba(109,146,155,120);
        background: rgba(255,255,255,8);
    }}

    QTextEdit {{
        min-height: 92px;
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
    """


class UserPage(QWidget):
    back_requested = Signal()      # optional, wenn du "Zurück" einbauen willst
    save_requested = Signal(dict)  # optional: emit form data

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setObjectName("Root")
        self._palette = Palette()
        self.setStyleSheet(build_qss(self._palette))
        self.setAttribute(Qt.WA_StyledBackground, True)

        # ---- Root layout (zentriert, wie eure Shell) ----
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(0)

        self._shell = QFrame()
        self._shell.setObjectName("Shell")
        self._shell.setAttribute(Qt.WA_StyledBackground, True)
        self._shell.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        shell_v = QVBoxLayout(self._shell)
        shell_v.setContentsMargins(22, 18, 22, 18)
        shell_v.setSpacing(14)

        shell_v.addWidget(self._build_topbar(), 0)
        shell_v.addWidget(self._build_content(), 1)

        root.addWidget(self._shell, 0, Qt.AlignCenter)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)

        # gleiche "tablet/shell"-Logik wie MainPage, aber etwas kompakter
        m = 40
        avail_w = max(300, self.width() - 2 * m)
        avail_h = max(300, self.height() - 2 * m)

        ratio = 1.35  # etwas "profiliger" als MainPage
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

        title = QLabel("Benutzerprofil")
        title.setObjectName("SectionTitle")

        avatar = QPushButton("N")
        avatar.setObjectName("Avatar")
        avatar.setFixedSize(44, 44)

        back = QPushButton("Zurück")
        back.setObjectName("Ghost")
        back.clicked.connect(self.back_requested.emit)

        h.addWidget(title, 0, Qt.AlignLeft)
        h.addStretch(1)
        h.addWidget(back, 0)
        h.addWidget(avatar, 0)

        return bar

    # --------------------------
    # Content
    # --------------------------
    def _build_content(self) -> QWidget:
        w = QWidget()
        w.setAttribute(Qt.WA_StyledBackground, True)

        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(14)

        left = self._build_profile_card()
        left.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        right = self._build_password_card()
        right.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        h.addWidget(left, 1)
        h.addWidget(right, 1)
        return w

    def _build_profile_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card.setAttribute(Qt.WA_StyledBackground, True)

        v = QVBoxLayout(card)
        v.setContentsMargins(18, 16, 18, 16)
        v.setSpacing(12)

        title = QLabel("Stammdaten")
        title.setObjectName("PanelTitle")

        hint = QLabel("Diese Angaben werden für Account und ggf. Abrechnung/Kommunikation verwendet.")
        hint.setObjectName("FinePrint")
        hint.setWordWrap(True)

        grid = QWidget()
        gh = QHBoxLayout(grid)
        gh.setContentsMargins(0, 0, 0, 0)
        gh.setSpacing(12)

        # Vorname
        self.first_name = QLineEdit()
        self.first_name.setPlaceholderText("Vorname")
        fn = self._field("Vorname", self.first_name)

        # Nachname
        self.last_name = QLineEdit()
        self.last_name.setPlaceholderText("Nachname")
        ln = self._field("Nachname", self.last_name)

        gh.addWidget(fn, 1)
        gh.addWidget(ln, 1)

        # E-Mail (optional read-only)
        self.email = QLineEdit()
        self.email.setPlaceholderText("E-Mail")
        self.email.setReadOnly(True)  # falls du später vom Login übernimmst
        em = self._field("E-Mail", self.email)

        # Adresse
        self.address = QTextEdit()
        self.address.setPlaceholderText("Straße, Hausnummer\nPLZ Ort\nLand")
        ad = self._field("Adresse", self.address)

        # Save button row
        btn_row = QWidget()
        bh = QHBoxLayout(btn_row)
        bh.setContentsMargins(0, 0, 0, 0)
        bh.setSpacing(10)

        self.save_profile_btn = QPushButton("Speichern")
        self.save_profile_btn.setObjectName("Primary")
        self.save_profile_btn.clicked.connect(self._emit_save)

        bh.addStretch(1)
        bh.addWidget(self.save_profile_btn)

        v.addWidget(title)
        v.addWidget(hint)
        v.addWidget(grid)
        v.addWidget(em)
        v.addWidget(ad)
        v.addStretch(1)
        v.addWidget(btn_row)

        return card

    def _build_password_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card.setAttribute(Qt.WA_StyledBackground, True)

        v = QVBoxLayout(card)
        v.setContentsMargins(18, 16, 18, 16)
        v.setSpacing(12)

        title = QLabel("Passwort ändern")
        title.setObjectName("PanelTitle")

        hint = QLabel("Fürs Prototyping nur UI. Die Validierung/Backend-Logik hängen wir später an.")
        hint.setObjectName("FinePrint")
        hint.setWordWrap(True)

        self.current_pw = QLineEdit()
        self.current_pw.setPlaceholderText("Aktuelles Passwort")
        self.current_pw.setEchoMode(QLineEdit.Password)

        self.new_pw = QLineEdit()
        self.new_pw.setPlaceholderText("Neues Passwort")
        self.new_pw.setEchoMode(QLineEdit.Password)

        self.new_pw2 = QLineEdit()
        self.new_pw2.setPlaceholderText("Neues Passwort bestätigen")
        self.new_pw2.setEchoMode(QLineEdit.Password)

        # Buttons
        btn_row = QWidget()
        bh = QHBoxLayout(btn_row)
        bh.setContentsMargins(0, 0, 0, 0)
        bh.setSpacing(10)

        self.clear_pw_btn = QPushButton("Leeren")
        self.clear_pw_btn.setObjectName("Ghost")
        self.clear_pw_btn.clicked.connect(self._clear_password_fields)

        self.save_pw_btn = QPushButton("Passwort speichern")
        self.save_pw_btn.setObjectName("Primary")
        self.save_pw_btn.clicked.connect(self._emit_save)

        bh.addStretch(1)
        bh.addWidget(self.clear_pw_btn)
        bh.addWidget(self.save_pw_btn)

        v.addWidget(title)
        v.addWidget(hint)
        v.addWidget(self._field("Aktuelles Passwort", self.current_pw))
        v.addWidget(self._field("Neues Passwort", self.new_pw))
        v.addWidget(self._field("Bestätigung", self.new_pw2))
        v.addStretch(1)
        v.addWidget(btn_row)

        return card

    def _field(self, label: str, widget: QWidget) -> QWidget:
        box = QWidget()
        box.setAttribute(Qt.WA_StyledBackground, True)
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)

        l = QLabel(label)
        l.setObjectName("FieldLabel")

        v.addWidget(l)
        v.addWidget(widget)
        return box

    def _clear_password_fields(self) -> None:
        self.current_pw.clear()
        self.new_pw.clear()
        self.new_pw2.clear()

    def _emit_save(self) -> None:
        data = {
            "first_name": self.first_name.text().strip(),
            "last_name": self.last_name.text().strip(),
            "email": self.email.text().strip(),
            "address": self.address.toPlainText().strip(),
            "current_pw": self.current_pw.text(),
            "new_pw": self.new_pw.text(),
            "new_pw2": self.new_pw2.text(),
        }
        self.save_requested.emit(data)
