import queue
import uuid

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Subscriber:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    queue: queue.Queue = field(default_factory=queue.Queue)
    created_at: datetime = field(default_factory=datetime.now)
    active: bool = True


@dataclass(frozen=True)
class Event:
    ...
