from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QVBoxLayout, QSizePolicy
)


@dataclass
class WatchlistAssetInfo:
    symbol: str
    name: str
    asset_type: str
    sector: str | None = None
    currency: str | None = None
    region: str | None = None


class _InsightCard(QFrame):
    def __init__(self, title: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("WatchInsightCard")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._title = QLabel(title)
        self._title.setObjectName("WatchInsightCardTitle")

        self._body = QLabel("")
        self._body.setObjectName("WatchInsightCardBody")
        self._body.setWordWrap(True)
        self._body.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        v = QVBoxLayout(self)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(8)
        v.addWidget(self._title, 0)
        v.addWidget(self._body, 0)

        self.setStyleSheet("""
            QFrame#WatchInsightCard {
                background: rgba(255,255,255,10);
                border: 1px solid rgba(255,255,255,16);
                border-radius: 14px;
            }

            QLabel#WatchInsightCardTitle {
                color: rgba(230,234,240,235);
                font-size: 12px;
                font-weight: 900;
            }

            QLabel#WatchInsightCardBody {
                color: rgba(174,183,194,220);
                font-size: 12px;
                line-height: 1.3;
            }
        """)

    def set_text(self, text: str) -> None:
        self._body.setText(text.strip() or "Keine Daten verfügbar.")


class WatchlistInsightsWidget(QFrame):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setObjectName("Panel")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setMinimumWidth(320)
        self.setMaximumWidth(360)

        self._title = QLabel("Watchlist Insights")
        self._title.setObjectName("PanelTitle")

        self._subtitle = QLabel(
            "Korrelationen, Klumpenrisiken und Exposure-Hinweise für deine Watchlist."
        )
        self._subtitle.setObjectName("Placeholder")
        self._subtitle.setWordWrap(True)
        self._subtitle.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self._sector_card = _InsightCard("Sektor-Konzentration")
        self._corr_card = _InsightCard("Korrelationshinweise")
        self._fx_card = _InsightCard("Währungs- / Asset-Exposure")

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        root.addWidget(self._title, 0, Qt.AlignLeft)
        root.addWidget(self._subtitle, 0)
        root.addWidget(self._sector_card, 0)
        root.addWidget(self._corr_card, 0)
        root.addWidget(self._fx_card, 0)
        root.addStretch(1)

        self.set_symbols([])

    def set_assets(self, assets: Iterable[WatchlistAssetInfo]) -> None:
        items = [a for a in assets if a and (a.symbol or "").strip()]

        if not items:
            self._sector_card.set_text("Noch keine Watchlist-Daten vorhanden.")
            self._corr_card.set_text(
                "Sobald mehrere Assets vorliegen, können ähnliche Bewegungsmuster erkannt werden."
            )
            self._fx_card.set_text(
                "Währungs- und Asset-Abhängigkeiten werden angezeigt, sobald Instrumente zugeordnet sind."
            )
            return

        self._sector_card.set_text(self._build_sector_text(items))
        self._corr_card.set_text(self._build_correlation_text(items))
        self._fx_card.set_text(self._build_exposure_text(items))

    def set_symbols(self, symbols: list[str] | None) -> None:
        mapped = [self._guess_asset_info(sym) for sym in (symbols or []) if (sym or "").strip()]
        self.set_assets(mapped)

    def _build_sector_text(self, items: list[WatchlistAssetInfo]) -> str:
        sectors = [(a.sector or "Unbekannt").strip() for a in items]
        counts = Counter(sectors)
        total = len(items)

        top_sector, top_count = counts.most_common(1)[0]
        top_pct = round((top_count / total) * 100)

        lines: list[str] = []

        if top_sector != "Unbekannt":
            if top_pct >= 60:
                lines.append(f"Deine Watchlist ist stark {top_sector}-lastig ({top_pct} %).")
            elif top_pct >= 40:
                lines.append(f"Erhöhte Konzentration im Bereich {top_sector} ({top_pct} %).")
            else:
                lines.append(f"Größter Bereich ist {top_sector} ({top_pct} %).")

        ranked = [
            f"{sector}: {count}"
            for sector, count in counts.most_common(3)
            if sector != "Unbekannt"
        ]
        if ranked:
            lines.append("Top-Bereiche: " + ", ".join(ranked))

        if len([s for s in counts if s != "Unbekannt"]) <= 2 and total >= 4:
            lines.append("Die Diversifikation über Sektoren ist aktuell eher gering.")

        return "\n".join(lines) if lines else "Noch keine belastbaren Sektor-Hinweise."

    def _build_correlation_text(self, items: list[WatchlistAssetInfo]) -> str:
        sector_counts = Counter((a.sector or "Unbekannt").strip() for a in items)
        type_counts = Counter((a.asset_type or "unknown").strip() for a in items)

        similar_groups = [
            (sector, count)
            for sector, count in sector_counts.items()
            if sector != "Unbekannt" and count >= 3
        ]

        if similar_groups:
            sector, count = max(similar_groups, key=lambda x: x[1])
            return (
                f"{count} Assets stammen aus demselben Bereich ({sector}) und könnten sich "
                f"in Stressphasen ähnlich bewegen.\n"
                f"Das erhöht das Risiko paralleler Drawdowns."
            )

        if type_counts.get("stock", 0) >= 4:
            return (
                "Die Watchlist enthält mehrere Einzelaktien. Ohne zusätzliche Preisreihen ist "
                "eine grobe Klumpung erkennbar, insbesondere innerhalb ähnlicher Branchen."
            )

        if len(items) >= 5:
            return (
                "Aktuell keine offensichtliche starke Klumpung über sehr ähnliche Zuordnungen.\n"
                "Für echte Korrelationswerte können später Preisreihen ergänzt werden."
            )

        return (
            "Für belastbare Korrelationshinweise sind mehr Watchlist-Daten sinnvoll.\n"
            "Sobald mehrere vergleichbare Assets vorliegen, wird die Ähnlichkeit genauer bewertet."
        )

    def _build_exposure_text(self, items: list[WatchlistAssetInfo]) -> str:
        currencies = [(a.currency or "Unbekannt").strip().upper() for a in items]
        asset_types = [(a.asset_type or "unknown").strip().lower() for a in items]

        ccy_counts = Counter(currencies)
        type_counts = Counter(asset_types)
        total = len(items)

        lines: list[str] = []

        top_ccy, top_ccy_count = ccy_counts.most_common(1)[0]
        top_ccy_pct = round((top_ccy_count / total) * 100)

        if top_ccy != "UNBEKANNT":
            if top_ccy_pct >= 60:
                lines.append(f"Hohe {top_ccy}-Abhängigkeit in der Watchlist ({top_ccy_pct} %).")
            elif top_ccy_pct >= 40:
                lines.append(f"Erhöhtes Exposure gegenüber {top_ccy} ({top_ccy_pct} %).")
            else:
                lines.append(f"Größte Währungszuordnung: {top_ccy} ({top_ccy_pct} %).")

        ranked_types = [f"{t}: {c}" for t, c in type_counts.most_common(3)]
        if ranked_types:
            lines.append("Asset-Mix: " + ", ".join(ranked_types))

        crypto_count = type_counts.get("crypto", 0)
        if crypto_count >= 2:
            lines.append("Erhöhte Krypto-Komponente mit potenziell höherer Volatilität.")

        commodity_count = type_counts.get("commodity", 0)
        if commodity_count >= 2:
            lines.append("Rohstoff-Exposure vorhanden, was diversifizierend wirken kann.")

        return "\n".join(lines) if lines else "Noch keine belastbaren Exposure-Hinweise."

    def _guess_asset_info(self, symbol: str) -> WatchlistAssetInfo:
        s = (symbol or "").strip().upper()

        known: dict[str, WatchlistAssetInfo] = {
            "AAPL": WatchlistAssetInfo("AAPL", "Apple", "stock", "Technology", "USD", "USA"),
            "AMZN": WatchlistAssetInfo("AMZN", "Amazon", "stock", "Consumer Discretionary", "USD", "USA"),
            "MSFT": WatchlistAssetInfo("MSFT", "Microsoft", "stock", "Technology", "USD", "USA"),
            "TSLA": WatchlistAssetInfo("TSLA", "Tesla", "stock", "Consumer Discretionary", "USD", "USA"),
            "NVDA": WatchlistAssetInfo("NVDA", "Nvidia", "stock", "Technology", "USD", "USA"),
            "MRNA": WatchlistAssetInfo("MRNA", "Moderna", "stock", "Healthcare", "USD", "USA"),
            "UL": WatchlistAssetInfo("UL", "Unilever", "stock", "Consumer Staples", "GBP", "UK"),
            "BMW": WatchlistAssetInfo("BMW", "BMW", "stock", "Consumer Discretionary", "EUR", "Germany"),
            "VOW3": WatchlistAssetInfo("VOW3", "Volkswagen", "stock", "Consumer Discretionary", "EUR", "Germany"),
            "RHM": WatchlistAssetInfo("RHM", "Rheinmetall", "stock", "Industrials", "EUR", "Germany"),
            "BAYN": WatchlistAssetInfo("BAYN", "Bayer", "stock", "Healthcare", "EUR", "Germany"),
            "BAS": WatchlistAssetInfo("BAS", "BASF", "stock", "Materials", "EUR", "Germany"),
            "AML": WatchlistAssetInfo("AML", "Aston Martin", "stock", "Consumer Discretionary", "GBP", "UK"),
            "MBG": WatchlistAssetInfo("MBG", "Mercedes-Benz", "stock", "Consumer Discretionary", "EUR", "Germany"),
            "CWR": WatchlistAssetInfo("CWR", "Ceres Power", "stock", "Industrials", "GBP", "UK"),
            "SHA": WatchlistAssetInfo("SHA", "Schaeffler", "stock", "Industrials", "EUR", "Germany"),
            "MNST": WatchlistAssetInfo("MNST", "Monster Beverage", "stock", "Consumer Staples", "USD", "USA"),
            "URTH": WatchlistAssetInfo("URTH", "iShares MSCI World ETF", "etf", "Global Equity", "USD", "Global"),
            "SPY": WatchlistAssetInfo("SPY", "SPDR S&P 500 ETF", "etf", "US Large Cap", "USD", "USA"),
            "SPX": WatchlistAssetInfo("SPX", "S&P 500 Index", "index", "US Large Cap", "USD", "USA"),
            "BTC": WatchlistAssetInfo("BTC", "Bitcoin", "crypto", "Digital Assets", "USD", "Global"),
            "SOL": WatchlistAssetInfo("SOL", "Solana", "crypto", "Digital Assets", "USD", "Global"),
            "DOGE": WatchlistAssetInfo("DOGE", "Dogecoin", "crypto", "Digital Assets", "USD", "Global"),
            "XAU": WatchlistAssetInfo("XAU", "Gold", "commodity", "Precious Metals", "USD", "Global"),
            "XAG": WatchlistAssetInfo("XAG", "Silver", "commodity", "Precious Metals", "USD", "Global"),
            "P911": WatchlistAssetInfo("P911", "Porsche AG", "stock", "Consumer Discretionary", "EUR", "Germany"),
        }

        return known.get(
            s,
            WatchlistAssetInfo(
                symbol=s,
                name=s,
                asset_type="unknown",
                sector="Unbekannt",
                currency="Unbekannt",
                region="Unbekannt",
            )
        )