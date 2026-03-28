from domain.sensor import Sensor
from infrastructure.persistence.sqlite.mappers import record_to_sensor, sensor_to_record
from infrastructure.persistence.sqlite.records import SensorRecord
from infrastructure.persistence.sqlite.repositories._base import SQLiteRepository


class SQLiteSensorRepository(SQLiteRepository):
    async def upsert(self, sensor: Sensor) -> None:
        record = sensor_to_record(sensor)
        await self._db.execute(
            """
            insert into sensors (
                sensor_id, node_id, sensor_type, channel, unit, display_name, created_at
            ) values (?, ?, ?, ?, ?, ?, ?)
            on conflict(sensor_id) do update set
                node_id = excluded.node_id,
                sensor_type = excluded.sensor_type,
                channel = excluded.channel,
                unit = excluded.unit,
                display_name = excluded.display_name
            """,
            (
                record.sensor_id,
                record.node_id,
                record.sensor_type,
                record.channel,
                record.unit,
                record.display_name,
                record.created_at,
            ),
        )

    async def get(self, sensor_id: str) -> Sensor | None:
        row = await self._fetchone(
            """
            select sensor_id, node_id, sensor_type, channel, unit, display_name, created_at
            from sensors
            where sensor_id = ?
            """,
            (sensor_id,),
        )
        if row is None:
            return None
        return record_to_sensor(SensorRecord(**dict(row)))

    async def list_by_node(self, node_id: str) -> list[Sensor]:
        rows = await self._fetchall(
            """
            select sensor_id, node_id, sensor_type, channel, unit, display_name, created_at
            from sensors
            where node_id = ?
            order by sensor_id
            """,
            (node_id,),
        )
        return [record_to_sensor(SensorRecord(**dict(row))) for row in rows]
