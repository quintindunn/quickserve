import logging

from playhouse.migrate import SqliteMigrator, migrate

logger = logging.getLogger(__name__)

def run(database):
    logger.info("Running migration 0001")
    from QuickServe.Database.users import UserModel
    from QuickServe.Database.instances import InstanceModel

    with database.atomic():
        database.create_tables([
            UserModel,
            InstanceModel,
        ])