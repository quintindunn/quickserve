from peewee import DateTimeField, UUIDField, IntegerField, Model, BooleanField

from QuickServeDatabase.database import db


class OccupiedPortModel(Model):
    port = IntegerField(null=False)
    TCP = BooleanField(default=False)
    UDP = BooleanField(default=True)
    service_uuid = UUIDField()
    created_on = DateTimeField()

    class Meta:
        database = db
