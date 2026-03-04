# gui/widgets/notes_widget.py
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QLineEdit, QTextEdit,
    QHBoxLayout, QVBoxLayout, QSizePolicy, QListWidget, QListWidgetItem
)


class NotesWidget(QFrame):
    """
    Notes UI (Editor + Recent Notes List), DB-agnostic:
      - emits signals for load/save/delete
      - can filter notes by scope: Global or by symbol
      - supports up to 6 favorite symbols as quick tabs

    Expected note dict fields (recommended):
      id, user_id, asset_id(optional), symbol(optional), title(optional),
      body, tags(optional), created_at(optional), updated_at(optional)
    """

    # UI -> Controller
    notes_refresh_requested = Signal(object)        # scope: None (global) or "AAPL"
    note_save_requested = Signal(dict)             # payload dict
    note_delete_requested = Signal(int)            # note_id

    # Optional: when user changes scope
    scope_changed = Signal(object)                 # None or "AAPL"

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._symbols: list[str] = []
        self._scope: str | None = None            # None = global, else symbol
        self._notes: list[dict] = []
        self._selected_note_id: int | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(10)

        # Header
        header = QWidget()
        hh = QHBoxLayout(header)
        hh.setContentsMargins(0, 0, 0, 0)
        hh.setSpacing(10)

        title = QLabel("Notizen")
        title.setObjectName("PanelTitle")

        self._status = QLabel("")
        self._status.setObjectName("FinePrint")
        self._status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        hh.addWidget(title, 1, Qt.AlignLeft)
        hh.addWidget(self._status, 0, Qt.AlignRight)
        root.addWidget(header)

        # Scope bar (Global + symbol buttons)
        self._scope_bar = QWidget()
        sb = QHBoxLayout(self._scope_bar)
        sb.setContentsMargins(0, 0, 0, 0)
        sb.setSpacing(8)

        self._btn_global = QPushButton("Global")
        self._btn_global.setObjectName("Primary")
        self._btn_global.setCursor(Qt.PointingHandCursor)
        self._btn_global.clicked.connect(lambda: self.set_scope(None, emit=True))
        sb.addWidget(self._btn_global, 0)

        self._sym_btns: dict[str, QPushButton] = {}
        sb.addStretch(1)
        root.addWidget(self._scope_bar)

        # Main row: Editor (left) + list (right)
        main = QWidget()
        mh = QHBoxLayout(main)
        mh.setContentsMargins(0, 0, 0, 0)
        mh.setSpacing(12)

        # ----- Editor panel -----
        editor = QFrame()
        editor.setObjectName("Panel")
        editor.setAttribute(Qt.WA_StyledBackground, True)
        editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        ev = QVBoxLayout(editor)
        ev.setContentsMargins(14, 12, 14, 12)
        ev.setSpacing(8)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Titel (optional)")

        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Tags (optional, z.B. thesis,risk,earnings)")

        self.body_input = QTextEdit()
        self.body_input.setPlaceholderText("Schreibe hier deine Notiz…")
        self.body_input.setMinimumHeight(130)

        # Buttons row
        btn_row = QWidget()
        bh = QHBoxLayout(btn_row)
        bh.setContentsMargins(0, 0, 0, 0)
        bh.setSpacing(10)

        self.clear_btn = QPushButton("Leeren")
        self.clear_btn.setObjectName("Ghost")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.clicked.connect(self.clear_editor)

        self.delete_btn = QPushButton("Löschen")
        self.delete_btn.setObjectName("Ghost")
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._on_delete_clicked)

        self.reload_btn = QPushButton("Neu laden")
        self.reload_btn.setObjectName("Ghost")
        self.reload_btn.setCursor(Qt.PointingHandCursor)
        self.reload_btn.clicked.connect(self._request_refresh)

        self.save_btn = QPushButton("Speichern")
        self.save_btn.setObjectName("Primary")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.clicked.connect(self._on_save_clicked)

        bh.addWidget(self.reload_btn, 0)
        bh.addStretch(1)
        bh.addWidget(self.clear_btn, 0)
        bh.addWidget(self.delete_btn, 0)
        bh.addWidget(self.save_btn, 0)

        ev.addWidget(self._field_label("Titel"))
        ev.addWidget(self.title_input)
        ev.addWidget(self._field_label("Tags"))
        ev.addWidget(self.tags_input)
        ev.addWidget(self._field_label("Notiz"))
        ev.addWidget(self.body_input, 1)
        ev.addWidget(btn_row, 0)

        # ----- List panel -----
        list_panel = QFrame()
        list_panel.setObjectName("Panel")
        list_panel.setAttribute(Qt.WA_StyledBackground, True)
        list_panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        list_panel.setFixedWidth(340)

        lv = QVBoxLayout(list_panel)
        lv.setContentsMargins(14, 12, 14, 12)
        lv.setSpacing(8)

        lt = QLabel("Letzte Notizen")
        lt.setObjectName("PanelTitle")

        lh = QLabel("Klick eine Notiz, um sie zu bearbeiten.")
        lh.setObjectName("FinePrint")
        lh.setWordWrap(True)

        self.list = QListWidget()
        self.list.setObjectName("NotesList")
        self.list.setSelectionMode(QListWidget.SingleSelection)
        self.list.itemClicked.connect(self._on_item_clicked)

        lv.addWidget(lt)
        lv.addWidget(lh)
        lv.addWidget(self.list, 1)

        mh.addWidget(editor, 1)
        mh.addWidget(list_panel, 0)

        root.addWidget(main)

        # initial
        self._render_scope_buttons()
        self._render_notes_list()

    # --------------------------
    # Public API
    # --------------------------
    def set_symbols(self, symbols: list[str]) -> None:
        syms: list[str] = []
        for s in (symbols or []):
            s = (s or "").strip().upper()
            if s and s not in syms:
                syms.append(s)
        self._symbols = syms[:6]
        # if scope was a symbol that disappeared, reset to global
        if self._scope is not None and self._scope not in self._symbols:
            self._scope = None
        self._render_scope_buttons()

    def set_scope(self, scope: str | None, emit: bool = False) -> None:
        # scope: None=global, else symbol
        if scope is not None:
            scope = (scope or "").strip().upper() or None

        self._scope = scope
        self._selected_note_id = None
        self.delete_btn.setEnabled(False)
        self._render_scope_buttons()
        self.clear_editor()

        if emit:
            self.scope_changed.emit(self._scope)
            self._request_refresh()

    def set_status(self, text: str) -> None:
        self._status.setText((text or "").strip())

    def set_notes(self, notes: list[dict] | None) -> None:
        self._notes = [n for n in (notes or []) if isinstance(n, dict)]
        self._render_notes_list()

    def clear_editor(self) -> None:
        self._selected_note_id = None
        self.title_input.clear()
        self.tags_input.clear()
        self.body_input.clear()
        self.delete_btn.setEnabled(False)
        self.list.clearSelection()

    # --------------------------
    # Internals
    # --------------------------
    def _request_refresh(self) -> None:
        # None => global, else symbol
        self.notes_refresh_requested.emit(self._scope)

    def _on_save_clicked(self) -> None:
        body = (self.body_input.toPlainText() or "").strip()
        if not body:
            self.set_status("Notiz ist leer.")
            return

        payload = {
            "id": self._selected_note_id,           # None => insert, else update
            "scope": self._scope,                   # None or symbol
            "symbol": self._scope,                  # convenience
            "title": (self.title_input.text() or "").strip(),
            "tags": (self.tags_input.text() or "").strip(),
            "body": body,
        }
        self.set_status("Speichern…")
        self.note_save_requested.emit(payload)

    def note_save_success(self, status: str = "Gespeichert.") -> None:
        self.set_status(status)

    def note_save_failed(self, msg: str) -> None:
        self.set_status("Fehler beim Speichern.")
        # keep text; controller should show message elsewhere if needed

    def _on_delete_clicked(self) -> None:
        if self._selected_note_id is None:
            return
        self.set_status("Löschen…")
        self.note_delete_requested.emit(int(self._selected_note_id))

    def note_delete_success(self, status: str = "Gelöscht.") -> None:
        self.set_status(status)
        self.clear_editor()

    def _render_scope_buttons(self) -> None:
        layout = self._scope_bar.layout()
        if layout is None:
            return

        # remove old symbol buttons
        for sym, btn in list(self._sym_btns.items()):
            btn.deleteLater()
        self._sym_btns.clear()

        # reset global button style
        self._btn_global.setObjectName("Primary" if self._scope is None else "Ghost")
        self._btn_global.style().unpolish(self._btn_global)
        self._btn_global.style().polish(self._btn_global)

        # insert symbol buttons before stretch (at index 1)
        insert_at = 1
        for sym in self._symbols:
            btn = QPushButton(sym)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setObjectName("Primary" if self._scope == sym else "Ghost")
            btn.clicked.connect(lambda _=False, s=sym: self.set_scope(s, emit=True))
            btn.setMinimumHeight(36)
            self._sym_btns[sym] = btn
            layout.insertWidget(insert_at, btn, 0)
            insert_at += 1

    def _render_notes_list(self) -> None:
        self.list.clear()
        if not self._notes:
            it = QListWidgetItem("— keine Notizen —")
            it.setFlags(Qt.NoItemFlags)
            self.list.addItem(it)
            return

        for n in self._notes:
            nid = n.get("id")
            title = (n.get("title") or "").strip()
            body = (n.get("body") or "").strip()
            sym = (n.get("symbol") or "").strip().upper()
            upd = (n.get("updated_at") or n.get("created_at") or "")

            # list line
            head = title if title else (body[:48] + ("…" if len(body) > 48 else ""))
            prefix = f"[{sym}] " if sym else ""
            text = f"{prefix}{head}"

            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, {"id": nid})
            # tooltip with date + tags
            tags = (n.get("tags") or "").strip()
            tip = "\n".join([x for x in [upd, tags, body] if x])
            item.setToolTip(tip[:1200])
            self.list.addItem(item)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        meta = item.data(Qt.UserRole) or {}
        nid = meta.get("id")
        if nid is None:
            return

        # find note dict
        note = None
        for n in self._notes:
            if n.get("id") == nid:
                note = n
                break
        if not note:
            return

        self._selected_note_id = int(nid)
        self.title_input.setText((note.get("title") or "").strip())
        self.tags_input.setText((note.get("tags") or "").strip())
        self.body_input.setPlainText((note.get("body") or "").strip())
        self.delete_btn.setEnabled(True)
        self.set_status("Bearbeiten…")

    def _field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("FinePrint")
        return lbl