import json
from datetime import UTC, datetime
from uuid import uuid4

from domain.mcu_bus_event import (
    AlertEvent,
    CommandResultEvent,
    DeviceStateEvent,
    HeartbeatEvent,
    MCUBusEvent,
    TelemetryEvent,
)
from domain.module import SensorModule
from domain.sensor import SensorType
from plant_core.domain.command import CommandStatus
from plant_core.domain.device import DeviceState, DeviceType
from plant_core.domain.event import EventLog, EventType
from plant_core.domain.node import Node, NodeKind, NodeStatus
from plant_core.domain.sensor import Sensor as CoreSensor
from plant_core.domain.sensor import SensorReading as CoreSensorReading
from plant_core.domain.sensor import SensorStatus as CoreSensorStatus
from plant_core.domain.sensor import SensorType as CoreSensorType
from plant_core.infrastructure.persistence.sqlite.bundle import SQLiteRepositoryBundle


class MonitorService:
    def __init__(self, modules: list[SensorModule], repositories: SQLiteRepositoryBundle):
        self._modules = modules
        self._repositories = repositories

    def add_module(self, module: SensorModule):
        self._modules.append(module)

    async def refresh_local_modules(self) -> None:
        now = datetime.now(UTC)
        for module in self._modules:
            node = Node(
                node_id=_local_node_id(module.module_id),
                node_kind=NodeKind.LOCAL,
                display_name=f"Local module {module.module_id}",
                serial_no=None,
                status=NodeStatus.ONLINE if module.is_online() else NodeStatus.OFFLINE,
                last_seen_at=now if module.is_online() else None,
                created_at=now,
                updated_at=now,
            )
            await self._repositories.nodes.upsert(node)

            if not module.is_online():
                continue

            readings = module.read_all()
            for reading in readings:
                sensor = CoreSensor(
                    sensor_id=_local_sensor_id(module.module_id, reading.sensor_id),
                    node_id=node.node_id,
                    sensor_type=_core_sensor_type(reading.sensor_type),
                    channel=None,
                    unit=reading.unit,
                    display_name=reading.sensor_id,
                    created_at=now,
                )
                await self._repositories.sensors.upsert(sensor)
                await self._repositories.sensor_readings.append(
                    CoreSensorReading(
                        reading_id=str(uuid4()),
                        sensor_id=sensor.sensor_id,
                        node_id=node.node_id,
                        sensor_type=sensor.sensor_type,
                        value=reading.value,
                        unit=reading.unit,
                        status=CoreSensorStatus.OK,
                        recorded_at=datetime.fromtimestamp(reading.timestamp, UTC),
                    )
                )

    async def ingest_mcu_event(self, event: MCUBusEvent) -> None:
        node_id = _mcu_node_id(event.source_node_id)
        await self._repositories.nodes.upsert(
            Node(
                node_id=node_id,
                node_kind=NodeKind.MCU,
                display_name=f"MCU {event.source_node_id}",
                serial_no=None,
                status=NodeStatus.ONLINE,
                last_seen_at=event.emitted_at,
                created_at=event.emitted_at,
                updated_at=event.emitted_at,
            )
        )

        payload = event.payload

        if isinstance(payload, TelemetryEvent):
            for reading in payload.readings:
                sensor_type = _core_sensor_type_from_name(reading.sensor_type)
                if sensor_type is None:
                    continue
                sensor_id = _mcu_sensor_id(event.source_node_id, reading.sensor_type, reading.channel)
                await self._repositories.sensors.upsert(
                    CoreSensor(
                        sensor_id=sensor_id,
                        node_id=node_id,
                        sensor_type=sensor_type,
                        channel=reading.channel or None,
                        unit=reading.unit,
                        display_name=sensor_id,
                        created_at=event.emitted_at,
                    )
                )
                await self._repositories.sensor_readings.append(
                    CoreSensorReading(
                        reading_id=f"{event.event_id}:{sensor_id}",
                        sensor_id=sensor_id,
                        node_id=node_id,
                        sensor_type=sensor_type,
                        value=reading.value,
                        unit=reading.unit,
                        status=_core_sensor_status_from_name(reading.status),
                        recorded_at=event.emitted_at,
                    )
                )

        if isinstance(payload, DeviceStateEvent):
            await self._repositories.device_states.upsert(
                DeviceState(
                    node_id=node_id,
                    device_type=_core_device_type(payload.device_type),
                    is_active=payload.is_active,
                    level=payload.level,
                    reason=payload.reason or None,
                    updated_at=event.emitted_at,
                )
            )

        if isinstance(payload, CommandResultEvent):
            command_status = _core_command_status(payload.status)
            if command_status is not None:
                existing = await self._repositories.command_logs.get(payload.command_id)
                if existing is not None:
                    accepted_at = event.emitted_at if command_status is CommandStatus.ACCEPTED else None
                    finished_at = None if command_status is CommandStatus.ACCEPTED else event.emitted_at
                    await self._repositories.command_logs.update_status(
                        payload.command_id,
                        command_status,
                        payload.message,
                        accepted_at,
                        finished_at,
                    )

        await self._repositories.event_logs.append(
            EventLog(
                event_id=event.event_id,
                node_id=node_id,
                event_type=_core_event_type(payload),
                correlation_id=event.correlation_id or None,
                command_id=await _persisted_command_id_for_event(self._repositories, event),
                payload_json=json.dumps(_payload_to_json(payload), sort_keys=True),
                recorded_at=event.emitted_at,
            )
        )

    async def get_all_status(self, node_id: str | None = None) -> dict:
        latest_readings = await self._latest_readings(node_id)
        updated_at = max((reading.recorded_at.timestamp() for reading in latest_readings), default=None)
        return {
            "readings": {
                reading.sensor_id: {
                    "node_id": reading.node_id,
                    "type": reading.sensor_type.value,
                    "value": reading.value,
                    "unit": reading.unit,
                    "status": reading.status.value,
                    "recorded_at": reading.recorded_at.isoformat(),
                }
                for reading in latest_readings
            },
            "updated_at": updated_at,
        }

    async def get_device_states(self, node_id: str | None = None) -> list[dict]:
        device_states = await self._device_states(node_id)
        return [
            {
                "node_id": state.node_id,
                "device_type": state.device_type.value,
                "is_active": state.is_active,
                "level": state.level,
                "reason": state.reason,
                "updated_at": state.updated_at.isoformat(),
            }
            for state in device_states
        ]

    async def get_event_history(
        self,
        node_id: str | None = None,
        command_id: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        if command_id:
            events = await self._repositories.event_logs.list_by_command(command_id)
            if not events:
                events = [
                    event
                    for event in await self._repositories.event_logs.list_recent(max(limit, 200))
                    if _event_matches_command(event, command_id)
                ]
        elif node_id:
            events = await self._repositories.event_logs.list_by_node(node_id, limit)
        else:
            events = await self._repositories.event_logs.list_recent(limit)

        return [
            {
                "event_id": event.event_id,
                "node_id": event.node_id,
                "event_type": event.event_type.value,
                "correlation_id": event.correlation_id,
                "command_id": _event_command_id(event),
                "payload": json.loads(event.payload_json),
                "recorded_at": event.recorded_at.isoformat(),
            }
            for event in events[:limit]
        ]

    async def _latest_readings(self, node_id: str | None) -> list:
        node_ids = [node_id] if node_id else [node.node_id for node in await self._repositories.nodes.list_all()]
        latest = []
        for current_node_id in node_ids:
            latest.extend(await self._repositories.sensor_readings.list_latest_by_node(current_node_id))
        latest.sort(key=lambda reading: (reading.node_id, reading.sensor_id))
        return latest

    async def _device_states(self, node_id: str | None) -> list[DeviceState]:
        node_ids = [node_id] if node_id else [node.node_id for node in await self._repositories.nodes.list_all()]
        states = []
        for current_node_id in node_ids:
            states.extend(await self._repositories.device_states.list_by_node(current_node_id))
        states.sort(key=lambda state: (state.node_id, state.device_type.value))
        return states


def _local_node_id(module_id: str) -> str:
    return f"local:{module_id}"


def _local_sensor_id(module_id: str, sensor_id: str) -> str:
    return f"{_local_node_id(module_id)}:{sensor_id}"


def _mcu_node_id(source_node_id: int) -> str:
    return f"mcu:{source_node_id}"


def _mcu_sensor_id(source_node_id: int, sensor_type: str, channel: str) -> str:
    base = f"{_mcu_node_id(source_node_id)}:{sensor_type}"
    return f"{base}:{channel}" if channel else base


def _core_sensor_type(sensor_type: SensorType) -> CoreSensorType:
    mapping = {
        SensorType.TEMPERATURE: CoreSensorType.TEMPERATURE,
        SensorType.HUMIDITY: CoreSensorType.HUMIDITY,
        SensorType.SOIL_MOISTURE: CoreSensorType.SOIL_MOISTURE,
        SensorType.LIGHT: CoreSensorType.LIGHT_LEVEL,
    }
    return mapping[sensor_type]


def _core_sensor_type_from_name(sensor_type: str) -> CoreSensorType | None:
    mapping = {
        "temperature": CoreSensorType.TEMPERATURE,
        "humidity": CoreSensorType.HUMIDITY,
        "soil_moisture": CoreSensorType.SOIL_MOISTURE,
        "light": CoreSensorType.LIGHT_LEVEL,
        "light_level": CoreSensorType.LIGHT_LEVEL,
        "water_level": CoreSensorType.WATER_LEVEL,
        "ph": CoreSensorType.PH,
    }
    return mapping.get(sensor_type)


def _core_sensor_status_from_name(status: str) -> CoreSensorStatus:
    mapping = {
        "ok": CoreSensorStatus.OK,
        "error": CoreSensorStatus.ERROR,
    }
    return mapping.get(status, CoreSensorStatus.UNKNOWN)


def _core_device_type(device_type: str) -> DeviceType:
    return DeviceType(device_type)


def _core_command_status(status: str) -> CommandStatus | None:
    try:
        return CommandStatus(status)
    except ValueError:
        return None


def _core_event_type(payload: object) -> EventType:
    mapping = {
        TelemetryEvent: EventType.TELEMETRY,
        HeartbeatEvent: EventType.HEARTBEAT,
        DeviceStateEvent: EventType.DEVICE_STATE,
        CommandResultEvent: EventType.COMMAND_RESULT,
        AlertEvent: EventType.ALERT,
    }
    return mapping[type(payload)]


def _payload_to_json(payload: object) -> dict:
    if isinstance(payload, TelemetryEvent):
        return {
            "readings": [
                {
                    "sensor_type": reading.sensor_type,
                    "value": reading.value,
                    "unit": reading.unit,
                    "channel": reading.channel,
                    "status": reading.status,
                }
                for reading in payload.readings
            ]
        }

    if isinstance(payload, HeartbeatEvent):
        return {
            "status": payload.status,
            "voltage": payload.voltage,
            "uptime_seconds": payload.uptime_seconds,
        }

    if isinstance(payload, DeviceStateEvent):
        return {
            "device_type": payload.device_type,
            "is_active": payload.is_active,
            "level": payload.level,
            "reason": payload.reason,
        }

    if isinstance(payload, CommandResultEvent):
        return {
            "command_id": payload.command_id,
            "status": payload.status,
            "message": payload.message,
            "device_type": payload.device_type,
        }

    if isinstance(payload, AlertEvent):
        return {
            "severity": payload.severity,
            "code": payload.code,
            "message": payload.message,
        }

    raise ValueError(f"Unsupported payload type: {type(payload).__name__}")


def _command_id_for_event(event: MCUBusEvent) -> str | None:
    if event.command_id:
        return event.command_id
    if isinstance(event.payload, CommandResultEvent) and event.payload.command_id:
        return event.payload.command_id
    return None


async def _persisted_command_id_for_event(
    repositories: SQLiteRepositoryBundle,
    event: MCUBusEvent,
) -> str | None:
    command_id = _command_id_for_event(event)
    if command_id is None:
        return None
    existing = await repositories.command_logs.get(command_id)
    return command_id if existing is not None else None


def _event_matches_command(event: EventLog, command_id: str) -> bool:
    if event.command_id == command_id:
        return True
    payload = json.loads(event.payload_json)
    return payload.get("command_id") == command_id


def _event_command_id(event: EventLog) -> str | None:
    if event.command_id is not None:
        return event.command_id
    payload = json.loads(event.payload_json)
    return payload.get("command_id")
