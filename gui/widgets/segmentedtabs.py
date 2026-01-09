# gui/widgets/segmentedtabs.py
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QRect, QTimer
from PySide6.QtGui import QPainterPath, QRegion
from PySide6.QtWidgets import QPushButton, QHBoxLayout, QFrame


class SegmentedTabs(QFrame):
    """
    2-Segment Tabs: "Analyse" und "Brokerage"
    - pill container + pill indicator
    - indicator animiert im Hintergrund (unter Buttons)
    - echte Round-Masks (Container + Indicator), damit garantiert rund
    - Single click always updates indicator (no double-click needed)
    """
    changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("SegmentedTabs")
        self.setAttribute(Qt.WA_StyledBackground, True)

        # Wichtig: QFrame soll NICHT selbst einen eckigen Frame zeichnen
        self.setFrameShape(QFrame.NoFrame)
        self.setLineWidth(0)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Indicator (hinter Buttons)
        self._indicator = QFrame(self)
        self._indicator.setObjectName("SegmentedIndicator")
        self._indicator.setAttribute(Qt.WA_StyledBackground, True)
        self._indicator.setFrameShape(QFrame.NoFrame)
        self._indicator.setLineWidth(0)

        # Buttons
        self._btn_analyse = self._make_btn("Analyse", "analyse")
        self._btn_brokerage = self._make_btn("Brokerage", "brokerage")

        self._layout.addWidget(self._btn_analyse)
        self._layout.addWidget(self._btn_brokerage)

        self._active = "brokerage"

        self._anim = QPropertyAnimation(self._indicator, b"geometry", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

        # Z-Order fix
        self._indicator.lower()
        self._btn_analyse.raise_()
        self._btn_brokerage.raise_()

        # Einheitliche Höhe (passt zu deinem QSS Padding)
        self.setFixedHeight(44)

        # Init nach Layout
        QTimer.singleShot(0, self._post_init)

    def _post_init(self) -> None:
        self.set_active(self._active, animate=False, emit=False)
        self._apply_container_mask()
        self._apply_indicator_mask()

    def _make_btn(self, text: str, key: str) -> QPushButton:
        b = QPushButton(text, self)
        b.setObjectName("SegmentedButton")
        b.setCursor(Qt.PointingHandCursor)
        b.setFocusPolicy(Qt.NoFocus)
        b.setProperty("active", "false")

        # Wichtig: immer direkt set_active -> kein "2x klicken"
        b.clicked.connect(lambda _=False, k=key: self.set_active(k, animate=True, emit=True))
        return b

    def active(self) -> str:
        return self._active

    def set_active(self, which: str, animate: bool = True, emit: bool = True) -> None:
        which = "analyse" if which == "analyse" else "brokerage"

        self._active = which
        self._sync_button_styles()
        self._move_indicator(animate=animate)

        if emit:
            self.changed.emit(which)

    def _sync_button_styles(self) -> None:
        self._btn_analyse.setProperty("active", "true" if self._active == "analyse" else "false")
        self._btn_brokerage.setProperty("active", "true" if self._active == "brokerage" else "false")

        # QSS refresh
        for b in (self._btn_analyse, self._btn_brokerage):
            b.style().unpolish(b)
            b.style().polish(b)

    def _target_rect_for(self, which: str) -> QRect:
        btn = self._btn_analyse if which == "analyse" else self._btn_brokerage
        r = btn.geometry()

        # Inset: muss zu #SegmentedTabs padding passen (siehe QSS Fix unten)
        pad = 2
        return QRect(
            r.x() + pad,
            r.y() + pad,
            max(0, r.width() - 2 * pad),
            max(0, r.height() - 2 * pad),
        )

    def _move_indicator(self, animate: bool) -> None:
        target = self._target_rect_for(self._active)

        # Indicator hinter Buttons
        self._indicator.lower()

        self._anim.stop()

        if not animate:
            self._indicator.setGeometry(target)
            self._apply_indicator_mask()
            return

        # Während Animation Maske nachziehen (sonst wirkt's eckig / "laggy")
        def _on_value_changed(_):
            self._apply_indicator_mask()

        try:
            self._anim.valueChanged.disconnect()
        except Exception:
            pass
        self._anim.valueChanged.connect(_on_value_changed)

        self._anim.setStartValue(self._indicator.geometry())
        self._anim.setEndValue(target)
        self._anim.finished.connect(self._apply_indicator_mask)
        self._anim.start()

    # --------------------------
    # Hard rounded masks (Container + Indicator)
    # --------------------------
    def _rounded_region(self, rect: QRect, radius: int) -> QRegion:
        path = QPainterPath()
        path.addRoundedRect(rect, float(radius), float(radius))
        poly = path.toFillPolygon().toPolygon()
        return QRegion(poly)

    def _apply_container_mask(self) -> None:
        r = self.rect()
        if r.width() <= 0 or r.height() <= 0:
            return
        radius = r.height() // 2
        self.setMask(self._rounded_region(r, radius))

    def _apply_indicator_mask(self) -> None:
        r = self._indicator.rect()
        if r.width() <= 0 or r.height() <= 0:
            return
        radius = r.height() // 2
        self._indicator.setMask(self._rounded_region(r, radius))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_container_mask()
        # Beim Resize immer hart positionieren, sonst wirkt der Indicator "versetzt"
        self._move_indicator(animate=False)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self._post_init)
