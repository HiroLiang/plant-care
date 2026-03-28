from datetime import datetime
from typing import Protocol

from domain.command import CommandLog, CommandStatus


class CommandLogRepository(Protocol):
    async def append(self, command: CommandLog) -> None:
        ...

    async def update_status(
        self,
        command_id: str,
        status: CommandStatus,
        message: str | None,
        accepted_at: datetime | None,
        finished_at: datetime | None,
    ) -> None:
        ...

    async def get(self, command_id: str) -> CommandLog | None:
        ...

    async def list_by_node(self, node_id: str, limit: int) -> list[CommandLog]:
        ...
