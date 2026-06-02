import threading
import time
from collections import defaultdict

from PyQt6.QtCore import QObject, pyqtSignal, QThreadPool

from core.test_context import TestContext
from core.metrics import AggregateMetrics
from modules.base import BaseTestModule
from workers.module_worker import ModuleWorker
from workers.stats_worker import StatsWorker


class TestRunnerSignals(QObject):
    all_done = pyqtSignal()
    worker_finished = pyqtSignal(str)
    log = pyqtSignal(str, str)
    serial = pyqtSignal(str, str)


class TestRunner(QObject):
    def __init__(self, ctx: TestContext):
        super().__init__()
        self.ctx = ctx
        self.stop_event = threading.Event()
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(50)
        self.aggregate = AggregateMetrics()
        self.signals = TestRunnerSignals()
        self._workers: list[ModuleWorker] = []
        self._stats_worker: StatsWorker | None = None
        self._group_done_event: threading.Event | None = None

    def start(self, modules: list[tuple[BaseTestModule, int, dict]]):
        """modules: list of (module_instance, group_number, config_dict)"""
        self.stop_event.clear()
        self.aggregate.clear()
        self._workers.clear()

        # Group modules by group number
        groups: dict[int, list[tuple[BaseTestModule, dict]]] = defaultdict(list)
        for mod, grp, cfg in modules:
            groups[grp].append((mod, cfg))

        sorted_groups = sorted(groups.items())

        # Start stats worker
        self._stats_worker = StatsWorker(self.aggregate, self.stop_event)
        self.threadpool.start(self._stats_worker)

        # Process groups sequentially
        def _run_groups():
            for group_num, mod_list in sorted_groups:
                if self.stop_event.is_set():
                    break
                self.signals.log.emit(f"--- Group {group_num} starting ({len(mod_list)} modules) ---", "info")
                workers_in_group = []
                pending = len(mod_list)
                done_event = threading.Event()

                def _on_finished(mid: str):
                    nonlocal pending
                    pending -= 1
                    self.signals.worker_finished.emit(mid)
                    if pending <= 0:
                        done_event.set()

                for mod, cfg in mod_list:
                    if self.stop_event.is_set():
                        break
                    worker = ModuleWorker(mod, self.ctx, cfg, self.stop_event)
                    worker.signals.log.connect(self.signals.log.emit)
                    worker.signals.serial.connect(self.signals.serial.emit)
                    worker.signals.finished.connect(_on_finished)
                    worker.signals.error.connect(
                        lambda mid, err: self.signals.log.emit(f"[{mid}] ERROR: {err}", "error")
                    )

                    def _on_result(mid, ok, lat):
                        mc = self.aggregate.get(mid)
                        if mc:
                            mc.record(ok, lat)

                    worker.signals.result.connect(_on_result)
                    self.aggregate.add(mod.module_id)
                    workers_in_group.append(worker)
                    self._workers.append(worker)
                    self.threadpool.start(worker)

                # Wait for all workers in this group to finish
                self._group_done_event = done_event
                while not done_event.is_set() and not self.stop_event.is_set():
                    done_event.wait(0.5)
                self._group_done_event = None

            self.stop_event.set()
            self.signals.all_done.emit()

        threading.Thread(target=_run_groups, daemon=True).start()

    def stop(self):
        self.stop_event.set()
        if self._group_done_event:
            self._group_done_event.set()

    def get_stats_worker(self) -> StatsWorker | None:
        return self._stats_worker
