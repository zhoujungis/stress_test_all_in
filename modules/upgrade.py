import threading
import time

from PyQt6.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
)

from core.test_context import TestContext
from modules.base import BaseTestModule
from ui.com_port_widget import ComPortWidget


class UpgradeModule(BaseTestModule):
    name = "升级"
    module_id = "upgrade"
    description = "通过云平台下发OTA升级指令，串口验证设备升级状态"

    def __init__(self):
        super().__init__()
        self._widget = None
        self._cpu_port = None
        self._wifi_port = None
        self._device_sn = None
        self._target_version = None
        self._ota_timeout = None
        self._loops = None
        self._saved_config = {
            "cpu_port": "", "cpu_baudrate": 115200,
            "wifi_port": "", "wifi_baudrate": 115200,
            "device_sn": "",
            "target_version": "",
            "ota_timeout": 300.0, "loops": 100,
        }

    def create_config_widget(self) -> QWidget:
        w = QWidget()
        layout = QFormLayout(w)

        self._cpu_port = ComPortWidget()
        layout.addRow("CPU串口:", self._cpu_port)
        self._wifi_port = ComPortWidget()
        layout.addRow("WiFi串口:", self._wifi_port)

        self._device_sn = QLineEdit("")
        self._device_sn.setPlaceholderText("设备序列号")
        layout.addRow("设备SN:", self._device_sn)

        self._target_version = QLineEdit("")
        self._target_version.setPlaceholderText("目标固件版本，留空则升到最新")
        layout.addRow("目标版本:", self._target_version)

        self._ota_timeout = QDoubleSpinBox()
        self._ota_timeout.setRange(10.0, 600.0)
        self._ota_timeout.setValue(300.0)
        self._ota_timeout.setSuffix(" s")
        layout.addRow("升级超时:", self._ota_timeout)

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
                "device_sn": self._device_sn.text(),
                "target_version": self._target_version.text(),
                "ota_timeout": self._ota_timeout.value(),
                "loops": self._loops.value(),
            }
        except RuntimeError:
            pass
        return dict(self._saved_config)

    def set_default_config(self):
        if self._device_sn:
            self._device_sn.setText("")
        if self._target_version:
            self._target_version.setText("")
        if self._ota_timeout:
            self._ota_timeout.setValue(300.0)
        if self._loops:
            self._loops.setValue(100)

    def run(self, ctx: TestContext, config: dict,
            stop_event: threading.Event, log, serial_log, record):
        cpu_port = config.get("cpu_port", "")
        cpu_baud = config.get("cpu_baudrate", 115200)
        wifi_port = config.get("wifi_port", "")
        wifi_baud = config.get("wifi_baudrate", 115200)
        device_sn = config.get("device_sn", "")
        target_version = config.get("target_version", "")
        ota_timeout = config.get("ota_timeout", 300.0)
        loops = config.get("loops", 100)

        cloud = ctx.cloud
        if not cloud.is_logged_in():
            log("Cloud not logged in (设置 → 云端设置)", "error")
            return
        if not device_sn:
            log("Device SN not configured", "error")
            return

        cpu = self._open_serial_port(cpu_port, cpu_baud)
        wifi = self._open_serial_port(wifi_port, wifi_baud)

        try:
            for i in range(loops):
                if stop_event.is_set():
                    log(f"[{i}] stopped by user", "warning")
                    break

                t0 = time.perf_counter()

                # Trigger OTA via cloud
                result = cloud.trigger_ota(device_sn, target_version)
                if not result.get("success"):
                    log(f"[{i}] OTA trigger failed → {result.get('error', '')}", "error")
                    record(False, (time.perf_counter() - t0) * 1000)
                    time.sleep(5)
                    continue

                log(f"[{i}] OTA triggered, waiting {ota_timeout}s...", "info")

                # Wait for OTA to complete (device will reboot)
                deadline = time.perf_counter() + ota_timeout
                success = False
                while time.perf_counter() < deadline and not stop_event.is_set():
                    if cpu:
                        resp, ok = self._send_and_wait(cpu, b"AT+VERSION?\r\n", timeout=5.0)
                        if ok:
                            success = True
                            serial_log(f"[{i}] device back online, version: {resp.decode(errors='ignore')[:80]}", "info")
                            break
                    time.sleep(5)

                if not success:
                    log(f"[{i}] OTA timeout — device did not come back", "error")

                latency_ms = (time.perf_counter() - t0) * 1000
                record(success, latency_ms)

                if i < loops - 1 and not stop_event.is_set():
                    time.sleep(5)

        finally:
            if cpu:
                cpu.close()
            if wifi:
                wifi.close()
