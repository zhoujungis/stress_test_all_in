from appium import webdriver
from appium.options.common import AppiumOptions


class AppiumClient:
    def __init__(self, server_url: str = "http://localhost:4723"):
        self.server_url = server_url
        self._driver: webdriver.Remote | None = None

    def connect(self, platform_name: str = "Android",
                device_name: str = "Android",
                app_package: str = "com.glazero.android",
                app_activity: str = "com.glazero.android.SplashActivity",
                automation_name: str = "UiAutomator2",
                no_reset: bool = True,
                new_command_timeout: int = 300,
                force_app_launch: bool = False) -> bool:
        try:
            options = AppiumOptions()
            options.set_capability("platformName", platform_name)
            options.set_capability("deviceName", device_name)
            options.set_capability("appPackage", app_package)
            options.set_capability("appActivity", app_activity)
            options.set_capability("automationName", automation_name)
            options.set_capability("noReset", no_reset)
            options.set_capability("newCommandTimeout", new_command_timeout)
            if force_app_launch:
                options.set_capability("forceAppLaunch", True)
            self._driver = webdriver.Remote(self.server_url, options=options)
            return True
        except Exception:
            return False

    def disconnect(self):
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                pass
            self._driver = None

    def check_alive(self) -> bool:
        if not self._driver:
            return False
        try:
            self._driver.current_activity
            return True
        except Exception:
            return False

    @property
    def driver(self) -> webdriver.Remote | None:
        return self._driver

    def is_connected(self) -> bool:
        return self._driver is not None
