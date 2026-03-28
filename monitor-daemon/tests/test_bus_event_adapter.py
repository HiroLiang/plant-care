from datetime import datetime, timezone

from google.protobuf.timestamp_pb2 import Timestamp
from mcubus.v1 import common_pb2, events_pb2

from infrastructure.mcu.bus_event_adapter import to_domain


def test_to_domain_sensor_event():
    ts = Timestamp()
    ts.FromDatetime(datetime(2026, 3, 18, tzinfo=timezone.utc))
    event = events_pb2.BusEvent(
        event_id="evt-1",
        source_node_id=1,
        emitted_at=ts,
        event_type=common_pb2.EVENT_TYPE_TELEMETRY,
        telemetry=events_pb2.TelemetryEvent(
            readings=[
                events_pb2.SensorReading(
                    sensor_type=common_pb2.SENSOR_TYPE_TEMPERATURE,
                    value=25.5,
                    unit=common_pb2.VALUE_UNIT_CELSIUS,
                    status=common_pb2.READING_STATUS_OK,
                ),
                events_pb2.SensorReading(
                    sensor_type=common_pb2.SENSOR_TYPE_HUMIDITY,
                    value=60.0,
                    unit=common_pb2.VALUE_UNIT_PERCENT,
                    status=common_pb2.READING_STATUS_OK,
                ),
            ]
        ),
    )

    domain_event = to_domain(event)

    assert domain_event.source_node_id == 1
    assert domain_event.payload.readings[0].value == 25.5
    assert domain_event.payload.readings[1].value == 60.0


def test_to_domain_alert_event():
    ts = Timestamp()
    ts.FromDatetime(datetime(2026, 3, 18, tzinfo=timezone.utc))
    event = events_pb2.BusEvent(
        event_id="evt-2",
        source_node_id=1,
        emitted_at=ts,
        event_type=common_pb2.EVENT_TYPE_ALERT,
        alert=events_pb2.AlertEvent(
            severity=common_pb2.ALERT_SEVERITY_ERROR,
            code="heartbeat_status_79",
            message="boom",
        ),
    )

    domain_event = to_domain(event)

    assert domain_event.payload.code == "heartbeat_status_79"
