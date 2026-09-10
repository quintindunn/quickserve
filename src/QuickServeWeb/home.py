"""
The home blueprint for QuickServe

Author: Quintin Dunn
Date: 09/09/2026
"""

from flask import Blueprint, render_template, current_app, ResponseReturnValue

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from QuickServeFS.path_resolver import Resolver

home = Blueprint("home", __name__)


@home.route("/")
def index() -> ResponseReturnValue:
    resolver: "Resolver" = current_app.config["resolver"]
    ctx = {"modules": resolver.modules}
    return render_template("home/home.html", context=ctx)
