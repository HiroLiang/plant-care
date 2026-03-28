from datetime import UTC, datetime

from domain.command import CommandLog, CommandStatus, CommandType
from domain.device import DeviceState, DeviceType
from domain.event import EventLog, EventType
from domain.node import Node, NodeKind, NodeStatus
from domain.sensor import LatestSensorReading, Sensor, SensorReading, SensorStatus, SensorType
from infrastructure.persistence.sqlite.records import (
    CommandLogRecord,
    DeviceStateRecord,
    EventLogRecord,
    LatestSensorReadingRecord,
    NodeRecord,
    SensorReadingRecord,
    SensorRecord,
)


def _to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    else:
        value = value.astimezone(UTC)
    return value.isoformat()


def _from_iso(value: str | None) -> datetime | None:
    if value is None:
        return None
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def node_to_record(node: Node) -> NodeRecord:
    return NodeRecord(
        node_id=node.node_id,
        node_kind=node.node_kind.value,
        display_name=node.display_name,
        serial_no=node.serial_no,
        status=node.status.value,
        last_seen_at=_to_iso(node.last_seen_at),
        created_at=_to_iso(node.created_at) or "",
        updated_at=_to_iso(node.updated_at) or "",
    )


def record_to_node(record: NodeRecord) -> Node:
    return Node(
        node_id=record.node_id,
        node_kind=NodeKind(record.node_kind),
        display_name=record.display_name,
        serial_no=record.serial_no,
        status=NodeStatus(record.status),
        last_seen_at=_from_iso(record.last_seen_at),
        created_at=_from_iso(record.created_at) or datetime.now(UTC),
        updated_at=_from_iso(record.updated_at) or datetime.now(UTC),
    )


def device_state_to_record(state: DeviceState) -> DeviceStateRecord:
    return DeviceStateRecord(
        node_id=state.node_id,
        device_type=state.device_type.value,
        is_active=1 if state.is_active else 0,
        level=state.level,
        reason=state.reason,
        updated_at=_to_iso(state.updated_at) or "",
    )


def record_to_device_state(record: DeviceStateRecord) -> DeviceState:
    return DeviceState(
        node_id=record.node_id,
        device_type=DeviceType(record.device_type),
        is_active=bool(record.is_active),
        level=record.level,
        reason=record.reason,
        updated_at=_from_iso(record.updated_at) or datetime.now(UTC),
    )


def sensor_to_record(sensor: Sensor) -> SensorRecord:
    return SensorRecord(
        sensor_id=sensor.sensor_id,
        node_id=sensor.node_id,
        sensor_type=sensor.sensor_type.value,
        channel=sensor.channel,
        unit=sensor.unit,
        display_name=sensor.display_name,
        created_at=_to_iso(sensor.created_at) or "",
    )


def record_to_sensor(record: SensorRecord) -> Sensor:
    return Sensor(
        sensor_id=record.sensor_id,
        node_id=record.node_id,
        sensor_type=SensorType(record.sensor_type),
        channel=record.channel,
        unit=record.unit,
        display_name=record.display_name,
        created_at=_from_iso(record.created_at) or datetime.now(UTC),
    )


def sensor_reading_to_record(reading: SensorReading) -> SensorReadingRecord:
    return SensorReadingRecord(
        reading_id=reading.reading_id,
        sensor_id=reading.sensor_id,
        node_id=reading.node_id,
        sensor_type=reading.sensor_type.value,
        value=reading.value,
        unit=reading.unit,
        status=reading.status.value,
        recorded_at=_to_iso(reading.recorded_at) or "",
    )


def record_to_sensor_reading(record: SensorReadingRecord) -> SensorReading:
    return SensorReading(
        reading_id=record.reading_id,
        sensor_id=record.sensor_id,
        node_id=record.node_id,
        sensor_type=SensorType(record.sensor_type),
        value=record.value,
        unit=record.unit,
        status=SensorStatus(record.status),
        recorded_at=_from_iso(record.recorded_at) or datetime.now(UTC),
    )


def latest_sensor_reading_to_record(reading: LatestSensorReading) -> LatestSensorReadingRecord:
    return LatestSensorReadingRecord(
        sensor_id=reading.sensor_id,
        reading_id=reading.reading_id,
        node_id=reading.node_id,
        sensor_type=reading.sensor_type.value,
        value=reading.value,
        unit=reading.unit,
        status=reading.status.value,
        recorded_at=_to_iso(reading.recorded_at) or "",
    )


def record_to_latest_sensor_reading(record: LatestSensorReadingRecord) -> LatestSensorReading:
    return LatestSensorReading(
        sensor_id=record.sensor_id,
        reading_id=record.reading_id,
        node_id=record.node_id,
        sensor_type=SensorType(record.sensor_type),
        value=record.value,
        unit=record.unit,
        status=SensorStatus(record.status),
        recorded_at=_from_iso(record.recorded_at) or datetime.now(UTC),
    )


def command_log_to_record(command: CommandLog) -> CommandLogRecord:
    return CommandLogRecord(
        command_id=command.command_id,
        node_id=command.node_id,
        command_type=command.command_type.value,
        device_type=command.device_type,
        correlation_id=command.correlation_id,
        requested_by=command.requested_by,
        payload_json=command.payload_json,
        status=command.status.value,
        message=command.message,
        requested_at=_to_iso(command.requested_at) or "",
        accepted_at=_to_iso(command.accepted_at),
        finished_at=_to_iso(command.finished_at),
    )


def record_to_command_log(record: CommandLogRecord) -> CommandLog:
    return CommandLog(
        command_id=record.command_id,
        node_id=record.node_id,
        command_type=CommandType(record.command_type),
        device_type=record.device_type,
        correlation_id=record.correlation_id,
        requested_by=record.requested_by,
        payload_json=record.payload_json,
        status=CommandStatus(record.status),
        message=record.message,
        requested_at=_from_iso(record.requested_at) or datetime.now(UTC),
        accepted_at=_from_iso(record.accepted_at),
        finished_at=_from_iso(record.finished_at),
    )


def event_log_to_record(event: EventLog) -> EventLogRecord:
    return EventLogRecord(
        event_id=event.event_id,
        node_id=event.node_id,
        event_type=event.event_type.value,
        correlation_id=event.correlation_id,
        command_id=event.command_id,
        payload_json=event.payload_json,
        recorded_at=_to_iso(event.recorded_at) or "",
    )


def record_to_event_log(record: EventLogRecord) -> EventLog:
    return EventLog(
        event_id=record.event_id,
        node_id=record.node_id,
        event_type=EventType(record.event_type),
        correlation_id=record.correlation_id,
        command_id=record.command_id,
        payload_json=record.payload_json,
        recorded_at=_from_iso(record.recorded_at) or datetime.now(UTC),
    )
