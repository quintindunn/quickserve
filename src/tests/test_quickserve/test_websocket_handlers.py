"""
Tests websocket handlers

Author: Quintin Dunn
Date: 10/08/2026
"""

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from QuickServe.Driver.networking import websocket_handlers

UUID = "b92cea29-b309-401e-a878-161ada76f2f4"


class TestInstanceHandler(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.server = MagicMock()
        self.connection = MagicMock()
        self.connection.remote_address = ("127.0.0.1", 54321)

        self.module = MagicMock()
        self.instance = SimpleNamespace(base_module=SimpleNamespace(module=self.module))

        self.server.get_instance_manager.return_value.from_uuid.return_value = (
            self.instance
        )

    async def test_instance_handler(self):
        messages = ["hello", "world"]

        async def receive_messages():
            for message in messages:
                yield message

        self.connection.__aiter__.side_effect = receive_messages

        with patch.object(websocket_handlers, "InstanceWebsocketConnection"):
            await websocket_handlers.instance_handler(
                self.server, self.connection, UUID
            )

        self.server.register_instance.assert_called_once()
        self.server.get_instance_manager.return_value.from_uuid.assert_called_once_with(
            UUID
        )
        self.assertEqual(
            self.module.on_message.call_args_list,
            [unittest.mock.call(message, self.instance) for message in messages],
        )

    async def test_instance_handler_without_on_message(self):
        del self.module.on_message

        async def receive_messages():
            yield "hello"
            yield "world"

        self.connection.__aiter__.side_effect = receive_messages

        with patch.object(websocket_handlers, "InstanceWebsocketConnection"):
            await websocket_handlers.instance_handler(
                self.server, self.connection, UUID
            )

        self.server.register_instance.assert_called_once()
