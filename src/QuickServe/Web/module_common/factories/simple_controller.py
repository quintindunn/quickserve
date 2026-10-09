import socket
from typing import Callable
from markupsafe import Markup

from QuickServe.Driver.networking.websocket import WebsocketServer
from QuickServe.Web.module_common.resources import get_resource
from flask import current_app, request

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]


def simple_controller_builder(
    module_name: str, websocket_server: "WebsocketServer", _: str | None = None
) -> Callable[[], str]:
    resource: str = get_resource("simple_controller.html", mode="r")

    def simple_controller():
        assert hasattr(request, "instance")

        template = current_app.jinja_env.from_string(resource)

        websocket_host = websocket_server.host

        if websocket_host == "0.0.0.0":
            websocket_host = local_ip
        context = {
            "module_name": module_name,
            "websocket_host": websocket_host,
            "websocket_port": websocket_server.port,
        }
        return Markup(template.render(context=context))

    return simple_controller
