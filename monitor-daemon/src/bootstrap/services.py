import os
import time

from application.monitor_service import MonitorService
from infrastructure.module.local_module import LocalSensorModule
from infrastructure.sensor.mock import MockTemperatureSensor, MockHumiditySensor
from infrastructure.sensor.sht31 import SHT31Device, SHT31TemperatureSensor, SHT31HumiditySensor

POLL_INTERVAL = 2.0


class Services:
    def __init__(self, monitor_service: MonitorService):
        self.monitor_service = monitor_service


async def init_services() -> Services:
    local_modules = build_local_module()

    return Services(
        monitor_service=MonitorService([local_modules])
    )


def start_polling(service: MonitorService):
    while True:
        service.poll()
        time.sleep(POLL_INTERVAL)


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
