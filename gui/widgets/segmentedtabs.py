# gui/widgets/segmentedtabs.py
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QRect, QEasingCurve, QTimer
from PySide6.QtWidgets import QWidget, QPushButton, QFrame, QHBoxLayout


class SegmentedTabs(QWidget):
    """
    iOS-like segmented control with sliding indicator.
    Emits `changed("analyse"|"brokerage")`.
    """
    changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("SegmentedTabs")
        self.setAttribute(Qt.WA_StyledBackground, True)

        self._active = "brokerage"

        # Indicator (the sliding pill)
        self._indicator = QFrame(self)
        self._indicator.setObjectName("SegmentedIndicator")
        self._indicator.setAttribute(Qt.WA_StyledBackground, True)

        # IMPORTANT FIX: indicator must NOT steal clicks (otherwise sometimes 2 clicks)
        self._indicator.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        # Keep it behind the buttons (still visible, because it's drawn as background)
        self._indicator.lower()

        # Buttons
        self._btn_analyse = QPushButton("Analyse", self)
        self._btn_brokerage = QPushButton("Brokerage", self)
        for b in (self._btn_analyse, self._btn_brokerage):
            b.setObjectName("SegmentedButton")
            b.setCursor(Qt.PointingHandCursor)
            b.setCheckable(False)
            b.setFlat(True)

        self._btn_analyse.clicked.connect(lambda: self.set_active("analyse", animate=True, emit=True))
        self._btn_brokerage.clicked.connect(lambda: self.set_active("brokerage", animate=True, emit=True))

        # Layout
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)  # padding inside outer capsule
        lay.setSpacing(6)
        lay.addWidget(self._btn_analyse)
        lay.addWidget(self._btn_brokerage)

        # Animation
        self._anim = QPropertyAnimation(self._indicator, b"geometry", self)
        self._anim.setDuration(240)
        self._anim.setEasingCurve(QEasingCurve.InOutCubic)

        # Ensure indicator is positioned after first layout pass
        QTimer.singleShot(0, lambda: self.set_active(self._active, animate=False, emit=False))

    def set_active(self, which: str, animate: bool = True, emit: bool = False) -> None:
        which = "analyse" if which == "analyse" else "brokerage"

        # FIX: don't early-return when same tab is set (keeps indicator in sync)
        # Only skip if we're already active AND no animation required.
        if which == self._active and not animate:
            return

        self._active = which
        self._apply_text_state()

        target = self._target_rect(which)

        if animate:
            self._anim.stop()
            self._anim.setStartValue(self._indicator.geometry())
            self._anim.setEndValue(target)
            self._anim.start()
        else:
            self._indicator.setGeometry(target)

        if emit:
            self.changed.emit(which)

    def _apply_text_state(self) -> None:
        # Toggle dynamic properties -> QSS can color active/inactive text.
        self._btn_analyse.setProperty("active", self._active == "analyse")
        self._btn_brokerage.setProperty("active", self._active == "brokerage")

        for b in (self._btn_analyse, self._btn_brokerage):
            b.style().unpolish(b)
            b.style().polish(b)
            b.update()

    def _target_rect(self, which: str) -> QRect:
        btn = self._btn_analyse if which == "analyse" else self._btn_brokerage
        g = btn.geometry()

        # Slight expansion for a nicer pill look
        pad_x = 4
        pad_y = 2
        return QRect(g.x() - pad_x, g.y() - pad_y, g.width() + 2 * pad_x, g.height() + 2 * pad_y)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        # Keep indicator aligned on resize
        self._indicator.setGeometry(self._target_rect(self._active))
