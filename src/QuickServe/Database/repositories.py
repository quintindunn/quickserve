"""
Peewee manager for QuickServe data.

Author: Quintin Dunn
Date: 09/14/2026
"""
import logging
from uuid import UUID

from QuickServe.contracts import InstanceRecord
from QuickServe.Database.instances import InstanceModel


logger = logging.getLogger(__name__)

class PeeweeInstanceManager:
    """
    Stores and retrieves instance records.
    """

    def create(self, record: InstanceRecord) -> InstanceRecord:
        """
        Stores an instance record.

        :param record: The instance data to persist.
        :return: The persisted instance data.
        """
        model = InstanceModel.create(
            instance_uuid=record.instance_uuid,
            instance_name=record.instance_name,
            module_name=record.module_name,
            active=True
        )
        return self._record(model)

    def get(self, identifier: str | UUID) -> InstanceRecord:
        """
        Gets a persisted instance record.

        :param identifier: The UUID of the requested instance.
        :return: The matching instance data.
        """
        logger.info("Getting instance %", identifier)
        model = InstanceModel.get(InstanceModel.instance_uuid == identifier).get(InstanceModel.active == True)
        return self._record(model)

    def load_all_active(self) -> list[InstanceRecord]:
        """
        Gets all instances from the database.

        :return: List of all instance records.
        """
        models = InstanceModel.select().where(InstanceModel.active == True)
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
