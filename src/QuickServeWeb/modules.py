from flask import Blueprint, current_app, render_template_string, url_for, send_file, request

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from QuickServeFS.path_resolver import Resolver
    from QuickServeFS.modules import Service, Module

modules = Blueprint("modules", __name__, url_prefix="/module/")


def _render_module_page(module_name: str):
    resolver: "Resolver" = current_app.config["resolver"]

    if module_name not in resolver.modules:
        return (
            "<!DOCTYPE HTML>"
            "<html><head><title>404 Not Found!</title></head>"
            "<body><h1>Page not found!</h1></body></html>"
        )

    module = resolver.modules[module_name]
    service: "Service" = module.service

    ctx = {
        "modules": resolver.modules,
        "module_name": service.NAME,
        "module_version": service.VERSION,
    }

    if hasattr(service, "AUTHORS"):
        ctx["module_authors"] = service.AUTHORS

    values = service.create()

    if isinstance(values, str):
        template = values

    elif isinstance(values, tuple):
        template, extra_ctx = values

        for key, value in extra_ctx.items():
            ctx[f"param_{key}"] = value

    else:
        template = "ERROR"

    def resource(filename: str):
        return url_for(
            "modules.resource",
            module_name=module_name,
            filename=filename,
        )

    def link(page: str):
        return url_for(
            f"modules.module_{page}",
            module_name=module_name,
        )

    def action(method: str):
        return ""

    return render_template_string(
        str(template),
        context=ctx,
        resource=resource,
        link=link,
        action=action
    )


@modules.route("/<module_name>")
def module_about(module_name: str):
    return _render_module_page(module_name)


@modules.route("/<module_name>/create")
def module_create(module_name: str):
    return _render_module_page(module_name)


@modules.route("/resources/<module_name>/<filename>")
def resource(module_name: str, filename: str):
    resolver: "Resolver" = current_app.config["resolver"]
    module: "Module" = resolver.modules[module_name]

    file_path = module.get_resource_path(filename)

    return send_file(file_path)


@modules.route("/action/<module_name>/<method>", methods=["POST"])
def action(module_name: str, method: str):
    resolver: "Resolver" = current_app.config["resolver"]
    module: "Module" = resolver.modules[module_name]

    print(method)