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
    start_callback: Callable[["ManagedProcess"], bool]
    _instance_process_map: dict["UUID", "ManagedProcess"]

    def __init__(self):
        # self.start_callback = start_callback
        # , start_callback: Callable[["ManagedProcess"], bool]
        self._instance_process_map = dict()

    def has_instance(self, instance: "BaseInstance"):
        return instance.uuid in self._instance_process_map

    def register(self, instance: "BaseInstance", process: "ManagedProcess"):
        self._instance_process_map[instance.uuid] = process

    def on_message(self, msg: str, instance: "BaseInstance"):
        logger.debug(f"New message for instance {instance.uuid}")
        msg = json.loads(msg)
        is_simple_controller = msg.get("isSimpleController") == True
        if not is_simple_controller:
            return

        msg_type = msg.get("type")

        process = self._instance_process_map.get(instance.uuid)

        if msg_type == "start":
            self.on_start(instance=instance)
        elif (process is None) or (not process.is_alive()):
            logger.debug("Not continuing checks, process it dead or non-existent.")
            return
        elif msg_type == "stop":
            self.on_stop(instance=instance)
        elif msg_type == "kill":
            self.on_kill(instance=instance)
        elif msg_type == "command":
            self.on_command(instance=instance, command=msg.get("raw"))
        else:
            logger.warning(f"Unknown message type {msg_type}")

    def on_start(self, instance: "BaseInstance"):
        process: "ManagedProcess" = self._instance_process_map[instance.uuid]
        logger.info(f"Starting process {instance.uuid}")
        if process.proc is None:
            process.start()
            return

        if not process.is_alive():
            process.start()
            return

        logger.info(f"Process already started {instance.uuid}")

    def on_stop(self, instance: "BaseInstance"):
        process: "ManagedProcess" = self._instance_process_map[instance.uuid]
        logger.info(f"Stopping process for {instance.uuid}")
        if process.is_alive():
            process.terminate()
        logger.info(f"Proces already dead {instance.uuid}")

    def on_kill(self, instance: "BaseInstance"):
        process: "ManagedProcess" = self._instance_process_map[instance.uuid]
        logger.info(f"Killing process {instance.uuid}")
        if process.is_alive():
            process.kill()
        logger.info(f"Process already dead {instance.uuid}")

    def on_command(self, instance: "BaseInstance", command: str):
        logger.info(
            f"Sending command {command[:32]}{'...' if len(command) > 32 else ''} to process {instance.uuid}"
        )
        process: "ManagedProcess" = self._instance_process_map[instance.uuid]
        if not process.is_alive():
            return
        process.write(command.encode())
