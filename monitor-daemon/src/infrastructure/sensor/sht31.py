from domain.sensor import TemperatureSensor, HumiditySensor

class _SHT31Device:
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


class SHT31TemperatureSensor(TemperatureSensor):
    def __init__(self, device: _SHT31Device):
        self._device = device

    def read(self) -> float:
        return self._device.read_temperature()

class SHT31HumiditySensor(HumiditySensor):
    def __init__(self, device: _SHT31Device):
        self._device = device

    def read(self) -> float:
        return self._device.read_humidity()