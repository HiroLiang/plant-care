import os

from dataclasses import dataclass
from pathlib import Path

from plant_core.infrastructure.persistence.sqlite.bundle import SQLiteRepositoryBundle
from plant_core.infrastructure.persistence.sqlite.datasource import SQLiteDatasource
from plant_core.ports.datasource import DataSource


@dataclass(frozen=True)
class DatabaseResources:
    db: SQLiteDatasource
    repositories: SQLiteRepositoryBundle


def get_db_path() -> Path:
    return Path(os.getenv("DB_PATH", "data/dev.sqlite3"))


async def init_database() -> DatabaseResources:
    db = SQLiteDatasource(get_db_path())
    await db.connect()
    await db.init_schema()
    repositories = SQLiteRepositoryBundle.from_datasource(db)
    return DatabaseResources(db=db, repositories=repositories)


async def shout_database(db: DataSource) -> None:
    await db.close()
