# gui/investment.py
from __future__ import annotations

import os
import json
from dataclasses import dataclass
from typing import Optional, List

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout, QSizePolicy,
    QLineEdit, QSpinBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView
)


# --------------------------
# Theme (same as MainPage)
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
        font-family: -apple-system, "SF Pro Display", "SF Pro Text", "Inter", "Helvetica Neue", "Arial";
        background-color: {p.bg0};
    }}

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

    #Placeholder {{
        color: rgba(174,183,194,180);
        font-size: 13px;
        padding: 2px 0px;
    }}

    /* Buttons */
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

    QPushButton#IconCircle {{
        background: rgba(109,146,155,18);
        border: 1px solid rgba(39,48,59,170);
        border-radius: 22px;
        padding: 0px;
    }}
    QPushButton#IconCircle:hover {{
        background: rgba(109,146,155,30);
        border: 1px solid rgba(109,146,155,90);
    }}

    /* Inputs */
    QLineEdit, QSpinBox {{
        background: rgba(255,255,255,6);
        border: 1px solid rgba(39,48,59,170);
        border-radius: 14px;
        padding: 10px 12px;
        color: rgba(230,234,240,220);
        font-size: 12px;
    }}
    QLineEdit:focus, QSpinBox:focus {{
        border: 1px solid rgba(109,146,155,140);
    }}

    /* Table */
    QTableWidget {{
        background: rgba(255,255,255,4);
        border: 1px solid rgba(39,48,59,170);
        border-radius: 14px;
        gridline-color: rgba(39,48,59,120);
        selection-background-color: rgba(109,146,155,35);
        selection-color: rgba(230,234,240,235);
        font-size: 12px;
    }}
    QHeaderView::section {{
        background: rgba(255,255,255,6);
        color: rgba(230,234,240,210);
        border: 0px;
        border-bottom: 1px solid rgba(39,48,59,170);
        padding: 8px 10px;
        font-weight: 900;
    }}
    QTableWidget::item {{
        padding: 8px 10px;
    }}
    """


# --------------------------
# Model
# --------------------------
@dataclass
class InvestmentRow:
    name: str
    amount: int


# --------------------------
# Investment Page
# --------------------------
class InvestmentPage(QWidget):
    """
    Investments im gleichen Design wie MainPage.
    - Hinzufügen: Name + Anzahl
    - Entfernen: ausgewählte Zeile
    - Speichern: data/investments.json (relativ zum Projekt)
    """

    back_clicked = Signal()  # optional: MainWindow kann zurück zur MainPage wechseln

    def __init__(self, background_path: str = "images/Backgroundimage.png", parent: QWidget | None = None):
        super().__init__(parent)

        self.setObjectName("Root")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)

        self._palette = Palette()
        self._background_path = background_path
        self.setStyleSheet(build_qss(self._palette, self._background_path))

        self._rows: List[InvestmentRow] = []
        self._data_path = self._resolve_data_path()

        # Root layout (centered shell like MainPage)
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
        shell_v.addWidget(self._build_body(), 1)

        root.addWidget(self._shell, 0, Qt.AlignCenter)

        # Initial sizing like MainPage feel
        self._shell.setFixedSize(980, 625)

        self._load()
        self._refresh_table()

    # --------------------------
    # Layout: Topbar
    # --------------------------
    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setAttribute(Qt.WA_StyledBackground, True)

        h = QHBoxLayout(bar)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(12)

        # Back button (circle)
        back_btn = QPushButton()
        back_btn.setObjectName("IconCircle")
        back_btn.setFixedSize(44, 44)
        back_btn.setToolTip("Zurück")
        back_btn.clicked.connect(self.back_clicked.emit)

        # Try to use an optional back icon if present; else show "<"
        base_dir = os.path.dirname(os.path.abspath(__file__))
        back_icon_path = os.path.abspath(os.path.join(base_dir, "..", "images", "back.png"))
        if os.path.exists(back_icon_path):
            back_btn.setIcon(QIcon(back_icon_path))
            back_btn.setIconSize(QSize(22, 22))
        else:
            back_btn.setText("‹")
            back_btn.setStyleSheet(back_btn.styleSheet() + "font-size:18px; font-weight:900;")

        title = QLabel("Investments")
        title.setObjectName("PanelTitle")

        # Right circle icon (invest.png)
        invest_btn = QPushButton()
        invest_btn.setObjectName("IconCircle")
        invest_btn.setFixedSize(44, 44)
        invest_btn.setToolTip("Investments")

        invest_icon_path = os.path.abspath(os.path.join(base_dir, "..", "images", "invest.png"))
        if os.path.exists(invest_icon_path):
            invest_btn.setIcon(QIcon(invest_icon_path))
            invest_btn.setIconSize(QSize(24, 24))

        h.addWidget(back_btn, 0, Qt.AlignLeft)
        h.addSpacing(4)
        h.addWidget(title, 0, Qt.AlignLeft)
        h.addStretch(1)
        h.addWidget(invest_btn, 0, Qt.AlignRight)
        return bar

    # --------------------------
    # Layout: Body
    # --------------------------
    def _build_body(self) -> QWidget:
        body = QWidget()
        body.setAttribute(Qt.WA_StyledBackground, True)

        v = QVBoxLayout(body)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(14)

        # Card container
        card = QFrame()
        card.setObjectName("Card")
        card.setAttribute(Qt.WA_StyledBackground, True)

        cv = QVBoxLayout(card)
        cv.setContentsMargins(18, 14, 18, 14)
        cv.setSpacing(12)

        hint = QLabel("Füge deine Investments hinzu und speichere sie lokal. (Name + Anzahl)")
        hint.setObjectName("FinePrint")
        hint.setWordWrap(True)
        cv.addWidget(hint)

        # Form row
        form = QWidget()
        form.setAttribute(Qt.WA_StyledBackground, True)
        fh = QHBoxLayout(form)
        fh.setContentsMargins(0, 0, 0, 0)
        fh.setSpacing(10)

        self._name = QLineEdit()
        self._name.setPlaceholderText("Investment (z. B. AAPL, BTC, ETF-Name)")
        self._name.setClearButtonEnabled(True)

        self._amount = QSpinBox()
        self._amount.setMinimum(1)
        self._amount.setMaximum(1_000_000)
        self._amount.setValue(1)
        self._amount.setButtonSymbols(QSpinBox.ButtonSymbols.PlusMinus)

        add_btn = QPushButton("Hinzufügen")
        add_btn.setObjectName("Primary")
        add_btn.clicked.connect(self._add_row)

        fh.addWidget(self._name, 1)
        fh.addWidget(QLabel("Anzahl:"), 0)
        fh.addWidget(self._amount, 0)
        fh.addWidget(add_btn, 0)

        cv.addWidget(form)

        # Table panel
        panel = QFrame()
        panel.setObjectName("Panel")
        panel.setAttribute(Qt.WA_StyledBackground, True)
        panel_v = QVBoxLayout(panel)
        panel_v.setContentsMargins(14, 12, 14, 12)
        panel_v.setSpacing(10)

        panel_title = QLabel("Deine Liste")
        panel_title.setObjectName("PanelTitle")
        panel_v.addWidget(panel_title, 0, Qt.AlignLeft)

        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Investment", "Anzahl"])
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(False)
        self._table.setShowGrid(False)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setMinimumHeight(320)

        panel_v.addWidget(self._table, 1)

        # Footer row (actions)
        footer = QWidget()
        footer.setAttribute(Qt.WA_StyledBackground, True)
        fh2 = QHBoxLayout(footer)
        fh2.setContentsMargins(0, 0, 0, 0)
        fh2.setSpacing(10)

        self._count_label = QLabel("0 Einträge")
        self._count_label.setObjectName("FinePrint")

        del_btn = QPushButton("Ausgewähltes entfernen")
        del_btn.setObjectName("Ghost")
        del_btn.clicked.connect(self._delete_selected)

        save_btn = QPushButton("Speichern")
        save_btn.setObjectName("Primary")
        save_btn.clicked.connect(self._save)

        fh2.addWidget(self._count_label, 1, Qt.AlignLeft)
        fh2.addWidget(del_btn, 0, Qt.AlignRight)
        fh2.addWidget(save_btn, 0, Qt.AlignRight)

        panel_v.addWidget(footer, 0)

        cv.addWidget(panel)

        v.addWidget(card, 1)
        return body

    # --------------------------
    # Data persistence
    # --------------------------
    def _resolve_data_path(self) -> str:
        # gui/ -> ../data/investments.json
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.abspath(os.path.join(base_dir, "..", "data"))
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "investments.json")

    def _load(self) -> None:
        self._rows = []
        if not os.path.exists(self._data_path):
            return
        try:
            with open(self._data_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, list):
                for r in raw:
                    if not isinstance(r, dict):
                        continue
                    name = str(r.get("name", "")).strip()
                    try:
                        amount = int(r.get("amount", 0))
                    except Exception:
                        amount = 0
                    if name and amount > 0:
                        self._rows.append(InvestmentRow(name=name, amount=amount))
        except Exception:
            self._rows = []

    def _save(self) -> None:
        try:
            payload = [{"name": r.name, "amount": int(r.amount)} for r in self._rows]
            with open(self._data_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Gespeichert", "Investments wurden gespeichert.")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Konnte nicht speichern:\n{e}")

    # --------------------------
    # Table helpers
    # --------------------------
    def _refresh_table(self) -> None:
        self._table.setRowCount(0)

        for r in self._rows:
            row_i = self._table.rowCount()
            self._table.insertRow(row_i)

            name_item = QTableWidgetItem(r.name)
            amt_item = QTableWidgetItem(str(r.amount))
            amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self._table.setItem(row_i, 0, name_item)
            self._table.setItem(row_i, 1, amt_item)

        self._count_label.setText(f"{len(self._rows)} Einträge")

    # --------------------------
    # Actions
    # --------------------------
    def _add_row(self) -> None:
        name = (self._name.text() or "").strip()
        amount = int(self._amount.value())

        if not name:
            QMessageBox.warning(self, "Fehlt", "Bitte einen Investment-Namen eingeben.")
            return

        # merge if exists (case-insensitive)
        for r in self._rows:
            if r.name.lower() == name.lower():
                r.amount += amount
                self._name.clear()
                self._amount.setValue(1)
                self._refresh_table()
                return

        self._rows.append(InvestmentRow(name=name, amount=amount))
        self._name.clear()
        self._amount.setValue(1)
        self._refresh_table()

    def _delete_selected(self) -> None:
        idx = self._table.currentRow()
        if idx < 0 or idx >= len(self._rows):
            return

        name = self._rows[idx].name
        ok = QMessageBox.question(
            self,
            "Entfernen",
            f"'{name}' wirklich entfernen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ok != QMessageBox.StandardButton.Yes:
            return

        self._rows.pop(idx)
        self._refresh_table()