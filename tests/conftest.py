import sys
import types
from datetime import datetime, timezone
from pathlib import Path


def _install_homeassistant_stubs() -> None:
    if "homeassistant" in sys.modules:
        return

    ha = types.ModuleType("homeassistant")
    ha_config_entries = types.ModuleType("homeassistant.config_entries")
    ha_core = types.ModuleType("homeassistant.core")
    ha_helpers = types.ModuleType("homeassistant.helpers")
    ha_helpers_selector = types.ModuleType("homeassistant.helpers.selector")
    ha_helpers_update = types.ModuleType("homeassistant.helpers.update_coordinator")
    ha_util = types.ModuleType("homeassistant.util")
    ha_util_dt = types.ModuleType("homeassistant.util.dt")

    class ConfigEntry:  # pragma: no cover - stub
        pass

    class ConfigFlow:  # pragma: no cover - stub
        def __init_subclass__(cls, **kwargs):
            return super().__init_subclass__()

    class OptionsFlow:  # pragma: no cover - stub
        def __init__(self, *args, **kwargs):
            pass

    class ConfigFlowResult(dict):  # pragma: no cover - stub
        pass

    def callback(func):  # pragma: no cover - stub
        return func

    class HomeAssistant:  # pragma: no cover - stub
        pass

    class DataUpdateCoordinator:  # pragma: no cover - stub
        def __init__(self, *args, **kwargs):
            pass

        def __class_getitem__(cls, item):
            return cls

    class TextSelector:  # pragma: no cover - stub
        def __init__(self, *args, **kwargs):
            pass

    class TextSelectorConfig:  # pragma: no cover - stub
        def __init__(self, *args, **kwargs):
            pass

    class NumberSelector:  # pragma: no cover - stub
        def __init__(self, *args, **kwargs):
            pass

    class NumberSelectorConfig:  # pragma: no cover - stub
        def __init__(self, *args, **kwargs):
            pass

    class NumberSelectorMode:  # pragma: no cover - stub
        BOX = "box"

    class SelectSelector:  # pragma: no cover - stub
        def __init__(self, *args, **kwargs):
            pass

    class SelectSelectorConfig:  # pragma: no cover - stub
        def __init__(self, *args, **kwargs):
            pass

    class ObjectSelector:  # pragma: no cover - stub
        def __init__(self, *args, **kwargs):
            pass

    def utcnow():
        return datetime.now(timezone.utc)

    ha_config_entries.ConfigEntry = ConfigEntry
    ha_config_entries.ConfigFlow = ConfigFlow
    ha_config_entries.ConfigFlowResult = ConfigFlowResult
    ha_config_entries.OptionsFlow = OptionsFlow
    ha_config_entries.callback = callback
    ha_core.HomeAssistant = HomeAssistant
    ha_helpers_update.DataUpdateCoordinator = DataUpdateCoordinator
    ha_helpers_selector.TextSelector = TextSelector
    ha_helpers_selector.TextSelectorConfig = TextSelectorConfig
    ha_helpers_selector.NumberSelector = NumberSelector
    ha_helpers_selector.NumberSelectorConfig = NumberSelectorConfig
    ha_helpers_selector.NumberSelectorMode = NumberSelectorMode
    ha_helpers_selector.SelectSelector = SelectSelector
    ha_helpers_selector.SelectSelectorConfig = SelectSelectorConfig
    ha_helpers_selector.ObjectSelector = ObjectSelector
    ha_util_dt.utcnow = utcnow

    sys.modules["homeassistant"] = ha
    sys.modules["homeassistant.config_entries"] = ha_config_entries
    sys.modules["homeassistant.core"] = ha_core
    sys.modules["homeassistant.helpers"] = ha_helpers
    sys.modules["homeassistant.helpers.selector"] = ha_helpers_selector
    sys.modules["homeassistant.helpers.update_coordinator"] = ha_helpers_update
    sys.modules["homeassistant.util"] = ha_util
    sys.modules["homeassistant.util.dt"] = ha_util_dt


_install_homeassistant_stubs()


def _add_custom_components_to_path() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    custom_components = repo_root / "custom_components"
    if str(custom_components) not in sys.path:
        sys.path.insert(0, str(custom_components))


_add_custom_components_to_path()
