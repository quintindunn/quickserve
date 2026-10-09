"""
Registration of common module functions

Author: Quintin Dunn
Date: 09/27/2026
"""

import typing
from typing import Callable

from QuickServe.Web.module_common.factories.link import link_builder
from QuickServe.Web.module_common.factories.action import action_builder
from QuickServe.Web.module_common.factories.resource import resource_builder
from QuickServe.Web.module_common.factories.simple_controller import (
    simple_controller_builder,
)
from QuickServe.Web.module_common.factories.simple_fs import simple_filesystem_builder

if typing.TYPE_CHECKING:
    from QuickServe.Driver.networking.websocket import WebsocketServer


class Registry:
    """
    Registry holds all registered common module functions.
    """

    registered: dict[str, Callable]

    def __init__(self, websocket_server: "WebsocketServer"):
        self.registered = dict()
        self.websocket_server = websocket_server

        self.register(
            "simple_controller",
            lambda module_name, _=None: simple_controller_builder(
                module_name, websocket_server
            ),
        )
        self.register(
            "simple_filesystem",
            lambda module_name, _=None: simple_filesystem_builder(
                module_name=module_name
            ),
        )
        self.register("action", action_builder)
        self.register("link", link_builder)
        self.register("resource", resource_builder)

    def register(self, key: str, value: Callable):
        self.registered[key] = value
