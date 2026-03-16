from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import Qt, QRect, QRectF, QPoint, QEvent, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QBrush
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QSizePolicy, QGraphicsDropShadowEffect
)


@dataclass
class TourStep:
    target: QWidget | None = None
    title: str = ""
    text: str = ""
    placement: str = "right"   # right | left | top | bottom | center


class TourBubble(QFrame):
    next_clicked = Signal()
    skip_clicked = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setObjectName("TourBubble")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setWindowFlags(Qt.Widget | Qt.FramelessWindowHint)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 140))
        self.setGraphicsEffect(shadow)

        self._title = QLabel("")
        self._title.setObjectName("TourTitle")
        self._title.setWordWrap(True)

        self._text = QLabel("")
        self._text.setObjectName("TourText")
        self._text.setWordWrap(True)

        self._progress = QLabel("1 / 1")
        self._progress.setObjectName("TourProgress")

        self._skip = QPushButton("Überspringen")
        self._skip.setObjectName("TourGhost")
        self._skip.setCursor(Qt.PointingHandCursor)
        self._skip.clicked.connect(self.skip_clicked.emit)

        self._next = QPushButton("Weiter")
        self._next.setObjectName("TourPrimary")
        self._next.setCursor(Qt.PointingHandCursor)
        self._next.clicked.connect(self.next_clicked.emit)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 14)
        root.setSpacing(12)

        root.addWidget(self._title, 0)
        root.addWidget(self._text, 0)

        bottom = QWidget()
        bh = QHBoxLayout(bottom)
        bh.setContentsMargins(0, 0, 0, 0)
        bh.setSpacing(8)

        bh.addWidget(self._progress, 0, Qt.AlignLeft)
        bh.addStretch(1)
        bh.addWidget(self._skip, 0, Qt.AlignRight)
        bh.addWidget(self._next, 0, Qt.AlignRight)

        root.addWidget(bottom, 0)

        self.setStyleSheet("""
            QFrame#TourBubble {
                background: rgba(15,19,24,245);
                border: 1px solid rgba(255,255,255,24);
                border-radius: 18px;
            }

            QLabel#TourTitle {
                color: rgba(230,234,240,240);
                font-size: 15px;
                font-weight: 950;
            }

            QLabel#TourText {
                color: rgba(174,183,194,225);
                font-size: 12px;
                line-height: 1.25;
            }

            QLabel#TourProgress {
                color: rgba(174,183,194,180);
                font-size: 11px;
                font-weight: 850;
            }

            QPushButton#TourGhost {
                background: rgba(255,255,255,7);
                border: 1px solid rgba(255,255,255,14);
                border-radius: 999px;
                padding: 8px 12px;
                color: rgba(230,234,240,210);
                font-weight: 900;
            }

            QPushButton#TourGhost:hover {
                background: rgba(255,255,255,12);
                border: 1px solid rgba(255,255,255,22);
            }

            QPushButton#TourPrimary {
                background: rgba(230,234,240,235);
                border: 1px solid rgba(39,48,59,110);
                border-radius: 999px;
                padding: 8px 14px;
                color: rgba(15,19,24,235);
                font-weight: 950;
            }

            QPushButton#TourPrimary:hover {
                background: rgba(255,255,255,245);
            }
        """)

        self.setFixedWidth(340)

    def set_content(self, title: str, text: str, index: int, total: int, is_last: bool) -> None:
        self._title.setText(title)
        self._text.setText(text)
        self._progress.setText(f"{index} / {total}")
        self._next.setText("Fertig" if is_last else "Weiter")
        self.adjustSize()


