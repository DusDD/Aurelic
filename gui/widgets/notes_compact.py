# gui/widgets/notes_compact.py
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QWidget, QLabel, QPushButton, QLineEdit,
    QHBoxLayout, QVBoxLayout, QSizePolicy
)


class NotesCompactWidget(QFrame):
    """
    Super-kompakter Notes-Bereich:
      - 1 Zeile Notiz (kurz)
      - Speichern / Neu laden
      - optional Scope-Info (Global oder Symbol)
    DB-agnostic via signals.

    Signals:
      - save_requested(scope, text)
      - refresh_requested(scope)
    """
    save_requested = Signal(object, str)     # scope: None or "AAPL", text
    refresh_requested = Signal(object)       # scope: None or "AAPL"

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._scope: str | None = None  # None = global, else symbol

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 10, 16, 10)
        root.setSpacing(6)

        # title row
        top = QWidget()
        th = QHBoxLayout(top)
        th.setContentsMargins(0, 0, 0, 0)
        th.setSpacing(10)

        self._title = QLabel("Notiz (Global)")
        self._title.setObjectName("PanelTitle")

        self._status = QLabel("")
        self._status.setObjectName("FinePrint")
        self._status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        th.addWidget(self._title, 1)
        th.addWidget(self._status, 0)
        root.addWidget(top)

        # input row
        row = QWidget()
        rh = QHBoxLayout(row)
        rh.setContentsMargins(0, 0, 0, 0)
        rh.setSpacing(10)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Kurze Notiz speichern… (Enter = Speichern)")
        self.input.returnPressed.connect(self._on_save)

        self.reload_btn = QPushButton("Neu laden")
        self.reload_btn.setObjectName("Ghost")
        self.reload_btn.setCursor(Qt.PointingHandCursor)
        self.reload_btn.clicked.connect(lambda: self.refresh_requested.emit(self._scope))

        self.save_btn = QPushButton("Speichern")
        self.save_btn.setObjectName("Primary")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.clicked.connect(self._on_save)

        rh.addWidget(self.input, 1)
        rh.addWidget(self.reload_btn, 0)
        rh.addWidget(self.save_btn, 0)

        root.addWidget(row)

    def set_scope(self, scope: str | None) -> None:
        scope = (scope or "").strip().upper() if scope else None
        self._scope = scope
        self._title.setText(f"Notiz ({scope})" if scope else "Notiz (Global)")

    def set_status(self, text: str) -> None:
        self._status.setText((text or "").strip())

    def clear(self) -> None:
        self.input.clear()

    def _on_save(self) -> None:
        txt = (self.input.text() or "").strip()
        if not txt:
            self.set_status("Leer.")
            return
        self.set_status("Speichern…")
        self.save_requested.emit(self._scope, txt)