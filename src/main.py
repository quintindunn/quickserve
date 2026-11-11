"""
Main entry point for quickserve

Author: Quintin Dunn
Date: 09/09/2026
"""
import gzip
from datetime import datetime
from threading import Thread

import asyncio
import logging
import sys

from QuickServe.Common.search import Search

QS_VERSION = "0.0.1"


def start_websocket(ws_server):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(ws_server.start())


if __name__ == "__main__":
    from QuickServe.Application.instances import InstanceManager
    from QuickServe.Database.database import create_database
    from QuickServe.Database.database import connect as db_connect
    from QuickServe.Database.database import initialize as db_initialize
    from QuickServe.Database.models import MODELS
    from QuickServe.Database.repositories import PeeweeInstanceManager
    from QuickServe.Web import create_app
    from QuickServe.FileSystem.config import Config
    from QuickServe.FileSystem.path_resolver import Workspace
    from QuickServe.FileSystem.plugins import PluginLoader
    from QuickServe.Driver.networking.websocket import WebsocketServer
    from QuickServe.Runtimes.runtime_manager import RuntimeManager
    import logging

    logging.getLogger("websockets.server").setLevel(logging.ERROR)

    workspace = Workspace()
    log_folder = workspace.root / "logs"

    log_folder.mkdir(exist_ok=True)

    log_path = log_folder / "log-latest.txt"

    if log_path.exists() and log_path.is_file():
        stat = log_path.stat()
        created = datetime.fromtimestamp(
            getattr(stat, "st_birthtime", stat.st_mtime)
        )

        with open(log_path, "rb") as f:
            compressed = gzip.compress(f.read())

        archive_path = log_folder / f"{created.isoformat().replace(':', '-')}.gz"

        with open(archive_path, "wb") as f:
            f.write(compressed)

        log_path.unlink()

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    runtime_manager = RuntimeManager(workspace=workspace)

    config = Config(workspace=workspace)

    database = create_database(file_path=config.database.file_path)
    db_initialize(database=database)
    db_connect(database=database)
    database.create_tables(models=MODELS)

    catalog = PluginLoader(
        workspace=workspace,
        runtime_manager=runtime_manager,
        config=config,
        qs_version=QS_VERSION,
    ).load_all()

    instance_manager = InstanceManager(
        catalog=catalog,
        workspace=workspace,
        repository=PeeweeInstanceManager(),
    )

    search_engine = Search(catalog=catalog, instance_manager=instance_manager)
    search_engine.update_all()

    websocket_server = WebsocketServer(
        config=config.web, instance_manager=instance_manager
    )

    Thread(
        target=start_websocket,
        args=[websocket_server],
        daemon=True,
    ).start()

    app = create_app(
        config=config,
        catalog=catalog,
        instance_manager=instance_manager,
        websocket_server=websocket_server,
        search_engine=search_engine,
    )
    app.run(
        host=config.web.website_host,
        port=config.web.website_port,
        debug=config.web.website_debug,
        use_reloader=False,
    )
