import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol


# Sensor type
class SensorType(Enum):
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    SOIL_MOISTURE = "soil_moisture"
    LIGHT = "light"


@dataclass(frozen=True)
class SensorReading:
    """
    Sensor reading info
    """

    sensor_id: str
    sensor_type: SensorType
    value: float
    unit: str
    timestamp: float = field(default_factory=time.time)
    module_id: str = ""


class Sensor(Protocol):
    """
    Basic sensor protocol
    """

    @property
    def sensor_id(self) -> str:
        ...

    @property
    def sensor_type(self) -> SensorType:
        ...

    def read(self) -> SensorReading:
        ...


class SensorRepository(Protocol):
    def save(self, reading: SensorReading) -> None:
        ...

    def save_batch(self, readings: list[SensorReading]) -> None:
        ...

    def get_latest(self, sensor_id: str) -> SensorReading | None:
        ...
