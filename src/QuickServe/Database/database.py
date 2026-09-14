"""
PeeWee database helper functions for connecting, and disconnecting.

Author: Quintin Dunn
Date: 09/09/2026
"""

import logging
from pathlib import Path

from peewee import DatabaseProxy, SqliteDatabase

logger = logging.getLogger("Database.database")

database_proxy = DatabaseProxy()


def create_database(file_path: str | Path) -> SqliteDatabase:
    """
    Creates an unconnected database from a file path.

    :param file_path: The SQLite database file to use.
    :return: The unconnected SQLite database.
    """
    database = SqliteDatabase(file_path)
    logger.debug("Initialized SQLite database at %s", file_path)
    return database


def initialize(database: SqliteDatabase) -> None:
    """
    Binds the model proxy after settings have been loaded.

    :param database: The database used by Peewee models.
    :return: None
    """
    database_proxy.initialize(database)


def connect(database: SqliteDatabase) -> None:
    """
    Connects to the database.

    :return: None
    """
    logger.debug("Connecting to database")
    database.connect(reuse_if_open=True)
    logger.info("Connected to database")


def close() -> None:
    """
    Disconnects/closes the database.

    :return: None
    """
    logger.info("Closing database")
    if not database_proxy.is_closed():
        database_proxy.close()
        logger.info("Database closed")
        return
    logger.info("Database already closed")
