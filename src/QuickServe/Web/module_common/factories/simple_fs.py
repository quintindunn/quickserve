import datetime
from typing import Callable
from markupsafe import Markup

from QuickServe.Web.module_common.resources import get_resource
from flask import current_app, request


def simple_filesystem_builder(
    module_name: str
) -> Callable[[], str]:
    resource: str = get_resource("simple_filesystem.html", mode="r")

    def simple_filesystem():
        assert hasattr(request, "instance")

        # TODO: Get the files dynamically
        files = [
            {
                "filename": "foo.txt",
                "modified": datetime.datetime.now().isoformat()
            },
            {
                "filename": "bar.txt",
                "modified": datetime.datetime.now().isoformat()
            },
            {
                "filename": "foobar.txt",
                "modified": datetime.datetime.now().isoformat()
            }
        ]

        template = current_app.jinja_env.from_string(resource)
        context = {
            "module_name": module_name,
            "files": files

        }
        return Markup(template.render(context=context))

    return simple_filesystem
