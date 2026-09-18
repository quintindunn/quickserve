from typing import Callable
from flask import url_for


def link_builder(module_name: str) -> Callable[[str], str]:
    def link(page: str) -> str:
        return url_for(f"modules.module_page", module_name=module_name, page=page)

    return link
