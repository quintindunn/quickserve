from typing import Callable
from flask import url_for


def link_builder(
    module_name: str, instance_uuid: str | None = None
) -> Callable[[str], str]:
    def link(page: str) -> str:
        if instance_uuid is None:
            return url_for(f"modules.module_page", module_name=module_name, page=page)
        return url_for(
            "modules.instances.module_instance", uuid=instance_uuid, page=page
        )

    return link
