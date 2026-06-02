from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QPushButton, QLabel, QSpinBox, QLineEdit,
    QDialogButtonBox, QTableWidget, QTableWidgetItem, QHeaderView,
)
from PyQt6.QtCore import pyqtSignal

from core.relay_manager import RelayManager
from core.serial_manager import SerialManager


class RelayDialog(QDialog):
    log = pyqtSignal(str, str)

    def __init__(self, relay: RelayManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Relay Settings")
        self.setMinimumWidth(520)
        self.relay = relay
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)

        # Port config
        port_group = QGroupBox("Relay Port")
        form = QFormLayout(port_group)

        self._port_combo = QComboBox()
        self._port_combo.setEditable(True)
        self._port_combo.setMinimumWidth(100)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self._port_combo)
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._on_refresh)
        btn_layout.addWidget(refresh_btn)
        form.addRow("Port:", btn_layout)

        self._baud_combo = QComboBox()
        self._baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self._baud_combo.setCurrentText("9600")
        form.addRow("Baud:", self._baud_combo)

        self._method_combo = QComboBox()
        self._method_combo.addItems(["命令", "RTS/DTR"])
        form.addRow("控制方式:", self._method_combo)

        self._chan_spin = QSpinBox()
        self._chan_spin.setRange(1, 16)
        self._chan_spin.setValue(4)
        self._chan_spin.valueChanged.connect(self._on_chan_changed)
        form.addRow("通道数:", self._chan_spin)

        layout.addWidget(port_group)

        # Channel commands table
        cmd_group = QGroupBox("通道命令 (HEX)")
        cmd_layout = QVBoxLayout(cmd_group)
        self._table = QTableWidget(4, 3)
        self._table.setHorizontalHeaderLabels(["通道", "开命令", "关命令"])
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        cmd_layout.addWidget(self._table)
        layout.addWidget(cmd_group)

        # Connect / Disconnect
        ctrl_layout = QHBoxLayout()
        self._connect_btn = QPushButton("Connect")
        self._connect_btn.clicked.connect(self._on_connect)
        ctrl_layout.addWidget(self._connect_btn)

        self._disconnect_btn = QPushButton("Disconnect")
        self._disconnect_btn.setEnabled(False)
        self._disconnect_btn.clicked.connect(self._on_disconnect)
        ctrl_layout.addWidget(self._disconnect_btn)

        # Test buttons
        ctrl_layout.addStretch()
        self._test_on_btn = QPushButton("Test ON")
        self._test_on_btn.clicked.connect(lambda: self._test(True))
        ctrl_layout.addWidget(self._test_on_btn)
        self._test_off_btn = QPushButton("Test OFF")
        self._test_off_btn.clicked.connect(lambda: self._test(False))
        ctrl_layout.addWidget(self._test_off_btn)

        layout.addLayout(ctrl_layout)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self._on_chan_changed(4)

    def _on_chan_changed(self, count: int):
        self._table.setRowCount(count + 1)
        for ch in range(count + 1):
            label = "All" if ch == 0 else str(ch)
            self._table.setItem(ch, 0, QTableWidgetItem(label))
            on_hex, off_hex = self.relay.get_channel_cmd(ch)
            self._table.setItem(ch, 1, QTableWidgetItem(on_hex))
            self._table.setItem(ch, 2, QTableWidgetItem(off_hex))

    def _on_refresh(self):
        current = self._port_combo.currentText()
        self._port_combo.clear()
        ports = SerialManager.list_available_ports()
        self._port_combo.addItems(ports)
        if current in ports:
            self._port_combo.setCurrentText(current)

    def _on_connect(self):
        self._save_to_relay()
        if self.relay.connect():
            self.log.emit("Relay connected", "info")
            self._connect_btn.setEnabled(False)
            self._disconnect_btn.setEnabled(True)
        else:
            self.log.emit("Relay connection failed", "error")

    def _on_disconnect(self):
        self.relay.disconnect()
        self.log.emit("Relay disconnected", "info")
        self._connect_btn.setEnabled(True)
        self._disconnect_btn.setEnabled(False)

    def _test(self, state: bool):
        self._save_to_relay()
        if not self.relay.is_connected():
            self.relay.connect()
        if not self.relay.is_connected():
            self.log.emit("Relay not connected", "error")
            return
        ch = max(1, self._table.currentRow() + 1)
        if state:
            self.relay.channel_on(ch)
            self.log.emit(f"Relay ch{ch} ON", "info")
        else:
            self.relay.channel_off(ch)
            self.log.emit(f"Relay ch{ch} OFF", "info")

    def _save_to_relay(self):
        self.relay.configure(
            port=self._port_combo.currentText().strip(),
            baudrate=int(self._baud_combo.currentText()),
            method=self._method_combo.currentText(),
            channels=self._chan_spin.value(),
        )
        for row in range(self._table.rowCount()):
            ch_text = self._table.item(row, 0).text() if self._table.item(row, 0) else str(row)
            ch = 0 if ch_text == "All" else int(ch_text)
            on_str = self._table.item(row, 1).text() if self._table.item(row, 1) else ""
            off_str = self._table.item(row, 2).text() if self._table.item(row, 2) else ""
            try:
                on_bytes = bytes.fromhex(on_str.replace(" ", ""))
                off_bytes = bytes.fromhex(off_str.replace(" ", ""))
                self.relay.set_channel_cmd(ch, on_bytes, off_bytes)
            except ValueError:
                pass

    def _on_ok(self):
        self._save_to_relay()
        self.save()
        self.accept()

    def save(self):
        import os, json
        data = self.relay.to_config()
        os.makedirs("config", exist_ok=True)
        with open("config/relay.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self):
        import os, json
        try:
            with open("config/relay.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            self.relay.from_config(data)
        except Exception:
            pass

    def showEvent(self, event):
        super().showEvent(event)
        self._on_refresh()
