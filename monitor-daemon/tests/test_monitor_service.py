import time

from application.monitor_service import MonitorService
from infrastructure.module.local_module import LocalSensorModule
from infrastructure.sensor.mock import (
    MockTemperatureSensor,
    MockHumiditySensor,
)


def test_monitor_service_poll_and_snapshot():
    # Arrange
    temp_sensor = MockTemperatureSensor(base=26.5)
    humidity_sensor = MockHumiditySensor(base=55.2)

    module = LocalSensorModule(module_id="test_module")
    module.add_sensor(temp_sensor)
    module.add_sensor(humidity_sensor)

    service = MonitorService(modules=[module])

    # Act
    service.poll()
    snapshot = service.snapshot()

    # Assert
    assert len(snapshot) > 0
