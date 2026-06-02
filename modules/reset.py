import threading
import time

from PyQt6.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
)

from core.test_context import TestContext
from modules.base import BaseTestModule
from ui.com_port_widget import ComPortWidget


class ResetModule(BaseTestModule):
    name = "RESET"
    module_id = "reset"
    description = "通过Appium点击设备复位按钮，验证复位后App恢复正常"

    def __init__(self):
        super().__init__()
        self._widget = None
        self._cpu_port = None
        self._wifi_port = None
        self._reset_element = None
        self._confirm_element = None
        self._app_wait = None
        self._loops = None
        self._saved_config = {
            "cpu_port": "", "cpu_baudrate": 115200,
            "wifi_port": "", "wifi_baudrate": 115200,
            "reset_element": "//*[@text='Reset']",
            "confirm_element": "//*[@text='OK']",
            "app_wait": 10.0, "loops": 50,
        }

    def create_config_widget(self) -> QWidget:
        w = QWidget()
        layout = QFormLayout(w)
        self._cpu_port = ComPortWidget()
        layout.addRow("CPU串口:", self._cpu_port)
        self._wifi_port = ComPortWidget()
        layout.addRow("WiFi串口:", self._wifi_port)
        self._reset_element = QLineEdit("//*[@text='Reset']")
        layout.addRow("复位按钮(XPath):", self._reset_element)
        self._confirm_element = QLineEdit("//*[@text='OK']")
        layout.addRow("确认弹窗按钮:", self._confirm_element)
        self._app_wait = QDoubleSpinBox()
        self._app_wait.setRange(1.0, 120.0)
        self._app_wait.setValue(10.0)
        self._app_wait.setSuffix(" s")
        layout.addRow("App恢复等待:", self._app_wait)
        self._loops = QSpinBox()
        self._loops.setRange(1, 100000)
        self._loops.setValue(50)
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
                "reset_element": self._reset_element.text(),
                "confirm_element": self._confirm_element.text(),
                "app_wait": self._app_wait.value(),
                "loops": self._loops.value(),
            }
        except RuntimeError:
            pass
        return dict(self._saved_config)

    def set_default_config(self):
        if self._reset_element:
            self._reset_element.setText("//*[@text='Reset']")
        if self._confirm_element:
            self._confirm_element.setText("//*[@text='OK']")
        if self._app_wait:
            self._app_wait.setValue(10.0)
        if self._loops:
            self._loops.setValue(50)

    def run(self, ctx: TestContext, config: dict,
            stop_event: threading.Event, log, serial_log, record):
        cpu_port = config.get("cpu_port", "")
        cpu_baud = config.get("cpu_baudrate", 115200)
        wifi_port = config.get("wifi_port", "")
        wifi_baud = config.get("wifi_baudrate", 115200)
        reset_xpath = config.get("reset_element", "//*[@text='Reset']")
        confirm_xpath = config.get("confirm_element", "//*[@text='OK']")
        app_wait = config.get("app_wait", 10.0)
        loops = config.get("loops", 50)

        driver = ctx.appium.driver
        if not driver:
            log("Appium not connected", "error")
            return

        cpu = self._open_serial_port(cpu_port, cpu_baud)
        wifi = self._open_serial_port(wifi_port, wifi_baud)

        try:
            for i in range(loops):
                if stop_event.is_set():
                    log(f"Loop {i}: stopped by user", "warning")
                    break

                t0 = time.perf_counter()
                try:
                    el = driver.find_element("xpath", reset_xpath)
                    el.click()
                    log(f"Loop {i}: clicked reset button", "info")
                    time.sleep(1.0)
                    try:
                        driver.find_element("xpath", confirm_xpath).click()
                        log(f"Loop {i}: confirmed reset dialog", "info")
                    except Exception:
                        pass

                    time.sleep(app_wait)
                    driver.find_element("xpath", "//*")
                    log(f"Loop {i}: app recovered OK", "info")

                    # CPU serial verification
                    cpu_ok = True
                    if cpu:
                        _, cpu_ok = self._send_and_wait(cpu, b"AT\r\n", timeout=3.0)
                        serial_log(f"Loop {i}: CPU check → {'OK' if cpu_ok else 'NO RESPONSE'}", "info" if cpu_ok else "error")

                    success = True
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
