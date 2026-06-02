from core.appium_client import AppiumClient
from core.cloud_client import CloudClient
from core.relay_manager import RelayManager


class TestContext:
    def __init__(self):
        self.appium = AppiumClient()
        self.cloud = CloudClient()
        self.relay = RelayManager()

    def cleanup(self):
        self.appium.disconnect()
        self.cloud.close()
        self.relay.disconnect()
