from PyQt6.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox
from PyQt6.QtCore import pyqtSignal

from core.serial_manager import SerialManager
from ui.serial_panel import SerialPanel


class SerialDialog(QDialog):
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    log = pyqtSignal(str, str)

    def __init__(self, serial: SerialManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Serial Port Settings")
        self.setMinimumWidth(480)
        self.serial = serial

        layout = QVBoxLayout(self)

        self._panel = SerialPanel(serial)
        self._panel.log.connect(self.log.emit)
        self._panel.connected.connect(self.connected.emit)
        self._panel.disconnected.connect(self.disconnected.emit)
        layout.addWidget(self._panel)

        self._buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self._buttons.rejected.connect(self.close)
        self._buttons.accepted.connect(self.close)
        layout.addWidget(self._buttons)

    def showEvent(self, event):
        super().showEvent(event)
        self._panel.refresh_on_show()

    @property
    def panel(self):
        return self._panel
