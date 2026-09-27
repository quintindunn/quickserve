"""
The module blueprint for installed services

Author: Quintin Dunn
Date: 09/09/2026
"""

import base64
import os.path
import shutil

from flask import (
    Blueprint,
    current_app,
    render_template_string,
    url_for,
    send_file,
    request,
    redirect,
)
from flask.typing import ResponseReturnValue

from QuickServe.Driver.networking.websocket import WebsocketServer
from QuickServe.Driver.instance.base_instance import BaseInstance
from QuickServe.contracts import Service

from pathlib import Path

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from QuickServe.Application.instances import InstanceService

modules = Blueprint("modules", __name__, url_prefix="/module/")
instances = Blueprint("instances", __name__, url_prefix="/instance/")
instance_static = Blueprint("instancestatic", __name__, url_prefix="/instancestatic/")
modules.register_blueprint(instances)
modules.register_blueprint(instance_static)


# TODO: Add check for invalid page.
def _render_module_page(
    module_name: str,
    page: str,
    context: dict | None = None,
) -> ResponseReturnValue:
    """
    Helper function to render a module's pages, along with helper functions, and base context values.

    :param module_name: The name of the module being rendered.
    :param page: The page being rendered.
    :return: The rendered page.
    """
    catalog = current_app.extensions["quickserve.catalog"]

    if context is None:
        context = dict()

    if module_name not in catalog:
        return (
            "<!DOCTYPE HTML>"
            "<html><head><title>RMP 404 Not Found!</title></head>"
            "<body><h1>Page not found!</h1></body></html>"
        )

    module = catalog.require(module_name)
    service = module.service

    websocket_server: "WebsocketServer" = current_app.extensions[
        "quickserve.websocket_server"
    ]

    ctx = {
        "module_name": service.NAME,
        "module_version": service.VERSION,
        "module_pages": service.PAGES,
        "websocket_host": websocket_server.host,
        "websocket_port": websocket_server.port,
    }

    if hasattr(service, "AUTHORS"):
        ctx["module_authors"] = service.AUTHORS

    if not hasattr(service, page):
        raise ValueError(f"Service {module_name} doesn't have method {page}")

    page = getattr(service, page)
    if "instance_uuid" in context:

        def build_callback():
            def callback(message: str):
                return websocket_server.send_instance(context["instance_uuid"], message)

            return callback

        values = page(send_callback=build_callback())
    else:
        values = page()

    if isinstance(values, str):
        template = values

    elif isinstance(values, tuple):
        template, extra_ctx = values

        for key, value in extra_ctx.items():
            ctx[f"param_{key}"] = value

    else:
        template = "ERROR"

    for key, value in context.items():
        ctx[key] = value

    kwargs = {}

    registry = current_app.extensions["quickserve.template_registry"]
    if "instance_uuid" in context:
        for key, builder in registry.registered.items():
            kwargs[key] = builder(module_name, context["instance_uuid"])
    else:
        for key, builder in registry.registered.items():
            kwargs[key] = builder(module_name)

    return render_template_string(str(template), context=ctx, **kwargs)


@modules.route("/<module_name>")
def module_about(module_name: str) -> ResponseReturnValue:
    """
    Route for the about page returned from Service.about.

    :param module_name: The name of the module being rendered.
    :return: the rendered page.
    """
    return _render_module_page(module_name, "about")


@modules.route("/<module_name>/<page>")
def module_page(module_name: str, page: str) -> ResponseReturnValue:
    """
    Route for the custom pages registered in Service.PAGES.

    :param module_name: The name of the module being rendered.
    :param page: The page to render
    :return: The rendered page.
    """
    return _render_module_page(module_name, page=page)


def get_instance_from_db(uuid: str):
    return current_app.extensions["quickserve.instance_service"].from_uuid(uuid)


@instances.route("/<uuid>/<page>")
def module_instance(uuid: str, page: str) -> ResponseReturnValue:
    instance = get_instance_from_db(uuid=uuid)
    setattr(request, "instance", instance)
    ctx = {"instance_uuid": instance.uuid, "service_name": instance.service_name}
    return _render_module_page(module_name=instance.module_name, page=page, context=ctx)


@modules.route("/resources/<module_name>/<filename>")
def resource(module_name: str, filename: str) -> ResponseReturnValue:
    """
    Route for serving resources within modules.

    :param module_name: The module that holds the resource.
    :param filename: The filename/path for the resource being rendered.
    :return: The resource being served.
    """
    catalog = current_app.extensions["quickserve.catalog"]
    module = catalog.require(module_name)

    file_path = module.get_resource_path(filename)

    return send_file(file_path)


