"""
Path helper class, os-independent. This class also holds module discovery, and loading.
TODO: Rework module discovery/loading to make less misplaced.

Author: Quintin Dunn
Date: 09/09/20206
"""

import platform
from pathlib import Path
import os
from typing import Callable, Any
import stat

from QuickServeFS.modules import Module

import logging

logger = logging.getLogger("QuickServerFS.Resolver")

PathType = str | Path | os.PathLike[str]

ROOT_PATH_TABLE: dict[str, Path] = {
    "Windows": Path.home() / ".quickserve",
    "Darwin": Path("/opt/quickserve"),
    "Linux": Path("/opt/quickserve"),
}


def _get_root() -> Path:
    """
    Gets the root working directory based off of OS.

    :return: The path to the root directory
    """

    system = platform.system()
    if system not in ("Windows", "Darwin", "Linux"):
        raise NotImplementedError(f"OS {platform.system()} is not supported!")
    elif system == "Windows":
        raise NotImplementedError(f"Windows is currently not supported!")

    root_dir = ROOT_PATH_TABLE[platform.system()]
    logger.info(f"Root directory: {root_dir}")
    return root_dir


class Resolver:
    modules: dict

    def __init__(self, root: PathType | None = None):
        if root is None:
            root = _get_root()

        self.modules = dict()
        self.root: Path = Path(root)
        self.ensure_directory(root)

    def get_path(self, path: PathType) -> Path:
        """
        Gets the path to a file/directory. Starting relative paths
        in the work directory of QuickServe.

        :param path: The path to get the absolute version of.
        :return: The absolute path.
        """
        path = Path(path)
        if path.is_absolute():
            return path
        else:
            return self.root / path

    def ensure_directory(self, path: PathType) -> Path:
        """
        Ensures that a directory exists,
        if it doesn't it creates the directory
        and changes permissions where applicable.

        :param path: The path to the directory.
        :return: The absolute path to the directory.
        """
        logger.debug(f"Ensuring directory {path.__str__()}")
        path = Path(path)

        if path.is_absolute():
            new = path
        else:
            new = self.root / path

        if not new.exists():
            new.mkdir(parents=True)
            logger.debug(f"Making directory {self.get_path(new)}")

        if platform.system() != "Windows":
            mode = stat.S_IMODE(new.stat().st_mode)
            if mode != 0o755:
                logger.debug(f"Changing permissions of {self.get_path(new)} to 755")
                new.chmod(0o755)
        return new.absolute()

    def ensure_file_path(self, path: PathType) -> Path:
        """
        Ensures that the parent directory of a file exists,
        if it doesn't it calls Resolver.ensure_directory on the directory.

        :param path: The path to the file
        :return: the absolute path of the file.
        """
        path = Path(path)

        if path.is_absolute():
            self.ensure_directory(path.parent)
            return path.absolute()

        path = self.root / path
        self.ensure_directory(path.parent)

        return path.absolute()

    def call_if_not_exist(
        self,
        path: PathType,
        callback: Callable,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> None:
        """
        Calls a callback function if a given path doesn't exist.
        :param path: The path that is being checked
        :param callback: The callback function being called if the path doesn't exist.
        :param args: The args passed into the callback.
        :param kwargs: The kwargs passed into the callback.

        :return: None
        """

        path = self.get_path(path)
        if not os.path.exists(path=path):
            if args is None:
                args = list()
            if kwargs is None:
                kwargs = dict()
            callback(*args, **kwargs)

    def discover_and_load_modules(self) -> None:
        """
        Discovers all modules in the modules directory, and creates and loads a new Module instance.

        :return: None
        """

        logger.debug("Discovering modules")
        modules_path = self.get_path("modules")
        self.ensure_directory(modules_path)

        self.modules.clear()

        dirs = [
            item for item in modules_path.iterdir() if item.is_dir(follow_symlinks=True)
        ]

        logger.debug(f"Discovered {len(dirs)} modules")

        logger.debug("Loading modules")
        for dir_ in dirs:
            logger.info(f"Loading {dir_}")
            module = Module(module_path=dir_, resolver=self)
            module.load_module()

            self.modules[module.service.NAME] = module

    @property
    def config_path(self) -> Path:
        """
        :return: The path to the config file
        """
        return self.root / "config.yml"


resolver = Resolver()
resolver.discover_and_load_modules()
