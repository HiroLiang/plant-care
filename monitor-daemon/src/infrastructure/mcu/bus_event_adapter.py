from datetime import timezone

from domain.mcu_bus_event import (
    AlertEvent,
    BusPayload,
    CommandResultEvent,
    DeviceStateEvent,
    HeartbeatEvent,
    MCUBusEvent,
    TelemetryEvent,
    TelemetryReading,
)
from mcubus.v1 import common_pb2, events_pb2


def to_domain(event: events_pb2.BusEvent) -> MCUBusEvent:
    return MCUBusEvent(
        event_id=event.event_id,
        source_node_id=event.source_node_id,
        emitted_at=event.emitted_at.ToDatetime().replace(tzinfo=timezone.utc),
        correlation_id=event.correlation_id,
        command_id=event.command_id,
        payload=to_payload(event),
    )


def to_payload(event: events_pb2.BusEvent) -> BusPayload:
    payload_type = event.WhichOneof("payload")

    if payload_type == "telemetry":
        return TelemetryEvent(
            readings=[
                TelemetryReading(
                    sensor_type=_sensor_type_name(reading.sensor_type),
                    value=reading.value,
                    unit=_value_unit_name(reading.unit),
                    channel=reading.channel,
                    status=_reading_status_name(reading.status),
                )
                for reading in event.telemetry.readings
            ]
        )

    if payload_type == "heartbeat":
        hb = event.heartbeat
        return HeartbeatEvent(
            status=hb.status,
            voltage=hb.voltage,
            uptime_seconds=hb.uptime_seconds,
        )

    if payload_type == "device_state":
        state = event.device_state
        return DeviceStateEvent(
            device_type=_device_type_name(state.device_type),
            is_active=state.is_active,
            level=state.level,
            reason=state.reason,
        )

    if payload_type == "command_result":
        result = event.command_result
        return CommandResultEvent(
            command_id=result.command_id,
            status=_command_status_name(result.status),
            message=result.message,
            device_type=_device_type_name(result.device_type),
        )

    if payload_type == "alert":
        alert = event.alert
        return AlertEvent(
            severity=_alert_severity_name(alert.severity),
            code=alert.code,
            message=alert.message,
        )

    raise ValueError(f"Unknown payload type: {payload_type}")


def _sensor_type_name(value: int) -> str:
    mapping = {
        common_pb2.SENSOR_TYPE_TEMPERATURE: "temperature",
        common_pb2.SENSOR_TYPE_HUMIDITY: "humidity",
        common_pb2.SENSOR_TYPE_SOIL_MOISTURE: "soil_moisture",
        common_pb2.SENSOR_TYPE_LIGHT_LEVEL: "light_level",
        common_pb2.SENSOR_TYPE_WATER_LEVEL: "water_level",
        common_pb2.SENSOR_TYPE_PH: "ph",
    }
    return mapping.get(value, "unknown")


def _value_unit_name(value: int) -> str:
    mapping = {
        common_pb2.VALUE_UNIT_CELSIUS: "celsius",
        common_pb2.VALUE_UNIT_PERCENT: "percent",
        common_pb2.VALUE_UNIT_VOLT: "volt",
        common_pb2.VALUE_UNIT_RATIO: "ratio",
    }
    return mapping.get(value, "unspecified")


def _reading_status_name(value: int) -> str:
    mapping = {
        common_pb2.READING_STATUS_OK: "ok",
        common_pb2.READING_STATUS_ERROR: "error",
    }
    return mapping.get(value, "unspecified")


def _device_type_name(value: int) -> str:
    mapping = {
        common_pb2.DEVICE_TYPE_PUMP: "pump",
        common_pb2.DEVICE_TYPE_FAN: "fan",
        common_pb2.DEVICE_TYPE_LIGHT: "light",
    }
    return mapping.get(value, "unspecified")


def _command_status_name(value: int) -> str:
    mapping = {
        common_pb2.COMMAND_STATUS_ACCEPTED: "accepted",
        common_pb2.COMMAND_STATUS_SUCCEEDED: "succeeded",
        common_pb2.COMMAND_STATUS_REJECTED: "rejected",
        common_pb2.COMMAND_STATUS_INVALID_ARGUMENT: "invalid_argument",
        common_pb2.COMMAND_STATUS_UNSUPPORTED: "unsupported",
        common_pb2.COMMAND_STATUS_FAILED: "failed",
    }
    return mapping.get(value, "unspecified")


def _alert_severity_name(value: int) -> str:
    mapping = {
        common_pb2.ALERT_SEVERITY_INFO: "info",
        common_pb2.ALERT_SEVERITY_WARNING: "warning",
        common_pb2.ALERT_SEVERITY_ERROR: "error",
        common_pb2.ALERT_SEVERITY_CRITICAL: "critical",
    }
    return mapping.get(value, "unspecified")
