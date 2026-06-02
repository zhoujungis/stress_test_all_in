from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QPushButton,
    QDialogButtonBox, QGroupBox, QHBoxLayout,
)
from PyQt6.QtCore import pyqtSignal

from core.cloud_client import CloudClient


class CloudDialog(QDialog):
    log = pyqtSignal(str, str)

    def __init__(self, cloud: CloudClient, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cloud Platform Settings")
        self.setMinimumWidth(400)
        self.cloud = cloud

        layout = QVBoxLayout(self)

        group = QGroupBox("Glazero Cloud")
        form = QFormLayout(group)

        self._username = QLineEdit("")
        self._username.setPlaceholderText("登录用户名")
        form.addRow("用户名:", self._username)

        self._password = QLineEdit("")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setPlaceholderText("登录密码")
        form.addRow("密码:", self._password)

        self._region = QComboBox()
        self._region.addItems(["CN", "US", "EU"])
        form.addRow("区域:", self._region)

        layout.addWidget(group)

        btn_layout = QHBoxLayout()
        self._login_btn = QPushButton("登录")
        self._login_btn.clicked.connect(self._on_login)
        btn_layout.addWidget(self._login_btn)

        self._status_label = QLineEdit("未登录")
        self._status_label.setReadOnly(True)
        btn_layout.addWidget(self._status_label)

        btn_layout.addStretch()
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        btn_layout.addWidget(btns)
        layout.addLayout(btn_layout)

    def _on_login(self):
        self.cloud.configure(
            self._username.text().strip(),
            self._password.text().strip(),
            self._region.currentText(),
        )
        if self.cloud.login():
            self._status_label.setText("已登录")
            self.log.emit("Cloud login OK", "info")
        else:
            self._status_label.setText("登录失败")
            self.log.emit("Cloud login failed", "error")

    def _on_ok(self):
        self._on_login()
        self.save()
        self.accept()

    def save(self):
        import os, json
        data = {
            "username": self._username.text(), "password": self._password.text(),
            "region": self._region.currentText(),
        }
        os.makedirs("config", exist_ok=True)
        with open("config/cloud.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self):
        import os, json
        try:
            with open("config/cloud.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            self._username.setText(data.get("username", ""))
            self._password.setText(data.get("password", ""))
            idx = self._region.findText(data.get("region", "CN"))
            if idx >= 0:
                self._region.setCurrentIndex(idx)
        except Exception:
            pass
