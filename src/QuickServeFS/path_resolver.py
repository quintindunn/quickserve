import platform
from pathlib import Path
import os
from typing import Callable, Any


PathType = str | Path | os.PathLike[str] | os.PathLike[bytes]

ROOT_PATH_TABLE: dict[str, Path] = {
    "Windows": Path.home() / ".quickserve",
    "Darwin": Path("/opt/quickserve"),
    "Linux": Path("/opt/quickserve"),
}


def _generate_root():
    system = platform.system()
    if system not in ("Windows", "Darwin", "Linux"):
        raise NotImplementedError(f"OS {platform.system()} is not supported!")
    elif system == "Windows":
        raise NotImplementedError(f"Windows is currently not supported!")

    return ROOT_PATH_TABLE[platform.system()]


class Resolver:
    def __init__(self, root: PathType | None = None):
        if root is None:
            root = _generate_root()

        self.root = root
        self._ensure_directory(root)

    def get_path(self, path: PathType):
        path = Path(path)
        if path.is_absolute():
            return path
        else:
            return self.root / path

    def _ensure_directory(self, path: PathType):
        path = Path(path)

        if path.is_absolute():
            new = path
        else:
            new = self.root / path

        new.mkdir(exist_ok=True)
        return new.absolute()

    def ensure_file_path(self, path: PathType) -> Path:
        path = Path(path)

        if path.is_absolute():
            self._ensure_directory(path.parent)
            return path.absolute()

        path = self.root / path
        self._ensure_directory(path.parent)

        return path.absolute()

    def call_if_not_exist(
        self,
        path: PathType,
        callback: Callable,
        args: list[Any] = None,
        kwargs: dict[str, Any] = None,
    ):
        path = self.get_path(path)
        if not os.path.exists(path=path):
            if args is None:
                args = list()
            if kwargs is None:
                kwargs = dict()
            callback(*args, **kwargs)

    @property
    def config(self):
        return self.root / "config.yml"


resolver = Resolver()
