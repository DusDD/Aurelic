# gui/analysepage.py
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout, QSizePolicy
)

# WICHTIG: exakt dasselbe Theme/QSS wie MainPage verwenden
from gui.mainpage import Palette, build_qss
from gui.widgets.segmentedtabs import SegmentedTabs

# World Bank feed widget
from gui.widgets.worldbank_feed import WorldBankFeedWidget
from src.auth.require_session import require_session_token, NotAuthenticatedError


class AnalysePage(QWidget):
    tab_changed = Signal(str)    # "brokerage" | "analyse"
    avatar_clicked = Signal()
    calendar_clicked = Signal()  # Kreis-Button (Kalender)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setObjectName("Root")
        self._palette = Palette()
        self.setStyleSheet(build_qss(self._palette))
        self.setAttribute(Qt.WA_StyledBackground, True)

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
        self._bottom = self._build_bottom_area()

        shell_v.addWidget(self._topbar, 0)
        shell_v.addWidget(self._middle, 1)
        shell_v.addWidget(self._bottom, 0)

        root.addWidget(self._shell, 0, Qt.AlignCenter)

        # Default tab state (keine Emission beim Init)
        self._seg_tabs.set_active("analyse", animate=False, emit=False)

    def showEvent(self, event):
        super().showEvent(event)
        try:
            require_session_token()
        except NotAuthenticatedError:
            self.back_requested.emit()  # oder stack.setCurrentWidget(StartPage)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)

        margin = 40
        avail_w = max(300, self.width() - 2 * margin)
        avail_h = max(300, self.height() - 2 * margin)

        ratio = 1.568  # width / height
        w = min(avail_w, int(avail_h * ratio))
        h = min(avail_h, int(w / ratio))
        self._shell.setFixedSize(w, h)

    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setAttribute(Qt.WA_StyledBackground, True)

        h = QHBoxLayout(bar)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(12)

        self._seg_tabs = SegmentedTabs()
        self._seg_tabs.setObjectName("SegmentedTabs")
        self._seg_tabs.changed.connect(self._set_active_tab)

        cal_btn = QPushButton("◯")
        cal_btn.setObjectName("CalendarBtn")
        cal_btn.setFixedSize(44, 44)
        cal_btn.setCursor(Qt.PointingHandCursor)
        cal_btn.clicked.connect(self.calendar_clicked.emit)

        avatar = QPushButton("N")
        avatar.setObjectName("Avatar")
        avatar.setFixedSize(44, 44)
        avatar.setCursor(Qt.PointingHandCursor)
        avatar.clicked.connect(self.avatar_clicked.emit)

        h.addWidget(self._seg_tabs, 0, Qt.AlignLeft)
        h.addStretch(1)
        h.addWidget(cal_btn, 0, Qt.AlignRight)
        h.addWidget(avatar, 0, Qt.AlignRight)
        return bar

    def _set_active_tab(self, which: str) -> None:
        # Defensive normalization
        which = "analyse" if which == "analyse" else "brokerage"
        self._seg_tabs.set_active(which, animate=True, emit=False)
        self.tab_changed.emit(which)

    def _build_middle_area(self) -> QWidget:
        w = QWidget()
        w.setAttribute(Qt.WA_StyledBackground, True)

        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(14)

        # LEFT: World Bank feed widget (etwas breiter)
        left = WorldBankFeedWidget()
        left.setMinimumWidth(420)
        left.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        # CENTER: minimal schmaler
        center = self._panel(
            title="",
            placeholder="Analyse-Chart / Indikatoren\n(Placeholder)",
            min_w=820
        )
        center.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # RIGHT: stacked panels
        right = QWidget()
        right.setAttribute(Qt.WA_StyledBackground, True)

        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(14)

        right_top = self._panel(
            title="Portfolio\nRisiko",
            placeholder="Heatmap / Risiko\n(Placeholder)",
            min_w=320
        )
        right_bottom = self._panel(
            title="Watchlist\nInsights",
            placeholder="Alerts / Insights\n(Placeholder)",
            min_w=320
        )

        right_top.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        right_bottom.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        rv.addWidget(right_top, 1)
        rv.addWidget(right_bottom, 1)

        h.addWidget(left, 0)
        h.addWidget(center, 4)
        h.addWidget(right, 0)
        return w

    def _build_bottom_area(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card.setAttribute(Qt.WA_StyledBackground, True)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        v = QVBoxLayout(card)
        v.setContentsMargins(18, 14, 18, 14)
        v.setSpacing(10)

        title = QLabel("Analyse-Notizen / Backtests")
        title.setObjectName("PanelTitle")

        hint = QLabel("Hier kommt später z. B. Backtests, Notizen oder ein Report-Export hin.")
        hint.setObjectName("FinePrint")
        hint.setWordWrap(True)

        placeholder = QFrame()
        placeholder.setObjectName("Panel")
        placeholder.setAttribute(Qt.WA_StyledBackground, True)
        placeholder.setFixedHeight(160)

        ph = QVBoxLayout(placeholder)
        ph.setContentsMargins(14, 14, 14, 14)

        txt = QLabel("Analyse-Bereich (Placeholder)")
        txt.setObjectName("Placeholder")
        txt.setAlignment(Qt.AlignCenter)
        txt.setWordWrap(True)
        txt.setMinimumHeight(28)

        ph.addWidget(txt, 0, Qt.AlignCenter)

        v.addWidget(title)
        v.addWidget(hint)
        v.addWidget(placeholder)
        return card

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
