"""
Helper function for getting resources in common module functions

Author: Quintin Dunn
Date: 09/27/2026
"""

from pathlib import Path
from typing import Union

from QuickServe.Web.module_common import resource_dir
from QuickServe.Web.module_common.exceptions import ResourceDoesntExistException


def get_resource(resource_name: str, mode: str = "r") -> Union[str, bytes]:
    """
    Gets a resource from the Web.module_common.resource_dir / {resource_name}
    :param resource_name: The name of the resource to read
    :param mode: The mode to open the resource file (inherited from open(... mode=mode))
    :return: String or Bytes depending on the mode
    """
    root = Path(resource_dir.__file__).parent

    file = root / resource_name

    if not file.exists() or not file.is_file():
        raise ResourceDoesntExistException(
            f'Resource "{resource_name}" not found in {root}!'
        )

    with open(file, mode=mode) as f:
        return f.read()
