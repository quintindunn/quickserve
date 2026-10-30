"""
The home blueprint for QuickServe

Author: Quintin Dunn
Date: 09/09/2026
"""

from flask import Blueprint, render_template, send_from_directory
from flask.typing import ResponseReturnValue

home = Blueprint("home", __name__)


@home.route("/")
def index() -> ResponseReturnValue:
    return render_template("home/home-first-time.html", context={})


@home.route("/favicon.ico")
def favicon() -> ResponseReturnValue:
    return send_from_directory(
        "static", "core/QuickServe.ico", mimetype="image/vnd.microsoft.icon"
    )
