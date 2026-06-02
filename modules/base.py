import time
from abc import ABC, abstractmethod
from typing import Callable
import threading

import serial
from PyQt6.QtWidgets import QWidget

from core.test_context import TestContext


class BaseTestModule(ABC):
    name: str = ""
    module_id: str = ""
    description: str = ""

    def __init__(self):
        self._saved_config: dict = {}

    @abstractmethod
    def create_config_widget(self) -> QWidget:
        ...

    @abstractmethod
    def get_config(self) -> dict:
        ...

    @abstractmethod
    def set_default_config(self):
        ...

    @abstractmethod
    def run(self, ctx: TestContext, config: dict,
            stop_event: threading.Event,
            log: Callable, serial_log: Callable, record: Callable):
        ...

    def save_config(self):
        try:
            self._saved_config = self.get_config()
        except RuntimeError:
            pass

    def get_saved_config(self) -> dict:
        return self._saved_config or self.get_config()

    @staticmethod
    def _open_serial_port(port: str, baudrate: int) -> serial.Serial | None:
        if not port:
            return None
        try:
            return serial.Serial(port, baudrate, timeout=1.0)
        except serial.SerialException:
            return None

    @staticmethod
    def _send_and_wait(ser: serial.Serial, cmd: bytes,
                       expect: bytes = b"OK", timeout: float = 3.0) -> tuple[bytes, bool]:
        ser.write(cmd)
        ser.timeout = timeout
        resp = b""
        deadline = time.perf_counter() + timeout
        while time.perf_counter() < deadline:
            chunk = ser.read(ser.in_waiting or 1)
            if chunk:
                resp += chunk
            if expect in resp:
                return resp, True
        return resp, False
