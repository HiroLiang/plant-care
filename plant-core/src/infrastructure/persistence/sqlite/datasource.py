import logging

import aiosqlite

from pathlib import Path

from ports.datasource import DataSource

logger = logging.getLogger(__name__)


class SQLiteDatasource(DataSource):
    def __init__(self, path: Path):
        self.path = path
        self._db: aiosqlite.Connection | None = None

    @property
    def raw_connection(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError("SQLiteDatasource is not connected")
        return self._db

    async def connect(self) -> None:
        logger.info("sqlite_connect", extra={"path": str(self.path)})
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(
            self.path,
            isolation_level=None,
        )
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA journal_mode=WAL;")
        await self._db.execute("PRAGMA foreign_keys=ON;")
        await self._db.execute("PRAGMA synchronous=NORMAL;")

    async def init_schema(self) -> None:
        schema_path = Path(__file__).with_name("schema.sql")
        logger.info("sqlite_initialize_schema", extra={"path": str(schema_path)})
        with schema_path.open() as query:
            await self.raw_connection.executescript(query.read())

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None
