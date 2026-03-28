from dataclasses import dataclass


@dataclass(frozen=True)
class NodeRecord:
    node_id: str
    node_kind: str
    display_name: str
    serial_no: str | None
    status: str
    last_seen_at: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class DeviceStateRecord:
    node_id: str
    device_type: str
    is_active: int
    level: float | None
    reason: str | None
    updated_at: str


@dataclass(frozen=True)
class SensorRecord:
    sensor_id: str
    node_id: str
    sensor_type: str
    channel: str | None
    unit: str
    display_name: str | None
    created_at: str


@dataclass(frozen=True)
class SensorReadingRecord:
    reading_id: str
    sensor_id: str
    node_id: str
    sensor_type: str
    value: float
    unit: str
    status: str
    recorded_at: str


@dataclass(frozen=True)
class LatestSensorReadingRecord:
    sensor_id: str
    reading_id: str
    node_id: str
    sensor_type: str
    value: float
    unit: str
    status: str
    recorded_at: str


@dataclass(frozen=True)
class CommandLogRecord:
    command_id: str
    node_id: str
    command_type: str
    device_type: str | None
    correlation_id: str | None
    requested_by: str
    payload_json: str
    status: str
    message: str | None
    requested_at: str
    accepted_at: str | None
    finished_at: str | None


@dataclass(frozen=True)
class EventLogRecord:
    event_id: str
    node_id: str
    event_type: str
    correlation_id: str | None
    command_id: str | None
    payload_json: str
    recorded_at: str
