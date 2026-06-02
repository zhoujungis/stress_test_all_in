from PyQt6.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox, QLabel

from modules.base import BaseTestModule


class ModuleConfigDialog(QDialog):
    def __init__(self, module: BaseTestModule, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Configure — {module.name}")
        self.setMinimumWidth(400)
        self.module = module

        layout = QVBoxLayout(self)

        desc = QLabel(module.description)
        desc.setStyleSheet("color:#888; font-size:11px;")
        layout.addWidget(desc)

        self._config_widget = module.create_config_widget()
        layout.addWidget(self._config_widget)

        layout.addStretch()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_ok(self):
        self.module.save_config()
        self.accept()
