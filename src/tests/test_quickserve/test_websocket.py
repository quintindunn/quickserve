"""
Tests the websocket server.

Author: Quintin Dunn
Date: 10/08/2026
"""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID as UUIDType

from QuickServe.Driver.networking import websocket


UUID = "b92cea29-b309-401e-a878-161ada76f2f4"


class TestWebsocket(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.config.websocket_host = "0.0.0.0"
        self.config.websocket_port = 5000
        self.instance_manager = MagicMock()
        self.instance_manager.from_uuid = MagicMock(return_value=UUID)

        self.websocket_server = websocket.WebsocketServer(
            config=self.config,
            instance_manager=self.instance_manager,
        )

    def tearDown(self):
        if not self.websocket_server._stop.is_set():
            self.websocket_server.stop()

    def test_wrap_endpoint(self):
        def bar(server, conn):
            self.assertEqual(server, "foo")
            self.assertEqual(conn, "some_connection_info")

        wrapped_endpoint = websocket.wrap_endpoint("foo", bar)
        wrapped_endpoint("some_connection_info")

    def test_register_instance(self):
        connection = MagicMock()
        self.websocket_server.register_instance(connection)

        self.assertIn(
            connection,
            self.websocket_server._connection_instances,
        )

    def test_send_instance_server_not_started(self):
        with self.assertRaisesRegex(ConnectionError, "Server is not started!"):
            self.websocket_server.send_instance(UUIDType(UUID), "hello")

    def test_send_instance(self):
        connection = MagicMock()
        connection.instance_uuid = UUID
        connection.connection.send = AsyncMock()

        self.websocket_server._connection_instances.add(connection)
        self.websocket_server._loop = MagicMock()

        with patch.object(
            websocket.asyncio,
            "run_coroutine_threadsafe",
        ) as run_coroutine:
            self.websocket_server.send_instance(UUIDType(UUID), "hello")

        run_coroutine.assert_called_once()
        coroutine, loop = run_coroutine.call_args.args

        self.assertIs(loop, self.websocket_server._loop)
        connection.connection.send.assert_called_once_with("hello")
        coroutine.close()

    def test_send_instance_different_uuid(self):
        connection = MagicMock()
        connection.instance_uuid = "a92cea29-b309-401e-a878-161ada76f2f4"

        self.websocket_server._connection_instances.add(connection)
        self.websocket_server._loop = MagicMock()

        with patch.object(
            websocket.asyncio,
            "run_coroutine_threadsafe",
        ) as run_coroutine:
            self.websocket_server.send_instance(UUIDType(UUID), "hello")

        run_coroutine.assert_not_called()

    def test_stop(self):
        self.websocket_server.stop()

        self.assertTrue(self.websocket_server._stop.is_set())


class TestWebsocketAsync(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.config = MagicMock()
        self.config.websocket_host = "127.0.0.1"
        self.config.websocket_port = 5000
        self.instance_manager = MagicMock()

        self.websocket_server = websocket.WebsocketServer(
            config=self.config,
            instance_manager=self.instance_manager,
        )
