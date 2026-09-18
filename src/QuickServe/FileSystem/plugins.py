"""
Discovers and loads QuickServe service plugins.

Author: Quintin Dunn
Date: 09/14/2026
"""

from __future__ import annotations

import logging
from pathlib import Path

from QuickServe.FileSystem.modules import Module
from QuickServe.FileSystem.path_resolver import Workspace
from QuickServe.Runtimes.runtime_manager import RuntimeManager

logger = logging.getLogger("QuickServe.plugins")


class ServiceCatalog:
    """
    Stores loaded service plugins by name.
    """

    def __init__(self, modules: dict[str, Module] | None = None) -> None:
        """
        Initializes a service catalog.

        :param modules: Loaded modules indexed by service name.
        :return: None
        """
        self._modules = modules or {}

    def get(self, name: str) -> Module | None:
        """
        Gets a service module if it is loaded.

        :param name: The service name.
        :return: The loaded module, or None when it is unknown.
        """
        return self._modules.get(name)

    def require(self, name: str) -> Module:
        """
        Gets a service module or raises when it is unknown.

        :param name: The service name.
        :return: The loaded module.
        :raises KeyError: If no module has the requested service name.
        """
        module = self.get(name)
        if module is None:
            raise KeyError(f"Unknown service module: {name}")
        return module

    def __contains__(self, name: str) -> bool:
        """
        Checks whether a service module is loaded.

        :param name: The service name.
        :return: True when the module is loaded.
        """
        return name in self._modules

    def items(self):
        """
        Gets the loaded service-name and module pairs.

        :return: The catalog items view.
        """
        return self._modules.items()

    @property
    def modules(self) -> dict[str, Module]:
        """
        Gets a copy of the loaded modules.

        A copy prevents web code from mutating the loaded catalog.

        :return: Loaded modules indexed by service name.
        """
        return self._modules.copy()


class PluginLoader:
    """
    Loads and validates service packages from the workspace modules directory.
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

    def load_all(self) -> ServiceCatalog:
        """
        Discovers, validates, and loads every service plugin.

        :return: The catalog of loaded service modules.
        :raises ValueError: If more than one plugin exposes the same service name.
        """
        modules_path = self.workspace.ensure_directory("modules")
        loaded: dict[str, Module] = {}
        for path in modules_path.iterdir():
            if not path.is_dir() or path.name.startswith("."):
                continue
            logger.info("Loading service plugin %s", path)
            module = Module(module_path=path, workspace=self.workspace, runtime_manager=self.runtime_manager)
            module.load_module()
            name = module.service.NAME
            if name in loaded:
                raise ValueError(f"Duplicate service name: {name}")
            loaded[name] = module
        return ServiceCatalog(loaded)
