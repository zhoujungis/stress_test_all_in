import threading
import time

from PyQt6.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
)

from core.test_context import TestContext
from modules.base import BaseTestModule
from ui.com_port_widget import ComPortWidget


class SleepWakeModule(BaseTestModule):
    name = "休眠唤醒"
    module_id = "sleep_wake"
    description = "反复让设备进入休眠并唤醒，验证低功耗模式稳定性"

    def __init__(self):
        super().__init__()
        self._widget = None
        self._cpu_port = None
        self._wifi_port = None
        self._sleep_cmd = None
        self._wake_method = None
        self._wake_cmd = None
        self._sleep_duration = None
        self._wake_delay = None
        self._loops = None
        self._saved_config = {
            "cpu_port": "", "cpu_baudrate": 115200,
            "wifi_port": "", "wifi_baudrate": 115200,
            "sleep_cmd": "AT+SLEEP", "wake_method": "RTS",
            "wake_cmd": "AT", "sleep_duration": 5.0,
            "wake_delay": 2.0, "loops": 100,
        }

    def create_config_widget(self) -> QWidget:
        w = QWidget()
        layout = QFormLayout(w)

        self._cpu_port = ComPortWidget()
        layout.addRow("CPU串口:", self._cpu_port)
        self._wifi_port = ComPortWidget()
        layout.addRow("WiFi串口:", self._wifi_port)

        self._sleep_cmd = QLineEdit("AT+SLEEP")
        layout.addRow("休眠命令:", self._sleep_cmd)
        self._wake_method = QComboBox()
        self._wake_method.addItems(["RTS", "DTR", "AT Command"])
        layout.addRow("唤醒方式:", self._wake_method)
        self._wake_cmd = QLineEdit("AT")
        layout.addRow("唤醒命令:", self._wake_cmd)
        self._sleep_duration = QDoubleSpinBox()
        self._sleep_duration.setRange(0.5, 300.0)
        self._sleep_duration.setValue(5.0)
        self._sleep_duration.setSuffix(" s")
        layout.addRow("休眠时长:", self._sleep_duration)
        self._wake_delay = QDoubleSpinBox()
        self._wake_delay.setRange(0.1, 60.0)
        self._wake_delay.setValue(2.0)
        self._wake_delay.setSuffix(" s")
        layout.addRow("唤醒后等待:", self._wake_delay)
        self._loops = QSpinBox()
        self._loops.setRange(1, 100000)
        self._loops.setValue(100)
        layout.addRow("循环次数:", self._loops)
        self._widget = w
        return w

    def get_config(self) -> dict:
        try:
            self._saved_config = {
                "cpu_port": self._cpu_port.get_port(),
                "cpu_baudrate": self._cpu_port.get_baudrate(),
                "wifi_port": self._wifi_port.get_port(),
                "wifi_baudrate": self._wifi_port.get_baudrate(),
                "sleep_cmd": self._sleep_cmd.text(),
                "wake_method": self._wake_method.currentText(),
                "wake_cmd": self._wake_cmd.text(),
                "sleep_duration": self._sleep_duration.value(),
                "wake_delay": self._wake_delay.value(),
                "loops": self._loops.value(),
            }
        except RuntimeError:
            pass
        return dict(self._saved_config)

    def set_default_config(self):
        if self._sleep_cmd:
            self._sleep_cmd.setText("AT+SLEEP")
        if self._wake_method:
            self._wake_method.setCurrentIndex(0)
        if self._wake_cmd:
            self._wake_cmd.setText("AT")
        if self._sleep_duration:
            self._sleep_duration.setValue(5.0)
        if self._wake_delay:
            self._wake_delay.setValue(2.0)
        if self._loops:
            self._loops.setValue(100)

    def run(self, ctx: TestContext, config: dict,
            stop_event: threading.Event, log, serial_log, record):
        cpu_port = config.get("cpu_port", "")
        cpu_baud = config.get("cpu_baudrate", 115200)
        wifi_port = config.get("wifi_port", "")
        wifi_baud = config.get("wifi_baudrate", 115200)
        sleep_cmd = config.get("sleep_cmd", "AT+SLEEP")
        wake_method = config.get("wake_method", "RTS")
        wake_cmd = config.get("wake_cmd", "AT")
        sleep_duration = config.get("sleep_duration", 5.0)
        wake_delay = config.get("wake_delay", 2.0)
        loops = config.get("loops", 100)

        cpu = self._open_serial_port(cpu_port, cpu_baud)
        wifi = self._open_serial_port(wifi_port, wifi_baud)

        if not cpu and not wifi:
            log("No serial port configured", "error")
            return

        try:
            for i in range(loops):
                if stop_event.is_set():
                    log(f"Loop {i}: stopped by user", "warning")
                    break

                t0 = time.perf_counter()
                try:
                    if cpu:
                        cpu.write(sleep_cmd.encode("utf-8"))
                    log(f"Loop {i}: sleep cmd sent", "info")
                    time.sleep(sleep_duration)

                    if cpu:
                        if wake_method == "RTS":
                            cpu.rts = False
                            time.sleep(0.1)
                            cpu.rts = True
                        elif wake_method == "DTR":
                            cpu.dtr = False
                            time.sleep(0.1)
                            cpu.dtr = True
                    log(f"Loop {i}: wake via {wake_method}", "info")
                    time.sleep(wake_delay)

                    success = True
                    if cpu:
                        _, success = self._send_and_wait(cpu, wake_cmd.encode("utf-8"), timeout=3.0)
                    serial_log(f"Loop {i}: CPU check → {'OK' if success else 'NO RESPONSE'}", "info" if success else "error")

                    if wifi and success:
                        _, wifi_ok = self._send_and_wait(wifi, b"AT+WIFI?\r\n", timeout=3.0)
                        serial_log(f"Loop {i}: WiFi check → {'OK' if wifi_ok else 'FAIL'}", "info" if wifi_ok else "error")

                except Exception as e:
                    success = False
                    log(f"Loop {i}: error → {e}", "error")

                latency_ms = (time.perf_counter() - t0) * 1000
                record(success, latency_ms)
        finally:
            if cpu:
                cpu.close()
            if wifi:
                wifi.close()
