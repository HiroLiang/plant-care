from typing import Protocol


class DataSource(Protocol):
    async def connect(self) -> None:
        ...

    async def init_schema(self) -> None:
        ...

    async def close(self) -> None:
        ...
