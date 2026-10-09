"""
Tests the simple_controller backend

Author: Quintin Dunn
Date: 10/09/2026
"""

import json
import unittest
from unittest.mock import MagicMock
from uuid import uuid4

from QuickServeModuleLibrary.simple_controller import SimpleControllerProcessManager


class TestSimpleControllerProcessManager(unittest.TestCase):
    """
    Tests the simple controller process manager backend.
    """

    def setUp(self):
        self.manager = SimpleControllerProcessManager()

        self.instance = MagicMock()
        self.instance.uuid = uuid4()

        self.process = MagicMock()
        self.manager.register(self.instance, self.process)

    @staticmethod
    def _message(msg_type, **kwargs) -> str:
        """
        Simulates the data sent from a websocket message from the frontend.
        :param msg_type: The type of message.
        :param kwargs: Extra arguments for the JSON object.
        :return: string of the generated JSON.
        """

        return json.dumps({
            "isSimpleController": True,
            "type": msg_type,
            **kwargs,
        })

    def test_has_instance(self):
        """
        Tests that has correctly validates having instances.
        """

        self.assertTrue(self.manager.has_instance(self.instance))

        instance = MagicMock()
        instance.uuid = uuid4()

        self.assertFalse(self.manager.has_instance(instance))

    def test_register_terminates_existing_process(self):
        """
        Tests the backend terminates any existing process if it attempts to register an instance twice.
        """

        self.process.is_alive.return_value = True
        new_process = MagicMock()

        self.manager.register(self.instance, new_process)

        self.process.terminate.assert_called_once()
        self.assertIs(
            self.manager._instance_process_map[self.instance.uuid],
            new_process,
        )


    def test_on_message_start_forward(self):
        """
        Tests that the manager correctly forwards `start` messages.
        """

        self.manager._on_start = MagicMock()

        result = self.manager.on_message(
            self._message("start"),
            self.instance,
        )

        self.assertTrue(result)
        self.manager._on_start.assert_called_once_with(instance=self.instance)

    def test_on_message_stop(self):
        """
        Tests that the manager correctly forwards `stop` messages.
        """

        self.process.is_alive.return_value = True
        self.manager._on_stop = MagicMock()

        result = self.manager.on_message(
            self._message("stop"),
            self.instance,
        )

        self.assertTrue(result)
        self.manager._on_stop.assert_called_once_with(instance=self.instance)

    def test_on_message_command(self):
        """
        Tests that the manager correctly forwards `command` messages and their raw command.
        """

        self.process.is_alive.return_value = True
        self.manager._on_command = MagicMock()

        result = self.manager.on_message(
            self._message("command", raw="quickserve command"),
            self.instance,
        )

        self.assertTrue(result)
        self.manager._on_command.assert_called_once_with(
            instance=self.instance,
            command="quickserve command",
        )

    def test_on_message_ignores_dead_process(self):
        """
        Tests that the manager doesn't try to kill a dead horse- I mean process.
        """

        self.process.is_alive.return_value = False
        self.manager._on_stop = MagicMock()

        result = self.manager.on_message(
            self._message("stop"),
            self.instance,
        )

        self.assertTrue(result)
        self.manager._on_stop.assert_not_called()

    def test_on_start_starts_process(self):
        """
        Tests that _on_start attempts to start the process.
        """

        self.process.proc = None

        self.manager._on_start(self.instance)

        self.process.start.assert_called_once()

    def test_on_stop_terminates_process(self):
        """
        Tests that _on_start attempts to terminate the process.
        """

        self.process.is_alive.return_value = True

        self.manager._on_stop(self.instance)

        self.process.terminate.assert_called_once()

    def test_on_command_writes_to_process(self):
        """
        Tests that _on_command attempts to write to the process.
        """

        self.process.is_alive.return_value = True

        self.manager._on_command(self.instance, "quickserve command")

        self.process.write.assert_called_once_with(b"quickserve command")