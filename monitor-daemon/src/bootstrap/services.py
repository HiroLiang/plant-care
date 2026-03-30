import asyncio
import logging
import os
from threading import Event, Thread

from application.monitor_service import MonitorService
from bootstrap.clients import Clients
from plant_core.infrastructure.persistence.sqlite.bundle import SQLiteRepositoryBundle
from infrastructure.module.local_module import LocalSensorModule
from infrastructure.sensor.mock import MockTemperatureSensor, MockHumiditySensor
from infrastructure.sensor.sht31 import SHT31Device, SHT31TemperatureSensor, SHT31HumiditySensor

POLL_INTERVAL = 2.0
logger = logging.getLogger(__name__)


class Services:
    def __init__(self, monitor_service: MonitorService):
        self.monitor_service = monitor_service
        self._polling_stop = Event()
        self._polling_thread: Thread | None = None

    def start_polling(self, loop) -> None:
        if self._polling_thread and self._polling_thread.is_alive():
            return

        self._polling_stop.clear()

        def _worker() -> None:
            while not self._polling_stop.wait(POLL_INTERVAL):
                future = asyncio.run_coroutine_threadsafe(
                    self.monitor_service.refresh_local_modules(),
                    loop,
                )
                try:
                    future.result()
                except Exception:
                    logger.exception("Local polling refresh failed")

        self._polling_thread = Thread(
            target=_worker,
            daemon=True,
            name="MonitorLocalPolling",
        )
        self._polling_thread.start()

    def stop_polling(self) -> None:
        self._polling_stop.set()
        if self._polling_thread and self._polling_thread.is_alive():
            self._polling_thread.join(timeout=POLL_INTERVAL + 1.0)
        self._polling_thread = None

async def init_services(
    repositories: SQLiteRepositoryBundle,
    clients: Clients | None = None,
) -> Services:
    local_modules = build_local_module()

    return Services(
        monitor_service=MonitorService([local_modules], repositories)
    )


def build_local_module():
    runtime = os.getenv("RUNTIME_ENV", "mock")

    module = LocalSensorModule()

    if runtime == "rasp":
        device = SHT31Device()
        module.add_sensor(SHT31TemperatureSensor(device))
        module.add_sensor(SHT31HumiditySensor(device))

    # default: mock
    module.add_sensor(MockTemperatureSensor(base=26.5))
    module.add_sensor(MockHumiditySensor(base=55.0))

    return module


async def shutdown_services(services: Services | None) -> None:
    if services is None:
        return
    services.stop_polling()
