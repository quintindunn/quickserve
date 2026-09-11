from abc import ABC

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from QuickServeDriver.instance.base_instance import BaseInstance


class SimpleControllerProcessor(ABC):
    @staticmethod
    def on_message(instance: "BaseInstance", message: str):
        """"""

    @staticmethod
    def send_message(message: str):
        """"""