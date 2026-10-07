import unittest
from unittest.mock import MagicMock
from uuid import UUID, uuid4

from QuickServe.Application.instances import InstanceManager
from QuickServe.contracts import InstanceRecord


class TestInstanceManager(unittest.TestCase):
    def setUp(self):
        self.catalog = MagicMock()
        self.workspace = MagicMock()
        self.repository = MagicMock()

        self.manager = InstanceManager(
            catalog=self.catalog,
            workspace=self.workspace,
            repository=self.repository,
        )

        self.module = MagicMock()
        self.catalog.require.return_value = self.module

    def test_new_instance(self):
        identifier = uuid4()

        self.repository.create.return_value = InstanceRecord(
            instance_uuid=identifier,
            instance_name="Test Instance",
            module_name="TestModule",
        )

        instance = self.manager.new_instance(
            "TestModule",
            "Test Instance",
        )

        self.catalog.require.assert_called_once_with("TestModule")
        self.repository.create.assert_called_once()

        record = self.repository.create.call_args.args[0]

        self.assertIsInstance(
            record.instance_uuid,
            UUID,
        )
        self.assertEqual(
            record.instance_name,
            "Test Instance",
        )
        self.assertEqual(
            record.module_name,
            "TestModule",
        )

        self.assertEqual(
            instance.instance_name,
            "Test Instance",
        )
        self.assertEqual(
            instance.module_name,
            "TestModule",
        )
        self.assertEqual(
            instance.uuid,
            identifier,
        )

    def test_get_from_uuid(self):
        identifier = uuid4()

        self.repository.get.return_value = InstanceRecord(
            instance_uuid=identifier,
            instance_name="Test Instance",
            module_name="TestModule",
        )

        result = self.manager.from_uuid(identifier)

        self.repository.get.assert_called_once_with(identifier)
        self.catalog.require.assert_called_once_with("TestModule")

        self.assertEqual(
            result.instance_name,
            "Test Instance",
        )
        self.assertEqual(
            result.module_name,
            "TestModule",
        )
        self.assertEqual(
            result.uuid,
            identifier,
        )

    def test_load_all(self):
        first_uuid = uuid4()
        second_uuid = uuid4()

        self.repository.load_all.return_value = [
            InstanceRecord(
                instance_uuid=first_uuid,
                instance_name="First",
                module_name="Module",
            ),
            InstanceRecord(
                instance_uuid=second_uuid,
                instance_name="Second",
                module_name="Module",
            ),
        ]

        instances = list(self.manager.load_all())

        self.assertEqual(len(instances), 2)

        self.assertEqual(
            instances[0].uuid,
            first_uuid,
        )
        self.assertEqual(
            instances[0].instance_name,
            "First",
        )

        self.assertEqual(
            instances[1].uuid,
            second_uuid,
        )
        self.assertEqual(
            instances[1].instance_name,
            "Second",
        )

        self.assertEqual(
            self.catalog.require.call_count,
            2,
        )

    def test_load_all_empty(self):
        self.repository.load_all.return_value = []

        instances = list(self.manager.load_all())

        self.assertEqual(instances, [])
