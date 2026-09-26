import datetime
import os
from pathlib import Path
from typing import Callable
from markupsafe import Markup

from QuickServe.Driver.instance.base_instance import BaseInstance
from QuickServe.Web.module_common.resources import get_resource
from flask import current_app, request


def validate_path(instance_root: Path, requested_path: Path) -> bool:
    """
    Checks if the requested path should be visible to the client.
    :param instance_root: The root of the instance that is being requested's working dir.
    :param requested_path: The requested path.
    :return: True if they should have access, otherwise False.
    """
    requested_path = requested_path.resolve()

    if not requested_path.is_relative_to(instance_root):
        return False

    return True


def simple_filesystem_builder(
    module_name: str
) -> Callable[[], str]:
    resource: str = str(get_resource("simple_filesystem.html", mode="r"))

    def format_date(dt: datetime.datetime):
        return dt.strftime("%m/%d/%Y %I:%M:%S%p")

    def simple_filesystem(root: str = "/"):
        assert hasattr(request, "instance")

        instance: "BaseInstance" = getattr(request, "instance")

        files = []

        working_dir = instance.working_directory() / root.lstrip("/")

        is_valid = validate_path(instance.working_directory(), working_dir)
        for file in os.listdir(working_dir) if is_valid else []:
            file_path = working_dir / file
            files.append({
                "filename": file,
                "modified": format_date(datetime.datetime.fromtimestamp(os.path.getmtime(file_path))),
                "size": f"{os.stat(file_path).st_size / 1000:.1f}kb",
                "isFile": os.path.isfile(file_path),
                "isDir": os.path.isdir(file_path)
            })

        template = current_app.jinja_env.from_string(resource)
        context = {
            "module_name": module_name,
            "files": files,
            "root_directory": "/",
        }
        return Markup(template.render(context=context))

    return simple_filesystem
