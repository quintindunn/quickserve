"""
The api blueprint for QuickServe

Author: Quintin Dunn
Date: 10/06/2026
"""

from flask import Blueprint, request, current_app
from flask.typing import ResponseReturnValue

from QuickServe.Common.search import Search

api = Blueprint("api", __name__, url_prefix="/api/v1")

@api.route("/search")
def search() -> ResponseReturnValue:
    query = request.args.get("query")

    if not query:
        return ""
    search: Search = current_app.extensions["quickserve.search"]

    modules, instances = search.search(query=query, max_results=5)
    print(f"{modules=} {instances=}")

    return "hello world"