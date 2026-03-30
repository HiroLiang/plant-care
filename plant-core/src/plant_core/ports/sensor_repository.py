from typing import Protocol

from plant_core.domain.sensor import Sensor


class SensorRepository(Protocol):
    async def upsert(self, sensor: Sensor) -> None:
        ...

    async def get(self, sensor_id: str) -> Sensor | None:
        ...

    async def list_by_node(self, node_id: str) -> list[Sensor]:
        ...
