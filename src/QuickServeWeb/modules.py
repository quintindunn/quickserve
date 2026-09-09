from flask import (
    Blueprint,
    current_app,
    render_template_string,
    url_for,
    send_file,
    request,
    redirect,
)

from QuickServeDriver.instance.base_instance import BaseInstance

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from QuickServeFS.path_resolver import Resolver
    from QuickServeFS.modules import Service, Module

modules = Blueprint("modules", __name__, url_prefix="/module/")


def _render_module_page(module_name: str, method: str):
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

    if not hasattr(service, method):
        raise ValueError(f"Service {module_name} doesn't have method {method}")

    method = getattr(service, method)

    values = method()

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

    def action_(method: str):
        return url_for("modules.action", module_name=module_name, method=method)

    return render_template_string(
        str(template), context=ctx, resource=resource, link=link, action=action_
    )


@modules.route("/<module_name>")
def module_about(module_name: str):
    return _render_module_page(module_name, "about")


@modules.route("/<module_name>/create")
def module_create(module_name: str):
    return _render_module_page(module_name, "create")


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
    service: "Service" = module.service

    if not hasattr(service, method):
        return "500", 500

    method = getattr(service, method)

    values = method(BaseInstance, **request.form.to_dict())
    code = 302

    if isinstance(values, tuple) and len(values) == 2 and isinstance(values[1], int):
        code = values[1]
        endpoint = values[0]
    elif isinstance(values, str):
        endpoint = values
    else:
        raise ValueError(f"Invalid response from action {module_name}.{action}")

    url = url_for(
        f"modules.module_{endpoint}",
        module_name=module_name,
    )
    return redirect(url, code=code)
