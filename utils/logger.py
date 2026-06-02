import logging
from PyQt6.QtCore import QObject, pyqtSignal


class LogSignal(QObject):
    message = pyqtSignal(str)


class QtLogHandler(logging.Handler):
    def __init__(self, signal: LogSignal):
        super().__init__()
        self.signal = signal
        self.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S"))

    def emit(self, record: logging.LogRecord):
        self.signal.message.emit(self.format(record))


def setup_logger(name: str, signal: LogSignal) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(QtLogHandler(signal))
    return logger
