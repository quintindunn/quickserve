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
    import logging

    logging.getLogger("websockets.server").setLevel(logging.ERROR)

    workspace = Workspace()

    config = Config(workspace)

    database = create_database(config.database.file_path)
    db_initialize(database)
    db_connect(database)
    database.create_tables(MODELS)

    catalog = PluginLoader(workspace).load_all()

    port_manager = PortManager(config.web)

    instance_service = InstanceService(
        catalog, workspace, port_manager, PeeweeInstanceRepository()
    )

    websocket_server = WebsocketServer(config.web, instance_service)
    Thread(
        target=start_websocket,
        args=[websocket_server],
        daemon=True,
    ).start()

    app = create_app(config.web, catalog, instance_service, websocket_server)
    app.run(host="0.0.0.0", port=8080, debug=True, use_reloader=False)
