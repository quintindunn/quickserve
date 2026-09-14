"""
PeeWee database helper functions for connecting, and disconnecting.

Author: Quintin Dunn
Date: 09/09/2026
"""

import logging

from peewee import SqliteDatabase

from QuickServe.FileSystem import config

logger = logging.getLogger("Database.database")

db = SqliteDatabase(config.database.file_path)
logger.debug(f"Initialized Sqlite Database at {config.database.file_path}")


def connect() -> None:
    """
    Connects to the database.

    :return: None
    """
    logger.debug("Connecting to database")
    db.connect(reuse_if_open=True)
    logger.info("Connected to database")


def close() -> None:
    """
    Disconnects/closes the database.

    :return: None
    """
    logger.info("Closing database")
    if not db.is_closed():
        db.close()
        logger.info("Database closed")
        return
    logger.info("Database already closed")
