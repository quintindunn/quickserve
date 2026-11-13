import logging

from peewee import CharField
from playhouse.migrate import SqliteMigrator, migrate

logger = logging.getLogger(__name__)


def run(database):
    logger.info("Running migration 0002")

    migrator = SqliteMigrator(database)

    with database.atomic():
        migrate(
            migrator.add_column(
                "instancemodel",
                "original_instance_name",
                CharField(null=False, default=""),
            )
        )

        database.execute_sql(
            """
            UPDATE instancemodel
            SET original_instance_name = instance_name
            """
        )
