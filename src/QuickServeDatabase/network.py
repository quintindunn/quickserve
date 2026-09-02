from peewee import DateTimeField, UUIDField, IntegerField, Model

from QuickServeDatabase.database import db

class OccupiedPort(Model):
    port = IntegerField(null=False)
    service_uuid = UUIDField()
    created_on = DateTimeField()

    class Meta:
        database = db