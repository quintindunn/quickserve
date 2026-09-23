"""
The home blueprint for QuickServe

Author: Quintin Dunn
Date: 09/09/2026
"""

from flask import Blueprint, render_template, current_app, url_for
from flask.typing import ResponseReturnValue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from QuickServe.Driver.instance.base_instance import BaseInstance

home = Blueprint("home", __name__)


@home.route("/")
def index() -> ResponseReturnValue:
    ctx = {}
    return render_template("home/home.html", context=ctx)
