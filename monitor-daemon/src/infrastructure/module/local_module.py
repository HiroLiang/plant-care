from typing import List

from domain.sensor import Sensor, SensorReading
from domain.module import SensorModule, ModuleType, ModuleInfo


class LocalSensorModule(SensorModule):
    """
    Module's implementation of local sensor module.
    """

    def __init__(self, module_id: str = "local"):
        self._module_id = module_id
        self._sensors: List[Sensor] = []

    @property
    def module_id(self) -> str:
        return self._module_id

    @property
    def module_type(self) -> ModuleType:
        return ModuleType.LOCAL

    def get_info(self) -> ModuleInfo:
        return ModuleInfo(
            module_id=self.module_id,
            module_type=ModuleType.LOCAL,
            sensors=[s.sensor_id for s in self._sensors],
        )

    def add_sensor(self, sensor: Sensor) -> None:
        self._sensors.append(sensor)

    def remove_sensor(self, sensor_id: str) -> None:
        for s in self._sensors:
            if s.sensor_id == sensor_id:
                self._sensors.remove(s)

    def get_sensor_ids(self) -> list[str]:
        return [s.sensor_id for s in self._sensors]

    def get_sensor(self, sensor_id: str) -> Sensor | None:
        for s in self._sensors:
            if s.sensor_id == sensor_id:
                return s
        return None

    def get_sensors(self) -> list[Sensor]:
        return self._sensors

    def read_all(self) -> list[SensorReading]:
        readings = []
        for sensor in self._sensors:
            reading = sensor.read()

            readings.append(SensorReading(
                sensor_id=reading.sensor_id,
                sensor_type=reading.sensor_type,
                value=reading.value,
                unit=reading.unit,
                timestamp=reading.timestamp,
                module_id=self._module_id
            ))
        return readings

    def is_online(self) -> bool:
        return len(self._sensors) > 0
