from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class DeviceType(StrEnum):
    PUMP = "pump"
    FAN = "fan"
    LIGHT = "light"


@dataclass(frozen=True)
class DeviceState:
    node_id: str
    device_type: DeviceType
    is_active: bool
    level: float | None
    reason: str | None
    updated_at: datetime
