"""
The home blueprint for QuickServe

Author: Quintin Dunn
Date: 09/09/2026
"""

from flask import Blueprint, render_template, send_from_directory, current_app, request, redirect, url_for
from flask.typing import ResponseReturnValue

from typing import TYPE_CHECKING

from QuickServeModuleLibrary.forms.datatypes import String
from QuickServeModuleLibrary.forms.forms import QSForm

if TYPE_CHECKING:
    from QuickServe.Application.instances import InstanceManager
    from QuickServe.FileSystem.plugins import ModuleCatalog

home = Blueprint("home", __name__)


class LoginForm(QSForm):
    username: String = String(placeholder="Username", required=True, minlength=4, maxlength=20)


@home.route("/")
def index() -> ResponseReturnValue:
    instance_manager: "InstanceManager" = current_app.extensions[
        "quickserve.instance_manager"
    ]
    module_catalog: "ModuleCatalog" = current_app.extensions["quickserve.catalog"]

    instances = list(instance_manager.load_all())
    modules = list(module_catalog.items())

    if (len(instances) + len(modules)) == 0:
        return render_template("home/home-first-time.html", context={})

    return render_template(
        "home/home-has-instances.html",
        context={"instances": instances, "modules": modules},
    )

@home.route("/login", methods=["GET", "POST"])
def login() -> ResponseReturnValue:
    if request.method == "GET":
        return render_template("authentication/login.html")
    elif request.method != "POST":
        return redirect(url_for("home.index"))

    username = request.form.get("username")
    password = request.form.get("password")


    return redirect(url_for("home.index"))


@home.route("/favicon.ico")
def favicon() -> ResponseReturnValue:
    return send_from_directory(
        "static", "core/QuickServe.ico", mimetype="image/vnd.microsoft.icon"
    )
