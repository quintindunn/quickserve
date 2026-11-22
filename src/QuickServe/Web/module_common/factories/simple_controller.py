from typing import Callable, TYPE_CHECKING

from flask_login import current_user
from markupsafe import Markup

from QuickServe.Database.users import UserModel
from QuickServe.Web.module_common.resources import get_resource
from flask import current_app, request

if TYPE_CHECKING:
    from QuickServe.Driver.networking.websocket import WebsocketServer
    from QuickServe.FileSystem.config import Config
    from QuickServe.Driver.networking.token_manager import WebsocketTokenManager

def simple_controller_builder(
    module_name: str,
    websocket_server: "WebsocketServer",
    config: "Config",
    token_manager: "WebsocketTokenManager",
    _: str | None = None,
) -> Callable[[], str]:
    resource: str = get_resource("simple_controller.html", mode="r")

    def simple_controller():
        assert hasattr(request, "instance")

        template = current_app.jinja_env.from_string(resource)

        token = ""
        if hasattr(current_app, "login_manager"):
            user_id = current_user.get_id()
            user = UserModel.select().where(UserModel.id == user_id).first()

            token = token_manager.generate_token(user=user)

        context = {
            "module_name": module_name,
            "websocket_port": websocket_server.port,
            "websocket_token": token,
            "terminal_buffer": config.web.simple_controller_terminal_buffer,
        }

        return Markup(template.render(context=context))

    return simple_controller
