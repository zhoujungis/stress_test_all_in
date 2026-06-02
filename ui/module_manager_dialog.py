from PyQt6.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox

from modules.base import BaseTestModule
from ui.module_panel import ModulePanel


class ModuleManagerDialog(QDialog):
    def __init__(self, modules: list[BaseTestModule], parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择模块")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        self._panel = ModulePanel()
        self._panel.load_modules(modules)
        layout.addWidget(self._panel)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_enabled(self) -> list[str]:
        return self._panel.get_enabled()
