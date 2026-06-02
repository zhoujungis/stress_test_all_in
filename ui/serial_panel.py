from PyQt6.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QPushButton,
)
from PyQt6.QtCore import pyqtSignal

from core.serial_manager import PortConfig, SerialManager


BAUD_RATES = ["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]
DATA_BITS = ["5", "6", "7", "8"]
STOP_BITS = ["1", "1.5", "2"]
PARITIES = ["N", "E", "O", "M", "S"]


class SerialPanel(QWidget):
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    log = pyqtSignal(str, str)

    def __init__(self, serial: SerialManager):
        super().__init__()
        self.serial = serial
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Port config
        group = QGroupBox("Serial Port")
        grid = QGridLayout(group)
        grid.setSpacing(6)

        grid.addWidget(QLabel("Port:"), 0, 0)
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(120)
        self.port_combo.setEditable(True)
        grid.addWidget(self.port_combo, 0, 1)

        grid.addWidget(QLabel("Baud:"), 0, 2)
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(BAUD_RATES)
        self.baud_combo.setCurrentText("115200")
        self.baud_combo.setEditable(True)
        grid.addWidget(self.baud_combo, 0, 3)

        grid.addWidget(QLabel("Data:"), 1, 0)
        self.data_combo = QComboBox()
        self.data_combo.addItems(DATA_BITS)
        self.data_combo.setCurrentText("8")
        grid.addWidget(self.data_combo, 1, 1)

        grid.addWidget(QLabel("Stop:"), 1, 2)
        self.stop_combo = QComboBox()
        self.stop_combo.addItems(STOP_BITS)
        self.stop_combo.setCurrentText("1")
        grid.addWidget(self.stop_combo, 1, 3)

        grid.addWidget(QLabel("Parity:"), 2, 0)
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(PARITIES)
        self.parity_combo.setCurrentText("N")
        grid.addWidget(self.parity_combo, 2, 1)

        layout.addWidget(group)

        # Buttons
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._on_refresh)
        btn_layout.addWidget(self.refresh_btn)

        btn_layout.addStretch()

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self._on_connect)
        btn_layout.addWidget(self.connect_btn)

        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.clicked.connect(self._on_disconnect)
        btn_layout.addWidget(self.disconnect_btn)

        layout.addLayout(btn_layout)

    def get_config(self) -> PortConfig:
        return PortConfig(
            port=self.port_combo.currentText().strip(),
            baudrate=int(self.baud_combo.currentText()),
            bytesize=int(self.data_combo.currentText()),
            parity=self.parity_combo.currentText(),
            stopbits=float(self.stop_combo.currentText()),
        )

    def _on_refresh(self):
        current = self.port_combo.currentText()
        self.port_combo.clear()
        ports = SerialManager.list_available_ports()
        self.port_combo.addItems(ports)
        if current in ports:
            self.port_combo.setCurrentText(current)

    def _on_connect(self):
        cfg = self.get_config()
        if not cfg.port:
            self.log.emit("No serial port selected", "error")
            return

        self.serial.add_port("device", cfg)
        failed = self.serial.open_all()
        if failed:
            self.log.emit(f"Failed to open port: {cfg.port}", "error")
        else:
            self.log.emit(f"Connected: {cfg.port} @ {cfg.baudrate}", "info")
            self._set_connected_ui(True)
            self.connected.emit()

    def _on_disconnect(self):
        self.serial.close_all()
        self.log.emit("Disconnected", "info")
        self._set_connected_ui(False)
        self.disconnected.emit()

    def _set_connected_ui(self, connected: bool):
        for w in [self.port_combo, self.baud_combo, self.data_combo,
                   self.stop_combo, self.parity_combo]:
            w.setEnabled(not connected)
        self.connect_btn.setEnabled(not connected)
        self.disconnect_btn.setEnabled(connected)
        self.refresh_btn.setEnabled(not connected)

    def refresh_on_show(self):
        self._on_refresh()
