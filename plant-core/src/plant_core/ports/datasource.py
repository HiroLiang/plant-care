from typing import Protocol

import aiosqlite


class DataSource(Protocol):
    async def connect(self) -> None:
        ...

    async def init_schema(self) -> None:
        ...

    async def close(self) -> None:
        ...

    @property
    def raw_connection(self) -> aiosqlite.Connection:
        ...
