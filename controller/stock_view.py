# controller/stock_view.py
from __future__ import annotations

from src.auth.require_session import require_session_token
from PySide6.QtCore import QObject, Signal, QThread
from src.stocks.charts import get_line_series

class StockSeriesWorker(QObject):
    finished = Signal(dict)   # series payload
    failed = Signal(str)

    def __init__(self, token: str, symbol: str, timeframe: str):
        super().__init__()
        self._token = token
        self._symbol = symbol
        self._timeframe = timeframe

    def run(self):
        try:
            data = get_line_series(self._token, self._symbol, self._timeframe)
            self.finished.emit(data)
        except Exception as e:
            self.failed.emit(str(e))


class StockViewController(QObject):
    series_ready = Signal(dict)
    series_failed = Signal(str)

    def __init__(self):
        super().__init__()
        self._thread: QThread | None = None
        self._worker: StockSeriesWorker | None = None

    def load_series_async(self, symbol: str, timeframe: str):
        try:
            token = require_session_token()
        except Exception:
            self.series_failed.emit("Not logged in")
            return

        self._thread = QThread()
        self._worker = StockSeriesWorker(token, symbol, timeframe)

        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self.series_ready.emit)
        self._worker.failed.connect(self.series_failed.emit)

        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def _on_series_failed(self, msg: str):
        if "Not logged in" in msg:
            QMessageBox.warning(self, "Session expired", "Please log in again.")
            self.tab_changed.emit("brokerage")  # oder StartPage