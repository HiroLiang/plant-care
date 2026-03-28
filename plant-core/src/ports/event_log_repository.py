from typing import Protocol

from domain.event import EventLog


class EventLogRepository(Protocol):
    async def append(self, event: EventLog) -> None:
        ...

    async def list_by_node(self, node_id: str, limit: int) -> list[EventLog]:
        ...

    async def list_by_command(self, command_id: str) -> list[EventLog]:
        ...
