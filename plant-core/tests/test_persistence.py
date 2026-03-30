import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from plant_core.domain.command import CommandLog, CommandStatus, CommandType
from plant_core.domain.device import DeviceState, DeviceType
from plant_core.domain.event import EventLog, EventType
from plant_core.domain.node import Node, NodeKind, NodeStatus
from plant_core.domain.sensor import LatestSensorReading, Sensor, SensorReading, SensorStatus, SensorType
from plant_core.infrastructure.persistence.sqlite.datasource import SQLiteDatasource
from plant_core.infrastructure.persistence.sqlite.bundle import SQLiteRepositoryBundle
from plant_core.infrastructure.persistence.sqlite.mappers import (
    command_log_to_record,
    event_log_to_record,
    latest_sensor_reading_to_record,
    node_to_record,
    record_to_command_log,
    record_to_event_log,
    record_to_latest_sensor_reading,
    record_to_node,
    record_to_sensor,
    record_to_sensor_reading,
    sensor_reading_to_record,
    sensor_to_record,
)
from plant_core.infrastructure.persistence.sqlite.repositories.sqlite_command_log_repository import (
    SQLiteCommandLogRepository,
)
from plant_core.infrastructure.persistence.sqlite.repositories.sqlite_device_state_repository import (
    SQLiteDeviceStateRepository,
)
from plant_core.infrastructure.persistence.sqlite.repositories.sqlite_event_log_repository import (
    SQLiteEventLogRepository,
)
from plant_core.infrastructure.persistence.sqlite.repositories.sqlite_node_repository import SQLiteNodeRepository
from plant_core.infrastructure.persistence.sqlite.repositories.sqlite_sensor_reading_repository import (
    SQLiteSensorReadingRepository,
)
from plant_core.infrastructure.persistence.sqlite.repositories.sqlite_sensor_repository import SQLiteSensorRepository


