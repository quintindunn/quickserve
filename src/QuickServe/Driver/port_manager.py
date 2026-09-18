"""
Manages ports used by QuickServe, and QuickServe Services.

Author: Quintin Dunn
Date: 09/17/2026
"""

from QuickServe.contracts import WebSettings

from enum import Enum

import logging

logger = logging.getLogger("port_manager.py")


class UsageType(Enum):
    service = "service"
    websocket = "websocket"
    httpserver = "httpserver"


class Port:
    usage_type: UsageType
    port: int | range

    def __init__(self, usage_type: UsageType, port: int | range):
        assert (
            0 <= port <= 65535
            if isinstance(port, int)
            else (0 <= port.start <= 65535 and 0 <= port.stop <= 65536)
        )

        self.usage_type = usage_type
        self.port = port

    def __contains__(self, port: int) -> bool:
        return port in self.port if isinstance(self.port, range) else port == self.port

    def __str__(self):
        return f"Port(type: {self.usage_type}, port: {self.port})"


class PortManager:
    ports: list[Port]

    def __init__(self, settings: WebSettings):
        self.ports = list()

        self.settings = settings

    def free(self, port_to_free: int):
        for port in self.ports:
            if port.port == port_to_free:
                self.ports.remove(port)

    def is_port_occupied(self, target_port: int) -> bool:
        for port in self.ports:
            if target_port in port:
                return True
        return False

    def register_port(self, port: int, usage_type: UsageType, key: str | None) -> Port:
        if usage_type == UsageType.websocket and key is None:
            raise ValueError("Cannot register websocket port without key")

        assert not self.is_port_occupied(port)

        port = Port(usage_type=usage_type, port=port)
        self.ports.append(port)

        return port
