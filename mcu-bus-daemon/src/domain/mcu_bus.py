import queue
import uuid

from dataclasses import dataclass, field
from datetime import datetime
from typing import Set, Union


@dataclass
class Subscriber:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    queue: queue.Queue = field(default_factory=queue.Queue)
    module_ids: Set[str] = field(default_factory=set)
    event_types: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    active: bool = True


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
class BusEvent:
    event_id: str
    module_id: str
    timestamp: datetime
    payload: BusPayload