class GuidedTourOverlay(QWidget):
    finished = Signal()

    def __init__(
        self,
        host: QWidget,
        steps: list[TourStep],
        on_finished: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent or host)

        self._host = host
        self._steps = list(steps)
        self._index = 0
        self._on_finished = on_finished

        self._bubble = TourBubble(self)
        self._bubble.hide()
        self._bubble.next_clicked.connect(self._next)
        self._bubble.skip_clicked.connect(self._finish)

        self._padding = 10
        self._spot_radius = 18
        self._arrow_size = 12
        self._bubble_gap = 18
        self._edge_margin = 18

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.hide()

        self._host.installEventFilter(self)

    # --------------------------
    # Public API
    # --------------------------
    def start(self) -> None:
        if not self._steps:
            self._finish()
            return

        self.setGeometry(self._host.rect())
        self.raise_()
        self.show()
        self.setFocus(Qt.OtherFocusReason)
        self._show_current_step()

    # --------------------------
    # Navigation
    # --------------------------
    def _next(self) -> None:
        self._index += 1
        if self._index >= len(self._steps):
            self._finish()
            return
        self._show_current_step()

    def _finish(self) -> None:
        try:
            self.hide()
            self.deleteLater()
        finally:
            try:
                if self._on_finished is not None:
                    self._on_finished()
            finally:
                self.finished.emit()

    def _show_current_step(self) -> None:
        if not (0 <= self._index < len(self._steps)):
            self._finish()
            return

        step = self._steps[self._index]
        target_rect = self._target_rect_in_overlay(step.target)

        if step.target is not None and (target_rect.isNull() or not target_rect.isValid()):
            self._next()
            return

        self._bubble.set_content(
            title=step.title,
            text=step.text,
            index=self._index + 1,
            total=len(self._steps),
            is_last=(self._index == len(self._steps) - 1),
        )
        self._position_bubble(step.placement, target_rect, has_target=step.target is not None)
        self._bubble.show()
        self._bubble.raise_()
        self.update()

    # --------------------------
    # Geometry
    # --------------------------
    def _target_rect_in_overlay(self, target: QWidget | None) -> QRect:
        if target is None or not target.isVisible():
            return QRect()

        global_pos = target.mapToGlobal(QPoint(0, 0))
        local_pos = self.mapFromGlobal(global_pos)
        r = QRect(local_pos, target.size())
        return r.adjusted(-self._padding, -self._padding, self._padding, self._padding)

    def _position_bubble(self, placement: str, target_rect: QRect, has_target: bool) -> None:
        self._bubble.adjustSize()

        bw = self._bubble.width()
        bh = self._bubble.height()

        host_w = self.width()
        host_h = self.height()
        gap = self._bubble_gap
        edge = self._edge_margin

        if not has_target or placement == "center":
            x = max(edge, (host_w - bw) // 2)
            y = max(edge, (host_h - bh) // 2)
            self._bubble.move(x, y)
            return

        candidates: list[tuple[str, int, int]] = []

        def add_candidate(place: str) -> None:
            if place == "left":
                x = target_rect.left() - bw - gap
                y = target_rect.center().y() - bh // 2
            elif place == "top":
                x = target_rect.center().x() - bw // 2
                y = target_rect.top() - bh - gap
            elif place == "bottom":
                x = target_rect.center().x() - bw // 2
                y = target_rect.bottom() + gap
            else:  # right
                x = target_rect.right() + gap
                y = target_rect.center().y() - bh // 2
            candidates.append((place, x, y))

        preferred = placement if placement in {"left", "right", "top", "bottom"} else "right"
        fallback_order = {
            "right": ["right", "left", "bottom", "top"],
            "left": ["left", "right", "bottom", "top"],
            "top": ["top", "bottom", "right", "left"],
            "bottom": ["bottom", "top", "right", "left"],
        }

        for place in fallback_order[preferred]:
            add_candidate(place)

        for _, x, y in candidates:
            fits_horiz = edge <= x <= host_w - bw - edge
            fits_vert = edge <= y <= host_h - bh - edge
            if fits_horiz and fits_vert:
                self._bubble.move(x, y)
                return

        _, x, y = candidates[0]
        x = max(edge, min(x, host_w - bw - edge))
        y = max(edge, min(y, host_h - bh - edge))
        self._bubble.move(x, y)

    # --------------------------
    # Events
    # --------------------------
    def eventFilter(self, obj, event):
        if obj is self._host and event.type() in {
            QEvent.Resize,
            QEvent.Move,
            QEvent.Show,
            QEvent.LayoutRequest,
        }:
            self.setGeometry(self._host.rect())
            if self.isVisible():
                self._show_current_step()
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event) -> None:
        if event.key() in {Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space, Qt.Key_Right}:
            self._next()
            return
        if event.key() in {Qt.Key_Escape}:
            self._finish()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event) -> None:
        if not self._bubble.isVisible():
            super().mousePressEvent(event)
            return

        pos = event.pos()

        if self._bubble.geometry().contains(pos):
            super().mousePressEvent(event)
            return

        step = self._steps[self._index] if 0 <= self._index < len(self._steps) else None
        if step is not None and step.target is not None:
            target_rect = self._target_rect_in_overlay(step.target)
            if target_rect.contains(pos):
                event.ignore()
                return

        self._next()

    # --------------------------
    # Paint
    # --------------------------
    def paintEvent(self, event) -> None:
        if not (0 <= self._index < len(self._steps)):
            return

        step = self._steps[self._index]

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        if step.target is None:
            p.fillRect(self.rect(), QColor(0, 0, 0, 165))
            p.end()
            return

        target_rect = self._target_rect_in_overlay(step.target)
        if target_rect.isNull():
            p.fillRect(self.rect(), QColor(0, 0, 0, 165))
            p.end()
            return

        overlay_path = QPainterPath()
        overlay_path.addRect(QRectF(self.rect()))

        hole_path = QPainterPath()
        hole_path.addRoundedRect(QRectF(target_rect), self._spot_radius, self._spot_radius)

        dim_path = overlay_path.subtracted(hole_path)
        p.fillPath(dim_path, QColor(0, 0, 0, 165))

        p.setPen(QPen(QColor(255, 255, 255, 110), 2))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(QRectF(target_rect), self._spot_radius, self._spot_radius)

        if self._bubble.isVisible():
            bubble_rect = self._bubble.geometry()
            arrow = self._build_arrow_path(bubble_rect, target_rect)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor(15, 19, 24, 245)))
            p.drawPath(arrow)

        p.end()

    def _build_arrow_path(self, bubble: QRect, target: QRect) -> QPainterPath:
        path = QPainterPath()

        bubble_center = bubble.center()
        target_center = target.center()

        dx = target_center.x() - bubble_center.x()
        dy = target_center.y() - bubble_center.y()

        size = self._arrow_size

        if abs(dx) >= abs(dy):
            if dx >= 0:
                ax = bubble.right()
                ay = max(bubble.top() + 28, min(target_center.y(), bubble.bottom() - 28))
                p1 = QPoint(ax, ay - size)
                p2 = QPoint(ax + size + 10, ay)
                p3 = QPoint(ax, ay + size)
            else:
                ax = bubble.left()
                ay = max(bubble.top() + 28, min(target_center.y(), bubble.bottom() - 28))
                p1 = QPoint(ax, ay - size)
                p2 = QPoint(ax - size - 10, ay)
                p3 = QPoint(ax, ay + size)
        else:
            if dy >= 0:
                ax = max(bubble.left() + 28, min(target_center.x(), bubble.right() - 28))
                ay = bubble.bottom()
                p1 = QPoint(ax - size, ay)
                p2 = QPoint(ax, ay + size + 10)
                p3 = QPoint(ax + size, ay)
            else:
                ax = max(bubble.left() + 28, min(target_center.x(), bubble.right() - 28))
                ay = bubble.top()
                p1 = QPoint(ax - size, ay)
                p2 = QPoint(ax, ay - size - 10)
                p3 = QPoint(ax + size, ay)

        path.moveTo(p1)
        path.lineTo(p2)
        path.lineTo(p3)
        path.closeSubpath()
        return path