from plant_core.domain.event import EventLog
from plant_core.infrastructure.persistence.sqlite.mappers import event_log_to_record, record_to_event_log
from plant_core.infrastructure.persistence.sqlite.records import EventLogRecord
from plant_core.infrastructure.persistence.sqlite.repositories._base import SQLiteRepository


class SQLiteEventLogRepository(SQLiteRepository):
    async def append(self, event: EventLog) -> None:
        record = event_log_to_record(event)
        await self._db.execute(
            """
            insert into event_logs (
                event_id, node_id, event_type, correlation_id, command_id, payload_json, recorded_at
            ) values (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.event_id,
                record.node_id,
                record.event_type,
                record.correlation_id,
                record.command_id,
                record.payload_json,
                record.recorded_at,
            ),
        )

    async def list_by_node(self, node_id: str, limit: int) -> list[EventLog]:
        rows = await self._fetchall(
            """
            select event_id, node_id, event_type, correlation_id, command_id, payload_json, recorded_at
            from event_logs
            where node_id = ?
            order by recorded_at desc
            limit ?
            """,
            (node_id, limit),
        )
        return [record_to_event_log(EventLogRecord(**dict(row))) for row in rows]

    async def list_recent(self, limit: int) -> list[EventLog]:
        rows = await self._fetchall(
            """
            select event_id, node_id, event_type, correlation_id, command_id, payload_json, recorded_at
            from event_logs
            order by recorded_at desc
            limit ?
            """,
            (limit,),
        )
        return [record_to_event_log(EventLogRecord(**dict(row))) for row in rows]

    async def list_by_command(self, command_id: str) -> list[EventLog]:
        rows = await self._fetchall(
            """
            select event_id, node_id, event_type, correlation_id, command_id, payload_json, recorded_at
            from event_logs
            where command_id = ?
            order by recorded_at desc
            """,
            (command_id,),
        )
        return [record_to_event_log(EventLogRecord(**dict(row))) for row in rows]
