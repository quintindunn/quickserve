import importlib
import sys
import logging
from pathlib import Path

from typing import TYPE_CHECKING
from types import ModuleType

from QuickServeFS.exceptions import InvalidModuleError, AssetDoesntExist

if TYPE_CHECKING:
    from QuickServeFS.path_resolver import Resolver

logger = logging.getLogger("QuickServerFS.Modules")


class Module:
    path: Path
    resolver: Resolver
    module: ModuleType | None
    service: object | None

    def __init__(self, module_path: str | Path, resolver: "Resolver"):
        self.path = Path(module_path)
        self.resolver = resolver
        self.module = None
        self.service = None

    def raise_if_attr_not_exist(
        self, attr_name: str, exception: Exception, service: bool = True
    ):
        obj = self.service if service else self.module

        if not hasattr(obj, attr_name):
            raise exception

    def validate_and_load_service(self):
        logger.debug(f"Validating module {self.path.name}")
        attr_error_map = {
            "NAME": "Missing module name",
            "VERSION": "Missing module version",
            "QUICKSERVE_VERSION": "Missing QuickServe version",
        }
        self.raise_if_attr_not_exist(
            "Service",
            InvalidModuleError(f'Module: "{self.path.name}" - Missing service class!'),
            service=False,
        )

        self.service = self.module.Service(module=self)
        for attr, error in attr_error_map.items():
            logger.debug(f"{self.path.name} - Validating {attr}")
            self.raise_if_attr_not_exist(
                attr, InvalidModuleError(f'Module: "{self.path.name}" - {error}')
            )

    def load_service(self):
        service_name = self.path.name
        logger.info(f"Loading service {service_name}")

        modules_path = self.resolver.get_path("modules")

        if str(modules_path) not in sys.path:
            sys.path.insert(0, str(modules_path))

        self.module = importlib.import_module(service_name)
        self.validate_and_load_service()

    def get_resource_path(self, resource: str):
        logger.debug(f"Getting path for in module {self.path / resource}")
        resources = self.path / "resources"

        if not resources.exists() or resources.is_file():
            raise AssetDoesntExist(f"Resources {resources / resource} not found!")

        resource = resources / resource
        if not resource.exists():
            raise AssetDoesntExist(f"Resources {resource} not found!")
        if not resource.is_file():
            raise AssetDoesntExist(f"Resource {resource} is not a file!")

        return resource
