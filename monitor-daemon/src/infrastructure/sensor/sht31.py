from domain.sensor import Sensor, SensorType, SensorReading


class SHT31Device:
    """
    Internal shared device wrapper.
    Only this class touches I2C / adafruit.
    """

    def __init__(self):
        # Delayed import for Raspberry Pi environment
        import board
        import busio
        import adafruit_sht31d

        i2c = busio.I2C(board.SCL, board.SDA)
        self._dev = adafruit_sht31d.SHT31D(i2c)

    def read_temperature(self) -> float:
        return float(self._dev.temperature)

    def read_humidity(self) -> float:
        return float(self._dev.relative_humidity)


class SHT31TemperatureSensor(Sensor):
    """
    Sensor's implementation of SHT31 temperature sensor.
    """

    def __init__(self, device: SHT31Device, sensor_id: str = "sht31-temperature-sensor"):
        self._device = device
        self._sensor_id = sensor_id

    @property
    def sensor_id(self) -> str:
        return self._sensor_id

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.TEMPERATURE

    def read(self) -> SensorReading:
        return SensorReading(
            sensor_id=self._sensor_id,
            sensor_type=SensorType.TEMPERATURE,
            value=self._device.read_temperature(),
            unit="°C"
        )


class SHT31HumiditySensor(Sensor):
    """
    Sensor's implementation of SHT31 humidity sensor.
    """

    def __init__(self, device: SHT31Device, sensor_id: str = "sht31-humidity-sensor"):
        self._device = device
        self._sensor_id = sensor_id

    @property
    def sensor_id(self) -> str:
        return self._sensor_id

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.HUMIDITY

    def read(self) -> SensorReading:
        return SensorReading(
            sensor_id=self._sensor_id,
            sensor_type=SensorType.HUMIDITY,
            value=self._device.read_humidity(),
            unit="%"
        )
