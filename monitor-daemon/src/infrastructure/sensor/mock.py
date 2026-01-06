import random

from domain.sensor import Sensor, SensorType, SensorReading


class MockTemperatureSensor(Sensor):
    def __init__(
            self,
            base: float = 26.0,
            drift: float = 0.2,
            min_value: float = 15.0,
            max_value: float = 35.0,
            sensor_id: str = "mock_temperature_sensor"
    ):
        self._sensor_id = sensor_id
        self._value = base
        self._drift = drift
        self._min = min_value
        self._max = max_value

    @property
    def sensor_id(self) -> str:
        return self._sensor_id

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.TEMPERATURE

    def read(self) -> SensorReading:
        delta = random.uniform(-self._drift, self._drift)
        self._value = max(self._min, min(self._max, self._value + delta))
        return SensorReading(
            sensor_id=self._sensor_id,
            sensor_type=SensorType.TEMPERATURE,
            value=round(self._value, 2),
            unit="°C"
        )


class MockHumiditySensor(Sensor):
    def __init__(
            self,
            base: float = 55.0,
            drift: float = 1.0,
            min_value: float = 30.0,
            max_value: float = 80.0,
            sensor_id: str = "mock_humidity_sensor"
    ):
        self._sensor_id = sensor_id
        self._value = base
        self._drift = drift
        self._min = min_value
        self._max = max_value

    @property
    def sensor_id(self) -> str:
        return self._sensor_id

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.HUMIDITY

    def read(self) -> SensorReading:
        delta = random.uniform(-self._drift, self._drift)
        self._value = max(self._min, min(self._max, self._value + delta))
        return SensorReading(
            sensor_id=self._sensor_id,
            sensor_type=SensorType.HUMIDITY,
            value=round(self._value, 1),
            unit="%"
        )
