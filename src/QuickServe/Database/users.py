"""
PeeWee models for registered users.

Author: Quintin Dunn
Date: 09/09/2026
"""

from peewee import Model, CharField, AutoField
from flask_login import UserMixin

from QuickServe.Database.database import database_proxy


class UserModel(UserMixin, Model):
    """Model for registered users."""

    id = AutoField()
    username = CharField(max_length=20, unique=True, null=False)
    password_hash = CharField(max_length=255, null=False)

    class Meta:
        database = database_proxy
