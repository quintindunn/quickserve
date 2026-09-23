"""
Defines shared interfaces and data structures for QuickServe services.

Author: Quintin Dunn
Date: 09/14/2026
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID
from typing import Any, Protocol, TypeAlias

PageResult: TypeAlias = str | tuple[str, dict[str, Any]]


class Service(Protocol):
    """
    Defines the required interface for a service plugin.
    """

    NAME: str
    VERSION: str
    QUICKSERVE_VERSION: str
    PAGES: list[str]

    def about(self, *args: Any, **kwargs: Any) -> PageResult: ...

    def create(self, *args: Any, **kwargs: Any) -> PageResult: ...


class WebSettings(Protocol):
    """
    Defines web settings used by QuickServe components.
    """

    secret_key: str
    websocket_port: int
    websocket_host: str


@dataclass(frozen=True, slots=True)
class InstanceRecord:
    """
    Stores identifying data for a service instance.
    """

    service_uuid: UUID
    service_name: str
    module_name: str


class InstanceRepository(Protocol):
    """
    Defines storage operations for service instances.
    """

    def create(self, record: InstanceRecord) -> InstanceRecord: ...

    def get(self, identifier: str | UUID) -> InstanceRecord: ...

    def load_all(self) -> list[InstanceRecord]: ...
