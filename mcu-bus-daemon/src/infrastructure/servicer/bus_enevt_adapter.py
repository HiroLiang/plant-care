from datetime import UTC, timezone

from google.protobuf.timestamp_pb2 import Timestamp

from domain.mcu_bus import (
    AlertEvent,
    BusEvent,
    CommandResultEvent,
    DeviceStateEvent,
    HeartbeatEvent,
    TelemetryEvent,
)
from mcubus.v1 import common_pb2, events_pb2


def to_proto(event: BusEvent) -> events_pb2.BusEvent:
    proto = events_pb2.BusEvent(
        event_id=event.event_id,
        source_node_id=event.source_node_id,
        correlation_id=event.correlation_id,
        command_id=event.command_id,
    )

    ts = Timestamp()
    event_timestamp = event.emitted_at
    if event_timestamp.tzinfo is None:
        event_timestamp = event_timestamp.replace(tzinfo=UTC)
    else:
        event_timestamp = event_timestamp.astimezone(timezone.utc)
    ts.FromDatetime(event_timestamp)
    proto.emitted_at.CopyFrom(ts)

    match event.payload:
        case TelemetryEvent():
            proto.event_type = common_pb2.EVENT_TYPE_TELEMETRY
            proto.telemetry.CopyFrom(
                events_pb2.TelemetryEvent(
                    readings=[
                        events_pb2.SensorReading(
                            sensor_type=_sensor_type(reading.sensor_type),
                            value=reading.value,
                            unit=_value_unit(reading.unit),
                            channel=reading.channel,
                            status=_reading_status(reading.status),
                        )
                        for reading in event.payload.readings
                    ]
                )
            )

        case HeartbeatEvent():
            proto.event_type = common_pb2.EVENT_TYPE_HEARTBEAT
            proto.heartbeat.CopyFrom(
                events_pb2.HeartbeatEvent(
                    status=event.payload.status,
                    voltage=event.payload.voltage,
                    uptime_seconds=event.payload.uptime_seconds,
                )
            )

        case DeviceStateEvent():
            proto.event_type = common_pb2.EVENT_TYPE_DEVICE_STATE
            proto.device_state.CopyFrom(
                events_pb2.DeviceStateEvent(
                    device_type=_device_type(event.payload.device_type),
                    is_active=event.payload.is_active,
                    level=event.payload.level,
                    reason=event.payload.reason,
                )
            )

        case CommandResultEvent():
            proto.event_type = common_pb2.EVENT_TYPE_COMMAND_RESULT
            proto.command_result.CopyFrom(
                events_pb2.CommandResultEvent(
                    command_id=event.payload.command_id,
                    status=_command_status(event.payload.status),
                    message=event.payload.message,
                    device_type=_device_type(event.payload.device_type),
                )
            )

        case AlertEvent():
            proto.event_type = common_pb2.EVENT_TYPE_ALERT
            proto.alert.CopyFrom(
                events_pb2.AlertEvent(
                    severity=_alert_severity(event.payload.severity),
                    code=event.payload.code,
                    message=event.payload.message,
                )
            )

        case _:
            raise ValueError(f"Unsupported payload type: {type(event.payload)}")

    return proto


def _sensor_type(name: str) -> int:
    mapping = {
        "temperature": common_pb2.SENSOR_TYPE_TEMPERATURE,
        "humidity": common_pb2.SENSOR_TYPE_HUMIDITY,
        "soil_moisture": common_pb2.SENSOR_TYPE_SOIL_MOISTURE,
        "light_level": common_pb2.SENSOR_TYPE_LIGHT_LEVEL,
        "water_level": common_pb2.SENSOR_TYPE_WATER_LEVEL,
        "ph": common_pb2.SENSOR_TYPE_PH,
    }
    return mapping.get(name, common_pb2.SENSOR_TYPE_UNSPECIFIED)


def _value_unit(name: str) -> int:
    mapping = {
        "celsius": common_pb2.VALUE_UNIT_CELSIUS,
        "percent": common_pb2.VALUE_UNIT_PERCENT,
        "volt": common_pb2.VALUE_UNIT_VOLT,
        "ratio": common_pb2.VALUE_UNIT_RATIO,
    }
    return mapping.get(name, common_pb2.VALUE_UNIT_UNSPECIFIED)


def _reading_status(name: str) -> int:
    mapping = {
        "ok": common_pb2.READING_STATUS_OK,
        "error": common_pb2.READING_STATUS_ERROR,
    }
    return mapping.get(name, common_pb2.READING_STATUS_UNSPECIFIED)


def _device_type(name: str) -> int:
    mapping = {
        "pump": common_pb2.DEVICE_TYPE_PUMP,
        "fan": common_pb2.DEVICE_TYPE_FAN,
        "light": common_pb2.DEVICE_TYPE_LIGHT,
    }
    return mapping.get(name, common_pb2.DEVICE_TYPE_UNSPECIFIED)


def _command_status(name: str) -> int:
    mapping = {
        "accepted": common_pb2.COMMAND_STATUS_ACCEPTED,
        "succeeded": common_pb2.COMMAND_STATUS_SUCCEEDED,
        "rejected": common_pb2.COMMAND_STATUS_REJECTED,
        "invalid_argument": common_pb2.COMMAND_STATUS_INVALID_ARGUMENT,
        "unsupported": common_pb2.COMMAND_STATUS_UNSUPPORTED,
        "failed": common_pb2.COMMAND_STATUS_FAILED,
    }
    return mapping.get(name, common_pb2.COMMAND_STATUS_UNSPECIFIED)


def _alert_severity(name: str) -> int:
    mapping = {
        "info": common_pb2.ALERT_SEVERITY_INFO,
        "warning": common_pb2.ALERT_SEVERITY_WARNING,
        "error": common_pb2.ALERT_SEVERITY_ERROR,
        "critical": common_pb2.ALERT_SEVERITY_CRITICAL,
    }
    return mapping.get(name, common_pb2.ALERT_SEVERITY_UNSPECIFIED)
