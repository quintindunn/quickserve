"""
Initializes, and configures the flask application

Author: Quintin Dunn
Date: 09/09/2026
"""

from pathlib import Path

from flask import Flask
from flask import url_for

from QuickServe.Web.home import home
from QuickServe.Web.modules import modules
from QuickServe.Web.api import api
from QuickServe.Web.module_common.registry import Registry
from QuickServe.contracts import WebSettings

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from QuickServe.FileSystem.plugins import ModuleCatalog
    from QuickServe.Application.instances import InstanceManager
    from QuickServe.Driver.networking.websocket import WebsocketServer


def create_app(
    settings: WebSettings,
    catalog: "ModuleCatalog",
    instance_manager: "InstanceManager",
    websocket_server: "WebsocketServer",
) -> Flask:
    """
    Creates a Flask application from already-constructed dependencies.

    :param settings: The web settings used to configure Flask.
    :param catalog: The catalog of loaded module instances.
    :param instance_manager: The application manager used by instance routes.
    :return: The configured Flask application.
    """

    root_dir = Path(__file__).resolve().parent
    template_dir = root_dir / "templates"
    static_dir = root_dir / "static"

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    if any(not hasattr(v, k) for k, v in {"secret_key": settings}.items()):
        raise Exception("Invalid Config")

    app.config["SECRET_KEY"] = settings.secret_key

    app.register_blueprint(home)
    app.register_blueprint(modules)
    app.register_blueprint(api)

    app.extensions["quickserve.catalog"] = catalog
    app.extensions["quickserve.instance_manager"] = instance_manager
    app.extensions["quickserve.websocket_server"] = websocket_server
    app.extensions["quickserve.template_registry"] = Registry(websocket_server)

    @app.context_processor
    def global_context():
        ctx = {"modules": catalog.modules, "instances": list()}
        for instance in instance_manager.load_all():
            ctx["instances"].append(
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
