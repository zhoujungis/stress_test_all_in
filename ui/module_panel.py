from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QCheckBox, QLabel,
)
from PyQt6.QtCore import pyqtSignal

from modules.base import BaseTestModule


class ModulePanel(QWidget):
    def __init__(self):
        super().__init__()
        self._modules: list[BaseTestModule] = []
        self._checkboxes: dict[str, QCheckBox] = {}
        self._build()

    def _build(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(2)

    def load_modules(self, modules: list[BaseTestModule]):
        self._modules = modules
        self._checkboxes.clear()
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for mod in modules:
            cb = QCheckBox(mod.name)
            cb.setChecked(True)
            cb.setStyleSheet("font-weight:bold; spacing:8px;")
            self._layout.addWidget(cb)

            desc = QLabel(f"    {mod.description}")
            desc.setStyleSheet("color:#888; font-size:11px; margin-bottom:2px;")
            self._layout.addWidget(desc)

            self._checkboxes[mod.module_id] = cb
        self._layout.addStretch()

    def get_enabled(self) -> list[str]:
        return [m.module_id for m in self._modules if self._checkboxes[m.module_id].isChecked()]
