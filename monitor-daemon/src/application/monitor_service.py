import time
import threading

from domain.sensor import SensorReading
from domain.module import SensorModule


class MonitorService:
    def __init__(self, modules: list[SensorModule]):
        self._lock = threading.Lock()
        self._modules = modules
        self._latest: dict[str, SensorReading] = {}
        self._updated_at: float | None = None

    def add_module(self, module: SensorModule):
        with self._lock:
            self._modules.append(module)

    def poll(self):
        with self._lock:
            for module in self._modules:
                if not module.is_online():
                    continue
                for reading in module.read_all():
                    self._latest[reading.sensor_id] = reading
            self._updated_at = time.time()

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "readings": {
                    sid: {
                        "module": r.module_id,
                        "type": r.sensor_type.value,
                        "value": r.value,
                        "unit": r.unit,
                    }
                    for sid, r in self._latest.items()
                },
                "updated_at": self._updated_at,
            }
