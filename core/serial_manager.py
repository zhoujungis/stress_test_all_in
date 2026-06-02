import threading
import serial
import serial.tools.list_ports


class PortConfig:
    def __init__(self, port: str = "", baudrate: int = 115200,
                 bytesize: int = 8, parity: str = "N", stopbits: int = 1,
                 timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.timeout = timeout

    def to_dict(self):
        return {
            "port": self.port, "baudrate": self.baudrate,
            "bytesize": self.bytesize, "parity": self.parity,
            "stopbits": self.stopbits, "timeout": self.timeout,
        }


class SerialPort:
    def __init__(self, name: str, config: PortConfig):
        self.name = name
        self.config = config
        self._serial: serial.Serial | None = None
        self._lock = threading.Lock()

    def open(self) -> bool:
        if not self.config.port:
            return False
        try:
            self._serial = serial.Serial(
                port=self.config.port,
                baudrate=self.config.baudrate,
                bytesize=self.config.bytesize,
                parity=self.config.parity,
                stopbits=self.config.stopbits,
                timeout=self.config.timeout,
            )
            return True
        except serial.SerialException:
            return False

    def close(self):
        with self._lock:
            if self._serial and self._serial.is_open:
                try:
                    self._serial.close()
                except serial.SerialException:
                    pass
            self._serial = None

    def is_open(self) -> bool:
        return self._serial is not None and self._serial.is_open

    def send(self, data: bytes) -> int:
        with self._lock:
            if not self.is_open():
                raise ConnectionError(f"Port '{self.name}' is not open")
            return self._serial.write(data)

    def recv(self, timeout: float | None = None) -> bytes:
        with self._lock:
            if not self.is_open():
                raise ConnectionError(f"Port '{self.name}' is not open")
            original = self._serial.timeout
            if timeout is not None:
                self._serial.timeout = timeout
            try:
                data = self._serial.read(self._serial.in_waiting or 1)
                return data
            finally:
                self._serial.timeout = original

    def recv_until(self, expect: bytes, timeout: float = 5.0) -> tuple[bytes, bool]:
        with self._lock:
            if not self.is_open():
                raise ConnectionError(f"Port '{self.name}' is not open")
            self._serial.timeout = timeout
            buffer = bytearray()
            start = threading.Event()
            start_t = threading.Timer(timeout, start.set)
            start_t.start()
            try:
                while not start.is_set():
                    if self._serial.in_waiting:
                        chunk = self._serial.read(self._serial.in_waiting)
                        buffer.extend(chunk)
                        if expect and expect in buffer:
                            return bytes(buffer), True
                    else:
                        start.wait(0.01)
            finally:
                start_t.cancel()
            return bytes(buffer), False

    def send_and_wait(self, data: bytes, expect: bytes = None, timeout: float = 5.0) -> tuple[bytes, bool]:
        self.send(data)
        if expect is None:
            return b"", True
        return self.recv_until(expect, timeout)

    def set_rts(self, state: bool):
        with self._lock:
            if self.is_open():
                self._serial.rts = state

    def set_dtr(self, state: bool):
        with self._lock:
            if self.is_open():
                self._serial.dtr = state


class SerialManager:
    def __init__(self):
        self._ports: dict[str, SerialPort] = {}

    def add_port(self, name: str, config: PortConfig = None):
        self._ports[name] = SerialPort(name, config or PortConfig())

    def remove_port(self, name: str):
        if name in self._ports:
            self._ports[name].close()
            del self._ports[name]

    def get_port(self, name: str) -> SerialPort | None:
        return self._ports.get(name)

    def get_names(self) -> list[str]:
        return list(self._ports.keys())

    def open_all(self) -> list[str]:
        failed = []
        for sp in self._ports.values():
            if sp.config.port and not sp.open():
                failed.append(sp.name)
        return failed

    def close_all(self):
        for sp in self._ports.values():
            sp.close()

    @staticmethod
    def list_available_ports() -> list[str]:
        return [p.device for p in serial.tools.list_ports.comports()]
