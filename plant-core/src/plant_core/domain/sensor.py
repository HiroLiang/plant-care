from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class SensorType(StrEnum):
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    SOIL_MOISTURE = "soil_moisture"
    LIGHT_LEVEL = "light_level"
    WATER_LEVEL = "water_level"
    PH = "ph"


class SensorStatus(StrEnum):
    OK = "ok"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Sensor:
    sensor_id: str
    node_id: str
    sensor_type: SensorType
    channel: str | None
    unit: str
    display_name: str | None
    created_at: datetime


@dataclass(frozen=True)
class SensorReading:
    reading_id: str
    sensor_id: str
    node_id: str
    sensor_type: SensorType
    value: float
    unit: str
    status: SensorStatus
    recorded_at: datetime


@dataclass(frozen=True)
class LatestSensorReading:
    sensor_id: str
    reading_id: str
    node_id: str
    sensor_type: SensorType
    value: float
    unit: str
    status: SensorStatus
    recorded_at: datetime
