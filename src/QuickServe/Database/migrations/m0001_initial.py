import logging

from peewee import AutoField, CharField
from playhouse.migrate import SqliteMigrator, migrate

logger = logging.getLogger(__name__)

def run(database):
    logger.info("Running migration 0001")

    with database.atomic():
        database.execute_sql("""
                             CREATE TABLE usermodel
                             (
                                 id            INTEGER      NOT NULL PRIMARY KEY AUTOINCREMENT,
                                 username      VARCHAR(20)  NOT NULL UNIQUE,
                                 password_hash VARCHAR(255) NOT NULL
                             )
                             """)

        database.execute_sql("""
CREATE TABLE instancemodel (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    instance_uuid TEXT NOT NULL,
    instance_name VARCHAR(255) NOT NULL,
    module_name VARCHAR(255) NOT NULL,
    created_on DATETIME NOT NULL
)
                             """)