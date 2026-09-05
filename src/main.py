import logging
import sys

from QuickServeDriver.services.base_service import BaseService

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    from QuickServeFS import config
    from QuickServeDatabase import db, connect, MODELS

    connect()
    db.create_tables(MODELS)

    service = BaseService(
        cfg=config,
        service_name="Minecraft1.8.9",
        module=config.resolver.modules.get("Minecraft"),
    )
    print(service.working_directory())
