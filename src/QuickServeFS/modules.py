"""
Module helper class. Resolves resources, and does the heavy lifting for module loading.

Author: Quintin Dunn
Date: 09/09/2026
"""

import importlib
import sys
import logging
from pathlib import Path

from typing import TYPE_CHECKING, Optional, Union, Tuple
from types import ModuleType

from QuickServeFS.exceptions import InvalidModuleError, AssetDoesntExist

from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from QuickServeFS.path_resolver import Resolver

logger = logging.getLogger("QuickServerFS.Modules")


class Service(ABC):
    """Interface for Module Service"""

    NAME: str
    VERSION: str
    QUICKSERVE_VERSION: str
    AUTHORS: dict

    @abstractmethod
    def about(self) -> Union[str, Tuple[str, dict]]:
        """
        Required page for the module's about page.
        :return: Union[str, Tuple[str, dict]], where the first str is
        always the string representation of the template, and the optional
        dictionary is any context to be passed to the renderer.
        **NOTE: All context passed in will be automatically prefixed with 'param_'**
        """

    @abstractmethod
    def create(self) -> Union[str, Tuple[str, dict]]:
        """
        Required page for the module's create page
        :return: Union[str, Tuple[str, dict]], where the first str is
        always the string representation of the template, and the optional
        dictionary is any context to be passed to the renderer.
        **NOTE: All context passed in will be automatically prefixed with 'param_'**
        """


class Module:
    path: Path
    resolver: Resolver
    module: ModuleType
    service: Service

    def __init__(self, module_path: str | Path, resolver: "Resolver"):
        self.path = Path(module_path)
        self.resolver = resolver

    def raise_if_attr_not_exist(
        self, attr_name: str, exception: Exception, service: bool = True
    ) -> None:
        """
        Raises an exception if an attribute doesn't exist in a service/module.

        :param attr_name: The name of the attribute to check.
        :param exception: The exception to raise if Object.<attr_name> doesn't exist.
        :param service: If true, check if self.service.<attr_name> exists,
        otherwise check self.module.<attr_name>
        :return: None
        """
        obj = self.service if service else self.module

        if not hasattr(obj, attr_name):
            raise exception

    def _validate_and_load_module(self) -> None:
        """
        Validates that a module has the required fields.

        :return: None
        """

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

    def load_module(self) -> None:
        """
        Loads the module, and validates the module.

        :return: None
        """
        service_name = self.path.name
        logger.info(f"Loading service {service_name}")

        modules_path = self.resolver.get_path("modules")

        if str(modules_path) not in sys.path:
            sys.path.insert(0, str(modules_path))

        self.module = importlib.import_module(service_name)
        self._validate_and_load_module()

    def get_resource_path(self, resource: str) -> Path:
        """
        Gets a resource relative to the module.

        :param resource: The path of the resource in the
        module relative to .../resources.
        :return: The path to the resource.
        """
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
