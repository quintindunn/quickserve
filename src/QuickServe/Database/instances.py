"""
PeeWee models for deployed instances.

Author: Quintin Dunn
Date: 09/09/2026
"""

from peewee import DateTimeField, UUIDField, Model, CharField

from datetime import datetime

from QuickServe.Database.database import db


class InstanceModel(Model):
    """Model for registered instances."""

    service_uuid = UUIDField(null=False)
    service_name = CharField(null=False)
    module_name = CharField(null=False)
    created_on = DateTimeField(default=datetime.now)

    class Meta:
        database = db
