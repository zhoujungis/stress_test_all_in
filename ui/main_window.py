from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QFileDialog, QInputDialog,
)
from PyQt6.QtGui import QAction, QKeySequence, QActionGroup

from core.test_context import TestContext
from core.test_runner import TestRunner
from core.config_manager import ConfigManager
from modules import get_all_modules
from ui.appium_dialog import AppiumDialog
from ui.cloud_dialog import CloudDialog
from ui.relay_dialog import RelayDialog
from ui.module_manager_dialog import ModuleManagerDialog
from ui.module_config_dialog import ModuleConfigDialog
from ui.log_panel import LogPanel
from ui.about_dialog import show_version, show_about, show_copyright
from ui.project_dialog import ProjectDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("压测")
        self.setMinimumSize(1100, 650)

        self.ctx = TestContext()
        self.runner: TestRunner | None = None
        self._project_dialog: ProjectDialog | None = None
        self._module_instances: list = []
        self._enabled: set[str] = set()
        self._config_mgr = ConfigManager("config")

        self._build_ui()
        self._build_menu_bar()
        self._load_modules()
        self._load_all_module_configs()
        self._project_dialog = ProjectDialog(self)
        self._load_project_config()
        self._appium_dialog = AppiumDialog(self.ctx.appium, self)
        self._appium_dialog.load()
        self._appium_dialog.log.connect(self.log_panel.append)
        self._cloud_dialog = CloudDialog(self.ctx.cloud, self)
        self._cloud_dialog.load()
        self._cloud_dialog.log.connect(self.log_panel.append)
        self._relay_dialog = RelayDialog(self.ctx.relay, self)
        self._relay_dialog.load()
        self._relay_dialog.log.connect(self.log_panel.append)

    def _build_menu_bar(self):
        mb = self.menuBar()

        file_menu = mb.addMenu("文件(&F)")
        file_menu.addAction(QAction("保存配置", self, shortcut=QKeySequence.StandardKey.Save, triggered=self._on_save_config))
        file_menu.addAction(QAction("加载配置", self, shortcut=QKeySequence.StandardKey.Open, triggered=self._on_load_config))
        file_menu.addSeparator()
        file_menu.addAction(QAction("退出(&X)", self, shortcut=QKeySequence.StandardKey.Quit, triggered=self.close))

        settings_menu = mb.addMenu("设置(&T)")
        settings_menu.addAction(QAction("项目配置...", self, triggered=self._on_project_config))
        settings_menu.addAction(QAction("Appium 设置...", self, triggered=self._on_appium_settings))
        settings_menu.addAction(QAction("云端设置...", self, triggered=self._on_cloud_settings))
        settings_menu.addAction(QAction("继电器设置...", self, triggered=self._on_relay_settings))

        mod_menu = mb.addMenu("模块(&M)")
        self._mod_mgr_act = QAction("模块管理...", self, triggered=self._on_module_manager)
        mod_menu.addAction(self._mod_mgr_act)
        self._mod_cfg_act = QAction("模块配置...", self, triggered=self._on_module_config)
        mod_menu.addAction(self._mod_cfg_act)

        run_menu = mb.addMenu("运行(&R)")
        self._start_act = QAction("开始压测", self, shortcut=QKeySequence("F5"), triggered=self._on_start)
        run_menu.addAction(self._start_act)
        self._stop_act = QAction("停止", self, shortcut=QKeySequence("Escape"), triggered=self._on_stop)
        self._stop_act.setEnabled(False)
        run_menu.addAction(self._stop_act)

        view_menu = mb.addMenu("查看(&V)")
        self._view_group = QActionGroup(self)
        self._view_group.setExclusive(True)
        view_modules = []
        for cls in get_all_modules():
            m = cls()
            view_modules.append((m.module_id, m.name))
            act = QAction(m.name, self)
            act.setCheckable(True)
            act.setData(m.module_id)
            act.triggered.connect(lambda checked, mid=m.module_id, nm=m.name: self._on_view_filter(mid, nm))
            view_menu.addAction(act)
            self._view_group.addAction(act)
        if view_modules:
            self._view_group.actions()[0].setChecked(True)
            self.log_panel.set_filter(view_modules[0][0], view_modules[0][1])

        help_menu = mb.addMenu("帮助(&H)")
        help_menu.addAction(QAction("版本", self, triggered=lambda: show_version(self)))
        help_menu.addAction(QAction("关于", self, triggered=lambda: show_about(self)))
        help_menu.addAction(QAction("版权", self, triggered=lambda: show_copyright(self)))

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(6, 6, 6, 6)
        self.log_panel = LogPanel()
        self.log_panel.init_log_dirs()
        root.addWidget(self.log_panel, 1)

    def _load_modules(self):
        self._module_instances = [cls() for cls in get_all_modules()]
        self._enabled = {m.module_id for m in self._module_instances}

    def _pick_module(self):
        names = [m.name for m in self._module_instances]
        item, ok = QInputDialog.getItem(self, "选择模块", "模块:", names, 0, False)
        if ok:
            return self._module_instances[names.index(item)]
        return None

    # ── View ──────────────────────────────────────
    def _on_view_filter(self, mid: str, name: str = ""):
        self.log_panel.set_filter(mid, name)

    # ── Module Manager ───────────────────────────
    def _on_module_manager(self):
        dlg = ModuleManagerDialog(self._module_instances, self)
        if dlg.exec() == ModuleManagerDialog.DialogCode.Accepted:
            self._enabled = set(dlg.get_enabled())
            self.log_panel.append(f"Modules selected: {len(self._enabled)}", "info")

    # ── Module Config ────────────────────────────
    def _on_module_config(self):
        mod = self._pick_module()
        if mod is None:
            return
        dlg = ModuleConfigDialog(mod, self)
        if dlg.exec() == ModuleConfigDialog.DialogCode.Accepted:
            self._save_module_config(mod)
            self.log_panel.append(f"Config updated: {mod.name}", "info")

    def _save_module_config(self, mod):
        self._config_mgr.save_module(mod.module_id, mod.get_saved_config())

    def _load_all_module_configs(self):
        for mod in self._module_instances:
            data = self._config_mgr.load_module(mod.module_id)
            if data:
                mod._saved_config = data

    # ── Settings ─────────────────────────────────
    def _on_project_config(self):
        dlg = self._project_dialog
        if dlg.exec() == ProjectDialog.DialogCode.Accepted:
            self._save_project_config()
            self.log_panel.set_project_info(dlg.get_project_name(), dlg.get_tester())
            self.log_panel.append(f"项目: {dlg.get_project_name()}  测试人员: {dlg.get_tester()}  测试时间: {dlg.get_test_time()}", "info")

    def _save_project_config(self):
        dlg = self._project_dialog
        data = {
            "project_name": dlg.get_project_name(), "tester": dlg.get_tester(),
            "test_time": dlg.get_test_time(), "dingtalk": dlg.get_dingtalk(),
            "email": dlg.get_email(), "notes": dlg.get_notes(),
        }
        self._config_mgr.save_project(data)

    def _load_project_config(self):
        data = self._config_mgr.load_project()
        if not data:
            return
        dlg = self._project_dialog
        if dlg:
            dlg._project_name.setText(data.get("project_name", ""))
            dlg._tester.setText(data.get("tester", ""))
            dlg._test_time.setText(data.get("test_time", ""))
            dlg._dingtalk.setText(data.get("dingtalk", ""))
            dlg._email.setText(data.get("email", ""))
            dlg._notes.setText(data.get("notes", ""))
        self.log_panel.set_project_info(
            data.get("project_name", ""), data.get("tester", "")
        )

    def _on_appium_settings(self):
        self._appium_dialog.show()
        self._appium_dialog.raise_()

    def _on_cloud_settings(self):
        self._cloud_dialog.show()
        self._cloud_dialog.raise_()

    def _on_relay_settings(self):
        self._relay_dialog.show()
        self._relay_dialog.raise_()

    # ── Run ──────────────────────────────────────
    def _on_start(self):
        modules_to_run = []
        for m in self._module_instances:
            if m.module_id in self._enabled:
                self._save_module_config(m)
                cfg = m.get_saved_config()
                modules_to_run.append((m, 1, cfg))

        if not modules_to_run:
            self.log_panel.append("No modules selected", "warning")
            return

        self.runner = TestRunner(self.ctx)
        self.runner.signals.log.connect(self.log_panel.append)
        self.runner.signals.serial.connect(self.log_panel.append_serial)
        self.runner.signals.all_done.connect(self._on_all_done)

        stats_worker = self.runner.get_stats_worker()
        if stats_worker:
            stats_worker.signals.stats.connect(
                lambda s: self.log_panel.set_stats(s["total"], s["success"], s["fail"])
            )
            stats_worker.signals.per_module.connect(self.log_panel.update_analysis)

        self.runner.start(modules_to_run)
        self._set_running_ui(True)
        self.log_panel.set_status("Running")

    def _on_stop(self):
        if self.runner:
            self.runner.stop()
            self.log_panel.append("Stop requested...", "warning")

    def _on_all_done(self):
        self._set_running_ui(False)
        self.log_panel.set_status("Done")

    def _set_running_ui(self, running: bool):
        self._start_act.setEnabled(not running)
        self._stop_act.setEnabled(running)
        self._mod_mgr_act.setEnabled(not running)
        self._mod_cfg_act.setEnabled(not running)

    # ── Config ───────────────────────────────────
    def _on_save_config(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存配置", self._config_mgr.config_dir, "JSON Files (*.json)")
        if not path:
            return
        modules_data = {}
        for mod in self._module_instances:
            modules_data[mod.module_id] = {
                "enabled": mod.module_id in self._enabled,
                "config": mod.get_saved_config(),
            }
        self._config_mgr.save_all(path, modules_data)
        self.log_panel.append(f"Config saved: {path}", "info")

    def _on_load_config(self):
        path, _ = QFileDialog.getOpenFileName(self, "加载配置", self._config_mgr.config_dir, "JSON Files (*.json)")
        if not path:
            return
        data = self._config_mgr.load_all(path)
        if data is None:
            self.log_panel.append(f"Failed to load config: {path}", "error")
            return
        self._enabled.clear()
        for mid, md in data.get("modules", {}).items():
            if md.get("enabled", True):
                self._enabled.add(mid)
        self.log_panel.append(f"Config loaded: {path}", "info")

    def closeEvent(self, event):
        if self.runner:
            self.runner.stop()
        self.ctx.cleanup()
        event.accept()
