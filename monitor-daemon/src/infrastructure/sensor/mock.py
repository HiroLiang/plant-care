import random

from domain.sensor import TemperatureSensor, HumiditySensor


class MockTemperatureSensor(TemperatureSensor):
    def __init__(
            self,
            base: float = 26.0,
            drift: float = 0.2,
            min_value: float = 15.0,
            max_value: float = 35.0,
    ):
        self._value = base
        self._drift = drift
        self._min = min_value
        self._max = max_value

    def read(self) -> float:
        delta = random.uniform(-self._drift, self._drift)
        self._value = max(self._min, min(self._max, self._value + delta))
        return round(self._value, 2)


class MockHumiditySensor(HumiditySensor):
    def __init__(
            self,
            base: float = 55.0,
            drift: float = 1.0,
            min_value: float = 30.0,
            max_value: float = 80.0,
    ):
        self._value = base
        self._drift = drift
        self._min = min_value
        self._max = max_value

    def read(self) -> float:
        delta = random.uniform(-self._drift, self._drift)
        self._value = max(self._min, min(self._max, self._value + delta))
        return round(self._value, 1)
