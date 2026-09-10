"""
PeeWee models for deployed instances.

Author: Quintin Dunn
Date: 09/09/2026
"""

from peewee import DateTimeField, UUIDField, Model

from datetime import datetime

from QuickServeDatabase.database import db


class InstanceModel(Model):
    """Model for registered instances."""

    service_uuid = UUIDField()
    created_on = DateTimeField(default=datetime.now)

    class Meta:
        database = db
