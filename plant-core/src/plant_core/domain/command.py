from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class CommandType(StrEnum):
    ACTUATOR = "actuator"
    REQUEST_TELEMETRY = "request_telemetry"
    RESET = "reset"
    SET_THRESHOLD = "set_threshold"


class CommandStatus(StrEnum):
    ACCEPTED = "accepted"
    SUCCEEDED = "succeeded"
    REJECTED = "rejected"
    INVALID_ARGUMENT = "invalid_argument"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"


@dataclass(frozen=True)
class CommandLog:
    command_id: str
    node_id: str
    command_type: CommandType
    device_type: str | None
    correlation_id: str | None
    requested_by: str
    payload_json: str
    status: CommandStatus
    message: str | None
    requested_at: datetime
    accepted_at: datetime | None
    finished_at: datetime | None
