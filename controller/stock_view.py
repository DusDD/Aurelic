# controller/stock_view.py
from __future__ import annotations

from datetime import date
from PySide6.QtCore import QObject, Signal, QThread, Qt

from src.auth.require_session import require_session_token
from src.stocks.charts import get_line_series, get_line_series_range, get_polygon_last_7d_daily


# -----------------------------
# Workers
# -----------------------------
class StockSeriesWorker(QObject):
    finished = Signal(dict)
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


class StockSeriesRangeWorker(QObject):
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(self, token: str, symbol: str, source: str, start: date, end: date):
        super().__init__()
        self._token = token
        self._symbol = symbol
        self._source = source
        self._start = start
        self._end = end

    def run(self):
        try:
            data = get_line_series_range(self._token, self._symbol, self._source, self._start, self._end)
            self.finished.emit(data)
        except Exception as e:
            self.failed.emit(str(e))


class Polygon7DWorker(QObject):
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(self, token: str, symbol: str):
        super().__init__()
        self._token = token
        self._symbol = symbol

    def run(self):
        try:
            data = get_polygon_last_7d_daily(self._token, self._symbol)
            self.finished.emit(data)
        except Exception as e:
            self.failed.emit(str(e))


# -----------------------------
# Controller
# -----------------------------
class StockViewController(QObject):
    series_ready = Signal(dict)
    series_failed = Signal(str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: QObject | None = None

    def _stop_thread(self):
        """Stoppt vorherigen Thread sauber (quit + wait), damit Qt nicht native crasht."""
        if self._thread is None:
            return

        try:
            # stop event loop
            self._thread.quit()
            # wait up to 1s
            self._thread.wait(1000)
        except Exception:
            pass

        self._thread = None
        self._worker = None

    def _start_worker(self, worker: QObject):
        """Startet Worker in neuem Thread (parented) und sorgt für sauberes Cleanup."""
        self._stop_thread()

        self._thread = QThread(self)  # parent -> verhindert GC/undefined behavior
        self._worker = worker
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run, Qt.QueuedConnection)

        self._worker.finished.connect(self.series_ready.emit, Qt.QueuedConnection)
        self._worker.failed.connect(self.series_failed.emit, Qt.QueuedConnection)

        # stop thread after work
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)

        # cleanup
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def load_series_async(self, symbol: str, timeframe: str):
        try:
            token = require_session_token()
        except Exception:
            self.series_failed.emit("Not logged in")
            return

        self._start_worker(StockSeriesWorker(token, symbol, timeframe))

    def load_series_range_async(self, token: str, symbol: str, source: str, start: date, end: date):
        self._start_worker(StockSeriesRangeWorker(token, symbol, source, start, end))

    def load_polygon_7d_async(self, token: str, symbol: str):
        self._start_worker(Polygon7DWorker(token, symbol))
