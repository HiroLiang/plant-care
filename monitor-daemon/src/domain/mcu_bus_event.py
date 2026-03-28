from dataclasses import dataclass, field
from datetime import datetime
from typing import Union


@dataclass(frozen=True)
class SensorDataEvent:
    temperature: float
    humidity: float
    soil_moisture: float
    light_level: float
    water_level: float
    ph_value: float


@dataclass(frozen=True)
class ControlStatusEvent:
    device: str
    is_active: bool
    power_level: float
    reason: str


@dataclass(frozen=True)
class AlertEvent:
    severity: str
    code: str
    message: str


BusPayload = Union[
    SensorDataEvent,
    ControlStatusEvent,
    AlertEvent,
]


@dataclass(frozen=True)
class MCUBusEvent:
    event_id: str
    module_id: str
    timestamp: datetime
    payload: BusPayload
