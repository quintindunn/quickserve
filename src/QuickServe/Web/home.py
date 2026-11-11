"""
The home blueprint for QuickServe

Author: Quintin Dunn
Date: 09/09/2026
"""

from flask import Blueprint, render_template, send_from_directory, current_app, request, redirect, url_for
from flask.typing import ResponseReturnValue
from flask_login import current_user, login_user, logout_user
from peewee import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from typing import TYPE_CHECKING

from QuickServeModuleLibrary.forms.datatypes import String
from QuickServeModuleLibrary.forms.forms import QSForm
from QuickServe.Database.users import UserModel

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
        if current_user.is_authenticated:
            return redirect(url_for("home.index"))
        has_users = UserModel.select().exists()
        return render_template("authentication/login.html", context={"has_users": has_users})

    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    user = UserModel.get_or_none(UserModel.username == username)

    if user is None or not check_password_hash(user.password_hash, password):
        return render_template(
            "authentication/login.html", error="Invalid username or password."
        ), 401

    login_user(user)
    return redirect(url_for("home.index"))


@home.route("/create", methods=["GET", "POST"])
def create_account() -> ResponseReturnValue:
    if request.method == "GET":
        return render_template("authentication/create.html")

    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    if len(username) <= 4 or len(username) >= 20:
        return render_template(
            "authentication/create.html",
            error="Username must be between 4 and 20 characters.",
        ), 400
    if len(password) <= 5 or len(password) >= 32:
        return render_template(
            "authentication/create.html",
            error="Password must be between 5 and 32 characters.",
        ), 400
    if UserModel.get_or_none(UserModel.username == username) is not None:
        return render_template(
            "authentication/create.html", error="That username is already taken."
        ), 409

    try:
        UserModel.create(
            username=username,
            password_hash=generate_password_hash(password),
        )
    except IntegrityError:
        return render_template(
            "authentication/create.html", error="That username is already taken."
        ), 409

    return redirect(url_for("home.login"))


@home.route("/logout", methods=["POST"])
def logout() -> ResponseReturnValue:
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for("home.login"))


@home.route("/favicon.ico")
def favicon() -> ResponseReturnValue:
    return send_from_directory(
        "static", "core/QuickServe.ico", mimetype="image/vnd.microsoft.icon"
    )
