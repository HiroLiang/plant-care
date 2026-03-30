from plant_core.domain.device import DeviceState, DeviceType
from plant_core.infrastructure.persistence.sqlite.mappers import device_state_to_record, record_to_device_state
from plant_core.infrastructure.persistence.sqlite.records import DeviceStateRecord
from plant_core.infrastructure.persistence.sqlite.repositories._base import SQLiteRepository


class SQLiteDeviceStateRepository(SQLiteRepository):
    async def upsert(self, state: DeviceState) -> None:
        record = device_state_to_record(state)
        await self._db.execute(
            """
            insert into device_states (
                node_id, device_type, is_active, level, reason, updated_at
            ) values (?, ?, ?, ?, ?, ?)
            on conflict(node_id, device_type) do update set
                is_active = excluded.is_active,
                level = excluded.level,
                reason = excluded.reason,
                updated_at = excluded.updated_at
            """,
            (
                record.node_id,
                record.device_type,
                record.is_active,
                record.level,
                record.reason,
                record.updated_at,
            ),
        )

    async def get(self, node_id: str, device_type: DeviceType) -> DeviceState | None:
        row = await self._fetchone(
            """
            select node_id, device_type, is_active, level, reason, updated_at
            from device_states
            where node_id = ? and device_type = ?
            """,
            (node_id, device_type.value),
        )
        if row is None:
            return None
        return record_to_device_state(DeviceStateRecord(**dict(row)))

    async def list_by_node(self, node_id: str) -> list[DeviceState]:
        rows = await self._fetchall(
            """
            select node_id, device_type, is_active, level, reason, updated_at
            from device_states
            where node_id = ?
            order by device_type
            """,
            (node_id,),
        )
        return [record_to_device_state(DeviceStateRecord(**dict(row))) for row in rows]
