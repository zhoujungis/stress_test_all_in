import os
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPlainTextEdit, QLabel,
)
from PyQt6.QtGui import QTextCharFormat, QColor, QFont
from PyQt6.QtCore import pyqtSlot, Qt


LEVEL_COLORS = {
    "info": QColor("#e0e0e0"),
    "debug": QColor("#888888"),
    "warning": QColor("#e5c07b"),
    "error": QColor("#e06c75"),
    "success": QColor("#98c379"),
}


class LogPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._log_entries: dict[str, list[tuple[str, str, str]]] = {}
        self._analysis_entries: dict[str, list[str]] = {}
        self._current_filter: str = ""
        self._project_name = "stress"
        self._tester = "tester"
        self._build()

    def set_project_info(self, project_name: str, tester: str):
        self._project_name = project_name or "stress"
        self._tester = tester or "tester"

    def _log_path(self, base_dir: str, module: str) -> str:
        now = datetime.now()
        prefix = f"{self._project_name}-{self._tester}"
        ts = now.strftime("%Y%m%d_%H%M%S")
        name = f"{prefix}_{ts}.log"
        d = os.path.join(base_dir, module)
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, name)

    def _write_file(self, base_dir: str, module: str, message: str):
        try:
            now = datetime.now()
            ts = now.strftime("%Y-%m-%d %H:%M:%S.") + f"{now.microsecond // 1000:03d}"
            path = self._log_path(base_dir, module)
            with open(path, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] {message}\n")
        except Exception:
            pass

    def init_log_dirs(self):
        modules = ["开关机", "RESET", "绑定解绑", "升级", "休眠唤醒", "开流"]
        for base in ["serial_logs", "run_logs"]:
            for m in modules:
                os.makedirs(os.path.join(base, m), exist_ok=True)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        lw = QWidget()
        ll = QVBoxLayout(lw)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(1)
        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumBlockCount(5000)
        self._log.setFont(QFont("Consolas", 10))
        ll.addWidget(self._log, 1)
        ll.addWidget(QLabel("日志"), 0, Qt.AlignmentFlag.AlignCenter)
        splitter.addWidget(lw)

        rw = QWidget()
        rl = QVBoxLayout(rw)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(1)
        self._analysis = QPlainTextEdit()
        self._analysis.setReadOnly(True)
        self._analysis.setMaximumBlockCount(500)
        self._analysis.setFont(QFont("Consolas", 10))
        rl.addWidget(self._analysis, 1)
        rl.addWidget(QLabel("分析"), 0, Qt.AlignmentFlag.AlignCenter)
        splitter.addWidget(rw)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, 1)

        bot = QHBoxLayout()
        self._status_label = QLabel("就绪")
        bot.addWidget(self._status_label)
        bot.addStretch()
        bot.addWidget(QLabel("Copyright © 深圳致翎科技有限公司"))
        bot.addStretch()
        self._filter_label = QLabel("")
        bot.addWidget(self._filter_label)
        layout.addLayout(bot)

    def set_filter(self, module_id: str, module_name: str = ""):
        self._current_filter = module_id
        self._filter_label.setText(f"查看: {module_name}" if module_name else "")
        self._redraw()

    def _redraw(self):
        self._log.clear()
        self._analysis.clear()
        filt = self._current_filter
        for mid, entries in self._log_entries.items():
            if not filt or mid == filt:
                for ts, msg, level in entries:
                    color = LEVEL_COLORS.get(level, QColor("#e0e0e0"))
                    fmt = QTextCharFormat()
                    fmt.setForeground(color)
                    self._log.mergeCurrentCharFormat(fmt)
                    self._log.appendPlainText(f"[{ts}] {msg}")
        for mid, lines in self._analysis_entries.items():
            if not filt or mid == filt:
                for line in lines:
                    self._analysis.appendPlainText(line)

    @pyqtSlot(str, str)
    def append(self, message: str, level: str = "info"):
        self._append_log("run_logs", message, level)

    @pyqtSlot(str, str)
    def append_serial(self, message: str, level: str = "info"):
        self._append_log("serial_logs", message, level)

    def _append_log(self, base_dir: str, message: str, level: str):
        ts = datetime.now().strftime("%H:%M:%S")
        module = ""
        if message.startswith("[") and "]" in message:
            module = message[1:].split("]")[0]

        if module:
            if module not in self._log_entries:
                self._log_entries[module] = []
            self._log_entries[module].append((ts, message, level))
            self._write_file(base_dir, module, message)

        filt = self._current_filter
        if not filt or filt == module:
            color = LEVEL_COLORS.get(level, QColor("#e0e0e0"))
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            self._log.mergeCurrentCharFormat(fmt)
            self._log.appendPlainText(f"[{ts}] {message}")

    def _on_clear(self):
        self._log.clear()
        self._analysis.clear()
        self._log_entries.clear()
        self._analysis_entries.clear()

    def set_status(self, text: str):
        self._status_label.setText(text)

    def set_stats(self, total: int, success: int, fail: int):
        rate = f"{success / total * 100:.1f}%" if total > 0 else "—"
        self._status_label.setText(f"共{total}次 通过{success} 失败{fail} 成功率{rate}")

    def update_analysis(self, per_module: list):
        now = datetime.now()
        ts = now.strftime("%H:%M:%S")
        for m in per_module:
            if m["total"] == 0:
                continue
            mid = m.get("name", "?")
            line = (
                f"[{ts}] {mid}: 共{m['total']} 通过{m['success']} 失败{m['fail']} "
                f"成功率{m['success_rate']:.1f}%  TPS:{m['tps']:.1f}  avg:{m['avg_latency_ms']:.0f}ms"
            )
            if mid not in self._analysis_entries:
                self._analysis_entries[mid] = []
            self._analysis_entries[mid].append(line)
            filt = self._current_filter
            if not filt or filt == mid:
                self._analysis.appendPlainText(line)
            self._write_file("run_logs", mid, line)
