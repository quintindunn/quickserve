"""
Creates and restores QuickServe service instances.

Author: Quintin Dunn
Date: 09/14/2026
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generator
from uuid import UUID, uuid4

from QuickServe.contracts import InstanceRecord, InstanceRepository
from QuickServe.Driver.instance.base_instance import BaseInstance

if TYPE_CHECKING:
    from QuickServe.FileSystem.path_resolver import Workspace
    from QuickServe.FileSystem.plugins import ServiceCatalog


class InstanceService:
    """
    Creates, restores, and tracks service instances.
    """

    def __init__(
        self,
        catalog: ServiceCatalog,
        workspace: Workspace,
        repository: InstanceRepository,
    ) -> None:
        """
        Initializes the service instance manager.

        :param catalog: The loaded service catalog.
        :param workspace: The workspace used for instance files.
        :param repository: The persistence implementation for instance records.
        :return: None
        """
        self.catalog = catalog
        self.workspace = workspace
        self.repository = repository
        self._instances: dict[str, BaseInstance] = {}

    def new_service(self, module_name: str, service_name: str) -> BaseInstance:
        """
        Creates and persists a service instance.

        :param module_name: The loaded service module name.
        :param service_name: The user-facing name of the instance.
        :return: The newly created instance.
        """
        module = self.catalog.require(module_name)
        identifier = uuid4()
        record = self.repository.create(
            InstanceRecord(
                service_uuid=identifier,
                service_name=service_name,
                module_name=module_name,
            )
        )
        return self._build(
            module, record.service_name, record.module_name, record.service_uuid
        )

    def from_uuid(self, identifier: str | UUID) -> BaseInstance:
        """
        Gets an instance from memory or reconstructs it from persistence.

        :param identifier: The UUID of the requested instance.
        :return: The requested instance.
        """
        key = str(identifier)
        if key in self._instances:
            return self._instances[key]

        record = self.repository.get(identifier)
        module = self.catalog.require(record.module_name)
        return self._build(
            module, record.service_name, record.module_name, record.service_uuid
        )

    def load_all(self) -> Generator[BaseInstance, Any, None]:
        for record in self.repository.load_all():
            module = self.catalog.require(record.module_name)
            yield self._build(
                module, record.service_name, record.module_name, record.service_uuid
            )

    def _build(
        self, module, service_name: str, module_name: str, identifier: UUID
    ) -> BaseInstance:
        """
        Builds an instance and assigns its websocket port.

        :param module: The loaded service module.
        :param service_name: The user-facing name of the instance.
        :param module_name: The loaded service module name.
        :param identifier: The UUID of the instance.
        :return: The constructed instance.
        :raises RuntimeError: If no websocket ports are available.
        """
        instance = BaseInstance(
            base_module=module,
            service_name=service_name,
            module_name=module_name,
            uuid=identifier,
            workspace=self.workspace,
        )
        self._instances[str(identifier)] = instance
        return instance
