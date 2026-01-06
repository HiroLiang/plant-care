import os
import threading
import time
import uvicorn

from application.monitor_service import MonitorService
from dotenv import load_dotenv
from interface.http.api import create_app

from infrastructure.module.local_module import LocalSensorModule

# Use mock while testing
from infrastructure.sensor.mock import (
    MockTemperatureSensor,
    MockHumiditySensor,
)

# While deploy on Raspberry：
from infrastructure.sensor.sht31 import (
    SHT31Device,
    SHT31TemperatureSensor,
    SHT31HumiditySensor,
)

# load env
load_dotenv()

POLL_INTERVAL = 2.0


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


def start_polling(service: MonitorService):
    while True:
        service.poll()
        time.sleep(POLL_INTERVAL)


def main():
    # --- wiring ---
    local_modules = build_local_module()

    service = MonitorService([local_modules])

    # --- background polling ---
    t = threading.Thread(
        target=start_polling,
        args=(service,),
        daemon=True,
    )
    t.start()

    # --- FastAPI ---
    app = create_app(service)

    host = os.getenv("HTTP_HOST", "0.0.0.0")
    port = int(os.getenv("HTTP_PORT", "8001"))
    print(f"Listening on {host}:{port}")

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
