from typing import Callable
from markupsafe import Markup

from QuickServe.Driver.networking.websocket import WebsocketServer
from QuickServe.Web.module_common.resources import get_resource
from flask import current_app, request


def simple_controller_builder(
    module_name: str, websocket_server: "WebsocketServer"
) -> Callable[[], str]:
    resource: str = get_resource("simple_controller.html", mode="r")

    def simple_controller():
        assert hasattr(request, "instance")

        template = current_app.jinja_env.from_string(resource)
        context = {
            "module_name": module_name,
            "websocket_host": websocket_server.host,
            "websocket_port": websocket_server.port,
        }
        return Markup(template.render(context=context))

    return simple_controller
