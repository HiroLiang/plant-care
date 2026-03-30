from datetime import datetime, UTC

from plant_core.domain.command import CommandLog, CommandStatus
from plant_core.infrastructure.persistence.sqlite.mappers import command_log_to_record, record_to_command_log
from plant_core.infrastructure.persistence.sqlite.records import CommandLogRecord
from plant_core.infrastructure.persistence.sqlite.repositories._base import SQLiteRepository


class SQLiteCommandLogRepository(SQLiteRepository):
    async def append(self, command: CommandLog) -> None:
        record = command_log_to_record(command)
        await self._db.execute(
            """
            insert into command_logs (
                command_id, node_id, command_type, device_type, correlation_id,
                requested_by, payload_json, status, message,
                requested_at, accepted_at, finished_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.command_id,
                record.node_id,
                record.command_type,
                record.device_type,
                record.correlation_id,
                record.requested_by,
                record.payload_json,
                record.status,
                record.message,
                record.requested_at,
                record.accepted_at,
                record.finished_at,
            ),
        )

    async def update_status(
        self,
        command_id: str,
        status: CommandStatus,
        message: str | None,
        accepted_at: datetime | None,
        finished_at: datetime | None,
    ) -> None:
        now = datetime.now(UTC)
        accepted_text = accepted_at.astimezone(UTC).isoformat() if accepted_at is not None else None
        finished_text = finished_at.astimezone(UTC).isoformat() if finished_at is not None else None
        await self._db.execute(
            """
            update command_logs
            set status = ?,
                message = ?,
                accepted_at = coalesce(?, accepted_at),
                finished_at = coalesce(?, finished_at),
                requested_at = requested_at
            where command_id = ?
            """,
            (status.value, message, accepted_text, finished_text, command_id),
        )

    async def get(self, command_id: str) -> CommandLog | None:
        row = await self._fetchone(
            """
            select command_id, node_id, command_type, device_type, correlation_id,
                   requested_by, payload_json, status, message,
                   requested_at, accepted_at, finished_at
            from command_logs
            where command_id = ?
            """,
            (command_id,),
        )
        if row is None:
            return None
        return record_to_command_log(CommandLogRecord(**dict(row)))

    async def list_by_node(self, node_id: str, limit: int) -> list[CommandLog]:
        rows = await self._fetchall(
            """
            select command_id, node_id, command_type, device_type, correlation_id,
                   requested_by, payload_json, status, message,
                   requested_at, accepted_at, finished_at
            from command_logs
            where node_id = ?
            order by requested_at desc
            limit ?
            """,
            (node_id, limit),
        )
        return [record_to_command_log(CommandLogRecord(**dict(row))) for row in rows]
