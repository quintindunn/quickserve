from flask import Blueprint, current_app, render_template_string, url_for, send_file

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from QuickServeFS.path_resolver import Resolver
    from QuickServeFS.modules import Service, Module

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

    about_template = service.about()

    def resource(filename: str):
        return url_for("modules.resource", module_name=module_name, filename=filename)

    return render_template_string(about_template, context=ctx, resource=resource)


@modules.route("/resources/<module_name>/<filename>")
def resource(module_name: str, filename: str):
    resolver: "Resolver" = current_app.config["resolver"]
    module: "Module" = resolver.modules[module_name]

    file_path = module.get_resource_path(filename)

    return send_file(file_path)