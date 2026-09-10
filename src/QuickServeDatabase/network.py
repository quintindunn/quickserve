"""
PeeWee models for network related records

Author: Quintin Dunn
Date: 09/09/2026
"""

from peewee import DateTimeField, UUIDField, IntegerField, Model, BooleanField

from QuickServeDatabase.database import db


class OccupiedPortModel(Model):
    """Model for an occupied port by a service."""

    port = IntegerField(null=False)
    TCP = BooleanField(default=False)
    UDP = BooleanField(default=True)
    service_uuid = UUIDField()
    created_on = DateTimeField()

    class Meta:
        database = db
