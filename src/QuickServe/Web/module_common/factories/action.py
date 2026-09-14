from typing import Callable
from flask import url_for


def action_builder(module_name: str) -> Callable[[str], str]:
    def action(method: str) -> str:
        return url_for("modules.action", module_name=module_name, method=method)

    return action
