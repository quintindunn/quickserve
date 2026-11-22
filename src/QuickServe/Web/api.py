"""
The api blueprint for QuickServe

Author: Quintin Dunn
Date: 10/06/2026
"""

from flask import Blueprint, request, current_app, render_template, jsonify
from flask.typing import ResponseReturnValue
from flask_login import current_user

from QuickServe.Application.instances import InstanceManager
from QuickServe.Common.search import Search
from QuickServe.Database.users import UserModel
from QuickServe.FileSystem.plugins import ModuleCatalog

api = Blueprint("api", __name__, url_prefix="/api/v1")


@api.route("/search")
def search() -> ResponseReturnValue:
    query = request.args.get("query")

    if not query:
        return ""
    search_: Search = current_app.extensions["quickserve.search"]
    catalog: "ModuleCatalog" = current_app.extensions["quickserve.catalog"]
    instance_manager: "InstanceManager" = current_app.extensions[
        "quickserve.instance_manager"
    ]

    modules, instances = search_.search(query=query, max_results=5)
    modules = [catalog.get(module[0].identifier).module for module in modules]
    instances = [
        instance_manager.from_uuid(instance[0].identifier) for instance in instances
    ]

    if len(modules) == len(instances) == 0:
        return "", 204

    return render_template(
        "core/search.html", context={"modules": modules, "instances": instances}
    )

@api.route("/websocket-token")
def get_websocket_token() -> ResponseReturnValue:
    token_manager = current_app.extensions["quickserve.websocket_token_manager"]
    token = token_manager.generate_token(user=current_user)
    return jsonify({
        "token": token
    })

@api.route("/delete-user", methods=["POST"])
def delete_user() -> ResponseReturnValue:
    target = request.json.get("target", None)
    row: UserModel = UserModel.select().where(UserModel.username == target).first()
    if target is None or row is None:
        return jsonify({
            "error": "bad request"
        }), 400

    UserModel.delete_by_id(row.id)
    return "", 200
