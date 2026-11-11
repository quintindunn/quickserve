import importlib
from pathlib import Path


def run_migrations(database):
    migrations_directory = Path(__file__).parent

    database.execute_sql(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            name TEXT PRIMARY KEY,
            applied_on DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    applied = {
        row[0]
        for row in database.execute_sql("SELECT name FROM schema_migrations").fetchall()
    }

    migration_files = sorted(
        path.stem for path in migrations_directory.glob("m[0-9]*.py")
    )

    for migration_name in migration_files:
        if migration_name in applied:
            continue

        migration = importlib.import_module(f"{__name__}.{migration_name}")

        with database.atomic():
            migration.run(database)

            database.execute_sql(
                "INSERT INTO schema_migrations (name) VALUES (?)",
                (migration_name,),
            )
