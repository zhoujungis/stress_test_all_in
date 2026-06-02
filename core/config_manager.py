import json
import os


class ConfigManager:
    def __init__(self, config_dir: str = "config"):
        self._config_dir = config_dir
        os.makedirs(self._config_dir, exist_ok=True)

    @property
    def config_dir(self) -> str:
        return self._config_dir

    # ── Module configs ────────────────────────────

    def _modules_dir(self) -> str:
        d = os.path.join(self._config_dir, "modules")
        os.makedirs(d, exist_ok=True)
        return d

    def save_module(self, module_id: str, config: dict):
        path = os.path.join(self._modules_dir(), f"{module_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def load_module(self, module_id: str) -> dict | None:
        path = os.path.join(self._modules_dir(), f"{module_id}.json")
        if not os.path.isfile(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    # ── Project config ────────────────────────────

    def _project_path(self) -> str:
        return os.path.join(self._config_dir, "project.json")

    def save_project(self, data: dict):
        with open(self._project_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_project(self) -> dict | None:
        try:
            with open(self._project_path(), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    # ── Full export / import ──────────────────────

    def save_all(self, path: str, modules_data: dict):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"modules": modules_data}, f, indent=2, ensure_ascii=False)

    def load_all(self, path: str) -> dict | None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
