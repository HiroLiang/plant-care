import os

from pathlib import Path

from infrastructure.persistence.datasource import DataSource
from infrastructure.persistence.sqlite import SQLiteDatasource

DB_PATH = Path(
    os.getenv("DB_PATH", "data/dev.sqlite3")
)


async def init_database() -> DataSource:
    db = SQLiteDatasource(DB_PATH)
    await db.connect()
    await db.init_schema()
    return db


async def shout_database(db: DataSource) -> None:
    await db.close()
