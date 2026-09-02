from QuickServeFS import config

from peewee import SqliteDatabase

db = SqliteDatabase(config.database.file_path)

def connect():
    db.connect(reuse_if_open=True)


def close():
    if not db.is_closed():
        db.close()
