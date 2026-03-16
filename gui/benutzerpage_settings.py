# gui/userpage.py
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QLineEdit,
    QHBoxLayout, QVBoxLayout, QSizePolicy, QMessageBox,
    QScrollArea
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


def _qss_url(path: str) -> str:
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

    /* ---- FIX: Inputs/Buttons sollen nicht "gestaucht" werden ---- */
    QLineEdit {{
        background: rgba(255,255,255,6);
        border: 1px solid rgba(39,48,59,170);
        border-radius: 14px;
        padding: 10px 12px;
        min-height: 40px;
        color: rgba(230,234,240,230);
        font-size: 13px;
        selection-background-color: rgba(109,146,155,70);
    }}

    QLineEdit:focus {{
        border: 1px solid rgba(109,146,155,120);
        background: rgba(255,255,255,8);
    }}

    QLineEdit[readOnly="true"] {{
        background: rgba(255,255,255,4);
        color: rgba(230,234,240,190);
        border: 1px solid rgba(39,48,59,150);
    }}

    QPushButton#Ghost {{
        background: transparent;
        border: 1px solid rgba(39,48,59,170);
        border-radius: 16px;
        padding: 10px 14px;
        min-height: 40px;
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
        min-height: 40px;
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

    /* ScrollArea clean */
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

    /* Favoriten Zeile */
    #FavRow {{
        background: rgba(255,255,255,0);
        border: 1px solid rgba(39,48,59,120);
        border-radius: 16px;
    }}
    #FavSymbol {{
        font-weight: 900;
        color: rgba(230,234,240,235);
        font-size: 14px;
    }}
    #FavName {{
        color: rgba(174,183,194,210);
        font-size: 12px;
    }}
    QPushButton#FavRemove {{
        background: transparent;
        border: 1px solid rgba(39,48,59,170);
        border-radius: 12px;
        padding: 6px 10px;
        min-height: 34px;
        font-weight: 900;
        color: rgba(230,234,240,200);
    }}
    QPushButton#FavRemove:hover {{
        border: 1px solid rgba(109,146,155,90);
        color: rgba(230,234,240,235);
    }}
    """


class UserPage(QWidget):
    back_requested = Signal()

    password_change_requested = Signal(str, str, str)  # current_pw, new_pw, new_pw2

    favorite_add_requested = Signal(str)    # symbol
    favorite_remove_requested = Signal(int) # asset_id
    favorites_refresh_requested = Signal()

    def __init__(
        self,
        background_path: str = "images/Backgroundimage.png",
        parent: QWidget | None = None
    ):
        super().__init__(parent)

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)

        self.setObjectName("Root")
        self._palette = Palette()
        self.setStyleSheet(build_qss(self._palette, background_path))

        self._avatar_btn: QPushButton | None = None

        self._favorites: list[dict] = []
        self._fav_rows: list[QWidget] = []
        self._fav_symbol_labels: list[QLabel] = []
        self._fav_name_labels: list[QLabel] = []
        self._fav_remove_btns: list[QPushButton] = []
        self._fav_text_boxes: list[QWidget] = []

        # ---- Root layout (zentriert) ----
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

        # ---- FIX: Content in ScrollArea, damit nix "gestaucht" wird ----
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self._content = self._build_content()
        self._scroll.setWidget(self._content)

        shell_v.addWidget(self._scroll, 1)

        root.addWidget(self._shell, 0, Qt.AlignCenter)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)

        m = 40
        avail_w = max(900, self.width() - 2 * m)   # FIX: Mindestbreite, sonst wirkt alles "gequetscht"
        avail_h = max(600, self.height() - 2 * m)  # FIX: Mindesthöhe

        # etwas näher an deinem MainPage-Look
        ratio = 1.52  # width/height
        w = min(avail_w, int(avail_h * ratio))
        h = min(avail_h, int(w / ratio))
        self._shell.setFixedSize(w, h)

        # nach Resize Text neu eliden
        self._render_favorites()

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

    # --------------------------
    # Favoriten API
    # --------------------------
    def set_favorites(self, items: list[dict] | None) -> None:
        self._favorites = []
        if items:
            for it in items[:6]:
                if not isinstance(it, dict):
                    continue
                aid = it.get("asset_id", None)
                sym = (it.get("symbol") or "").strip()
                name = (it.get("name") or "").strip()
                if aid is None or not sym:
                    continue
                if not name:
                    name = sym
                self._favorites.append({"asset_id": int(aid), "symbol": sym, "name": name})
        self._render_favorites()

    def clear_favorites(self) -> None:
        self._favorites = []
        self._render_favorites()

    # --------------------------
    # Public setter helpers
    # --------------------------
    def set_profile(self, first_name: str, last_name: str, email: str) -> None:
        self.first_name.setText((first_name or "").strip())
        self.last_name.setText((last_name or "").strip())
        self.email.setText((email or "").strip())

    def set_address(self, street: str, postal_code: str, city: str, country: str) -> None:
        self.street.setText((street or "").strip())
        self.postal_code.setText((postal_code or "").strip())
        self.city.setText((city or "").strip())
        self.country.setText((country or "").strip())

    def load_user(self, user: dict | None) -> None:
        if not user:
            self.set_profile("", "", "")
            self.set_address("", "", "", "")
            self.set_avatar_letter("N")
            return

        self.set_profile(
            user.get("first_name", "") or "",
            user.get("last_name", "") or "",
            user.get("email", "") or "",
        )
        self.set_address(
            user.get("street", "") or "",
            user.get("postal_code", "") or "",
            user.get("city", "") or "",
            user.get("country", "") or "",
        )

        self.set_avatar_from_user(user)
        self.favorites_refresh_requested.emit()

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

        self._avatar_btn = QPushButton("N")
        self._avatar_btn.setObjectName("Avatar")
        self._avatar_btn.setFixedSize(44, 44)

        back = QPushButton("Zurück")
        back.setObjectName("Ghost")
        back.clicked.connect(self.back_requested.emit)

        h.addWidget(title, 0, Qt.AlignLeft)
        h.addStretch(1)
        h.addWidget(back, 0)
        h.addWidget(self._avatar_btn, 0)

        return bar

    # --------------------------
    # Content
    # --------------------------
    def _build_content(self) -> QWidget:
        w = QWidget()
        w.setAttribute(Qt.WA_StyledBackground, True)

        vroot = QVBoxLayout(w)
        vroot.setContentsMargins(0, 0, 0, 0)
        vroot.setSpacing(14)

        # row 1: Profile + Password
        row = QWidget()
        row.setAttribute(Qt.WA_StyledBackground, True)
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(14)

        left = self._build_profile_card()
        left.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        right = self._build_password_card()
        right.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        h.addWidget(left, 1, Qt.AlignTop)
        h.addWidget(right, 1, Qt.AlignTop)

        # row 2: Favorites
        fav = self._build_favorites_card()
        fav.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        vroot.addWidget(row, 0)
        vroot.addWidget(fav, 0)
        vroot.addStretch(1)  # damit oben "luftig" bleibt und nicht gedrückt wirkt

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

        self.first_name = QLineEdit()
        self.first_name.setPlaceholderText("Max")
        self.first_name.setReadOnly(True)
        fn = self._field("Vorname", self.first_name)

        self.last_name = QLineEdit()
        self.last_name.setPlaceholderText("Gewinnhoff")
        self.last_name.setReadOnly(True)
        ln = self._field("Nachname", self.last_name)

        gh.addWidget(fn, 1)
        gh.addWidget(ln, 1)

        self.email = QLineEdit()
        self.email.setPlaceholderText("E-Mail")
        self.email.setReadOnly(True)
        em = self._field("E-Mail", self.email)

        self.street = QLineEdit()
        self.street.setPlaceholderText("Straße, Hausnummer")
        self.street.setReadOnly(True)

        self.postal_code = QLineEdit()
        self.postal_code.setPlaceholderText("PLZ")
        self.postal_code.setReadOnly(True)

        self.city = QLineEdit()
        self.city.setPlaceholderText("Ort")
        self.city.setReadOnly(True)

        self.country = QLineEdit()
        self.country.setPlaceholderText("Land")
        self.country.setReadOnly(True)

        addr_row1 = QWidget()
        ar1 = QHBoxLayout(addr_row1)
        ar1.setContentsMargins(0, 0, 0, 0)
        ar1.setSpacing(12)
        ar1.addWidget(self._field("Straße", self.street), 2)
        ar1.addWidget(self._field("PLZ", self.postal_code), 1)

        addr_row2 = QWidget()
        ar2 = QHBoxLayout(addr_row2)
        ar2.setContentsMargins(0, 0, 0, 0)
        ar2.setSpacing(12)
        ar2.addWidget(self._field("Ort", self.city), 1)
        ar2.addWidget(self._field("Land", self.country), 1)

        # read-only: Speichern-Button weg (spart Platz & wirkt weniger "gequetscht")
        v.addWidget(title)
        v.addWidget(hint)
        v.addWidget(grid)
        v.addWidget(em)
        v.addWidget(addr_row1)
        v.addWidget(addr_row2)

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

        hint = QLabel("Gib dein aktuelles Passwort ein und vergib ein neues.")
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

        btn_row = QWidget()
        bh = QHBoxLayout(btn_row)
        bh.setContentsMargins(0,  0, 0, 0)
        bh.setSpacing(10)

        self.clear_pw_btn = QPushButton("Leeren")
        self.clear_pw_btn.setObjectName("Ghost")
        self.clear_pw_btn.clicked.connect(self._clear_password_fields)

        self.save_pw_btn = QPushButton("Passwort speichern")
        self.save_pw_btn.setObjectName("Primary")
        self.save_pw_btn.clicked.connect(self._on_password_save_clicked)

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

    # --------------------------
    # Favoriten Card
    # --------------------------
    def _build_favorites_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card.setAttribute(Qt.WA_StyledBackground, True)

        v = QVBoxLayout(card)
        v.setContentsMargins(18, 16, 18, 16)
        v.setSpacing(12)

        title = QLabel("Favoriten (max. 6)")
        title.setObjectName("PanelTitle")

        hint = QLabel("Füge bis zu 6 Favoriten hinzu. Keine Reihenfolge – nur Auswahl.")
        hint.setObjectName("FinePrint")
        hint.setWordWrap(True)

        add_row = QWidget()
        ah = QHBoxLayout(add_row)
        ah.setContentsMargins(0, 0, 0, 0)
        ah.setSpacing(10)

        self.fav_input = QLineEdit()
        self.fav_input.setPlaceholderText("Symbol hinzufügen (z.B. AAPL, MSFT, SAP.DE)")
        self.fav_input.returnPressed.connect(self._on_fav_add_clicked)

        self.fav_add_btn = QPushButton("Hinzufügen")
        self.fav_add_btn.setObjectName("Primary")
        self.fav_add_btn.clicked.connect(self._on_fav_add_clicked)

        self.fav_reload_btn = QPushButton("Neu laden")
        self.fav_reload_btn.setObjectName("Ghost")
        self.fav_reload_btn.clicked.connect(self.favorites_refresh_requested.emit)

        ah.addWidget(self.fav_input, 1)
        ah.addWidget(self.fav_reload_btn, 0)
        ah.addWidget(self.fav_add_btn, 0)

        self._fav_rows_container = QWidget()
        self._fav_rows_container.setAttribute(Qt.WA_StyledBackground, True)
        rows_v = QVBoxLayout(self._fav_rows_container)
        rows_v.setContentsMargins(0, 0, 0, 0)
        rows_v.setSpacing(10)

        for _ in range(6):
            row = QWidget()
            row.setObjectName("FavRow")
            row.setAttribute(Qt.WA_StyledBackground, True)
            row.setMinimumHeight(62)
            row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            row_h = QHBoxLayout(row)
            row_h.setContentsMargins(14, 12, 14, 12)
            row_h.setSpacing(12)

            text_box = QWidget()
            text_box.setAttribute(Qt.WA_StyledBackground, True)
            text_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            tv = QVBoxLayout(text_box)
            tv.setContentsMargins(0, 0, 0, 0)
            tv.setSpacing(2)

            sym = QLabel("—")
            sym.setObjectName("FavSymbol")
            sym.setWordWrap(False)
            sym.setMinimumHeight(20)
            sym.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            name = QLabel("")
            name.setObjectName("FavName")
            name.setWordWrap(False)  # elide
            name.setMinimumHeight(18)
            name.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            tv.addWidget(sym)
            tv.addWidget(name)

            rm = QPushButton("Entfernen")
            rm.setObjectName("FavRemove")
            rm.setEnabled(False)
            rm.clicked.connect(self._on_fav_remove_clicked)

            row_h.addWidget(text_box, 1)
            row_h.addWidget(rm, 0)

            rows_v.addWidget(row)

            self._fav_rows.append(row)
            self._fav_text_boxes.append(text_box)
            self._fav_symbol_labels.append(sym)
            self._fav_name_labels.append(name)
            self._fav_remove_btns.append(rm)

        v.addWidget(title)
        v.addWidget(hint)
        v.addWidget(add_row)
        v.addWidget(self._fav_rows_container)

        self._render_favorites()
        return card

    # --------------------------
    # Favorites rendering (elide + tooltip)
    # --------------------------
    def _set_elided(self, lbl: QLabel, full_text: str, max_px: int) -> None:
        full_text = (full_text or "").strip()
        lbl.setToolTip(full_text if full_text else "")
        if not full_text:
            lbl.setText("")
            return
        fm = QFontMetrics(lbl.font())
        lbl.setText(fm.elidedText(full_text, Qt.ElideRight, max(10, int(max_px))))

    def _render_favorites(self) -> None:
        for i in range(6):
            sym_lbl = self._fav_symbol_labels[i]
            name_lbl = self._fav_name_labels[i]
            rm = self._fav_remove_btns[i]
            text_box = self._fav_text_boxes[i]

            max_px = max(140, text_box.width() - 8)

            if i < len(self._favorites):
                it = self._favorites[i]
                sym_full = (it.get("symbol") or "—").strip() or "—"
                name_full = (it.get("name") or "").strip() or sym_full

                self._set_elided(sym_lbl, sym_full, max_px)
                self._set_elided(name_lbl, name_full, max_px)

                rm.setEnabled(True)
                rm.setProperty("asset_id", int(it.get("asset_id")))
            else:
                sym_lbl.setToolTip("")
                name_lbl.setToolTip("")
                sym_lbl.setText("—")
                name_lbl.setText("")
                rm.setEnabled(False)
                rm.setProperty("asset_id", None)

    def _on_fav_add_clicked(self) -> None:
        symbol = (self.fav_input.text() if hasattr(self, "fav_input") else "").strip()
        if not symbol:
            QMessageBox.warning(self, "Favoriten", "Bitte ein Symbol eingeben (z.B. AAPL).")
            return

        if len(self._favorites) >= 6:
            QMessageBox.warning(self, "Favoriten", "Du hast bereits 6 Favoriten. Bitte zuerst einen entfernen.")
            return

        self.fav_input.clear()
        self.favorite_add_requested.emit(symbol)

    def _on_fav_remove_clicked(self) -> None:
        btn = self.sender()
        if not isinstance(btn, QPushButton):
            return
        aid = btn.property("asset_id")
        if aid is None:
            return
        try:
            aid_int = int(aid)
        except Exception:
            return

        self.favorite_remove_requested.emit(aid_int)

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

    def _on_password_save_clicked(self) -> None:
        current_pw = self.current_pw.text()
        new_pw = self.new_pw.text()
        new_pw2 = self.new_pw2.text()

        if not current_pw or not new_pw or not new_pw2:
            QMessageBox.warning(self, "Fehlende Angaben", "Bitte alle Passwortfelder ausfüllen.")
            return

        if new_pw != new_pw2:
            QMessageBox.warning(self, "Passwort", "Die neuen Passwörter stimmen nicht überein.")
            return

        if len(new_pw) < 8:
            QMessageBox.warning(self, "Passwort", "Das neue Passwort muss mindestens 8 Zeichen lang sein.")
            return

        self.save_pw_btn.setEnabled(False)
        self.save_pw_btn.setText("Speichern...")

        self.password_change_requested.emit(current_pw, new_pw, new_pw2)

    def password_change_ui_done(self) -> None:
        self.save_pw_btn.setEnabled(True)
        self.save_pw_btn.setText("Passwort speichern")

    def password_change_success(self) -> None:
        self.password_change_ui_done()
        self._clear_password_fields()