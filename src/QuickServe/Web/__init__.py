"""
Initializes, and configures the flask application

Author: Quintin Dunn
Date: 09/09/2026
"""

from pathlib import Path

from flask import Flask, request
from flask_login import current_user
from flask import url_for
from flask_login import LoginManager

from QuickServe.Common.search import Search
from QuickServe.Driver.networking.token_manager import WebsocketTokenManager
from QuickServe.Web.home import home
from QuickServe.Web.modules import modules
from QuickServe.Web.api import api
from QuickServe.Web.module_common.registry import Registry
from QuickServe.Database.users import UserModel

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from QuickServe.FileSystem.plugins import ModuleCatalog
    from QuickServe.Application.instances import InstanceManager
    from QuickServe.Driver.networking.websocket import WebsocketServer
    from QuickServe.FileSystem.config import Config


login_manager = LoginManager()
login_manager.login_view = "home.login"


@login_manager.user_loader
def load_user(user_id: str):
    try:
        return UserModel.get_or_none(UserModel.id == int(user_id))
    except (TypeError, ValueError):
        return None


def create_app(
    config: Config,
    catalog: "ModuleCatalog",
    instance_manager: "InstanceManager",
    websocket_server: "WebsocketServer",
    search_engine: "Search",
    token_manager: "WebsocketTokenManager",
) -> Flask:
    """
    Creates a Flask application from already-constructed dependencies.

    :param config: The QuickServe config.
    :param catalog: The catalog of loaded module instances.
    :param instance_manager: The application manager used by instance routes.
    :param websocket_server: The QuickServe websocket server
    :param search_engine: The TFIDF search engine
    :return: The configured Flask application.
    """

    root_dir = Path(__file__).resolve().parent
    template_dir = root_dir / "templates"
    static_dir = root_dir / "static"

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    if any(not hasattr(v, k) for k, v in {"secret_key": config.web}.items()):
        raise Exception("Invalid Config")

    app.config["SECRET_KEY"] = config.web.secret_key
    login_manager.init_app(app)

    @app.before_request
    def require_login():
        if request.endpoint == "home.create_account":
            if not UserModel.select().exists():
                return None
            return login_manager.unauthorized()

        public_endpoints = {
            "static",
            "home.index",
            "home.login",
            "home.favicon",
        }
        if current_user.is_authenticated or request.endpoint in public_endpoints:
            return None
        return login_manager.unauthorized()

    app.register_blueprint(home)
    app.register_blueprint(modules)
    app.register_blueprint(api)

    app.extensions["quickserve.catalog"] = catalog
    app.extensions["quickserve.instance_manager"] = instance_manager
    app.extensions["quickserve.websocket_server"] = websocket_server
    app.extensions["quickserve.template_registry"] = Registry(
        websocket_server=websocket_server, config=config, token_manager=token_manager
    )
    app.extensions["quickserve.search"] = search_engine

    @app.context_processor
    def global_context():
        ctx = {"modules": catalog.modules, "instances": list()}
        for instance in instance_manager.load_all():
            ctx["instances"].append(  # noqa
                {
                    "uuid": instance.uuid,
                    "name": instance.instance_name,
                    "url": url_for(
                        "modules.instances.module_instance",
                        uuid=instance.uuid,
                        page="about",
                    ),
                }
            )
        return ctx

    return app
