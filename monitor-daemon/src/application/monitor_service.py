import time
import threading

from domain import TemperatureSensor
from domain.sensor import HumiditySensor


class MonitorService:
    def __init__(self,
                 temp_sensor: TemperatureSensor,
                 humidity_sensor: HumiditySensor):
        self._lock = threading.Lock()
        self._temp_sensor = temp_sensor
        self._humidity_sensor = humidity_sensor
        self._latest_temp: float | None = None
        self._latest_humidity: float | None = None
        self._updated_at: float | None = None

    def poll(self):
        with self._lock:
            self._latest_temp = self._temp_sensor.read()
            self._latest_humidity = self._humidity_sensor.read()
            self._updated_at = time.time()

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "temperature": self._latest_temp,
                "humidity": self._latest_humidity,
                "updated_at": self._updated_at,
            }
