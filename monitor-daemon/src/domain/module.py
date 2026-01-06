from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Protocol, runtime_checkable

from .sensor import Sensor, SensorReading


class ModuleType(Enum):
    LOCAL = auto()
    MCU_SERIAL = auto()


@dataclass
class ModuleInfo:
    module_id: str
    module_type: ModuleType
    sensors: list[str] = field(default_factory=list)
    actuators: list[str] = field(default_factory=list)


@runtime_checkable
class SensorModule(Protocol):
    """
    Modulize Sensor Protocol
    """

    @property
    def module_id(self) -> str:
        ...

    @property
    def module_type(self) -> ModuleType:
        ...

    def get_info(self) -> ModuleInfo:
        ...

    def get_sensor_ids(self) -> list[str]:
        ...

    def get_sensors(self) -> list[Sensor]:
        ...

    def get_sensor(self, id: str) -> Sensor:
        ...

    def read_all(self) -> list[SensorReading]:
        ...

    def is_online(self) -> bool:
        ...
