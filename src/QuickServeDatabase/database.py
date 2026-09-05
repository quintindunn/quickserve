import logging

from peewee import SqliteDatabase

from QuickServeFS import config

logger = logging.getLogger("QuickServeDatabase.database")

db = SqliteDatabase(config.database.file_path)
logger.debug(f"Initialized Sqlite Database at {config.database.file_path}")


def connect():
    logger.debug("Connecting to database")
    db.connect(reuse_if_open=True)
    logger.info("Connected to database")

def close():
    logger.info("Closing database")
    if not db.is_closed():
        db.close()
        logger.info("Database closed")
        return
    logger.info("Database already closed")
