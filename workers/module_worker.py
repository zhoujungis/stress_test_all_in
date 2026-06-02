import threading
import time

from PyQt6.QtCore import QRunnable, QObject, pyqtSignal

from core.test_context import TestContext
from modules.base import BaseTestModule


class ModuleWorkerSignals(QObject):
    log = pyqtSignal(str, str)
    serial = pyqtSignal(str, str)
    result = pyqtSignal(str, bool, float)
    finished = pyqtSignal(str)
    error = pyqtSignal(str, str)


class ModuleWorker(QRunnable):
    def __init__(self, module: BaseTestModule, ctx: TestContext,
                 config: dict, stop_event: threading.Event):
        super().__init__()
        self.module = module
        self.ctx = ctx
        self.config = config
        self.stop_event = stop_event
        self.signals = ModuleWorkerSignals()
        self._start_time = 0.0

    @property
    def module_id(self) -> str:
        return self.module.module_id

    @property
    def elapsed(self) -> float:
        if self._start_time == 0:
            return 0
        return time.perf_counter() - self._start_time

    def run(self):
        self._start_time = time.perf_counter()

        def log_cb(msg: str, level: str = "info"):
            self.signals.log.emit(f"[{self.module.name}] {msg}", level)

        def serial_cb(msg: str, level: str = "info"):
            self.signals.serial.emit(f"[{self.module.name}] {msg}", level)

        def record_cb(success: bool, latency_ms: float):
            self.signals.result.emit(self.module.module_id, success, latency_ms)

        try:
            self.module.run(self.ctx, self.config, self.stop_event, log_cb, serial_cb, record_cb)
        except Exception as e:
            self.signals.error.emit(self.module.module_id, str(e))
        finally:
            self.signals.finished.emit(self.module.module_id)
