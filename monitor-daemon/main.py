import os
import threading
import time
import uvicorn

from application.monitor_service import MonitorService
from dotenv import load_dotenv
from interface.http.api import create_app

# Use mock while testing
from infrastructure.sensor.mock import (
    MockTemperatureSensor,
    MockHumiditySensor,
)

# While deploy on Raspberry：
from infrastructure.sensor.sht31 import (
    _SHT31Device,
    SHT31TemperatureSensor,
    SHT31HumiditySensor,
)

# load env
load_dotenv()

POLL_INTERVAL = 2.0


def build_sensors():
    backend = os.getenv("SENSOR_BACKEND", "mock")

    if backend == "sht31":
        device = _SHT31Device()
        return (
            SHT31TemperatureSensor(device),
            SHT31HumiditySensor(device),
        )

    # default: mock
    return (
        MockTemperatureSensor(base=26.5),
        MockHumiditySensor(base=55.0),
    )


def start_polling(service: MonitorService):
    while True:
        service.poll()
        time.sleep(POLL_INTERVAL)


def main():
    # --- wiring ---
    temp_sensor, humidity_sensor = build_sensors()

    service = MonitorService(
        temp_sensor=temp_sensor,
        humidity_sensor=humidity_sensor,
    )

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
