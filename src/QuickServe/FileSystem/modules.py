"""
Module helper class. Resolves resources, and does the heavy lifting for module loading.

Author: Quintin Dunn
Date: 09/09/2026
"""

import importlib
import sys
import logging
from pathlib import Path

from typing import TYPE_CHECKING
from types import ModuleType

from QuickServe.contracts import Module
from QuickServe.FileSystem.exceptions import InvalidModuleError, AssetDoesntExist

if TYPE_CHECKING:
    from QuickServe.FileSystem.path_resolver import Workspace
from QuickServe.Runtimes.runtime_manager import RuntimeManager

logger = logging.getLogger("QuickServerFS.Modules")


class BaseModule:
    path: Path
    workspace: "Workspace"
    _module: ModuleType
    module: Module
    runtime_manager: "RuntimeManager"

    def __init__(
        self,
        module_path: str | Path,
        workspace: "Workspace",
        runtime_manager: "RuntimeManager",
        **kwargs
    ):
        self.path = Path(module_path)
        self.workspace = workspace
        self.runtime_manager = runtime_manager

        self._remove_attr_on_load = None
        if "remove_attr_on_load" in kwargs:
            self._remove_attr_on_load = kwargs["remove_attr_on_load"]

    def raise_if_attr_not_exist(
        self, attr_name: str, exception: Exception, raw_import: bool = True
    ) -> None:
        """
        Raises an exception if an attribute doesn't exist in a module.

        :param attr_name: The name of the attribute to check.
        :param exception: The exception to raise if Object.<attr_name> doesn't exist.
        :param raw_import: If true, check if self.module.<attr_name> exists,
        otherwise check self._module.<attr_name> (The actual loaded module as a result of importing, not the instantiated module).
        :return: None
        """
        obj = self.module if raw_import else self._module

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
            "PAGES": "Missing module pages"
        }
        self.raise_if_attr_not_exist(
            "Module",
            InvalidModuleError(f'Module: "{self.path.name}" - Missing Module class!'),
            raw_import=False,
        )

        self.module = self._module.Module(
            module=self, runtime_manager=self.runtime_manager
        )

        if isinstance(self._remove_attr_on_load, str):
            if hasattr(self.module.__class__, self._remove_attr_on_load):
                delattr(self.module.__class__, self._remove_attr_on_load)
            if hasattr(self.module, self._remove_attr_on_load):
                delattr(self.module, self._remove_attr_on_load)

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
        module_name = self.path.name
        logger.info(f"Loading module {module_name}")

        modules_path = self.workspace.get_path("modules")

        if str(modules_path) not in sys.path:
            sys.path.insert(0, str(modules_path))

        self._module = importlib.import_module(module_name)
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
