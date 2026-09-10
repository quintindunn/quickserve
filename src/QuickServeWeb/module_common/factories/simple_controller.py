from typing import Callable

from markupsafe import Markup

from QuickServeWeb.module_common.resources import get_resource

from flask import current_app


def simple_controller_builder(module_name: str) -> Callable[[], str]:
    resource: str = get_resource("simple_controller.html", mode="r")

    def simple_controller():
        template = current_app.jinja_env.from_string(resource)
        context = {"module_name": module_name}
        return Markup(template.render(context=context))

    return simple_controller
