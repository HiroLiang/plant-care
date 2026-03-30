from datetime import UTC, datetime

from plant_core.domain.node import Node, NodeStatus
from plant_core.infrastructure.persistence.sqlite.mappers import node_to_record, record_to_node
from plant_core.infrastructure.persistence.sqlite.records import NodeRecord
from plant_core.infrastructure.persistence.sqlite.repositories._base import SQLiteRepository


class SQLiteNodeRepository(SQLiteRepository):
    async def upsert(self, node: Node) -> None:
        record = node_to_record(node)
        await self._db.execute(
            """
            insert into nodes (
                node_id, node_kind, display_name, serial_no, status,
                last_seen_at, created_at, updated_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(node_id) do update set
                node_kind = excluded.node_kind,
                display_name = excluded.display_name,
                serial_no = excluded.serial_no,
                status = excluded.status,
                last_seen_at = excluded.last_seen_at,
                updated_at = excluded.updated_at
            """,
            (
                record.node_id,
                record.node_kind,
                record.display_name,
                record.serial_no,
                record.status,
                record.last_seen_at,
                record.created_at,
                record.updated_at,
            ),
        )

    async def get(self, node_id: str) -> Node | None:
        row = await self._fetchone(
            """
            select node_id, node_kind, display_name, serial_no, status,
                   last_seen_at, created_at, updated_at
            from nodes
            where node_id = ?
            """,
            (node_id,),
        )
        if row is None:
            return None
        return record_to_node(NodeRecord(**dict(row)))

    async def list_all(self) -> list[Node]:
        rows = await self._fetchall(
            """
            select node_id, node_kind, display_name, serial_no, status,
                   last_seen_at, created_at, updated_at
            from nodes
            order by node_id
            """,
            (),
        )
        return [record_to_node(NodeRecord(**dict(row))) for row in rows]

    async def update_status(
        self,
        node_id: str,
        status: NodeStatus,
        last_seen_at: datetime | None,
    ) -> None:
        await self._db.execute(
            """
            update nodes
            set status = ?, last_seen_at = ?, updated_at = ?
            where node_id = ?
            """,
            (
                status.value,
                last_seen_at.isoformat() if last_seen_at is not None else None,
                datetime.now(UTC).isoformat(),
                node_id,
            ),
        )
