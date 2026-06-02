from modules.base import BaseTestModule
from modules.power_cycle import PowerCycleModule
from modules.reset import ResetModule
from modules.bind_unbind import BindUnbindModule
from modules.upgrade import UpgradeModule
from modules.sleep_wake import SleepWakeModule
from modules.stream_view import StreamViewModule


_registry: dict[str, type[BaseTestModule]] = {
    "power_cycle": PowerCycleModule,
    "reset": ResetModule,
    "bind_unbind": BindUnbindModule,
    "upgrade": UpgradeModule,
    "sleep_wake": SleepWakeModule,
    "stream_view": StreamViewModule,
}


def get_all_modules() -> list[type[BaseTestModule]]:
    return list(_registry.values())


def create_module(module_id: str) -> BaseTestModule | None:
    cls = _registry.get(module_id)
    if cls is None:
        return None
    return cls()
