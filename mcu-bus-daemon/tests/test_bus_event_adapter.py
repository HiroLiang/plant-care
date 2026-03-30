from datetime import datetime, timezone

import pytest

from domain.mcu_bus import AlertEvent, BusEvent, HeartbeatEvent, TelemetryEvent, TelemetryReading
from infrastructure.servicer.bus_enevt_adapter import to_proto
from plant_core.generated.mcubus.v1 import common_pb2


def test_to_proto_telemetry_event_sets_core_fields():
    event = BusEvent(
        event_id="evt-telemetry",
        source_node_id=3,
        emitted_at=datetime(2026, 3, 18, tzinfo=timezone.utc),
        payload=TelemetryEvent(
            readings=[
                TelemetryReading(
                    sensor_type="temperature",
                    value=24.5,
                    unit="celsius",
                    status="ok",
                )
            ]
        ),
        correlation_id="corr-1",
    )

    proto = to_proto(event)

    assert proto.event_id == "evt-telemetry"
    assert proto.source_node_id == 3
    assert proto.correlation_id == "corr-1"
    assert proto.event_type == common_pb2.EVENT_TYPE_TELEMETRY
    assert proto.WhichOneof("payload") == "telemetry"
    assert proto.telemetry.readings[0].sensor_type == common_pb2.SENSOR_TYPE_TEMPERATURE
    assert proto.telemetry.readings[0].unit == common_pb2.VALUE_UNIT_CELSIUS


def test_to_proto_heartbeat_event_sets_core_fields():
    event = BusEvent(
        event_id="evt-heartbeat",
        source_node_id=8,
        emitted_at=datetime(2026, 3, 18, tzinfo=timezone.utc),
        payload=HeartbeatEvent(
            status=5,
            voltage=12.1,
            uptime_seconds=123,
        ),
    )

    proto = to_proto(event)

    assert proto.event_type == common_pb2.EVENT_TYPE_HEARTBEAT
    assert proto.WhichOneof("payload") == "heartbeat"
    assert proto.heartbeat.status == 5
    assert proto.heartbeat.voltage == pytest.approx(12.1)
    assert proto.heartbeat.uptime_seconds == 123


def test_to_proto_alert_event_sets_core_fields():
    event = BusEvent(
        event_id="evt-alert",
        source_node_id=5,
        emitted_at=datetime(2026, 3, 18, tzinfo=timezone.utc),
        payload=AlertEvent(
            severity="critical",
            code="can_fault",
            message="bus off",
        ),
    )

    proto = to_proto(event)

    assert proto.event_type == common_pb2.EVENT_TYPE_ALERT
    assert proto.WhichOneof("payload") == "alert"
    assert proto.alert.severity == common_pb2.ALERT_SEVERITY_CRITICAL
    assert proto.alert.code == "can_fault"
    assert proto.alert.message == "bus off"
