from peewee import DateTimeField, UUIDField, IntegerField, Model, ForeignKeyField

from QuickServeDatabase.database import db
from QuickServeDatabase.network import OccupiedPortModel

class ServiceModel(Model):
    port = ForeignKeyField(OccupiedPortModel, backref="service")
    service_uuid = UUIDField()
    created_on = DateTimeField()

    class Meta:
        database = db