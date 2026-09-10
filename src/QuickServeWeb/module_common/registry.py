from typing import Callable

from QuickServeWeb.module_common.factories import (
    action_builder,
    link_builder,
    resource_builder,
    simple_controller_builder,
)


class Registry:
    registered: dict[str, Callable]

    def __init__(self):
        self.registered = dict()

        self.register("simple_controller", simple_controller_builder)
        self.register("action", action_builder)
        self.register("link", link_builder)
        self.register("resource", resource_builder)

    def register(self, key: str, value: Callable):
        self.registered[key] = value


registry = Registry()
