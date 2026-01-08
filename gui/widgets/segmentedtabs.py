# gui/widgets/segmentedtabs.py
from __future__ import annotations

from PySide6.QtCore import (
    Qt, Signal, QPropertyAnimation, QRect, QEasingCurve, QTimer, QEvent
)
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

        # Indicator (sliding pill)
        self._indicator = QFrame(self)
        self._indicator.setObjectName("SegmentedIndicator")
        self._indicator.setAttribute(Qt.WA_StyledBackground, True)

        # IMPORTANT: indicator must NOT steal clicks
        self._indicator.setAttribute(Qt.WA_TransparentForMouseEvents, True)
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
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.InOutCubic)

        # Reposition management (prevents "needs 2 clicks" due to late geometry)
        self._queued_reposition = False

        # Ensure indicator is positioned after first layout pass
        QTimer.singleShot(0, self._reposition_indicator)

    # --------------------------
    # Public API
    # --------------------------
    def set_active(self, which: str, animate: bool = True, emit: bool = False) -> None:
        which = "analyse" if which == "analyse" else "brokerage"

        self._active = which
        self._apply_text_state()

        # Geometry may not be ready yet; ensure reposition happens robustly.
        self._reposition_indicator(animate=animate)

        if emit:
            self.changed.emit(which)

    # --------------------------
    # Internal helpers
    # --------------------------
    def _apply_text_state(self) -> None:
        self._btn_analyse.setProperty("active", self._active == "analyse")
        self._btn_brokerage.setProperty("active", self._active == "brokerage")

        for b in (self._btn_analyse, self._btn_brokerage):
            b.style().unpolish(b)
            b.style().polish(b)
            b.update()

    def _target_rect(self, which: str) -> QRect:
        btn = self._btn_analyse if which == "analyse" else self._btn_brokerage
        g = btn.geometry()

        # When widget is not yet laid out, geometry can be empty.
        if g.width() <= 0 or g.height() <= 0:
            return QRect(0, 0, 0, 0)

        pad_x = 4
        pad_y = 2
        return QRect(g.x() - pad_x, g.y() - pad_y, g.width() + 2 * pad_x, g.height() + 2 * pad_y)

    def _reposition_indicator(self, animate: bool = False) -> None:
        # If geometry isn't ready yet, queue a retry.
        target = self._target_rect(self._active)
        if target.width() <= 0 or target.height() <= 0:
            self._queue_reposition()
            return

        if animate and self._indicator.geometry().isValid() and self._indicator.geometry().width() > 0:
            self._anim.stop()
            self._anim.setStartValue(self._indicator.geometry())
            self._anim.setEndValue(target)
            self._anim.start()
        else:
            self._anim.stop()
            self._indicator.setGeometry(target)

    def _queue_reposition(self) -> None:
        if self._queued_reposition:
            return
        self._queued_reposition = True

        def _do():
            self._queued_reposition = False
            self._reposition_indicator(animate=False)

        QTimer.singleShot(0, _do)

    # --------------------------
    # Qt events (ensure correct first render)
    # --------------------------
    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._reposition_indicator(animate=False)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._reposition_indicator(animate=False)

    def event(self, e) -> bool:
        # Catch layout/style changes that can affect geometry
        if e.type() in (QEvent.LayoutRequest, QEvent.Polish, QEvent.StyleChange):
            self._queue_reposition()
        return super().event(e)
