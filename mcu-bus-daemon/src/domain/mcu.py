from typing import Protocol


class MCUInfos:
    mcu_id: int
    mcu_location: str
    temperature: float
    humidity: float


class MCU(Protocol):
    def get_id(self) -> int:
        ...

    def get_infos(self) -> MCUInfos:
        ...
