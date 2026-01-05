from typing import Protocol

class TemperatureSensor(Protocol):
    def read(self) -> float:
        ...

class HumiditySensor(Protocol):
    def read(self) -> float:
        ...