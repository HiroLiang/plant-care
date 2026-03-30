from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class DeviceType(StrEnum):
    PUMP = "pump"
    FAN = "fan"
    LIGHT = "light"


class ActuatorAction(StrEnum):
    ON = "on"
    OFF = "off"
    SET_LEVEL = "set_level"


class SensorType(StrEnum):
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    SOIL_MOISTURE = "soil_moisture"
    LIGHT_LEVEL = "light_level"
    WATER_LEVEL = "water_level"
    PH = "ph"


class ValueUnit(StrEnum):
    CELSIUS = "celsius"
    PERCENT = "percent"
    VOLT = "volt"
    RATIO = "ratio"


class CommandStatus(StrEnum):
    ACCEPTED = "accepted"
    SUCCEEDED = "succeeded"
    REJECTED = "rejected"
    INVALID_ARGUMENT = "invalid_argument"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"
    UNSPECIFIED = "unspecified"


@dataclass(frozen=True)
class CommandDispatchResult:
    command_id: str
    accepted: bool
    status: CommandStatus
    message: str
    accepted_at: datetime | None
    target_node_id: int
