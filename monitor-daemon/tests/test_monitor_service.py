import time

from application.monitor_service import MonitorService
from infrastructure.sensor.mock import (
    MockTemperatureSensor,
    MockHumiditySensor,
)


def test_monitor_service_poll_and_snapshot():
    # Arrange
    temp_sensor = MockTemperatureSensor(base=26.5)
    humidity_sensor = MockHumiditySensor(base=55.2)

    service = MonitorService(
        temp_sensor=temp_sensor,
        humidity_sensor=humidity_sensor,
    )

    # Act
    before = time.time()
    service.poll()
    snapshot = service.snapshot()

    # Assert
    assert snapshot["temperature"] is not None
    assert snapshot["humidity"] is not None
    assert snapshot["updated_at"] is not None
    assert snapshot["updated_at"] >= before
