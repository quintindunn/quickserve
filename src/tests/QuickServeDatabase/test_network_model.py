import unittest
import uuid
from datetime import datetime

from peewee import SqliteDatabase

from QuickServeDatabase.network import OccupiedPortModel


class TestOccupiedPort(unittest.TestCase):

    def setUp(self):
        # Use an isolated in-memory database for every test.
        self.db = SqliteDatabase(":memory:")

        # Temporarily point the model at our test database.
        self.db.bind([OccupiedPortModel])
        self.db.connect()
        self.db.create_tables([OccupiedPortModel])

    def tearDown(self):
        OccupiedPortModel.delete().execute()
        self.db.drop_tables([OccupiedPortModel])
        self.db.close()

    def test_create_occupied_port(self):
        service_uuid = uuid.uuid4()
        created_on = datetime.now()

        occupied_port = OccupiedPortModel.create(
            port=8080,
            service_uuid=service_uuid,
            created_on=created_on,
        )

        self.assertIsNotNone(occupied_port.id)
        self.assertEqual(occupied_port.port, 8080)
        self.assertEqual(occupied_port.service_uuid, service_uuid)
        self.assertEqual(occupied_port.created_on, created_on)

    def test_retrieve_occupied_port(self):
        service_uuid = uuid.uuid4()

        OccupiedPortModel.create(
            port=8080,
            service_uuid=service_uuid,
            created_on=datetime.now(),
        )

        occupied_port = OccupiedPortModel.get(OccupiedPortModel.port == 8080)

        self.assertEqual(occupied_port.port, 8080)
        self.assertEqual(occupied_port.service_uuid, service_uuid)

    def test_multiple_occupied_ports(self):
        service_uuid = uuid.uuid4()

        OccupiedPortModel.create(
            port=8080,
            service_uuid=service_uuid,
            created_on=datetime.now(),
        )

        OccupiedPortModel.create(
            port=8443,
            service_uuid=service_uuid,
            created_on=datetime.now(),
        )

        ports = list(OccupiedPortModel.select().order_by(OccupiedPortModel.port))

        self.assertEqual(len(ports), 2)
        self.assertEqual(ports[0].port, 8080)
        self.assertEqual(ports[1].port, 8443)

    def test_delete_occupied_port(self):
        occupied_port = OccupiedPortModel.create(
            port=8080,
            service_uuid=uuid.uuid4(),
            created_on=datetime.now(),
        )

        occupied_port.delete_instance()

        self.assertEqual(
            OccupiedPortModel.select().count(),
            0,
        )

    def test_port_cannot_be_null(self):
        with self.assertRaises(Exception):
            OccupiedPortModel.create(
                port=None,
                service_uuid=uuid.uuid4(),
                created_on=datetime.now(),
            )


if __name__ == "__main__":
    unittest.main()
