from pathlib import Path
from typing import Union

from QuickServeWeb.module_common import resource_dir
from QuickServeWeb.module_common.exceptions import ResourceDoesntExistException


def get_resource(resource_name: str, mode: str = "r") -> Union[str, bytes]:
    root = Path(resource_dir.__file__).parent

    file = root / resource_name

    if not file.exists() or not file.is_file():
        raise ResourceDoesntExistException(
            f'Resource "{resource_name}" not found in {root}!'
        )

    with open(file, mode=mode) as f:
        return f.read()
