from dataclasses import dataclass, field
from datetime import datetime
from typing import Union


@dataclass(frozen=True)
class TelemetryReading:
    sensor_type: str
    value: float
    unit: str
    channel: str = ""
    status: str = "ok"


@dataclass(frozen=True)
class TelemetryEvent:
    readings: list[TelemetryReading] = field(default_factory=list)


@dataclass(frozen=True)
class HeartbeatEvent:
    status: int
    voltage: float
    uptime_seconds: int


@dataclass(frozen=True)
class DeviceStateEvent:
    device_type: str
    is_active: bool
    level: float = 0.0
    reason: str = ""


@dataclass(frozen=True)
class CommandResultEvent:
    command_id: str
    status: str
    message: str
    device_type: str = ""


@dataclass(frozen=True)
class AlertEvent:
    severity: str
    code: str
    message: str


BusPayload = Union[
    TelemetryEvent,
    HeartbeatEvent,
    DeviceStateEvent,
    CommandResultEvent,
    AlertEvent,
]


@dataclass(frozen=True)
class MCUBusEvent:
    event_id: str
    source_node_id: int
    emitted_at: datetime
    payload: BusPayload
    correlation_id: str = ""
    command_id: str = ""
