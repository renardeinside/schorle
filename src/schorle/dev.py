import importlib
from types import ModuleType
from typing import Callable, Tuple

from uvicorn import Server
from uvicorn.importer import ImportFromStringError

from schorle.app import Schorle


class DevServer(Server):
    def install_signal_handlers(self) -> None:
        pass


class AppLoader:
    def __init__(self, app: str):
        self.module, self.instance_getter = self.import_from_string(app)

    @staticmethod
    def import_from_string(import_str: str) -> Tuple[ModuleType, Callable]:
        if not isinstance(import_str, str):
            raise Exception("App coordinates should be provided as a string!")

        module_str, _, attrs_str = import_str.partition(":")
        if not module_str or not attrs_str:
            message = 'Import string "{import_str}" must be in format "<module>:<attribute>".'
            raise ImportFromStringError(message.format(import_str=import_str))

        try:
            module = importlib.import_module(module_str)
        except ImportError as exc:
            if exc.name != module_str:
                raise exc from None
            message = 'Could not import module "{module_str}".'
            raise ImportFromStringError(message.format(module_str=module_str))

        def instance_getter(instance: ModuleType):
            try:
                for attr_str in attrs_str.split("."):
                    instance = getattr(instance, attr_str)
            except AttributeError:
                message = 'Attribute "{attrs_str}" not found in module "{module_str}".'
                raise ImportFromStringError(message.format(attrs_str=attrs_str, module_str=module_str))

            return instance

        return module, instance_getter

    def reload_and_get_instance(self) -> Schorle:
        _reloaded_module = importlib.reload(self.module)
        return self.instance_getter(_reloaded_module)
