"""
Discovers and loads QuickServe modules.

Author: Quintin Dunn
Date: 09/14/2026
"""

from __future__ import annotations

import logging

from QuickServe.FileSystem.modules import BaseModule
from QuickServe.FileSystem.path_resolver import Workspace
from QuickServe.Runtimes.runtime_manager import RuntimeManager

logger = logging.getLogger("QuickServe.plugins")


class ModuleCatalog:
    """
    Stores loaded plugins by name.
    """

    def __init__(self, modules: dict[str, BaseModule] | None = None) -> None:
        """
        Initializes a module catalog.

        :param modules: Loaded modules indexed by module name.
        :return: None
        """
        self._modules = modules or {}

    def get(self, name: str) -> BaseModule | None:
        """
        Gets a module if it is loaded.

        :param name: The module name.
        :return: The loaded module, or None when it is unknown.
        """
        return self._modules.get(name)

    def require(self, name: str) -> BaseModule:
        """
        Gets a module or raises when it is unknown.

        :param name: The module name.
        :return: The loaded module.
        :raises KeyError: If no module has the requested module name.
        """
        module = self.get(name)
        if module is None:
            raise KeyError(f"Unknown module: {name}")
        return module

    def __contains__(self, name: str) -> bool:
        """
        Checks whether a module is loaded.

        :param name: The module name.
        :return: True when the module is loaded.
        """
        return name in self._modules

    def items(self):
        """
        Gets the loaded module-name and module pairs.

        :return: The catalog items view.
        """
        return self._modules.items()

    @property
    def modules(self) -> dict[str, BaseModule]:
        """
        Gets a copy of the loaded modules.

        A copy prevents web code from mutating the loaded catalog.

        :return: Loaded modules indexed by module name.
        """
        return self._modules.copy()


class PluginLoader:
    """
    Loads and validates module packages from the workspace modules directory.
    """

    def __init__(self, workspace: Workspace, runtime_manager: "RuntimeManager") -> None:
        """
        Initializes the plugin loader.

        :param workspace: The workspace containing the modules directory.
        :param runtime_manager: The server runtime manager.
        :return: None
        """
        self.workspace = workspace
        self.runtime_manager = runtime_manager

    def load_all(self) -> ModuleCatalog:
        """
        Discovers, validates, and loads every module.

        :return: The catalog of loaded modules.
        :raises ValueError: If more than one plugin exposes the same module name.
        """
        modules_path = self.workspace.ensure_directory("modules")
        loaded: dict[str, BaseModule] = {}
        for path in modules_path.iterdir():
            if not path.resolve().is_dir() or path.name.startswith("."):
                logger.debug(f"Skipping {path}")
                continue
            logger.info("Loading module %s", path)
            module = BaseModule(
                module_path=path,
                workspace=self.workspace,
                runtime_manager=self.runtime_manager,
            )
            module.load_module()
            name = module.module.NAME
            if name in loaded:
                raise ValueError(f"Duplicate module name: {name}")
            loaded[name] = module
        return ModuleCatalog(loaded)
