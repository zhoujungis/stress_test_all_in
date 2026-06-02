import os
import json

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QGroupBox, QPushButton, QHBoxLayout,
)
from PyQt6.QtCore import pyqtSignal

from core.appium_client import AppiumClient


class AppiumDialog(QDialog):
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    log = pyqtSignal(str, str)

    def __init__(self, appium: AppiumClient, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Appium 设置")
        self.setMinimumWidth(420)
        self.appium = appium

        layout = QVBoxLayout(self)

        group = QGroupBox("Appium Server")
        form = QFormLayout(group)

        self._url = QLineEdit("http://localhost:4723")
        form.addRow("Server URL:", self._url)
        self._platform = QLineEdit("Android")
        form.addRow("Platform:", self._platform)
        self._device = QLineEdit("Android")
        form.addRow("Device Name:", self._device)
        self._app_package = QLineEdit("com.glazero.android")
        form.addRow("App Package:", self._app_package)
        self._app_activity = QLineEdit("com.glazero.android.SplashActivity")
        form.addRow("App Activity:", self._app_activity)

        layout.addWidget(group)

        btn_layout = QHBoxLayout()
        self._connect_btn = QPushButton("Connect")
        self._connect_btn.clicked.connect(self._on_connect)
        btn_layout.addWidget(self._connect_btn)
        self._disconnect_btn = QPushButton("Disconnect")
        self._disconnect_btn.setEnabled(False)
        self._disconnect_btn.clicked.connect(self._on_disconnect)
        btn_layout.addWidget(self._disconnect_btn)
        btn_layout.addStretch()

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        btn_layout.addWidget(btns)
        layout.addLayout(btn_layout)

    def _on_connect(self):
        self.appium.server_url = self._url.text()
        ok = self.appium.connect(
            platform_name=self._platform.text(),
            device_name=self._device.text(),
            app_package=self._app_package.text(),
            app_activity=self._app_activity.text(),
        )
        if ok:
            self.log.emit("Appium connected", "info")
            self._connect_btn.setEnabled(False)
            self._disconnect_btn.setEnabled(True)
            self.connected.emit()
        else:
            self.log.emit("Appium connection failed", "error")

    def _on_disconnect(self):
        self.appium.disconnect()
        self.log.emit("Appium disconnected", "info")
        self._connect_btn.setEnabled(True)
        self._disconnect_btn.setEnabled(False)
        self.disconnected.emit()

    def _on_ok(self):
        self.save()
        self.accept()

    def save(self):
        data = {
            "url": self._url.text(), "platform": self._platform.text(),
            "device": self._device.text(), "app_package": self._app_package.text(),
            "app_activity": self._app_activity.text(),
        }
        os.makedirs("config", exist_ok=True)
        with open("config/appium.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self):
        try:
            with open("config/appium.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            self._url.setText(data.get("url", "http://localhost:4723"))
            self._platform.setText(data.get("platform", "Android"))
            self._device.setText(data.get("device", "Android"))
            self._app_package.setText(data.get("app_package", "com.glazero.android"))
            self._app_activity.setText(data.get("app_activity", "com.glazero.android.SplashActivity"))
        except Exception:
            pass
