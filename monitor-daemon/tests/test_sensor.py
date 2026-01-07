import logging
from domain.sensor import SensorType
from infrastructure.sensor.mock import MockTemperatureSensor

logger = logging.getLogger(__name__)


def test_sensor_features():
    sensor = MockTemperatureSensor(60)

    reading = sensor.read()
    logger.info("sensor_read %s", reading)

    assert sensor.sensor_id == "mock_temperature_sensor"
    assert sensor.sensor_type == SensorType.TEMPERATURE
    assert reading is not None
