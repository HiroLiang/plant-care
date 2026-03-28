import time
import threading
import logging

from domain.mcu_bus_event import AlertEvent, MCUBusEvent, SensorDataEvent
from domain.sensor import SensorReading
from domain.module import SensorModule
from domain.sensor import SensorType

logger = logging.getLogger(__name__)


class MonitorService:
    def __init__(self, modules: list[SensorModule]):
        self._lock = threading.Lock()
        self._modules = modules
        self._latest: dict[str, SensorReading] = {}
        self._updated_at: float | None = None

    def add_module(self, module: SensorModule):
        with self._lock:
            self._modules.append(module)

    def upsert_reading(self, reading: SensorReading) -> None:
        with self._lock:
            self._latest[reading.sensor_id] = reading
            self._updated_at = reading.timestamp

    def ingest_mcu_event(self, event: MCUBusEvent) -> None:
        payload = event.payload

        if isinstance(payload, SensorDataEvent):
            event_ts = event.timestamp.timestamp()
            self.upsert_reading(SensorReading(
                sensor_id=f"mcu:{event.module_id}:temperature",
                sensor_type=SensorType.TEMPERATURE,
                value=payload.temperature,
                unit="°C",
                timestamp=event_ts,
                module_id=event.module_id,
            ))
            self.upsert_reading(SensorReading(
                sensor_id=f"mcu:{event.module_id}:humidity",
                sensor_type=SensorType.HUMIDITY,
                value=payload.humidity,
                unit="%",
                timestamp=event_ts,
                module_id=event.module_id,
            ))
            return

        if isinstance(payload, AlertEvent):
            logger.warning(
                "MCU alert received from module %s: [%s] %s",
                event.module_id,
                payload.code,
                payload.message,
            )
            return

        logger.info("Ignored MCU event payload type: %s", type(payload).__name__)

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
