from typing import Callable

from QuickServe.Web.module_common.factories.link import link_builder
from QuickServe.Web.module_common.factories.action import action_builder
from QuickServe.Web.module_common.factories.resource import resource_builder


class Registry:
    registered: dict[str, Callable]

    def __init__(self):
        self.registered = dict()

        # self.register("simple_controller", simple_controller_builder)
        self.register("action", action_builder)
        self.register("link", link_builder)
        self.register("resource", resource_builder)

    def register(self, key: str, value: Callable):
        self.registered[key] = value
