import threading
import time

from PyQt6.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit,
)

from core.test_context import TestContext
from modules.base import BaseTestModule
from ui.com_port_widget import ComPortWidget


class BindUnbindModule(BaseTestModule):
    name = "绑定解绑"
    module_id = "bind_unbind"
    description = "通过Appium进行BLE扫描绑定+WiFi配网+解绑，验证绑定流程稳定性"

    def __init__(self):
        super().__init__()
        self._widget = None
        self._cpu_port = None
        self._wifi_port = None
        self._device_sns = None
        self._device_names = None
        self._wifi_ssid = None
        self._wifi_password = None
        self._wait = None
        self._loops = None
        self._saved_config = {
            "cpu_port": "", "cpu_baudrate": 115200,
            "wifi_port": "", "wifi_baudrate": 115200,
            "device_sns": "SN001\nSN002",
            "device_names": "Device1\nDevice2",
            "wifi_ssid": "", "wifi_password": "",
            "wait": 5.0, "loops": 30,
        }

    def create_config_widget(self) -> QWidget:
        w = QWidget()
        layout = QFormLayout(w)

        self._cpu_port = ComPortWidget()
        layout.addRow("CPU串口:", self._cpu_port)
        self._wifi_port = ComPortWidget()
        layout.addRow("WiFi串口:", self._wifi_port)

        self._device_sns = QTextEdit()
        self._device_sns.setPlaceholderText("每行一个设备SN")
        self._device_sns.setMaximumHeight(60)
        self._device_sns.setText("SN001\nSN002")
        layout.addRow("设备SN列表:", self._device_sns)

        self._device_names = QTextEdit()
        self._device_names.setPlaceholderText("每行一个设备名，与SN对应")
        self._device_names.setMaximumHeight(60)
        self._device_names.setText("Device1\nDevice2")
        layout.addRow("设备名列表:", self._device_names)

        self._wifi_ssid = QLineEdit("")
        layout.addRow("WiFi SSID:", self._wifi_ssid)
        self._wifi_password = QLineEdit("")
        self._wifi_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("WiFi 密码:", self._wifi_password)

        self._wait = QDoubleSpinBox()
        self._wait.setRange(0.5, 60.0)
        self._wait.setValue(5.0)
        self._wait.setSuffix(" s")
        layout.addRow("操作等待:", self._wait)
        self._loops = QSpinBox()
        self._loops.setRange(1, 100000)
        self._loops.setValue(30)
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
                "device_sns": self._device_sns.toPlainText(),
                "device_names": self._device_names.toPlainText(),
                "wifi_ssid": self._wifi_ssid.text(),
                "wifi_password": self._wifi_password.text(),
                "wait": self._wait.value(),
                "loops": self._loops.value(),
            }
        except RuntimeError:
            pass
        return dict(self._saved_config)

    def set_default_config(self):
        if self._device_sns:
            self._device_sns.setText("SN001\nSN002")
        if self._device_names:
            self._device_names.setText("Device1\nDevice2")
        if self._wifi_ssid:
            self._wifi_ssid.setText("")
        if self._wifi_password:
            self._wifi_password.setText("")
        if self._wait:
            self._wait.setValue(5.0)
        if self._loops:
            self._loops.setValue(30)

    def _wait_for(self, driver, by, value, timeout=15):
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        try:
            return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
        except Exception:
            return None

    def _swipe_screen(self, driver, direction="down", duration=500):
        from appium.webdriver.common.appiumby import AppiumBy
        size = driver.get_window_size()
        w, h = size["width"], size["height"]
        mx, my = w // 2, h // 2
        if direction == "down":
            ey = my - 800
        else:
            ey = my + 800
        try:
            driver.swipe(mx, my, mx, ey, duration)
        except Exception:
            pass

    def _unbind_all(self, driver, device_names: list, wait: float, log=None):
        from appium.webdriver.common.appiumby import AppiumBy
        log_msgs = []
        for dn in device_names:
            try:
                el = self._wait_for(driver, AppiumBy.ID, "com.glazero.android:id/device_name", 3)
                if el and el.text == dn:
                    self._wait_for(driver, AppiumBy.ID, "com.glazero.android:id/tv_device_settings", 3)
                    if driver.find_element(AppiumBy.ID, "com.glazero.android:id/tv_device_settings"):
                        driver.find_element(AppiumBy.ID, "com.glazero.android:id/tv_device_settings").click()
                    time.sleep(2)
                    self._swipe_screen(driver, "down", 500)
                    unbind = self._wait_for(driver, AppiumBy.XPATH, "//android.widget.TextView[@text='解绑设备']", 3)
                    if unbind:
                        time.sleep(1)
                        unbind.click()
                        time.sleep(1)
                        confirm = self._wait_for(driver, AppiumBy.ID, "com.glazero.android:id/btn_dialog_confirm", 3)
                        if confirm:
                            confirm.click()
                            log_msgs.append(f"Unbound: {dn}")
                            time.sleep(10)
            except Exception as e:
                if log:
                    log(f"Unbind {dn} error: {e}", "warning")
        return log_msgs

    def _bind_one_device(self, driver, sn: str, dn: str, wifi_ssid: str,
                         wifi_password: str, loop_idx: int, log) -> bool:
        """Bind a single device via BLE + WiFi. Returns True on success."""
        from appium.webdriver.common.appiumby import AppiumBy

        # Navigate to add device
        self._wait_for(driver, AppiumBy.ID, "com.glazero.android:id/img_add_device", 10)
        driver.find_element(AppiumBy.ID, "com.glazero.android:id/img_add_device").click()
        time.sleep(10)

        # Scan for BLE device by SN
        found = False
        for _ in range(3):
            ble_el = self._wait_for(
                driver, AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().text("SN: {sn}")', timeout=5
            )
            if ble_el:
                found = True
                break
            self._swipe_screen(driver, "down", 200)
            time.sleep(0.5)

        if not found:
            log(f"Loop {loop_idx}: BLE device SN:{sn} not found", "error")
            driver.back()
            time.sleep(2)
            return False

        # Click add button
        add_btn = self._wait_for(driver, AppiumBy.XPATH,
            f"//android.widget.TextView[@text='SN: {sn}']/..//android.widget.Button[@text='添加']", 3)
        if add_btn:
            add_btn.click()

        # Single device mode (optional)
        time.sleep(2)
        try:
            driver.find_element(AppiumBy.XPATH, "//android.widget.TextView[@text='单机配对']").click()
        except Exception:
            pass

        # Next
        self._wait_for(driver, AppiumBy.XPATH, "//android.widget.Button[@text='下一步']", 10)
        time.sleep(1)
        try:
            driver.find_element(AppiumBy.XPATH, "//android.widget.Button[@text='下一步']").click()
        except Exception as e:
            log(f"Loop {loop_idx}: next button click failed: {e}", "warning")
        time.sleep(2)

        # Wait for WiFi list screen
        self._wait_for(driver, AppiumBy.XPATH, "//android.widget.TextView[@text='选择设备连接的Wi-Fi']", 45)
        time.sleep(2)

        # Click "manually add network"
        if not self._click_manual_add_wifi(driver, loop_idx, log):
            return False

        time.sleep(1)
        self._fill_wifi_credentials(driver, wifi_ssid, wifi_password)

        # Click connect
        driver.find_element(AppiumBy.XPATH, "//android.widget.Button[@text='连接']").click()
        log(f"Loop {loop_idx}: WiFi connecting for {dn}...", "info")
        time.sleep(5)

        # Wait for pairing result
        pair_el = self._wait_for(driver, AppiumBy.ID, "com.glazero.android:id/tv_tip", timeout=60)
        if pair_el and pair_el.text == "配对成功":
            log(f"Loop {loop_idx}: {dn} paired successfully", "info")
        else:
            log(f"Loop {loop_idx}: {dn} pairing may have failed", "warning")

        # Close pairing screen
        time.sleep(2)
        try:
            driver.find_element(AppiumBy.XPATH, "//android.widget.Button[@text='关闭']").click()
        except Exception:
            try:
                driver.back()
            except Exception:
                pass
        time.sleep(2)
        return True

    def _click_manual_add_wifi(self, driver, loop_idx: int, log) -> bool:
        try:
            manual = driver.find_element("xpath", "//android.widget.TextView[@text='手动添加其他网络']")
            manual.click()
            return True
        except Exception:
            try:
                self._swipe_screen(driver, "up", 200)
                manual = driver.find_element("xpath", "//android.widget.TextView[@text='手动添加其他网络']")
                manual.click()
                return True
            except Exception:
                log(f"Loop {loop_idx}: manual WiFi add not found", "error")
                driver.back()
                return False

    def _fill_wifi_credentials(self, driver, ssid: str, password: str):
        ssid_field = self._wait_for(driver, "xpath", "//android.widget.EditText[@text='输入WiFi名称']", 5)
        if ssid_field:
            ssid_field.clear()
            ssid_field.send_keys(ssid)
        else:
            ssid_field = self._wait_for(driver, "xpath", "//android.widget.EditText[1]", 3)
            if ssid_field:
                ssid_field.clear()
                ssid_field.send_keys(ssid)

        pwd_field = self._wait_for(driver, "xpath", "//android.widget.EditText[@text='输入密码']", 3)
        if not pwd_field:
            pwd_field = self._wait_for(driver, "xpath", "//android.widget.EditText[2]", 3)
        if pwd_field:
            pwd_field.clear()
            pwd_field.send_keys(password)

    def _restart_app(self, driver, loop_idx: int, log):
        log(f"Loop {loop_idx}: restarting app...", "info")
        try:
            driver.terminate_app("com.glazero.android")
            time.sleep(2)
            driver.activate_app("com.glazero.android")
            time.sleep(5)
        except Exception as e:
            log(f"Loop {loop_idx}: app restart failed: {e}", "warning")

    def run(self, ctx: TestContext, config: dict,
            stop_event: threading.Event, log, serial_log, record):
        cpu_port = config.get("cpu_port", "")
        cpu_baud = config.get("cpu_baudrate", 115200)
        wifi_port = config.get("wifi_port", "")
        wifi_baud = config.get("wifi_baudrate", 115200)
        device_sns_text = config.get("device_sns", "")
        device_names_text = config.get("device_names", "")
        wifi_ssid = config.get("wifi_ssid", "")
        wifi_password = config.get("wifi_password", "")
        wait = config.get("wait", 5.0)
        loops = config.get("loops", 30)

        sns = [s.strip() for s in device_sns_text.strip().split("\n") if s.strip()]
        names = [s.strip() for s in device_names_text.strip().split("\n") if s.strip()]

        driver = ctx.appium.driver
        if not driver:
            log("Appium not connected (设置 → Appium设置)", "error")
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
                    unbind_logs = self._unbind_all(driver, names, wait, log)
                    for msg in unbind_logs:
                        log(f"Loop {i}: {msg}", "info")

                    time.sleep(1)

                    for di, sn in enumerate(sns):
                        if stop_event.is_set():
                            break
                        dn = names[di] if di < len(names) else sn
                        log(f"Loop {i}: binding {dn} (SN:{sn})...", "info")
                        self._bind_one_device(driver, sn, dn, wifi_ssid, wifi_password, i, log)

                    success = True
                except Exception as e:
                    success = False
                    log(f"Loop {i}: error → {e}", "error")

                latency_ms = (time.perf_counter() - t0) * 1000
                record(success, latency_ms)

                if (i + 1) % 10 == 0 and i < loops - 1:
                    self._restart_app(driver, i, log)
        finally:
            if cpu:
                cpu.close()
            if wifi:
                wifi.close()
