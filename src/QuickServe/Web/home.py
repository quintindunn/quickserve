"""
The home blueprint for QuickServe

Author: Quintin Dunn
Date: 09/09/2026
"""

from flask import Blueprint, render_template, current_app
from flask.typing import ResponseReturnValue

home = Blueprint("home", __name__)


@home.route("/")
def index() -> ResponseReturnValue:
    catalog = current_app.extensions["quickserve.catalog"]
    ctx = {"modules": catalog.modules}
    return render_template("home/home.html", context=ctx)
