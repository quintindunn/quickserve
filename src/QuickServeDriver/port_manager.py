from QuickServeFS.config import config
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from QuickServeDriver.instance.base_instance import BaseInstance

from enum import Enum


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


class PortManager:
    ports: list[Port]
    websocket_ports: dict[str, Port]

    def __init__(self):
        self.ports = list()
        self.websocket_ports = dict()

        self.last_websocket_port = config.web.websocket_port_range_start

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

        if usage_type == UsageType.websocket:
            self.websocket_ports[key] = port

        return port

    def request_websocket_port(self, instance: "BaseInstance") -> Port | None:
        if str(instance.uuid) in self.websocket_ports:
            return self.websocket_ports[str(instance.uuid)]

        while self.last_websocket_port + 1 > config.web.websocket_port_range_end:
            self.last_websocket_port += 1
            if not self.is_port_occupied(self.last_websocket_port):
                return self.register_port(
                    port=self.last_websocket_port,
                    usage_type=UsageType.websocket,
                    key=str(instance.uuid),
                )

        return None


port_manager = PortManager()