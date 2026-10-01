"""
Helper class for routing websocket messages between the ManagedProcess, and the websocket.

Author: Quintin Dunn
Date: 10/01/2026
"""

import json
import logging

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .process import ManagedProcess
    from QuickServe.Driver.instance.base_instance import BaseInstance
    from uuid import UUID

logger = logging.getLogger(__name__)


class SimpleControllerProcessManager:
    """
    Helper class to aid in routing websocket messages between ManagedProcess and the websocket.
    """

    start_callback: Callable[["ManagedProcess"], bool]
    _instance_process_map: dict["UUID", "ManagedProcess"]

    def __init__(self):
        """
        Instantiated the SimpleControllerProcessManager
        """

        self._instance_process_map = dict()

    def has_instance(self, instance: "BaseInstance") -> bool:
        """
        Checks if the manager has an instance's process made.
        :param instance: The instance to check if is contained in SimpleControllerProcessManager.
        :return: bool True if the instance is stored in the manager.
        """

        return instance.uuid in self._instance_process_map

    def register(self, instance: "BaseInstance", process: "ManagedProcess") -> None:
        """
        Registers a process in the manager.

        if there's an existing registration, it will attempt to kill it, and then overwrite it.

        :param instance: The instance for the process.
        :param process: The process to manage.
        :return: None
        """

        if self.has_instance(instance):
            existing = self._instance_process_map[instance.uuid]
            if existing.is_alive():
                existing.terminate()

        self._instance_process_map[instance.uuid] = process

    def on_message(self, msg: str, instance: "BaseInstance") -> bool:
        """
        Handles websocket messages
        :param msg: The websocket message
        :param instance: The instance corresponding to the message
        :return: True if the message was for a SimpleController, else False.
        """

        logger.debug(f"New message for instance {instance.uuid}")
        msg = json.loads(msg)
        is_simple_controller = msg.get("isSimpleController") == True
        if not is_simple_controller:
            return False

        msg_type = msg.get("type")

        process = self._instance_process_map.get(instance.uuid)

        if msg_type == "start":
            self._on_start(instance=instance)
        elif (process is None) or (not process.is_alive()):
            logger.debug("Not continuing checks, process it dead or non-existent.")
            return True
        elif msg_type == "stop":
            self._on_stop(instance=instance)
        elif msg_type == "kill":
            self._on_kill(instance=instance)
        elif msg_type == "command":
            self._on_command(instance=instance, command=msg.get("raw"))
        else:
            logger.warning(f"Unknown message type {msg_type}")

        return True

    def _on_start(self, instance: "BaseInstance") -> None:
        """
        Called when the websocket sends the process a `start` command, starts the process.

        :param instance: The instance which holds the process.
        :return: None
        """

        process: "ManagedProcess" = self._instance_process_map[instance.uuid]
        logger.info(f"Starting process {instance.uuid}")
        if process.proc is None:
            process.start()
            return

        if not process.is_alive():
            process.start()
            return

        logger.info(f"Process already started {instance.uuid}")

    def _on_stop(self, instance: "BaseInstance"):
        """
        Called when the websocket sends the process a `stop` command, stops the process.

        :param instance: The instance which holds the process.
        :return: None
        """

        process: "ManagedProcess" = self._instance_process_map[instance.uuid]
        logger.info(f"Stopping process for {instance.uuid}")
        if process.is_alive():
            process.terminate()
        logger.info(f"Proces already dead {instance.uuid}")

    def _on_kill(self, instance: "BaseInstance"):
        """
        Called when the websocket sends the process a `kill` command, kills the process.

        :param instance: The instance which holds the process.
        :return: None
        """

        process: "ManagedProcess" = self._instance_process_map[instance.uuid]
        logger.info(f"Killing process {instance.uuid}")
        if process.is_alive():
            process.kill()
        logger.info(f"Process already dead {instance.uuid}")

    def _on_command(self, instance: "BaseInstance", command: str):
        """
        Called when the websocket sends the process a `command` command, sends the process the command to stdin.

        :param instance: The instance which holds the process.
        :param command: The command to send to the stdin of the process.
        :return: None
        """

        logger.info(
            f"Sending command {command[:32]}{'...' if len(command) > 32 else ''} to process {instance.uuid}"
        )
        process: "ManagedProcess" = self._instance_process_map[instance.uuid]
        if not process.is_alive():
            return
        process.write(command.encode())
