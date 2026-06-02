import threading
import time

from PyQt6.QtWidgets import (
    QWidget, QFormLayout, QSpinBox, QDoubleSpinBox,
)

from core.test_context import TestContext
from modules.base import BaseTestModule
from ui.com_port_widget import ComPortWidget


class PowerCycleModule(BaseTestModule):
    name = "开关机"
    module_id = "power_cycle"
    description = "通过继电器控制设备电源通断，验证开关机稳定性"

    def __init__(self):
        super().__init__()
        self._widget = None
        self._cpu_port = None
        self._wifi_port = None
        self._relay_channel = None
        self._open_duration = None
        self._close_duration = None
        self._test_count = None
        self._boot_wait = None
        self._saved_config = {
            "cpu_port": "", "cpu_baudrate": 115200,
            "wifi_port": "", "wifi_baudrate": 115200,
            "relay_channel": 1,
            "open_duration": 1.0, "close_duration": 2.0,
            "test_count": 100,
            "boot_wait": 5.0,
        }

    def create_config_widget(self) -> QWidget:
        w = QWidget()
        layout = QFormLayout(w)

        self._cpu_port = ComPortWidget()
        layout.addRow("CPU串口:", self._cpu_port)
        self._wifi_port = ComPortWidget()
        layout.addRow("WiFi串口:", self._wifi_port)

        self._relay_channel = QSpinBox()
        self._relay_channel.setRange(1, 4)
        self._relay_channel.setValue(1)
        layout.addRow("继电器通道:", self._relay_channel)

        self._open_duration = QDoubleSpinBox()
        self._open_duration.setRange(0.001, 99999.0)
        self._open_duration.setDecimals(3)
        self._open_duration.setValue(1.0)
        self._open_duration.setSuffix(" s")
        layout.addRow("通电时长:", self._open_duration)

        self._close_duration = QDoubleSpinBox()
        self._close_duration.setRange(0.001, 99999.0)
        self._close_duration.setDecimals(3)
        self._close_duration.setValue(2.0)
        self._close_duration.setSuffix(" s")
        layout.addRow("断电时长:", self._close_duration)

        self._test_count = QSpinBox()
        self._test_count.setRange(1, 100000)
        self._test_count.setValue(100)
        layout.addRow("循环次数:", self._test_count)

        self._boot_wait = QDoubleSpinBox()
        self._boot_wait.setRange(0.5, 120.0)
        self._boot_wait.setValue(5.0)
        self._boot_wait.setSuffix(" s")
        layout.addRow("开机等待:", self._boot_wait)

        self._widget = w
        return w

    def get_config(self) -> dict:
        try:
            self._saved_config = {
                "cpu_port": self._cpu_port.get_port(),
                "cpu_baudrate": self._cpu_port.get_baudrate(),
                "wifi_port": self._wifi_port.get_port(),
                "wifi_baudrate": self._wifi_port.get_baudrate(),
                "relay_channel": self._relay_channel.value(),
                "open_duration": self._open_duration.value(),
                "close_duration": self._close_duration.value(),
                "test_count": self._test_count.value(),
                "boot_wait": self._boot_wait.value(),
            }
        except RuntimeError:
            pass
        return dict(self._saved_config)

    def set_default_config(self):
        if self._relay_channel:
            self._relay_channel.setValue(1)
        if self._open_duration:
            self._open_duration.setValue(1.0)
        if self._close_duration:
            self._close_duration.setValue(2.0)
        if self._test_count:
            self._test_count.setValue(100)
        if self._boot_wait:
            self._boot_wait.setValue(5.0)

    def run(self, ctx: TestContext, config: dict,
            stop_event: threading.Event, log, serial_log, record):
        cpu_port = config.get("cpu_port", "")
        cpu_baud = config.get("cpu_baudrate", 115200)
        wifi_port = config.get("wifi_port", "")
        wifi_baud = config.get("wifi_baudrate", 115200)
        relay_ch = config.get("relay_channel", 1)
        open_dur = config.get("open_duration", 1.0)
        close_dur = config.get("close_duration", 2.0)
        test_count = config.get("test_count", 100)
        boot_wait = config.get("boot_wait", 5.0)

        relay = ctx.relay
        if not relay.is_connected():
            log("Relay not connected (设置 → 继电器设置)", "error")
            return

        cpu = self._open_serial_port(cpu_port, cpu_baud)
        wifi = self._open_serial_port(wifi_port, wifi_baud)

        try:
            for i in range(test_count):
                if stop_event.is_set():
                    log(f"[{i}] stopped by user", "warning")
                    break

                t0 = time.perf_counter()

                relay.channel_off(relay_ch)
                log(f"[{i}] ch{relay_ch} OFF", "info")
                time.sleep(close_dur)

                relay.channel_on(relay_ch)
                log(f"[{i}] ch{relay_ch} ON, {open_dur}s", "info")
                time.sleep(open_dur)

                success = True
                if cpu:
                    _, success = self._send_and_wait(cpu, b"AT\r\n", timeout=boot_wait)
                    serial_log(f"[{i}] boot → {'OK' if success else 'NO RESPONSE'}", "info" if success else "error")

                if wifi and success:
                    _, wifi_ok = self._send_and_wait(wifi, b"AT+WIFI?\r\n", timeout=5.0)
                    serial_log(f"[{i}] WiFi → {'OK' if wifi_ok else 'FAIL'}", "info" if wifi_ok else "error")

                latency_ms = (time.perf_counter() - t0) * 1000
                record(success, latency_ms)

        finally:
            if cpu:
                cpu.close()
            if wifi:
                wifi.close()
            relay.channel_off(relay_ch)
