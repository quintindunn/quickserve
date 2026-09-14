"""
Path helper class, os-independent.

Author: Quintin Dunn
Date: 09/09/20206
"""

import platform
from pathlib import Path
import os
from typing import Callable, Any
import stat

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


class Workspace:
    """
    Manages filesystem paths and directories for a QuickServe installation.
    """

    def __init__(self, root: PathType | None = None):
        """
        Initializes the workspace and ensures its root directory exists.

        :param root: The workspace root, or the platform default when omitted.
        :return: None
        """
        if root is None:
            root = _get_root()

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

# Maintains compatibility for callers using the Resolver name.
Resolver = Workspace
