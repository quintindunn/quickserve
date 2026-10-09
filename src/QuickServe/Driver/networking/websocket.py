"""
Websocket server for communication with modules

Author: Quintin Dunn
Date: 09/17/2026
"""

import asyncio
import logging

from typing import TYPE_CHECKING

from websockets.asyncio.router import route
from werkzeug.routing import Map, Rule

from QuickServe.Driver.networking.websocket_handlers import instance_handler

from uuid import UUID

if TYPE_CHECKING:
    from QuickServe.Driver.networking.common import InstanceWebsocketConnection
    from QuickServe.Application.instances import InstanceManager
    from QuickServe.contracts import WebSettings


logger = logging.getLogger(__name__)

HOST = "0.0.0.0"
PORT = 5002




def wrap_endpoint(server, endpoint):
    def _endpoint(conn, *args, **kwargs):
        return endpoint(server, conn, *args, **kwargs)

    return _endpoint


class WebsocketServer:
    """
    Common websocket server for all modules streamed communication to backend.
    """

    host: str
    port: int
    router_map: Map
    _stop_flag: asyncio.Event
    _connection_instances: set["InstanceWebsocketConnection"]
    _instance_manager: "InstanceManager"
    _loop: asyncio.AbstractEventLoop | None

    def __init__(self, config: "WebSettings", instance_manager: "InstanceManager"):
        self.host = config.websocket_host
        self.port = config.websocket_port
        self.router_map = Map(
            [
                Rule(
                    "/instance/<string:instance_uuid>",
                    endpoint=wrap_endpoint(self, instance_handler),
                )
            ]
        )
        self._instance_manager = instance_manager
        self._stop_flag = asyncio.Event()
        self._connection_instances: set["InstanceWebsocketConnection"] = set()
        self._loop = None
        self._stop = asyncio.Event()

    def get_instance_manager(self):
        return self._instance_manager

    def send_instance(self, instance_uuid: UUID, message: str):
        if self._loop is None:
            raise ConnectionError("Server is not started!")

        logger.debug(f"Sending instance {instance_uuid} {message!r}")
        for connection in self._connection_instances:
            if UUID(connection.instance_uuid) == instance_uuid:
                asyncio.run_coroutine_threadsafe(
                    connection.connection.send(message), self._loop
                )

    def register_instance(
        self, connection_instance: "InstanceWebsocketConnection"
    ) -> None:
        if connection_instance in self._connection_instances:
            raise ValueError("Instance is already registered in WebsocketServer")
        self._connection_instances.add(connection_instance)

    async def start(self) -> None:
        """
        Starts the websocket server on WebsocketServer.host:WebsocketServer.port

        :return: None
        """

        self._loop = asyncio.get_running_loop()

        async with route(self.router_map, host=self.host, port=self.port):
            logger.info(f"Started websocket server on {self.host}:{self.port}")
            await self._stop.wait()
