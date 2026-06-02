import threading
import time

import serial


# Specific relay board protocol commands
RELAY_COMMANDS = {
    0: {  # All channels
        "on":  bytes.fromhex("48 3A 01 57 01 01 01 01 00 00 00 00 DE 45 44".replace(" ", "")),
        "off": bytes.fromhex("48 3A 01 57 00 00 00 00 00 00 00 00 DA 45 44".replace(" ", "")),
    },
    1: {
        "on":  bytes.fromhex("48 3A 01 70 01 01 00 00 45 44".replace(" ", "")),
        "off": bytes.fromhex("48 3A 01 70 01 00 00 00 45 44".replace(" ", "")),
    },
    2: {
        "on":  bytes.fromhex("48 3A 01 70 02 01 00 00 45 44".replace(" ", "")),
        "off": bytes.fromhex("48 3A 01 70 02 00 00 00 45 44".replace(" ", "")),
    },
    3: {
        "on":  bytes.fromhex("48 3A 01 70 03 01 00 00 45 44".replace(" ", "")),
        "off": bytes.fromhex("48 3A 01 70 03 00 00 00 45 44".replace(" ", "")),
    },
    4: {
        "on":  bytes.fromhex("48 3A 01 70 04 01 00 00 45 44".replace(" ", "")),
        "off": bytes.fromhex("48 3A 01 70 04 00 00 00 45 44".replace(" ", "")),
    },
}


class RelayManager:
    def __init__(self):
        self._port: str = ""
        self._baudrate: int = 9600
        self._method: str = "命令"
        self._channels: int = 4
        self._chan_cmds: dict[int, tuple[bytes, bytes]] = {}
        self._serial: serial.Serial | None = None
        self._lock = threading.Lock()
        self._init_default_cmds()

    def _init_default_cmds(self):
        for ch, cmds in RELAY_COMMANDS.items():
            self._chan_cmds[ch] = (cmds["on"], cmds["off"])
        for ch in range(5, 17):
            self._chan_cmds[ch] = (b"", b"")

    def configure(self, port: str, baudrate: int = 9600, method: str = "命令",
                  channels: int = 4):
        self._port = port
        self._baudrate = baudrate
        self._method = method
        self._channels = channels

    def set_channel_cmd(self, channel: int, on_cmd: bytes, off_cmd: bytes):
        self._chan_cmds[channel] = (on_cmd, off_cmd)

    def connect(self) -> bool:
        if not self._port:
            return False
        with self._lock:
            try:
                self._serial = serial.Serial(self._port, self._baudrate, timeout=0.1)
                return True
            except serial.SerialException:
                return False

    def disconnect(self):
        with self._lock:
            if self._serial and self._serial.is_open:
                try:
                    self._serial.close()
                except serial.SerialException:
                    pass
            self._serial = None

    def is_connected(self) -> bool:
        return self._serial is not None and self._serial.is_open

    @property
    def channel_count(self) -> int:
        return self._channels

    @property
    def method(self) -> str:
        return self._method

    def channel_on(self, channel: int):
        if self._method == "RTS/DTR":
            with self._lock:
                if self._serial and self._serial.is_open:
                    self._serial.rts = True
                    self._serial.dtr = True
            return

        on_cmd, _ = self._chan_cmds.get(channel, (b"", b""))
        with self._lock:
            if self._serial and self._serial.is_open and on_cmd:
                self._serial.write(on_cmd)
                self._serial.flush()

    def channel_off(self, channel: int):
        if self._method == "RTS/DTR":
            with self._lock:
                if self._serial and self._serial.is_open:
                    self._serial.rts = False
                    self._serial.dtr = False
            return

        _, off_cmd = self._chan_cmds.get(channel, (b"", b""))
        with self._lock:
            if self._serial and self._serial.is_open and off_cmd:
                self._serial.write(off_cmd)
                self._serial.flush()

    def all_on(self):
        self.channel_on(0)

    def all_off(self):
        self.channel_off(0)

    def pulse(self, channel: int, duration: float):
        self.channel_off(channel)
        time.sleep(duration)
        self.channel_on(channel)

    def get_channel_cmd(self, channel: int) -> tuple[str, str]:
        on_cmd, off_cmd = self._chan_cmds.get(channel, (b"", b""))
        return (on_cmd.hex(" ").upper(), off_cmd.hex(" ").upper())

    def to_config(self) -> dict:
        cmds = {}
        for ch in range(self._channels + 1):
            on_hex, off_hex = self.get_channel_cmd(ch)
            cmds[str(ch)] = {"on": on_hex, "off": off_hex}
        return {
            "port": self._port, "baudrate": self._baudrate,
            "method": self._method, "channels": self._channels,
            "commands": cmds,
        }

    def from_config(self, cfg: dict):
        self._port = cfg.get("port", "")
        self._baudrate = cfg.get("baudrate", 9600)
        self._method = cfg.get("method", "命令")
        self._channels = cfg.get("channels", 4)
        for ch_str, cmds in cfg.get("commands", {}).items():
            ch = int(ch_str)
            try:
                on_bytes = bytes.fromhex(cmds["on"].replace(" ", ""))
                off_bytes = bytes.fromhex(cmds["off"].replace(" ", ""))
                self._chan_cmds[ch] = (on_bytes, off_bytes)
            except (ValueError, KeyError):
                pass
