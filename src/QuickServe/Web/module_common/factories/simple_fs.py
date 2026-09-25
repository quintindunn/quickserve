import datetime
import os
from typing import Callable
from markupsafe import Markup

from QuickServe.Driver.instance.base_instance import BaseInstance
from QuickServe.Web.module_common.resources import get_resource
from flask import current_app, request


def simple_filesystem_builder(
    module_name: str
) -> Callable[[], str]:
    resource: str = get_resource("simple_filesystem.html", mode="r")

    def format_date(dt: datetime.datetime):
        return dt.strftime("%m/%d/%Y %I:%M:%S%p")

    def simple_filesystem(root: str = "/"):
        assert hasattr(request, "instance")

        instance: "BaseInstance" = getattr(request, "instance")

        files = []

        working_dir = instance.working_directory() / root.lstrip("/")
        for file in os.listdir(working_dir):
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
