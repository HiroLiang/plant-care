import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from pathlib import Path
from tempfile import TemporaryDirectory

from application.monitor_service import MonitorService
from bootstrap.bootstrap import wire_mcu_bus_subscription
from domain.mcu_bus_event import AlertEvent, DeviceStateEvent, MCUBusEvent, TelemetryEvent, TelemetryReading
from infrastructure.module.local_module import LocalSensorModule
from infrastructure.sensor.mock import (
    MockTemperatureSensor,
    MockHumiditySensor,
)
from plant_core.infrastructure.persistence.sqlite.bundle import SQLiteRepositoryBundle
from plant_core.infrastructure.persistence.sqlite.datasource import SQLiteDatasource


class FakeMCUBusClient:
    def __init__(self):
        self.connected = False
        self.subscription = None

    def is_connected(self) -> bool:
        return self.connected

    def connect(self) -> None:
        self.connected = True

    def disconnect(self) -> None:
        self.connected = False

    def subscribe_events(self, on_event, on_error=None) -> None:
        self.subscription = (on_event, on_error)

    def subscribe_events_async(self, on_event, on_error=None) -> None:
        self.subscription = (on_event, on_error)


def test_monitor_service_persists_local_poll_results():
    async def scenario() -> None:
        temp_sensor = MockTemperatureSensor(base=26.5)
        humidity_sensor = MockHumiditySensor(base=55.2)

        module = LocalSensorModule(module_id="test_module")
        module.add_sensor(temp_sensor)
        module.add_sensor(humidity_sensor)

        with TemporaryDirectory() as tmp:
            db = SQLiteDatasource(Path(tmp) / "monitor.sqlite3")
            await db.connect()
            await db.init_schema()
            repos = SQLiteRepositoryBundle.from_datasource(db)
            service = MonitorService(modules=[module], repositories=repos)

            await service.refresh_local_modules()
            snapshot = await service.get_all_status()

            assert "local:test_module:mock_temperature_sensor" in snapshot["readings"]
            assert "local:test_module:mock_humidity_sensor" in snapshot["readings"]
            await db.close()

    asyncio.run(scenario())


def test_monitor_service_ingests_mcu_sensor_event():
    async def scenario() -> None:
        with TemporaryDirectory() as tmp:
            db = SQLiteDatasource(Path(tmp) / "monitor.sqlite3")
            await db.connect()
            await db.init_schema()
            repos = SQLiteRepositoryBundle.from_datasource(db)
            service = MonitorService(modules=[], repositories=repos)

            await service.ingest_mcu_event(MCUBusEvent(
                event_id="evt-1",
                source_node_id=1,
                emitted_at=datetime(2026, 3, 18, tzinfo=timezone.utc),
                payload=TelemetryEvent(
                    readings=[
                        TelemetryReading(sensor_type="temperature", value=25.5, unit="celsius"),
                        TelemetryReading(sensor_type="humidity", value=60.0, unit="percent"),
                    ]
                ),
            ))

            snapshot = await service.get_all_status()

            assert snapshot["readings"]["mcu:1:temperature"]["value"] == 25.5
            assert snapshot["readings"]["mcu:1:humidity"]["value"] == 60.0
            await db.close()

    asyncio.run(scenario())


def test_monitor_service_persists_device_state_and_event_log():
    async def scenario() -> None:
        with TemporaryDirectory() as tmp:
            db = SQLiteDatasource(Path(tmp) / "monitor.sqlite3")
            await db.connect()
            await db.init_schema()
            repos = SQLiteRepositoryBundle.from_datasource(db)
            service = MonitorService(modules=[], repositories=repos)

            await service.ingest_mcu_event(MCUBusEvent(
                event_id="evt-2",
                source_node_id=7,
                emitted_at=datetime(2026, 3, 18, tzinfo=timezone.utc),
                payload=DeviceStateEvent(
                    device_type="pump",
                    is_active=True,
                    level=0.7,
                    reason="auto",
                ),
            ))

            device_states = await service.get_device_states(node_id="mcu:7")
            events = await service.get_event_history(node_id="mcu:7")

            assert device_states[0]["device_type"] == "pump"
            assert device_states[0]["is_active"] is True
            assert events[0]["event_type"] == "device_state"
            assert events[0]["payload"]["reason"] == "auto"
            await db.close()

    asyncio.run(scenario())


def test_wire_mcu_bus_subscription_starts_client_and_routes_events():
    async def scenario() -> None:
        with TemporaryDirectory() as tmp:
            db = SQLiteDatasource(Path(tmp) / "monitor.sqlite3")
            await db.connect()
            await db.init_schema()
            repos = SQLiteRepositoryBundle.from_datasource(db)
            service = MonitorService(modules=[], repositories=repos)
            fake_client = FakeMCUBusClient()
            ctx = SimpleNamespace(
                db=db,
                repositories=repos,
                clients=SimpleNamespace(mcu_bus_client=fake_client),
                services=SimpleNamespace(monitor_service=service),
            )

            wire_mcu_bus_subscription(ctx, asyncio.get_running_loop())

            assert fake_client.connected is True
            assert fake_client.subscription is not None

            on_event, _ = fake_client.subscription
            on_event(MCUBusEvent(
                event_id="evt-1",
                source_node_id=1,
                emitted_at=datetime(2026, 3, 18, tzinfo=timezone.utc),
                payload=TelemetryEvent(
                    readings=[
                        TelemetryReading(sensor_type="temperature", value=25.5, unit="celsius"),
                        TelemetryReading(sensor_type="humidity", value=60.0, unit="percent"),
                    ]
                ),
            ))
            await asyncio.sleep(0.05)

            snapshot = await service.get_all_status()
            assert snapshot["readings"]["mcu:1:temperature"]["value"] == 25.5
            await db.close()

    asyncio.run(scenario())
