from PyQt6.QtWidgets import QWidget, QHBoxLayout, QComboBox, QLabel
from PyQt6.QtCore import pyqtSignal

from core.serial_manager import SerialManager


BAUD_RATES = ["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]


class ComPortWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)
        self.port_combo.setMinimumWidth(90)
        layout.addWidget(QLabel("Port:"))
        layout.addWidget(self.port_combo)

        self.baud_combo = QComboBox()
        self.baud_combo.addItems(BAUD_RATES)
        self.baud_combo.setCurrentText("115200")
        self.baud_combo.setEditable(True)
        self.baud_combo.setMinimumWidth(80)
        layout.addWidget(QLabel("Baud:"))
        layout.addWidget(self.baud_combo)

    def get_port(self) -> str:
        return self.port_combo.currentText().strip()

    def get_baudrate(self) -> int:
        return int(self.baud_combo.currentText())

    def refresh_ports(self):
        current = self.port_combo.currentText()
        self.port_combo.clear()
        ports = SerialManager.list_available_ports()
        self.port_combo.addItems(ports)
        if current in ports:
            self.port_combo.setCurrentText(current)
