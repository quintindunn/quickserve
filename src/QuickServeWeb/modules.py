"""
The module blueprint for installed services

Author: Quintin Dunn
Date: 09/09/2026
"""

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


# TODO: Add check for invalid page.
def _render_module_page(module_name: str, page: str) -> str:
    """
    Helper function to render a module's pages, along with helper functions, and base context values.
    :param module_name: The name of the module being rendered.
    :param page: The page being rendered.
    :return: The rendered page.
    """
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

    if not hasattr(service, page):
        raise ValueError(f"Service {module_name} doesn't have method {page}")

    page = getattr(service, page)

    values = page()

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
    """
    Route for the about page returned from Service.about.
    :param module_name: The name of the module being rendered.
    :return: the rendered page.
    """
    return _render_module_page(module_name, "about")


@modules.route("/<module_name>/create")
def module_create(module_name: str):
    """
    Route for the create/installation page returned from Service.create.
    :param module_name: The name of the module being rendered.
    :return: The rendered page.
    """
    return _render_module_page(module_name, "create")


@modules.route("/resources/<module_name>/<filename>")
def resource(module_name: str, filename: str):
    """
    Route for serving resources within modules.
    :param module_name: The module that holds the resource.
    :param filename: The filename/path for the resource being rendered.
    :return: The resource being served.
    """
    resolver: "Resolver" = current_app.config["resolver"]
    module: "Module" = resolver.modules[module_name]

    file_path = module.get_resource_path(filename)

    return send_file(file_path)


@modules.route("/action/<module_name>/<method>", methods=["POST"])
def action(module_name: str, method: str):
    """
    Calls an action within a given module.

    ** Kwargs that are in the current request are passed into the action **
    :param module_name: The module that holds the action.
    :param method: The action being called.
    :return:
    """
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
