import struct

from enum import IntEnum
from dataclasses import dataclass
from typing import Tuple


# CAN ID (11 bits)
class NodeId(IntEnum):
    """
    Node ID (4 bits, 0x00 - 0x0F)
    """
    MASTER = 0x00  # Raspberry Pi ID (For commands)
    BROADCAST = 0x0F  # Broadcast ID


class DataType(IntEnum):
    """
    Data type (7 bits, 0x00 - 0x7F)
    """

    # Sensor data (0x00-0x1F)
    TEMPERATURE = 0x01
    HUMIDITY = 0x02
    TEMP_HUM = 0x03
    SOIL_MOISTURE = 0x04
    LIGHT = 0x05
    WATER_LEVEL = 0x06

    # System status (0x20-0x3F)
    STATUS = 0x20
    ERROR = 0x21
    HEARTBEAT = 0x22

    # Control commend (0x40-0x5F) - Master → Node
    CMD_PUMP_CTRL = 0x40
    CMD_FAN_CTRL = 0x41
    CMD_LIGHT_CTRL = 0x42
    CMD_REQUEST_DATA = 0x43
    CMD_SET_THRESHOLD = 0x44
    CMD_RESET = 0x45

    # Response (0x60-0x7F)
    RESP_ACK = 0x60
    RESP_NACK = 0x61
    RESP_DATA = 0x62


class ErrorCode(IntEnum):
    """
    Error code (1 byte, in payload)
    """

    # 0x0X = no error
    NONE = 0x00

    # 0x1X = Sensor errors

    # 0x2X = Communication errors

    # 0x3X = Command errors

    # 0x4X = System error
    UNKNOWN_ERROR = 0x4F


@dataclass
class HeartbeatData:
    """
    Heartbeat data
    """
    node_id: int
    status: int
    voltage: float  # V
    uptime: int  # second

    @classmethod
    def from_bytes(cls, data: bytes) -> 'HeartbeatData':
        if len(data) < 8:
            raise ValueError(f"Invalid data length: {len(data)}")

        node_id, status, voltage_raw, uptime = struct.unpack('<BBHI', data[:8])
        return cls(
            node_id=node_id,
            status=status,
            voltage=voltage_raw / 1000.0,
            uptime=uptime
        )

    def __str__(self):
        status_str = ErrorCode(
            self.status).name if self.status in ErrorCode._value2member_map_ else f"0x{self.status:02X}"
        return f"Node {self.node_id}: Status={status_str}, Voltage={self.voltage:.2f}V, Uptime={self.uptime}s"


@dataclass
class TempHumData:
    """
    Temperature and humidity hybrid data
    """
    temperature: float  # °C
    humidity: float  # %RH
    status: int  # 0=OK, 1=Error

    @classmethod
    def from_bytes(cls, data: bytes) -> 'TempHumData':
        """
        Analyze from can
        :param data: Data bytes
        :return: TempHumData
        """
        if len(data) < 5:
            raise ValueError(f"Invalid data length: {len(data)}")

        # struct: int16 temp, uint16 hum, uint8 status
        temp_raw, hum_raw, status = struct.unpack('<hHB', data[:5])
        return cls(
            temperature=temp_raw / 100.0,
            humidity=hum_raw / 100.0,
            status=status
        )

    def __str__(self):
        status_str = "OK" if self.status == 0 else "ERROR"
        return f"Temp: {self.temperature:.2f}°C, Humidity: {self.humidity:.2f}%, Status: {status_str}"


def parse_can_id(can_id: int) -> Tuple[int, int]:
    """
    Analyze CAN ID -> (node_id, data_type)
    """
    node_id = (can_id >> 7) & 0x0F
    data_type = can_id & 0x7F
    return node_id, data_type
