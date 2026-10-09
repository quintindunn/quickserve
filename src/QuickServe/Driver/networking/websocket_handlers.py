"""
Handlers for the websocket server

Author: Quintin Dunn
Date: 09/17/2026
"""

import logging

from uuid import UUID
from typing import TYPE_CHECKING

from websockets.asyncio.server import ServerConnection

from QuickServe.Driver.networking.common import InstanceWebsocketConnection
from QuickServe.contracts import Module

if TYPE_CHECKING:
    from QuickServe.Driver.networking.websocket import WebsocketServer


logger = logging.getLogger(__name__)


async def instance_handler(
    server: "WebsocketServer", connection: "ServerConnection", instance_uuid: str
) -> None:
    """
    Handles connections from frontend of instances. Routes messages to their respective backend instance.
    :param server: The WebsocketServer caller.
    :param connection: The connection to the client.
    :param instance_uuid: The UUID to the instance referenced from the client.
    :return: None
    """
    logger.info(f"New connecting from instance {instance_uuid}")
    instance_websocket_object = InstanceWebsocketConnection(
        instance_uuid=instance_uuid,
        authentication="",
        is_authenticated=False,
        remote_host=connection.remote_address[0],
        remote_port=connection.remote_address[1],
        connection=connection,
    )

    server.register_instance(instance_websocket_object)

    instance_manager = server.get_instance_manager()
    instance = instance_manager.from_uuid(instance_uuid)
    module: "Module" = instance.base_module.module

    async for message in connection:
        if not hasattr(module, "on_message"):
            break
        module.on_message(message, instance)  # noqa
        logger.debug(
            f"New message from {connection.remote_address} - {message[:32]}{'...' if len(message) > 32 else ''}"
        )
