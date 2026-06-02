import threading
import time

from PyQt6.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
)

from core.test_context import TestContext
from modules.base import BaseTestModule
from ui.com_port_widget import ComPortWidget


class StreamViewModule(BaseTestModule):
    name = "开流"
    module_id = "stream_view"
    description = "通过Appium打开设备实时画面(开流)，验证视频流加载稳定性"

    def __init__(self):
        super().__init__()
        self._widget = None
        self._cpu_port = None
        self._wifi_port = None
        self._device_name = None
        self._stream_wait = None
        self._cooldown = None
        self._wired_device = None
        self._cold_start = None
        self._loops = None
        self._saved_config = {
            "cpu_port": "", "cpu_baudrate": 115200,
            "wifi_port": "", "wifi_baudrate": 115200,
            "device_name": "",
            "stream_wait": 20.0,
            "cooldown": 40.0,
            "wired_device": False,
            "cold_start": False,
            "loops": 50,
        }

    def create_config_widget(self) -> QWidget:
        w = QWidget()
        layout = QFormLayout(w)

        self._cpu_port = ComPortWidget()
        layout.addRow("CPU串口:", self._cpu_port)
        self._wifi_port = ComPortWidget()
        layout.addRow("WiFi串口:", self._wifi_port)

        self._device_name = QLineEdit("")
        self._device_name.setPlaceholderText("App中显示的设备名称")
        layout.addRow("设备名称:", self._device_name)

        self._stream_wait = QDoubleSpinBox()
        self._stream_wait.setRange(1.0, 120.0)
        self._stream_wait.setValue(20.0)
        self._stream_wait.setSuffix(" s")
        layout.addRow("开流等待:", self._stream_wait)

        self._cooldown = QDoubleSpinBox()
        self._cooldown.setRange(1.0, 300.0)
        self._cooldown.setValue(40.0)
        self._cooldown.setSuffix(" s")
        layout.addRow("冷却等待:", self._cooldown)

        self._wired_device = QCheckBox("长电/套包设备")
        layout.addRow("", self._wired_device)

        self._cold_start = QCheckBox("每轮冷启动App")
        layout.addRow("", self._cold_start)

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
                "device_name": self._device_name.text(),
                "stream_wait": self._stream_wait.value(),
                "cooldown": self._cooldown.value(),
                "wired_device": self._wired_device.isChecked(),
                "cold_start": self._cold_start.isChecked(),
                "loops": self._loops.value(),
            }
        except RuntimeError:
            pass
        return dict(self._saved_config)

    def set_default_config(self):
        if self._device_name:
            self._device_name.setText("")
        if self._stream_wait:
            self._stream_wait.setValue(20.0)
        if self._cooldown:
            self._cooldown.setValue(40.0)
        if self._wired_device:
            self._wired_device.setChecked(False)
        if self._loops:
            self._loops.setValue(50)

    def run(self, ctx: TestContext, config: dict,
            stop_event: threading.Event, log, serial_log, record):
        cpu_port = config.get("cpu_port", "")
        cpu_baud = config.get("cpu_baudrate", 115200)
        wifi_port = config.get("wifi_port", "")
        wifi_baud = config.get("wifi_baudrate", 115200)
        device_name = config.get("device_name", "")
        stream_wait = config.get("stream_wait", 20.0)
        cooldown = config.get("cooldown", 40.0)
        wired_device = config.get("wired_device", False)
        cold_start = config.get("cold_start", False)
        loops = config.get("loops", 50)

        driver = ctx.appium.driver
        if not driver:
            log("Appium not connected (设置 → Appium设置)", "error")
            return

        if not device_name:
            log("Device name not configured", "error")
            return

        cpu = self._open_serial_port(cpu_port, cpu_baud)
        wifi = self._open_serial_port(wifi_port, wifi_baud)

        try:
            for i in range(loops):
                if stop_event.is_set():
                    log(f"Loop {i}: stopped by user", "warning")
                    break

                # Cold start: restart app
                if cold_start and ctx.appium.check_alive():
                    try:
                        driver.terminate_app("com.glazero.android")
                        time.sleep(3)
                        driver.activate_app("com.glazero.android")
                        time.sleep(5)
                        log(f"Loop {i}: cold start done", "info")
                    except Exception as e:
                        log(f"Loop {i}: cold start failed: {e}", "warning")

                t0 = time.perf_counter()

                try:
                    from appium.webdriver.common.appiumby import AppiumBy

                    log(f"Loop {i}: looking for device '{device_name}'...", "info")
                    device_el = driver.find_element(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        f'new UiScrollable(new UiSelector().scrollable(true)).scrollIntoView(new UiSelector().text("{device_name}"))'
                    )
                    device_el.click()
                    log(f"Loop {i}: stream opening, waiting {stream_wait}s...", "info")
                    time.sleep(stream_wait)

                    try:
                        driver.find_element(AppiumBy.ID, 'com.glazero.android:id/btn_back')
                        log(f"Loop {i}: stream page loaded", "info")
                    except Exception:
                        log(f"Loop {i}: stream page may not have loaded", "warning")

                    driver.find_element(AppiumBy.ID, 'com.glazero.android:id/btn_back').click()
                    log(f"Loop {i}: back to home", "info")

                    success = True

                except Exception as e:
                    success = False
                    log(f"Loop {i}: error → {e}", "error")
                    try:
                        driver.find_element(AppiumBy.ID, 'com.glazero.android:id/btn_back').click()
                    except Exception:
                        pass

                latency_ms = (time.perf_counter() - t0) * 1000
                record(success, latency_ms)

                if i < loops - 1 and not stop_event.is_set():
                    cd = 130.0 if wired_device else cooldown
                    log(f"Loop {i}: waiting {cd}s for device cooldown...", "info")
                    time.sleep(cd)

        finally:
            if cpu:
                cpu.close()
            if wifi:
                wifi.close()
