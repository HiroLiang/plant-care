from datetime import datetime, timezone

import pytest
from google.protobuf.timestamp_pb2 import Timestamp
from plant_core.generated.mcubus.v1 import common_pb2, events_pb2

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
    assert domain_event.payload.severity == "error"


def test_to_domain_heartbeat_event_preserves_fields():
    ts = Timestamp()
    ts.FromDatetime(datetime(2026, 3, 18, tzinfo=timezone.utc))
    event = events_pb2.BusEvent(
        event_id="evt-3",
        source_node_id=9,
        emitted_at=ts,
        event_type=common_pb2.EVENT_TYPE_HEARTBEAT,
        heartbeat=events_pb2.HeartbeatEvent(
            status=7,
            voltage=12.4,
            uptime_seconds=321,
        ),
    )

    domain_event = to_domain(event)

    assert domain_event.source_node_id == 9
    assert domain_event.payload.status == 7
    assert domain_event.payload.voltage == pytest.approx(12.4)
    assert domain_event.payload.uptime_seconds == 321
    assert domain_event.emitted_at == datetime(2026, 3, 18, tzinfo=timezone.utc)
