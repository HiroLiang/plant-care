import asyncio
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.monitor_service import MonitorService
from domain.mcu_bus_event import CommandResultEvent, DeviceStateEvent, MCUBusEvent, TelemetryEvent, TelemetryReading
from infrastructure.module.local_module import LocalSensorModule
from infrastructure.sensor.mock import MockTemperatureSensor
from interface.http.api import register_routers
from plant_core.infrastructure.persistence.sqlite.bundle import SQLiteRepositoryBundle
from plant_core.infrastructure.persistence.sqlite.datasource import SQLiteDatasource


def test_http_routes_return_repository_backed_data():
    async def prepare():
        db = SQLiteDatasource(Path(tmpdir) / "monitor.sqlite3")
        await db.connect()
        await db.init_schema()
        repos = SQLiteRepositoryBundle.from_datasource(db)

        module = LocalSensorModule(module_id="local-module")
        module.add_sensor(MockTemperatureSensor(base=24.5))
        service = MonitorService([module], repos)
        await service.refresh_local_modules()
        await service.ingest_mcu_event(MCUBusEvent(
            event_id="evt-telemetry",
            source_node_id=2,
            emitted_at=datetime(2026, 3, 18, tzinfo=timezone.utc),
            payload=TelemetryEvent(
                readings=[TelemetryReading(sensor_type="temperature", value=22.5, unit="celsius")]
            ),
        ))
        await service.ingest_mcu_event(MCUBusEvent(
            event_id="evt-state",
            source_node_id=2,
            emitted_at=datetime(2026, 3, 18, 0, 0, 1, tzinfo=timezone.utc),
            payload=DeviceStateEvent(device_type="pump", is_active=True, level=0.8, reason="manual"),
        ))
        await service.ingest_mcu_event(MCUBusEvent(
            event_id="evt-command",
            source_node_id=2,
            emitted_at=datetime(2026, 3, 18, 0, 0, 2, tzinfo=timezone.utc),
            command_id="cmd-1",
            payload=CommandResultEvent(
                command_id="cmd-1",
                status="failed",
                message="timeout",
                device_type="pump",
            ),
        ))
        return db, repos, service

    with TemporaryDirectory() as tmpdir:
        db, repos, service = asyncio.run(prepare())
        app = FastAPI()
        register_routers(app)
        app.state.ctx = SimpleNamespace(
            db=db,
            repositories=repos,
            clients=None,
            services=SimpleNamespace(monitor_service=service),
        )

        try:
            client = TestClient(app)

            all_status = client.get("/monitors/all-status")
            assert all_status.status_code == 200
            status_payload = all_status.json()
            assert "local:local-module:mock_temperature_sensor" in status_payload["readings"]
            assert "mcu:2:temperature" in status_payload["readings"]

            states = client.get("/monitors/device-states")
            assert states.status_code == 200
            assert states.json()["device_states"][0]["device_type"] == "pump"

            events = client.get("/monitors/events", params={"command_id": "cmd-1"})
            assert events.status_code == 200
            assert events.json()["events"][0]["command_id"] == "cmd-1"
            assert events.json()["events"][0]["payload"]["status"] == "failed"
        finally:
            asyncio.run(db.close())
