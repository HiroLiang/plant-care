import struct

from infrastructure.bus.can_protocol import HeartbeatData, TempHumData, parse_can_id


def test_parse_can_id_for_temp_hum():
    node_id, data_type = parse_can_id(0x83)

    assert node_id == 0x01
    assert data_type == 0x03


def test_parse_can_id_for_heartbeat():
    node_id, data_type = parse_can_id(0xA2)

    assert node_id == 0x01
    assert data_type == 0x22


def test_temp_hum_from_bytes():
    payload = struct.pack("<hHB", 2534, 6123, 1)

    data = TempHumData.from_bytes(payload)

    assert data.temperature == 25.34
    assert data.humidity == 61.23
    assert data.status == 1


def test_heartbeat_from_bytes():
    payload = struct.pack("<BBHI", 1, 0, 3300, 123)

    data = HeartbeatData.from_bytes(payload)

    assert data.node_id == 1
    assert data.status == 0
    assert data.voltage == 3.3
    assert data.uptime == 123
