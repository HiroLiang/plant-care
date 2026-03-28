import aiosqlite


class SQLiteRepository:
    def __init__(self, db: aiosqlite.Connection):
        self._db = db

    async def _fetchone(self, query: str, params: tuple) -> aiosqlite.Row | None:
        cursor = await self._db.execute(query, params)
        try:
            return await cursor.fetchone()
        finally:
            await cursor.close()

    async def _fetchall(self, query: str, params: tuple) -> list[aiosqlite.Row]:
        cursor = await self._db.execute(query, params)
        try:
            return await cursor.fetchall()
        finally:
            await cursor.close()
