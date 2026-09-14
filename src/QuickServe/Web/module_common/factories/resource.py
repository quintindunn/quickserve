from typing import Callable

from flask import url_for


def resource_builder(module_name: str) -> Callable[[str], str]:
    def resource(filename: str) -> str:
        return url_for(
            "modules.resource",
            module_name=module_name,
            filename=filename,
        )

    return resource
