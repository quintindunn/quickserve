"""
The home blueprint for QuickServe

Author: Quintin Dunn
Date: 09/09/2026
"""

from flask import Blueprint, render_template
from flask.typing import ResponseReturnValue

home = Blueprint("home", __name__)


@home.route("/")
def index() -> ResponseReturnValue:
    return render_template("home/home.html", context={})
