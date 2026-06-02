import threading
import time


class MetricsCollector:
    def __init__(self, name: str = ""):
        self.name = name
        self._lock = threading.Lock()
        self._start_time = 0.0
        self.reset()

    def reset(self):
        with self._lock:
            self.total = 0
            self.success = 0
            self.fail = 0
            self.total_latency_ms = 0.0
            self.min_latency_ms = float("inf")
            self.max_latency_ms = 0.0
            self._start_time = time.perf_counter()

    def record(self, success: bool, latency_ms: float):
        with self._lock:
            self.total += 1
            self.total_latency_ms += latency_ms
            if latency_ms < self.min_latency_ms:
                self.min_latency_ms = latency_ms
            if latency_ms > self.max_latency_ms:
                self.max_latency_ms = latency_ms
            if success:
                self.success += 1
            else:
                self.fail += 1

    def snapshot(self) -> dict:
        with self._lock:
            elapsed = time.perf_counter() - self._start_time
            if self.total == 0:
                return {
                    "name": self.name,
                    "total": 0, "success": 0, "fail": 0,
                    "success_rate": 0.0, "tps": 0.0,
                    "avg_latency_ms": 0.0, "min_latency_ms": 0.0,
                    "max_latency_ms": 0.0, "elapsed_s": elapsed,
                }
            return {
                "name": self.name,
                "total": self.total,
                "success": self.success,
                "fail": self.fail,
                "success_rate": self.success / self.total * 100,
                "tps": self.total / elapsed if elapsed > 0 else 0.0,
                "avg_latency_ms": self.total_latency_ms / self.total,
                "min_latency_ms": self.min_latency_ms,
                "max_latency_ms": self.max_latency_ms,
                "elapsed_s": elapsed,
            }


class AggregateMetrics:
    def __init__(self):
        self._collectors: dict[str, MetricsCollector] = {}
        self._start_time = 0.0

    def add(self, name: str) -> MetricsCollector:
        mc = MetricsCollector(name)
        self._collectors[name] = mc
        if not self._collectors or self._start_time == 0.0:
            self._start_time = time.perf_counter()
        return mc

    def get(self, name: str) -> MetricsCollector | None:
        return self._collectors.get(name)

    def remove(self, name: str):
        self._collectors.pop(name, None)

    def clear(self):
        self._collectors.clear()
        self._start_time = 0.0

    def snapshot_all(self) -> list[dict]:
        return [mc.snapshot() for mc in self._collectors.values()]

    def snapshot_total(self) -> dict:
        total = 0
        success = 0
        fail = 0
        total_lat = 0.0
        min_lat = float("inf")
        max_lat = 0.0
        for mc in self._collectors.values():
            s = mc.snapshot()
            total += s["total"]
            success += s["success"]
            fail += s["fail"]
            total_lat += s["avg_latency_ms"] * s["total"]
            if s["min_latency_ms"] < min_lat:
                min_lat = s["min_latency_ms"]
            if s["max_latency_ms"] > max_lat:
                max_lat = s["max_latency_ms"]
        elapsed = time.perf_counter() - self._start_time if self._start_time > 0 else 0.0
        if total == 0:
            return {"total": 0, "success": 0, "fail": 0, "success_rate": 0.0,
                    "tps": 0.0, "avg_latency_ms": 0.0, "min_latency_ms": 0.0,
                    "max_latency_ms": 0.0, "elapsed_s": elapsed}
        return {
            "total": total, "success": success, "fail": fail,
            "success_rate": success / total * 100 if total > 0 else 0.0,
            "tps": total / elapsed if elapsed > 0 else 0.0,
            "avg_latency_ms": total_lat / total,
            "min_latency_ms": min_lat if min_lat != float("inf") else 0.0,
            "max_latency_ms": max_lat,
            "elapsed_s": elapsed,
        }
