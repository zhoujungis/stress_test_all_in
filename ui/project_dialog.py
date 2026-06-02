from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, QGroupBox,
)


class ProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("项目配置")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)

        group = QGroupBox("项目信息")
        form = QFormLayout(group)

        self._project_name = QLineEdit("")
        self._project_name.setPlaceholderText("输入项目名称")
        form.addRow("项目名字:", self._project_name)

        self._tester = QLineEdit("")
        self._tester.setPlaceholderText("输入测试人员")
        form.addRow("测试人员:", self._tester)

        self._test_time = QLineEdit("")
        self._test_time.setPlaceholderText("如: 24h / 7天 / 1000次")
        form.addRow("测试时间:", self._test_time)

        self._dingtalk = QLineEdit("")
        self._dingtalk.setPlaceholderText("钉钉账号")
        form.addRow("钉钉账号:", self._dingtalk)

        self._email = QLineEdit("")
        self._email.setPlaceholderText("邮箱账号")
        form.addRow("邮箱账号:", self._email)

        self._notes = QLineEdit("")
        self._notes.setPlaceholderText("备注（可选）")
        form.addRow("备注:", self._notes)

        layout.addWidget(group)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_project_name(self) -> str:
        return self._project_name.text().strip()

    def get_tester(self) -> str:
        return self._tester.text().strip()

    def get_test_time(self) -> str:
        return self._test_time.text().strip()

    def get_dingtalk(self) -> str:
        return self._dingtalk.text().strip()

    def get_email(self) -> str:
        return self._email.text().strip()

    def get_notes(self) -> str:
        return self._notes.text().strip()
