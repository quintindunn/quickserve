"""
Models used by networking in QuickServe.

Author: Quintin Dunn
Date: 09/17/2026
"""

from websockets.asyncio.server import ServerConnection
from dataclasses import dataclass

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from QuickServe.Database.users import UserModel


@dataclass
class InstanceWebsocketConnection:
    instance_uuid: str
    remote_host: str
    remote_port: int
    user: "UserModel | None"
    is_authenticated: bool
    connection: ServerConnection

    def __hash__(self):
        return hash(
            (
                self.instance_uuid,
                self.remote_host,
                self.remote_port,
            )
        )
