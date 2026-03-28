from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class NodeKind(StrEnum):
    MCU = "mcu"
    LOCAL = "local"


class NodeStatus(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Node:
    node_id: str
    node_kind: NodeKind
    display_name: str
    serial_no: str | None
    status: NodeStatus
    last_seen_at: datetime | None
    created_at: datetime
    updated_at: datetime
