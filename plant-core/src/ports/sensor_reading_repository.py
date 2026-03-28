from typing import Protocol

from domain.sensor import LatestSensorReading, SensorReading


class SensorReadingRepository(Protocol):
    async def append(self, reading: SensorReading) -> None:
        ...

    async def append_batch(self, readings: list[SensorReading]) -> None:
        ...

    async def get_latest(self, sensor_id: str) -> LatestSensorReading | None:
        ...

    async def list_latest_by_node(self, node_id: str) -> list[LatestSensorReading]:
        ...

    async def list_history(self, sensor_id: str, limit: int) -> list[SensorReading]:
        ...
