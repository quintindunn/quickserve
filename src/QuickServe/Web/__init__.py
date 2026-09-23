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
from QuickServe.Web.module_common.registry import Registry
from QuickServe.contracts import WebSettings

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from QuickServe.FileSystem.plugins import ServiceCatalog
    from QuickServe.Application.instances import InstanceService
    from QuickServe.Driver.networking.websocket import WebsocketServer


def create_app(
    settings: WebSettings,
    catalog: "ServiceCatalog",
    instance_service: "InstanceService",
    websocket_server: "WebsocketServer",
) -> Flask:
    """
    Creates a Flask application from already-constructed dependencies.

    :param settings: The web settings used to configure Flask.
    :param catalog: The catalog of loaded service plugins.
    :param instance_service: The application service used by instance routes.
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
    app.extensions["quickserve.catalog"] = catalog
    app.extensions["quickserve.instance_service"] = instance_service
    app.extensions["quickserve.websocket_server"] = websocket_server
    app.extensions["quickserve.template_registry"] = Registry(websocket_server)

    @app.context_processor
    def global_context():
        # catalog = current_app.extensions["quickserve.catalog"]
        # instance_service = current_app.extensions["quickserve.instance_service"]
        ctx = {"modules": catalog.modules, "services": list()}
        for instance in instance_service.load_all():
            ctx["services"].append({
                "uuid": instance.uuid,
                "name": instance.service_name,
                "url": url_for("modules.instances.module_instance", uuid=instance.uuid, page="about")
            })
        return ctx

    return app
