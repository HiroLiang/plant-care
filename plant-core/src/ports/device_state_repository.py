from typing import Protocol

from domain.device import DeviceState, DeviceType


class DeviceStateRepository(Protocol):
    async def upsert(self, state: DeviceState) -> None:
        ...

    async def get(self, node_id: str, device_type: DeviceType) -> DeviceState | None:
        ...

    async def list_by_node(self, node_id: str) -> list[DeviceState]:
        ...
