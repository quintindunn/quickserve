from flask import Blueprint, render_template, current_app

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from QuickServeFS.path_resolver import Resolver

modules = Blueprint("modules", __name__, url_prefix="/module/")


@modules.route("/<module_name>")
def module(module_name: str):
    resolver: "Resolver" = current_app.config["resolver"]
    ctx = {"modules": resolver.modules}

    if module_name not in resolver.modules:
        return "<!DOCTYPE HTML><html><head><title>404 Not Found!</title></head><body><h1>Page not found!</h1></body></html>"

    return render_template("home/home.html", context=ctx)
