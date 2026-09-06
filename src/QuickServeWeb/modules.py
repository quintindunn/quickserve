from flask import Blueprint, render_template, current_app

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from QuickServeFS.path_resolver import Resolver
    from QuickServeFS.modules import Service

modules = Blueprint("modules", __name__, url_prefix="/module/")


@modules.route("/<module_name>")
def module_about(module_name: str):
    resolver: "Resolver" = current_app.config["resolver"]
    ctx = {
        "modules": resolver.modules,
    }

    if module_name not in resolver.modules:
        return "<!DOCTYPE HTML><html><head><title>404 Not Found!</title></head><body><h1>Page not found!</h1></body></html>"

    module = resolver.modules[module_name]
    service: "Service" = module.service
    ctx["module_name"] = resolver.modules[module_name].service.NAME
    ctx["module_version"] = service.VERSION
    ctx["module_about"] = service.about()
    return render_template("modules/about.html", context=ctx)
