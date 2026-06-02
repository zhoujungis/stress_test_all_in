from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QLabel, QStackedWidget

from modules.base import BaseTestModule


class ConfigStack(QWidget):
    def __init__(self):
        super().__init__()
        self._modules: dict[str, BaseTestModule] = {}
        self._widgets: dict[str, QWidget] = {}
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("Module Configuration")
        g_layout = QVBoxLayout(group)

        self._stack = QStackedWidget()
        self._placeholder = QWidget()
        ph_layout = QVBoxLayout(self._placeholder)
        ph_layout.addWidget(QLabel("Select a module from the list"))
        ph_layout.addStretch()
        self._stack.addWidget(self._placeholder)

        g_layout.addWidget(self._stack)
        layout.addWidget(group)

    def load_modules(self, modules: list[BaseTestModule]):
        self._modules.clear()
        self._widgets.clear()
        while self._stack.count() > 1:
            w = self._stack.widget(1)
            self._stack.removeWidget(w)

        for mod in modules:
            self._modules[mod.module_id] = mod
            config_widget = mod.create_config_widget()
            self._widgets[mod.module_id] = config_widget
            self._stack.addWidget(config_widget)

        self._stack.setCurrentWidget(self._placeholder)

    def show_config(self, module_id: str):
        w = self._widgets.get(module_id)
        if w:
            self._stack.setCurrentWidget(w)
        else:
            self._stack.setCurrentWidget(self._placeholder)
