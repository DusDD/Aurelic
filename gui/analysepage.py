# gui/analysepage.py
from __future__ import annotations

import os

from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout, QSizePolicy
)

from gui.mainpage import Palette, build_qss
from gui.widgets.segmentedtabs import SegmentedTabs
from gui.widgets.worldbank_feed import WorldBankFeedWidget
from gui.widgets.quant_analysis import QuantAnalysisWidget


class AnalysePage(QWidget):
    tab_changed = Signal(str)    # "brokerage" | "analyse"
    avatar_clicked = Signal()
    calendar_clicked = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setObjectName("Root")
        self._palette = Palette()
        self.setStyleSheet(build_qss(self._palette))
        self.setAttribute(Qt.WA_StyledBackground, True)

        self._resize_debounce = QTimer(self)
        self._resize_debounce.setSingleShot(True)
        self._resize_debounce.setInterval(60)
        self._resize_debounce.timeout.connect(self._on_resized_debounced)
        self._last_shell_size: tuple[int, int] | None = None

        self._avatar_letter: str = "N"
        self._avatar_btn: QPushButton | None = None

        self._quant: QuantAnalysisWidget | None = None

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

        self._topbar = self._build_topbar()
        self._middle = self._build_middle_area()

        shell_v.addWidget(self._topbar, 0)
        shell_v.addWidget(self._middle, 1)

        root.addWidget(self._shell, 0, Qt.AlignCenter)

        self._seg_tabs.set_active("analyse", animate=False, emit=False)
        QTimer.singleShot(0, self._apply_initial_shell_size)

    # --------------------------
    # Public API: Avatar
    # --------------------------
    def set_avatar_letter(self, letter: str) -> None:
        letter = (letter or "").strip() or "N"
        self._avatar_letter = letter[:1].upper()
        if self._avatar_btn is not None:
            self._avatar_btn.setText(self._avatar_letter)

    def set_avatar_from_user(self, user: dict | None) -> None:
        if not user:
            self.set_avatar_letter("N")
            return
        first = (user.get("first_name") or "").strip()
        if first:
            self.set_avatar_letter(first[0])
            return
        email = (user.get("email") or "").strip()
        if email:
            self.set_avatar_letter(email[0])
            return
        self.set_avatar_letter("N")

    # --------------------------
    # Public API: Favorites -> Quant
    # --------------------------
    def set_favorite_symbols(self, symbols: list[str] | None) -> None:
        syms = [(s or "").strip().upper() for s in (symbols or []) if (s or "").strip()]
        if self._quant is not None:
            self._quant.set_symbols(syms)

    # --------------------------
    # Shell sizing
    # --------------------------
    def _apply_initial_shell_size(self) -> None:
        margin = 40
        avail_w = max(300, self.width() - 2 * margin)
        avail_h = max(300, self.height() - 2 * margin)

        ratio = 1.568
        w = min(avail_w, int(avail_h * ratio))
        h = min(avail_h, int(w / ratio))

        new_size = (w, h)
        if new_size != self._last_shell_size:
            self._shell.setFixedSize(w, h)
            self._last_shell_size = new_size

    def _on_resized_debounced(self) -> None:
        pass

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)

        margin = 40
        avail_w = max(300, self.width() - 2 * margin)
        avail_h = max(300, self.height() - 2 * margin)

        ratio = 1.568
        w = min(avail_w, int(avail_h * ratio))
        h = min(avail_h, int(w / ratio))

        new_size = (w, h)
        if new_size != self._last_shell_size:
            self._shell.setFixedSize(w, h)
            self._last_shell_size = new_size

        self._resize_debounce.start()

    # --------------------------
    # Topbar
    # --------------------------
    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setAttribute(Qt.WA_StyledBackground, True)

        h = QHBoxLayout(bar)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(12)

        self._seg_tabs = SegmentedTabs()
        self._seg_tabs.setObjectName("SegmentedTabs")
        self._seg_tabs.changed.connect(self._set_active_tab)

        cal_btn = QPushButton()
        cal_btn.setObjectName("CalendarBtn")
        cal_btn.setFixedSize(44, 44)
        cal_btn.setCursor(Qt.PointingHandCursor)
        cal_btn.clicked.connect(self.calendar_clicked.emit)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.abspath(os.path.join(base_dir, "..", "images", "icons8-kalender-30.png"))
        cal_btn.setIcon(QIcon(icon_path))
        cal_btn.setIconSize(QSize(24, 24))

        self._avatar_btn = QPushButton(self._avatar_letter)
        self._avatar_btn.setObjectName("Avatar")
        self._avatar_btn.setFixedSize(44, 44)
        self._avatar_btn.setCursor(Qt.PointingHandCursor)
        self._avatar_btn.clicked.connect(self.avatar_clicked.emit)

        h.addWidget(self._seg_tabs, 0, Qt.AlignLeft)
        h.addStretch(1)
        h.addWidget(cal_btn, 0, Qt.AlignRight)
        h.addWidget(self._avatar_btn, 0, Qt.AlignRight)
        return bar

    def _set_active_tab(self, which: str) -> None:
        which = "analyse" if which == "analyse" else "brokerage"
        self._seg_tabs.set_active(which, animate=True, emit=False)
        self.tab_changed.emit(which)

    # --------------------------
    # Middle
    # --------------------------
    def _build_middle_area(self) -> QWidget:
        w = QWidget()
        w.setAttribute(Qt.WA_StyledBackground, True)

        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(14)

        left = WorldBankFeedWidget()
        left.setMinimumWidth(320)
        left.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        center = QuantAnalysisWidget()
        center.setMinimumWidth(0)
        center.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        center.error.connect(lambda msg: print("[QuantAnalysis]", msg))
        self._quant = center

        right = QWidget()
        right.setAttribute(Qt.WA_StyledBackground, True)

        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(14)

        right_top = self._panel("Portfolio\nRisiko", "Heatmap / Risiko\n(Placeholder)", 320)
        right_bottom = self._panel("Watchlist\nInsights", "Alerts / Insights\n(Placeholder)", 320)
        right_top.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        right_bottom.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        rv.addWidget(right_top, 1)
        rv.addWidget(right_bottom, 1)

        h.addWidget(left, 0)
        h.addWidget(center, 1)
        h.addWidget(right, 0)
        return w

    # --------------------------
    # Generic panel helper
    # --------------------------
    def _panel(self, title: str, placeholder: str, min_w: int = 260) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        panel.setAttribute(Qt.WA_StyledBackground, True)
        panel.setMinimumWidth(min_w)
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        v = QVBoxLayout(panel)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(10)

        if title.strip():
            t = QLabel(title)
            t.setObjectName("PanelTitle")
            t.setWordWrap(True)
            v.addWidget(t, 0, Qt.AlignLeft)

        body = QLabel(placeholder)
        body.setObjectName("Placeholder")
        body.setWordWrap(True)
        body.setAlignment(Qt.AlignCenter)

        v.addStretch(1)
        v.addWidget(body, 0, Qt.AlignCenter)
        v.addStretch(1)
        return panel