from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt


def show_version(parent):
    dlg = QDialog(parent)
    dlg.setWindowTitle("版本")
    dlg.setFixedSize(300, 180)
    dlg.setStyleSheet("QDialog { background:white; }")
    layout = QVBoxLayout(dlg)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.setSpacing(4)
    layout.addStretch()
    _add(dlg, layout, "压测", 20, True)
    _add(dlg, layout, "V0.1", 14, False)
    layout.addSpacing(12)
    _add(dlg, layout, "Build 2025.05.22", 10, False, "#999")
    _add(dlg, layout, "底层框架: PyQt6 + Appium + pyserial", 10, False, "#aaa")
    layout.addStretch()
    _btn(dlg, layout)
    dlg.exec()


def show_about(parent):
    dlg = QDialog(parent)
    dlg.setWindowTitle("关于")
    dlg.setFixedSize(340, 200)
    dlg.setStyleSheet("QDialog { background:white; }")
    layout = QVBoxLayout(dlg)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.setSpacing(4)
    layout.addStretch()
    _add(dlg, layout, "嵌入式设备压测工具", 15, True)
    layout.addSpacing(8)
    _add(dlg, layout, "针对 Glazero 系列嵌入式设备", 10, False, "#666")
    _add(dlg, layout, "提供开关机/RESET/绑定解绑/升级/休眠唤醒/开流", 10, False, "#666")
    _add(dlg, layout, "等模块化压力测试能力", 10, False, "#666")
    layout.addSpacing(12)
    _add(dlg, layout, "联系: zhoujun@glazero.com", 10, False, "#888")
    layout.addStretch()
    _btn(dlg, layout)
    dlg.exec()


def show_copyright(parent):
    dlg = QDialog(parent)
    dlg.setWindowTitle("版权")
    dlg.setFixedSize(320, 180)
    dlg.setStyleSheet("QDialog { background:white; }")
    layout = QVBoxLayout(dlg)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.setSpacing(4)
    layout.addStretch()
    _add(dlg, layout, "© 2025 深圳市致翎科技有限公司", 12, True)
    layout.addSpacing(8)
    _add(dlg, layout, "Glazero (Shenzhen) Co., Ltd.", 10, False, "#999")
    layout.addSpacing(12)
    _add(dlg, layout, "本工具仅限内部测试使用", 10, False, "#888")
    _add(dlg, layout, "未经授权不得复制、分发或用于商业目的", 10, False, "#aaa")
    layout.addStretch()
    _btn(dlg, layout)
    dlg.exec()


def _add(_dlg, layout, text, size, bold, color="#333"):
    lb = QLabel(text)
    lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
    w = "font-weight:bold;" if bold else ""
    lb.setStyleSheet(f"font-size:{size}px; color:{color}; {w}")
    layout.addWidget(lb)


def _btn(_dlg, layout):
    b = QPushButton("确定")
    b.setFixedWidth(80)
    b.clicked.connect(_dlg.accept)
    bl = QVBoxLayout()
    bl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    bl.addWidget(b)
    layout.addLayout(bl)
    layout.addSpacing(10)
