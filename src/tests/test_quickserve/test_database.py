"""
Tests the peewee database

Author: Quintin Dunn
Date: 10/02/2026
"""

import unittest
import uuid

from QuickServe.Database.database import create_database, initialize, connect
from QuickServe.Database.models import MODELS
from QuickServe.Database.instances import InstanceModel
from QuickServe.Database.repositories import PeeweeInstanceManager
from QuickServe.contracts import InstanceRecord


class TestDatabase(unittest.TestCase):
    DB_PATH = ":memory:"

    def setUp(self):
        """
        Sets up an in memory database for each test.
        """

        self.database = create_database(file_path=self.DB_PATH)
        initialize(database=self.database)
        connect(database=self.database)
        self.database.create_tables(models=MODELS)

        self.addCleanup(self.database.close)

    def test_db_connect(self):
        """
        Tests connecting to the database.
        """

        self.assertTrue(self.database.is_closed() is False)

    def test_db_create_tables(self):
        """
        Tests creating database tables.
        """

        self.assertEqual(
            set(self.database.get_tables()),
            {model._meta.table_name for model in MODELS},
        )

    def test_db_create_instance_direct(self):
        """
        Tests creating instances by direct insertion into the database.
        """

        instance_uuid = uuid.uuid4()

        InstanceModel.create(
            instance_uuid=instance_uuid,
            instance_name="Test instance",
            module_name="test_database.py",
        )

        record = (
            InstanceModel.select()
            .where(InstanceModel.instance_uuid == instance_uuid)
            .first()
        )

        self.assertIsNotNone(record)
        self.assertEqual(record.instance_uuid, instance_uuid)
        self.assertEqual(record.instance_name, "Test instance")
        self.assertEqual(record.module_name, "test_database.py")

    def test_db_peewee_instance_manager_create(self):
        """
        Tests instance creating through the PeeweeInstanceManager.
        """

        instance_manager = PeeweeInstanceManager()
        instance_uuid = uuid.uuid4()

        instance_record = InstanceRecord(
            instance_uuid=instance_uuid,
            instance_name="Test instance 2",
            module_name="test_database.py",
        )

        instance_manager.create(instance_record)

        record = (
            InstanceModel.select()
            .where(InstanceModel.instance_uuid == instance_uuid)
            .first()
        )

        self.assertIsNotNone(record)
        self.assertEqual(record.instance_uuid, instance_uuid)
        self.assertEqual(record.instance_name, "Test instance 2")
        self.assertEqual(record.module_name, "test_database.py")

    def test_db_peewee_instance_manager_get(self):
        """
        Tests instance getting through the PeeweeInstanceManager.
        """

        instance_manager = PeeweeInstanceManager()
        instance_uuid = uuid.uuid4()

        InstanceModel.create(
            instance_uuid=instance_uuid,
            instance_name="Test instance 3",
            module_name="test_database.py",
        )

        record = instance_manager.get(instance_uuid)

        self.assertIsNotNone(record)
        self.assertEqual(record.instance_uuid, instance_uuid)
        self.assertEqual(record.instance_name, "Test instance 3")
        self.assertEqual(record.module_name, "test_database.py")

    def test_db_peewee_instance_manager_get_missing(self):
        """
        Tests getting an instance that does not exist.
        """

        instance_manager = PeeweeInstanceManager()

        self.assertTrue(hasattr(InstanceModel, "DoesNotExist"))
        with self.assertRaises(
            InstanceModel.DoesNotExist
        ):  # noqa - PyCharm gets angry at this.
            instance_manager.get(uuid.uuid4())

    def test_db_peewee_instance_manager_load_all(self):
        """
        Tests loading all instances through the PeeweeInstanceManager.
        """

        instance_manager = PeeweeInstanceManager()
        instance_uuids = set()

        for i in range(50):
            instance_uuid = uuid.uuid4()
            instance_uuids.add(instance_uuid)

            InstanceModel.create(
                instance_uuid=instance_uuid,
                instance_name=f"Test instance {i}",
                module_name="test_database.py",
            )

        records = instance_manager.load_all()

        self.assertEqual(len(records), 50)
        self.assertEqual(
            {record.instance_uuid for record in records},
            instance_uuids,
        )

        for record in records:
            self.assertEqual(record.module_name, "test_database.py")
