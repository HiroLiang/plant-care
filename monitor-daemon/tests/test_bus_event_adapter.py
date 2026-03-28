from datetime import datetime, timezone

from google.protobuf.timestamp_pb2 import Timestamp
from mcubus.v1 import events_pb2

from infrastructure.mcu.bus_event_adapter import to_domain


def test_to_domain_sensor_event():
    ts = Timestamp()
    ts.FromDatetime(datetime(2026, 3, 18, tzinfo=timezone.utc))
    event = events_pb2.BusEvent(
        event_id="evt-1",
        module_id="1",
        timestamp=ts,
        sensor_data=events_pb2.SensorData(
            temperature=25.5,
            humidity=60.0,
        ),
    )

    domain_event = to_domain(event)

    assert domain_event.module_id == "1"
    assert domain_event.payload.temperature == 25.5
    assert domain_event.payload.humidity == 60.0


def test_to_domain_alert_event():
    ts = Timestamp()
    ts.FromDatetime(datetime(2026, 3, 18, tzinfo=timezone.utc))
    event = events_pb2.BusEvent(
        event_id="evt-2",
        module_id="1",
        timestamp=ts,
        alert=events_pb2.AlertEvent(
            severity="error",
            code="heartbeat_status_79",
            message="boom",
        ),
    )

    domain_event = to_domain(event)

    assert domain_event.payload.code == "heartbeat_status_79"
