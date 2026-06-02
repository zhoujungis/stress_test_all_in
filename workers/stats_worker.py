import threading
import time

from PyQt6.QtCore import QRunnable, QObject, pyqtSignal

from core.metrics import AggregateMetrics


class StatsWorkerSignals(QObject):
    stats = pyqtSignal(dict)       # aggregated stats
    per_module = pyqtSignal(list)  # list of per-module snapshots


class StatsWorker(QRunnable):
    def __init__(self, aggregate: AggregateMetrics, stop_event: threading.Event,
                 interval: float = 0.5):
        super().__init__()
        self.aggregate = aggregate
        self.stop_event = stop_event
        self.interval = interval
        self.signals = StatsWorkerSignals()

    def run(self):
        while not self.stop_event.is_set():
            self.signals.stats.emit(self.aggregate.snapshot_total())
            self.signals.per_module.emit(self.aggregate.snapshot_all())
            time.sleep(self.interval)