@modules.route("/action/<module_name>/<method>", methods=["POST"])
def action(module_name: str, method: str) -> ResponseReturnValue:
    """
    Calls an action within a given module.

    ** Kwargs that are in the current request are passed into the action **
    :param module_name: The module that holds the action.
    :param method: The action being called.
    :return:
    """
    method = f"action_{method}"

    catalog = current_app.extensions["quickserve.catalog"]
    module = catalog.require(module_name)
    service: "Service" = module.service

    if not hasattr(service, method):
        return "500", 500

    method = getattr(service, method)

    instance_service = current_app.extensions["quickserve.instance_service"]
    values = method(instance_service, **request.form.to_dict())
    code = 302

    instance = None
    if isinstance(values, tuple) and len(values) >= 2 and isinstance(values[1], int):
        code = values[1]
        endpoint = values[0]
        if len(values) >= 3:
            instance = values[2]
            assert isinstance(instance, BaseInstance)
    elif isinstance(values, str):
        endpoint = values
    else:
        raise ValueError(f"Invalid response from action {module_name}.{action}")

    if instance is not None:
        url = url_for(
            "modules.instances.module_instance", uuid=instance.uuid, page=endpoint
        )
    else:
        url = url_for("modules.module_page", module_name=service.NAME, page=endpoint)
    return redirect(url, code=code)


def _get_file(instance: BaseInstance, filepath: str) -> Path | None:
    fs_root = getattr(instance.module.service, "FS_ROOT", "")
    working_dir = (instance.working_directory() / fs_root).resolve()
    file = (working_dir / filepath.rstrip("/")).resolve()

    if (
        not file.is_relative_to(working_dir)
        or not file.exists()
        or not file.is_file()
    ):
        return None

    return file



@instance_static.route("/<uuid>/savefile/", methods=["POST"])
def instance_save_file(uuid: str):
    data = request.get_json()
    filepath = data.get("filepath")
    content = data.get("content")

    if not filepath:
        return {"error": "Missing filepath"}, 400
    if not content:
        return {"error": "Missing content"}, 400

    instance_service: "InstanceService" = current_app.extensions[
        "quickserve.instance_service"
    ]
    instance = instance_service.from_uuid(uuid)

    file = _get_file(instance, str(filepath))
    if file is None:
        return {"error": "File not found!"}, 400

    with open(file, "wb") as f:
        f.write(base64.b64decode(content))

    return "ok", 200


@instance_static.route("/<uuid>/downloadfile/", methods=["POST"])
def instance_download_file(uuid: str):
    data = request.get_json()
    filepath = data.get("filepath")

    if not filepath:
        return {"error": "Missing filepath"}, 400

    instance_service: "InstanceService" = current_app.extensions[
        "quickserve.instance_service"
    ]
    instance = instance_service.from_uuid(uuid)

    file = _get_file(instance, str(filepath))
    if file is None:
        return {"error": "File not found!"}, 400

    return send_file(file)


@instance_static.route("/<uuid>/deletefile/", methods=["POST"])
def instance_delete_file(uuid: str):
    data = request.get_json()
    filepath = data.get("filepath")

    if not filepath:
        return {"error": "Missing filepath"}, 400

    instance_service: "InstanceService" = current_app.extensions[
        "quickserve.instance_service"
    ]
    instance = instance_service.from_uuid(uuid)

    file = _get_file(instance, str(filepath))
    if file is None:
        return {"error": "File not found!"}, 400

    os.remove(file)
    return "ok", 200

@instance_static.route("/<uuid>/renamefile/", methods=["POST"])
def instance_rename_file(uuid: str):
    data = request.get_json()
    cwd = data.get("cwd")
    src = data.get("src")
    dst = data.get("dst")

    if not cwd:
        return {"error": "Missing current working directory"}, 400
    if not src:
        return {"error": "Missing source file"}, 400
    if not dst:
        return {"error": "Missing destination file"}, 400

    if "/" in src:
        return {"error": "Invalid source file"}, 400
    if "/" in dst:
        return {"error": "Invalid destination file"}, 400

    instance_service: "InstanceService" = current_app.extensions[
        "quickserve.instance_service"
    ]
    instance = instance_service.from_uuid(uuid)

    fs_root = getattr(instance.module.service, "FS_ROOT", "")
    working_dir = (instance.working_directory() / fs_root).resolve()
    src_file = (working_dir / cwd.lstrip("/") / src).resolve()
    dst_file = (working_dir / cwd.lstrip("/") / dst).resolve()

    if (
        not src_file.is_relative_to(working_dir)
        or not src_file.exists()
        or not src_file.is_file()
    ):
        return {"error": "Missing source file"}, 400

    if not dst_file.is_relative_to(working_dir):
        return {"error": "Invalid destination file"}, 400

    if dst_file.exists():
        return {"error": "Destination file already exists"}, 400

    shutil.move(src_file, dst_file)

    return "ok", 200

