"""
Main entry point for quickserve

Author: Quintin Dunn
Date: 09/09/2026
"""

from threading import Thread

import asyncio
import logging
import sys


def start_websocket(ws_server):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(ws_server.start())


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    from QuickServe.Application.instances import InstanceService
    from QuickServe.Database.database import create_database
    from QuickServe.Database.database import connect as db_connect
    from QuickServe.Database.database import initialize as db_initialize
    from QuickServe.Database.models import MODELS
    from QuickServe.Database.repositories import PeeweeInstanceRepository
    from QuickServe.Driver.port_manager import PortManager
    from QuickServe.Web import create_app
    from QuickServe.FileSystem.config import Config
    from QuickServe.FileSystem.path_resolver import Workspace
    from QuickServe.FileSystem.plugins import PluginLoader
    from QuickServe.Driver.networking.websocket import WebsocketServer
    from QuickServe.Runtimes.runtime_manager import RuntimeManager
    import logging

    logging.getLogger("websockets.server").setLevel(logging.ERROR)

    workspace = Workspace()

    runtime_manager = RuntimeManager(workspace=workspace)

    config = Config(workspace=workspace)

    database = create_database(file_path=config.database.file_path)
    db_initialize(database=database)
    db_connect(database=database)
    database.create_tables(models=MODELS)

    catalog = PluginLoader(workspace=workspace, runtime_manager=runtime_manager).load_all()

    port_manager = PortManager(settings=config.web)

    instance_service = InstanceService(
        catalog=catalog, workspace=workspace, port_manager=port_manager, repository=PeeweeInstanceRepository()
    )

    websocket_server = WebsocketServer(config=config.web, instance_service=instance_service)
    Thread(
        target=start_websocket,
        args=[websocket_server],
        daemon=True,
    ).start()

    app = create_app(settings=config.web, catalog=catalog, instance_service=instance_service, websocket_server=websocket_server)
    app.run(host="0.0.0.0", port=8080, debug=True, use_reloader=False)
