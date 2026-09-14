"""
Main entry point for quickserve

Author: Quintin Dunn
Date: 09/09/2026
"""

import logging
import sys

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    from QuickServe.Application.instances import InstanceService
    from QuickServe.Database.database import create_database, connect, initialize
    from QuickServe.Database.models import MODELS
    from QuickServe.Database.repositories import PeeweeInstanceRepository
    from QuickServe.Driver.port_manager import PortManager
    from QuickServe.Web import create_app
    from QuickServe.FileSystem.config import Config
    from QuickServe.FileSystem.path_resolver import Workspace
    from QuickServe.FileSystem.plugins import PluginLoader

    # Workspace manages QuickServe's runtime directory and filesystem paths.
    workspace = Workspace()

    # Config reads config.toml from that workspace and validates its settings.
    config = Config(workspace)

    # Create the database from config, then bind the model proxy before use.
    database = create_database(config.database.file_path)
    initialize(database)

    # Connect once at startup and ensure the application's tables exist.
    connect(database)
    database.create_tables(MODELS)

    # Discover service plugins only after filesystem and configuration setup.
    catalog = PluginLoader(workspace).load_all()

    # Allocate service ports from the configured range as instances are created.
    port_manager = PortManager(config.web)

    # Coordinate instance records, loaded plugins, workspace directories, and ports.
    instance_service = InstanceService(
        catalog, workspace, port_manager, PeeweeInstanceRepository()
    )

    # Give Flask the already-built services; routes do not import global state.
    app = create_app(config.web, catalog, instance_service)
    app.run(host="0.0.0.0", port=8080, debug=True)
