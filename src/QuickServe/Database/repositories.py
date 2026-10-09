"""
Peewee manager for QuickServe data.

Author: Quintin Dunn
Date: 09/14/2026
"""

from uuid import UUID

from QuickServe.contracts import InstanceRecord
from QuickServe.Database.instances import InstanceModel


class PeeweeInstanceManager:
    """
    Stores and retrieves instance records.
    """

    def create(self, record: InstanceRecord) -> InstanceRecord:
        """
        Stores a instance record.

        :param record: The instance data to persist.
        :return: The persisted instance data.
        """
        model = InstanceModel.create(
            instance_uuid=record.instance_uuid,
            instance_name=record.instance_name,
            module_name=record.module_name,
        )
        return self._record(model)

    def get(self, identifier: str | UUID) -> InstanceRecord:
        """
        Gets a persisted instance record.

        :param identifier: The UUID of the requested instance.
        :return: The matching instance data.
        """
        model = InstanceModel.get(InstanceModel.instance_uuid == identifier)
        return self._record(model)

    def load_all(self) -> list[InstanceRecord]:
        """
        Gets all instances from the database.

        :return: List of all instance records.
        """
        models = InstanceModel.select()
        return [self._record(model) for model in models]

    @staticmethod
    def _record(model: InstanceModel) -> InstanceRecord:
        """
        Converts a Peewee model into persistence-neutral instance data.

        :param model: The Peewee instance model.
        :return: The corresponding instance record.
        """
        return InstanceRecord(
            instance_uuid=model.instance_uuid,
            instance_name=model.instance_name,
            module_name=model.module_name,
        )
