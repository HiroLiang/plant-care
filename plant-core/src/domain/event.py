from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class EventType(StrEnum):
    TELEMETRY = "telemetry"
    HEARTBEAT = "heartbeat"
    DEVICE_STATE = "device_state"
    COMMAND_RESULT = "command_result"
    ALERT = "alert"


@dataclass(frozen=True)
class EventLog:
    event_id: str
    node_id: str
    event_type: EventType
    correlation_id: str | None
    command_id: str | None
    payload_json: str
    recorded_at: datetime
