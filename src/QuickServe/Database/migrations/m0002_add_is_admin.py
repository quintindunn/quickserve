import logging

from peewee import BooleanField
from playhouse.migrate import SqliteMigrator, migrate

logger = logging.getLogger(__name__)


def run(database):
    logger.info("Running migration 0002")

    migrator = SqliteMigrator(database)

    with database.atomic():
        migrate(
            migrator.add_column(
                "usermodel",
                "is_admin",
                BooleanField(default=False),
            )
        )
