"""
The api blueprint for QuickServe

Author: Quintin Dunn
Date: 10/06/2026
"""

from flask import Blueprint, render_template, redirect, current_app
from flask_login import current_user

from QuickServe.Database.users import UserModel

settings = Blueprint("settings", __name__, url_prefix="/settings")


@settings.route("/users/")
def user():
    if not current_user.is_admin:
        login_manager = current_app.extensions["quickserve.login_manager"]
        return login_manager.unauthorized()

    users = list(UserModel.select())
    return render_template("settings/users.html", context={"users": users})