def utc(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


def sample_node() -> Node:
    now = utc("2026-03-28T12:00:00+00:00")
    return Node(
        node_id="node-1",
        node_kind=NodeKind.MCU,
        display_name="MCU 1",
        serial_no="SN-001",
        status=NodeStatus.ONLINE,
        last_seen_at=now,
        created_at=now,
        updated_at=now,
    )


def sample_sensor() -> Sensor:
    return Sensor(
        sensor_id="sensor-1",
        node_id="node-1",
        sensor_type=SensorType.TEMPERATURE,
        channel="ch-1",
        unit="celsius",
        display_name="Temp 1",
        created_at=utc("2026-03-28T12:00:00+00:00"),
    )


def sample_reading(reading_id: str = "reading-1", value: float = 25.5) -> SensorReading:
    return SensorReading(
        reading_id=reading_id,
        sensor_id="sensor-1",
        node_id="node-1",
        sensor_type=SensorType.TEMPERATURE,
        value=value,
        unit="celsius",
        status=SensorStatus.OK,
        recorded_at=utc("2026-03-28T12:01:00+00:00"),
    )


def sample_command() -> CommandLog:
    return CommandLog(
        command_id="cmd-1",
        node_id="node-1",
        command_type=CommandType.ACTUATOR,
        device_type=DeviceType.PUMP.value,
        correlation_id="corr-1",
        requested_by="control-daemon",
        payload_json=json.dumps({"device": "pump", "action": "on"}),
        status=CommandStatus.ACCEPTED,
        message="queued",
        requested_at=utc("2026-03-28T12:02:00+00:00"),
        accepted_at=utc("2026-03-28T12:02:01+00:00"),
        finished_at=None,
    )


def sample_event() -> EventLog:
    return EventLog(
        event_id="evt-1",
        node_id="node-1",
        event_type=EventType.TELEMETRY,
        correlation_id="corr-1",
        command_id="cmd-1",
        payload_json=json.dumps({"temperature": 25.5}),
        recorded_at=utc("2026-03-28T12:03:00+00:00"),
    )


def test_mapper_round_trip():
    node = sample_node()
    sensor = sample_sensor()
    reading = sample_reading()
    latest = LatestSensorReading(
        sensor_id=reading.sensor_id,
        reading_id=reading.reading_id,
        node_id=reading.node_id,
        sensor_type=reading.sensor_type,
        value=reading.value,
        unit=reading.unit,
        status=reading.status,
        recorded_at=reading.recorded_at,
    )
    command = sample_command()
    event = sample_event()

    assert record_to_node(node_to_record(node)) == node
    assert record_to_sensor(sensor_to_record(sensor)) == sensor
    assert record_to_sensor_reading(sensor_reading_to_record(reading)) == reading
    assert record_to_latest_sensor_reading(latest_sensor_reading_to_record(latest)) == latest
    assert record_to_command_log(command_log_to_record(command)) == command
    assert record_to_event_log(event_log_to_record(event)) == event


def test_schema_init_is_idempotent(tmp_path: Path):
    async def scenario() -> None:
        db = SQLiteDatasource(tmp_path / "core.sqlite3")
        await db.connect()
        await db.init_schema()
        await db.init_schema()
        await db.close()

    asyncio.run(scenario())


def test_repository_bundle_factory(tmp_path: Path):
    async def scenario() -> None:
        db = SQLiteDatasource(tmp_path / "core.sqlite3")
        await db.connect()
        await db.init_schema()

        bundle = SQLiteRepositoryBundle.from_datasource(db)

        await bundle.nodes.upsert(sample_node())
        assert await bundle.nodes.get("node-1") is not None

        await db.close()

    asyncio.run(scenario())


def test_repository_crud_and_query_behaviour(tmp_path: Path):
    async def scenario() -> None:
        db = SQLiteDatasource(tmp_path / "core.sqlite3")
        await db.connect()
        await db.init_schema()

        nodes = SQLiteNodeRepository(db.raw_connection)
        devices = SQLiteDeviceStateRepository(db.raw_connection)
        sensors = SQLiteSensorRepository(db.raw_connection)
        readings = SQLiteSensorReadingRepository(db.raw_connection)
        commands = SQLiteCommandLogRepository(db.raw_connection)
        events = SQLiteEventLogRepository(db.raw_connection)

        await nodes.upsert(sample_node())
        assert await nodes.get("node-1") == sample_node()
        assert len(await nodes.list_all()) == 1

        await devices.upsert(
            DeviceState(
                node_id="node-1",
                device_type=DeviceType.PUMP,
                is_active=True,
                level=1.0,
                reason="manual",
                updated_at=utc("2026-03-28T12:00:10+00:00"),
            )
        )
        device = await devices.get("node-1", DeviceType.PUMP)
        assert device is not None
        assert device.is_active is True
        assert len(await devices.list_by_node("node-1")) == 1

        await sensors.upsert(sample_sensor())
        sensor = await sensors.get("sensor-1")
        assert sensor is not None
        assert sensor.sensor_type is SensorType.TEMPERATURE
        assert len(await sensors.list_by_node("node-1")) == 1

        await readings.append_batch(
            [
                sample_reading("reading-1", 25.5),
                SensorReading(
                    reading_id="reading-2",
                    sensor_id="sensor-1",
                    node_id="node-1",
                    sensor_type=SensorType.TEMPERATURE,
                    value=26.0,
                    unit="celsius",
                    status=SensorStatus.OK,
                    recorded_at=utc("2026-03-28T12:02:00+00:00"),
                ),
            ]
        )
        latest = await readings.get_latest("sensor-1")
        assert latest is not None
        assert latest.reading_id == "reading-2"
        assert len(await readings.list_latest_by_node("node-1")) == 1
        history = await readings.list_history("sensor-1", 10)
        assert [row.reading_id for row in history] == ["reading-2", "reading-1"]

        await commands.append(sample_command())
        await commands.update_status(
            "cmd-1",
            CommandStatus.SUCCEEDED,
            "done",
            utc("2026-03-28T12:02:01+00:00"),
            utc("2026-03-28T12:02:05+00:00"),
        )
        command = await commands.get("cmd-1")
        assert command is not None
        assert command.status is CommandStatus.SUCCEEDED
        assert len(await commands.list_by_node("node-1", 10)) == 1

        await events.append(sample_event())
        assert len(await events.list_by_node("node-1", 10)) == 1
        assert len(await events.list_by_command("cmd-1")) == 1

        await db.close()

    asyncio.run(scenario())


def test_foreign_key_cascade_for_node_delete(tmp_path: Path):
    async def scenario() -> None:
        db = SQLiteDatasource(tmp_path / "core.sqlite3")
        await db.connect()
        await db.init_schema()

        nodes = SQLiteNodeRepository(db.raw_connection)
        devices = SQLiteDeviceStateRepository(db.raw_connection)
        sensors = SQLiteSensorRepository(db.raw_connection)
        readings = SQLiteSensorReadingRepository(db.raw_connection)

        await nodes.upsert(sample_node())
        await devices.upsert(
            DeviceState(
                node_id="node-1",
                device_type=DeviceType.PUMP,
                is_active=False,
                level=0.0,
                reason=None,
                updated_at=utc("2026-03-28T12:00:10+00:00"),
            )
        )
        await sensors.upsert(sample_sensor())
        await readings.append(sample_reading())

        await db.raw_connection.execute("delete from nodes where node_id = ?", ("node-1",))

        assert await nodes.get("node-1") is None
        assert await devices.get("node-1", DeviceType.PUMP) is None
        assert await sensors.get("sensor-1") is None
        assert await readings.get_latest("sensor-1") is None

        await db.close()

    asyncio.run(scenario())


def test_event_log_command_fk_sets_null_on_command_delete(tmp_path: Path):
    async def scenario() -> None:
        db = SQLiteDatasource(tmp_path / "core.sqlite3")
        await db.connect()
        await db.init_schema()

        nodes = SQLiteNodeRepository(db.raw_connection)
        commands = SQLiteCommandLogRepository(db.raw_connection)
        events = SQLiteEventLogRepository(db.raw_connection)

        await nodes.upsert(sample_node())
        await commands.append(sample_command())
        await events.append(sample_event())

        await db.raw_connection.execute("delete from event_logs where event_id = ?", ("evt-1",))
        await db.raw_connection.execute("delete from command_logs where command_id = ?", ("cmd-1",))

        assert await commands.get("cmd-1") is None
        assert await events.list_by_command("cmd-1") == []

        await db.close()

    asyncio.run(scenario())
