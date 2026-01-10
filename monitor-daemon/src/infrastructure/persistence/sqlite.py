import aiosqlite
import logging

from pathlib import Path

from infrastructure.persistence.datasource import DataSource

logger = logging.getLogger(__name__)


class SQLiteDatasource(DataSource):
    def __init__(self, path: Path):
        self.path = path
        self._db: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        """
        Connect to the SQLite database
        """
        logger.info("sqlite_connect", extra={"path": self.path})

        self._db = await aiosqlite.connect(
            self.path,
            isolation_level=None,
        )

        # SQLite optimize
        await self._db.execute("PRAGMA journal_mode=WAL;")
        await self._db.execute("PRAGMA foreign_keys=ON;")
        await self._db.execute("PRAGMA synchronous=NORMAL;")

    async def init_schema(self) -> None:
        """
        Initialize the SQLite database (process queries from schema.sql)
        """
        logger.info("sqlite_initialize_schema")
        with open("src/infrastructure/persistence/schema.sql") as query:
            await self._db.executescript(query.read())

    async def close(self) -> None:
        """
        Close the SQLite database connection
        """
        if self._db:
            await self._db.close()
            self._db = None
