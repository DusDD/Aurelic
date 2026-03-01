# gui/investment.py
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, List

from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout, QSizePolicy,
    QLineEdit, QDoubleSpinBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QComboBox
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
    QLineEdit, QDoubleSpinBox, QComboBox {{
        background: rgba(255,255,255,6);
        border: 1px solid rgba(39,48,59,170);
        border-radius: 14px;
        padding: 10px 12px;
        color: rgba(230,234,240,220);
        font-size: 12px;
    }}
    QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus {{
        border: 1px solid rgba(109,146,155,140);
    }}
    QComboBox::drop-down {{
        border: 0px;
        width: 22px;
    }}
    QComboBox::down-arrow {{
        width: 0px;
        height: 0px;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid rgba(230,234,240,160);
        margin-right: 8px;
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
# Investment Page
# --------------------------
class InvestmentPage(QWidget):
    """
    DB-basierte Investments:
      - stocks.assets: canonical_symbol, name, category
      - stocks.investments: (user_id, asset_id, quantity)

    Erwartet einen InvestmentsController mit:
      - upsert_user_investment(symbol, name, category, quantity)
      - list_user_investments()
      - delete_user_investment(symbol)
    """

    back_clicked = Signal()

    def __init__(
        self,
        investments_ctrl,
        background_path: str = "images/Backgroundimage.png",
        parent: QWidget | None = None
    ):
        super().__init__(parent)

        self._ctrl = investments_ctrl

        self.setObjectName("Root")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)

        self._palette = Palette()
        self._background_path = background_path
        self.setStyleSheet(build_qss(self._palette, self._background_path))

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

        self._shell.setFixedSize(980, 625)

        # auto initial load (defer to allow stack/layout)
        QTimer.singleShot(0, self.reload)

    # --------------------------
    # Public API
    # --------------------------
    def reload(self) -> None:
        try:
            items = self._ctrl.list_user_investments()
        except Exception as e:
            QMessageBox.critical(self, "Investments", f"Konnte Investments nicht laden:\n{e}")
            items = []
        self._render_table(items)

    # --------------------------
    # Layout: Topbar
    # --------------------------
    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setAttribute(Qt.WA_StyledBackground, True)

        h = QHBoxLayout(bar)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(12)

        back_btn = QPushButton()
        back_btn.setObjectName("IconCircle")
        back_btn.setFixedSize(44, 44)
        back_btn.setToolTip("Zurück")
        back_btn.clicked.connect(self.back_clicked.emit)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        back_icon_path = os.path.abspath(os.path.join(base_dir, "..", "images", "back.png"))
        if os.path.exists(back_icon_path):
            back_btn.setIcon(QIcon(back_icon_path))
            back_btn.setIconSize(QSize(22, 22))
        else:
            back_btn.setText("‹")

        title = QLabel("Investments")
        title.setObjectName("PanelTitle")

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

        card = QFrame()
        card.setObjectName("Card")
        card.setAttribute(Qt.WA_StyledBackground, True)

        cv = QVBoxLayout(card)
        cv.setContentsMargins(18, 14, 18, 14)
        cv.setSpacing(12)

        hint = QLabel("Füge ein Asset hinzu (Symbol + optional Name/Kategorie) und setze deine Stückzahl.")
        hint.setObjectName("FinePrint")
        hint.setWordWrap(True)
        cv.addWidget(hint)

        form = QWidget()
        form.setAttribute(Qt.WA_StyledBackground, True)
        fh = QHBoxLayout(form)
        fh.setContentsMargins(0, 0, 0, 0)
        fh.setSpacing(10)

        self._symbol = QLineEdit()
        self._symbol.setPlaceholderText("Symbol (z. B. AAPL, MSFT, BTC)")
        self._symbol.setClearButtonEnabled(True)

        self._name = QLineEdit()
        self._name.setPlaceholderText("Name (optional)")
        self._name.setClearButtonEnabled(True)

        self._category = QComboBox()
        self._category.addItems(["stock", "etf", "crypto", "commodity", "index"])
        self._category.setCurrentText("stock")

        self._qty = QDoubleSpinBox()
        self._qty.setMinimum(0.0)
        self._qty.setMaximum(1_000_000_000.0)
        self._qty.setDecimals(8)
        self._qty.setValue(1.0)

        add_btn = QPushButton("Speichern")
        add_btn.setObjectName("Primary")
        add_btn.clicked.connect(self._upsert_clicked)

        fh.addWidget(self._symbol, 1)
        fh.addWidget(self._name, 1)
        fh.addWidget(self._category, 0)
        fh.addWidget(QLabel("Anzahl:"), 0)
        fh.addWidget(self._qty, 0)
        fh.addWidget(add_btn, 0)

        cv.addWidget(form)

        panel = QFrame()
        panel.setObjectName("Panel")
        panel.setAttribute(Qt.WA_StyledBackground, True)
        panel_v = QVBoxLayout(panel)
        panel_v.setContentsMargins(14, 12, 14, 12)
        panel_v.setSpacing(10)

        panel_title = QLabel("Dein Portfolio")
        panel_title.setObjectName("PanelTitle")
        panel_v.addWidget(panel_title, 0, Qt.AlignLeft)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["Symbol", "Name", "Kategorie", "Anzahl", "Updated"])
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(False)
        self._table.setShowGrid(False)

        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setMinimumHeight(320)

        panel_v.addWidget(self._table, 1)

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

        refresh_btn = QPushButton("Neu laden")
        refresh_btn.setObjectName("Ghost")
        refresh_btn.clicked.connect(self.reload)

        fh2.addWidget(self._count_label, 1, Qt.AlignLeft)
        fh2.addWidget(refresh_btn, 0, Qt.AlignRight)
        fh2.addWidget(del_btn, 0, Qt.AlignRight)

        panel_v.addWidget(footer, 0)

        cv.addWidget(panel)
        v.addWidget(card, 1)
        return body

    # --------------------------
    # Actions
    # --------------------------
    def _upsert_clicked(self) -> None:
        sym = (self._symbol.text() or "").strip().upper()
        nm = (self._name.text() or "").strip()
        cat = (self._category.currentText() or "stock").strip()
        qty = float(self._qty.value())

        if not sym:
            QMessageBox.warning(self, "Fehlt", "Bitte ein Symbol eingeben (z. B. AAPL).")
            return

        try:
            self._ctrl.upsert_user_investment(sym, nm or None, cat, qty)
        except Exception as e:
            QMessageBox.critical(self, "Investments", f"Konnte nicht speichern:\n{e}")
            return

        self._symbol.clear()
        self._name.clear()
        self._category.setCurrentText("stock")
        self._qty.setValue(1.0)

        self.reload()

    def _delete_selected(self) -> None:
        idx = self._table.currentRow()
        if idx < 0:
            return

        sym_item = self._table.item(idx, 0)
        sym = (sym_item.text() if sym_item else "").strip().upper()
        if not sym:
            return

        ok = QMessageBox.question(
            self,
            "Entfernen",
            f"'{sym}' wirklich entfernen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ok != QMessageBox.StandardButton.Yes:
            return

        try:
            self._ctrl.delete_user_investment(sym)
        except Exception as e:
            QMessageBox.critical(self, "Investments", f"Konnte nicht entfernen:\n{e}")
            return

        self.reload()

    # --------------------------
    # Table rendering
    # --------------------------
    def _render_table(self, items: list[dict]) -> None:
        self._table.setRowCount(0)

        for it in (items or []):
            row_i = self._table.rowCount()
            self._table.insertRow(row_i)

            sym = str(it.get("symbol") or "")
            name = str(it.get("name") or "")
            cat = str(it.get("category") or "")
            qty = float(it.get("quantity") or 0.0)
            upd = it.get("updated_at")

            sym_item = QTableWidgetItem(sym)
            sym_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            name_item = QTableWidgetItem(name)

            cat_item = QTableWidgetItem(cat)
            cat_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            qty_item = QTableWidgetItem(f"{qty:.8f}".rstrip("0").rstrip("."))
            qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            upd_txt = ""
            try:
                upd_txt = upd.strftime("%Y-%m-%d %H:%M") if upd else ""
            except Exception:
                upd_txt = str(upd or "")
            upd_item = QTableWidgetItem(upd_txt)
            upd_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self._table.setItem(row_i, 0, sym_item)
            self._table.setItem(row_i, 1, name_item)
            self._table.setItem(row_i, 2, cat_item)
            self._table.setItem(row_i, 3, qty_item)
            self._table.setItem(row_i, 4, upd_item)

        self._count_label.setText(f"{len(items or [])} Einträge")