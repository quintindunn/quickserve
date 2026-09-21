import datetime
from typing import Callable
from markupsafe import Markup

from QuickServe.Web.module_common.resources import get_resource
from flask import current_app, request


def simple_filesystem_builder(
    module_name: str
) -> Callable[[], str]:
    resource: str = get_resource("simple_filesystem.html", mode="r")

    def format_date(dt: datetime.datetime):
        return dt.strftime("%m/%d/%Y %I:%M:%S%p")

    def simple_filesystem():
        assert hasattr(request, "instance")

        # TODO: Get the files dynamically
        files = [
            {
                "filename": "foo.txt",
                "modified": format_date(datetime.datetime.now()),
                "size": "124.2kb"
            },
            {
                "filename": "bar.txt",
                "modified": format_date(datetime.datetime.now()),
                "size": "23.2kb"
            },
            {
                "filename": "foobar.txt",
                "modified": format_date(datetime.datetime.now()),
                "size": "11.1kb"
            }
        ]

        template = current_app.jinja_env.from_string(resource)
        context = {
            "module_name": module_name,
            "files": files,
            "root_directory": "/",
        }
        return Markup(template.render(context=context))

    return simple_filesystem
