from typing import Callable, Any


def simple_controller_builder(module_name: str) -> Callable[[], str]:
    def simple_controller():
        return ""

    return simple_controller
