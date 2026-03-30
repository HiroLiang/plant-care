from datetime import datetime
from typing import Protocol

from plant_core.domain.node import Node, NodeStatus


class NodeRepository(Protocol):
    async def upsert(self, node: Node) -> None:
        ...

    async def get(self, node_id: str) -> Node | None:
        ...

    async def list_all(self) -> list[Node]:
        ...

    async def update_status(
        self,
        node_id: str,
        status: NodeStatus,
        last_seen_at: datetime | None,
    ) -> None:
        ...
