from datetime import datetime, timezone
import asyncio

from application.monitor_service import MonitorService
from bootstrap.bootstrap import AppContext, wire_mcu_bus_subscription
from bootstrap.clients import Clients
from bootstrap.services import Services
from domain.mcu_bus_event import AlertEvent, MCUBusEvent, SensorDataEvent
from infrastructure.module.local_module import LocalSensorModule
from infrastructure.sensor.mock import (
    MockTemperatureSensor,
    MockHumiditySensor,
)
from interface.http.routers.monitors import get_all_status


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


def test_monitor_service_poll_and_snapshot():
    # Arrange
    temp_sensor = MockTemperatureSensor(base=26.5)
    humidity_sensor = MockHumiditySensor(base=55.2)

    module = LocalSensorModule(module_id="test_module")
    module.add_sensor(temp_sensor)
    module.add_sensor(humidity_sensor)

    service = MonitorService(modules=[module])

    # Act
    service.poll()
    snapshot = service.snapshot()

    # Assert
    assert len(snapshot) > 0


def test_monitor_service_ingests_mcu_sensor_event():
    service = MonitorService(modules=[])

    service.ingest_mcu_event(MCUBusEvent(
        event_id="evt-1",
        module_id="1",
        timestamp=datetime(2026, 3, 18, tzinfo=timezone.utc),
        payload=SensorDataEvent(
            temperature=25.5,
            humidity=60.0,
            soil_moisture=0.0,
            light_level=0.0,
            water_level=0.0,
            ph_value=0.0,
        ),
    ))

    snapshot = service.snapshot()

    assert snapshot["readings"]["mcu:1:temperature"]["value"] == 25.5
    assert snapshot["readings"]["mcu:1:humidity"]["value"] == 60.0


def test_monitor_service_ignores_alert_event_for_snapshot():
    service = MonitorService(modules=[])

    service.ingest_mcu_event(MCUBusEvent(
        event_id="evt-1",
        module_id="1",
        timestamp=datetime(2026, 3, 18, tzinfo=timezone.utc),
        payload=AlertEvent(
            severity="error",
            code="heartbeat_status_79",
            message="boom",
        ),
    ))

    assert service.snapshot()["readings"] == {}


def test_all_status_contains_local_and_mcu_readings():
    temp_sensor = MockTemperatureSensor(base=26.5)
    humidity_sensor = MockHumiditySensor(base=55.2)
    module = LocalSensorModule(module_id="test_module")
    module.add_sensor(temp_sensor)
    module.add_sensor(humidity_sensor)
    service = MonitorService(modules=[module])
    service.ingest_mcu_event(MCUBusEvent(
        event_id="evt-1",
        module_id="1",
        timestamp=datetime(2026, 3, 18, tzinfo=timezone.utc),
        payload=SensorDataEvent(
            temperature=25.5,
            humidity=60.0,
            soil_moisture=0.0,
            light_level=0.0,
            water_level=0.0,
            ph_value=0.0,
        ),
    ))

    snapshot = asyncio.run(get_all_status(service))

    assert "mock_temperature_sensor" in snapshot["readings"]
    assert "mcu:1:temperature" in snapshot["readings"]
    assert "mcu:1:humidity" in snapshot["readings"]


def test_wire_mcu_bus_subscription_starts_client_and_routes_events():
    service = MonitorService(modules=[])
    fake_client = FakeMCUBusClient()
    ctx = AppContext(
        db=None,
        clients=Clients(ctrl_client=None, rs485_client=None, mcu_bus_client=fake_client),
        services=Services(monitor_service=service),
    )

    wire_mcu_bus_subscription(ctx)

    assert fake_client.connected is True
    assert fake_client.subscription is not None

    on_event, _ = fake_client.subscription
    on_event(MCUBusEvent(
        event_id="evt-1",
        module_id="1",
        timestamp=datetime(2026, 3, 18, tzinfo=timezone.utc),
        payload=SensorDataEvent(
            temperature=25.5,
            humidity=60.0,
            soil_moisture=0.0,
            light_level=0.0,
            water_level=0.0,
            ph_value=0.0,
        ),
    ))

    assert service.snapshot()["readings"]["mcu:1:temperature"]["value"] == 25.5
