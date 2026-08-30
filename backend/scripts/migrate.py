"""Initialize a fresh database or upgrade an Alembic-managed database."""

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

import app.models  # noqa: F401 - registers all ORM tables on Base.metadata
from app.core.database import Base, engine


def main() -> None:
    config = Config("alembic.ini")
    existing_tables = set(inspect(engine).get_table_names())

    if "alembic_version" in existing_tables:
        command.upgrade(config, "head")
        print("Existing database upgraded to the latest Alembic revision.")
        return

    if existing_tables:
        table_list = ", ".join(sorted(existing_tables)[:10])
        raise RuntimeError(
            "Database contains tables but has no Alembic version. "
            "Refusing to guess its schema state. Found: " + table_list
        )

    Base.metadata.create_all(bind=engine)
    command.stamp(config, "head")
    print("Fresh database schema created and stamped at the Alembic head revision.")


if __name__ == "__main__":
    main()
