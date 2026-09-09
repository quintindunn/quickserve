from peewee import DateTimeField, UUIDField, Model

from datetime import datetime

from QuickServeDatabase.database import db


class InstanceModel(Model):
    service_uuid = UUIDField()
    created_on = DateTimeField(default=datetime.now)

    class Meta:
        database = db
