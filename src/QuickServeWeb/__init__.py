from pathlib import Path

from flask import Flask

from QuickServeWeb.home import home
from QuickServeWeb.modules import modules

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from QuickServeFS.config import Config
    from QuickServeFS.path_resolver import Resolver


def create_app(cfg: "Config"):
    root_dir = Path(__file__).resolve().parent
    template_dir = root_dir / "templates"
    static_dir = root_dir / "static"

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    if any(
        not hasattr(v, k)
        for k, v in {"secret_key": cfg.web, "file_path": cfg.database}.items()
    ):
        raise Exception("Invalid Config")

    app.config["SECRET_KEY"] = cfg.web.secret_key
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite://{cfg.database.file_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.register_blueprint(home)
    app.register_blueprint(modules)
    app.config["resolver"]: Resolver = cfg.resolver

    return app
