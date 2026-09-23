"""
Peewee repositories for QuickServe data.

Author: Quintin Dunn
Date: 09/14/2026
"""

from uuid import UUID

from QuickServe.contracts import InstanceRecord
from QuickServe.Database.instances import InstanceModel


class PeeweeInstanceRepository:
    """
    Stores and retrieves service instance records.
    """

    def create(self, record: InstanceRecord) -> InstanceRecord:
        """
        Stores a service instance record.

        :param record: The instance data to persist.
        :return: The persisted instance data.
        """
        model = InstanceModel.create(
            service_uuid=record.service_uuid,
            service_name=record.service_name,
            module_name=record.module_name,
        )
        return self._record(model)

    def get(self, identifier: str | UUID) -> InstanceRecord:
        """
        Gets a persisted service instance record.

        :param identifier: The UUID of the requested instance.
        :return: The matching instance data.
        """
        model = InstanceModel.get(InstanceModel.service_uuid == identifier)
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
            service_uuid=model.service_uuid,
            service_name=model.service_name,
            module_name=model.module_name,
        )
