"""
The api blueprint for QuickServe

Author: Quintin Dunn
Date: 10/06/2026
"""

from flask import Blueprint, request, current_app
from flask.typing import ResponseReturnValue

from QuickServe.FileSystem.plugins import ModuleCatalog

api = Blueprint("api", __name__, url_prefix="/api/v1")

@api.route("/search")
def search() -> ResponseReturnValue:
    query = request.args.get("query")

    if not query:
        return ""
    catalog: ModuleCatalog = current_app.extensions["quickserve.catalog"]

    modules = catalog.items()



    return "hello world"