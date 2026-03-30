from plant_core.domain.sensor import LatestSensorReading, SensorReading
from plant_core.infrastructure.persistence.sqlite.mappers import (
    latest_sensor_reading_to_record,
    record_to_latest_sensor_reading,
    record_to_sensor_reading,
    sensor_reading_to_record,
)
from plant_core.infrastructure.persistence.sqlite.records import LatestSensorReadingRecord, SensorReadingRecord
from plant_core.infrastructure.persistence.sqlite.repositories._base import SQLiteRepository


class SQLiteSensorReadingRepository(SQLiteRepository):
    async def append(self, reading: SensorReading) -> None:
        await self.append_batch([reading])

    async def append_batch(self, readings: list[SensorReading]) -> None:
        for reading in readings:
            record = sensor_reading_to_record(reading)
            await self._db.execute(
                """
                insert into sensor_readings (
                    reading_id, sensor_id, node_id, sensor_type, value, unit, status, recorded_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.reading_id,
                    record.sensor_id,
                    record.node_id,
                    record.sensor_type,
                    record.value,
                    record.unit,
                    record.status,
                    record.recorded_at,
                ),
            )

            latest = LatestSensorReading(
                sensor_id=reading.sensor_id,
                reading_id=reading.reading_id,
                node_id=reading.node_id,
                sensor_type=reading.sensor_type,
                value=reading.value,
                unit=reading.unit,
                status=reading.status,
                recorded_at=reading.recorded_at,
            )
            latest_record = latest_sensor_reading_to_record(latest)
            await self._db.execute(
                """
                insert into latest_sensor_readings (
                    sensor_id, reading_id, node_id, sensor_type, value, unit, status, recorded_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(sensor_id) do update set
                    reading_id = excluded.reading_id,
                    node_id = excluded.node_id,
                    sensor_type = excluded.sensor_type,
                    value = excluded.value,
                    unit = excluded.unit,
                    status = excluded.status,
                    recorded_at = excluded.recorded_at
                """,
                (
                    latest_record.sensor_id,
                    latest_record.reading_id,
                    latest_record.node_id,
                    latest_record.sensor_type,
                    latest_record.value,
                    latest_record.unit,
                    latest_record.status,
                    latest_record.recorded_at,
                ),
            )

    async def get_latest(self, sensor_id: str) -> LatestSensorReading | None:
        row = await self._fetchone(
            """
            select sensor_id, reading_id, node_id, sensor_type, value, unit, status, recorded_at
            from latest_sensor_readings
            where sensor_id = ?
            """,
            (sensor_id,),
        )
        if row is None:
            return None
        return record_to_latest_sensor_reading(LatestSensorReadingRecord(**dict(row)))

    async def list_latest_by_node(self, node_id: str) -> list[LatestSensorReading]:
        rows = await self._fetchall(
            """
            select sensor_id, reading_id, node_id, sensor_type, value, unit, status, recorded_at
            from latest_sensor_readings
            where node_id = ?
            order by sensor_id
            """,
            (node_id,),
        )
        return [record_to_latest_sensor_reading(LatestSensorReadingRecord(**dict(row))) for row in rows]

    async def list_history(self, sensor_id: str, limit: int) -> list[SensorReading]:
        rows = await self._fetchall(
            """
            select reading_id, sensor_id, node_id, sensor_type, value, unit, status, recorded_at
            from sensor_readings
            where sensor_id = ?
            order by recorded_at desc
            limit ?
            """,
            (sensor_id, limit),
        )
        return [record_to_sensor_reading(SensorReadingRecord(**dict(row))) for row in rows]
