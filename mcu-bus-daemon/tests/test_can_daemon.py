from datetime import datetime

from domain.mcu_bus import AlertEvent, SensorDataEvent
from domain.subscription import Subscriber
from infrastructure.bus.can_daemon import CanBusDaemon
from fake.fake_bus_handler import FakeSubscriptionHandler


def test_handle_temp_hum_publishes_sensor_event():
    handler = FakeSubscriptionHandler()
    subscriber = Subscriber()
    handler.handle_subscriber(subscriber)
    daemon = CanBusDaemon(handler)

    daemon._handle_temp_hum(1, bytes([0xE6, 0x09, 0x8B, 0x17, 0x00]))

    event = subscriber.queue.get(timeout=1.0)
    assert isinstance(event.payload, SensorDataEvent)
    assert event.module_id == "1"
    assert event.payload.temperature == 25.34
    assert event.payload.humidity == 60.27


def test_handle_heartbeat_updates_last_seen_without_publishing_ok_status():
    handler = FakeSubscriptionHandler()
    daemon = CanBusDaemon(handler)

    daemon._handle_heartbeat(1, bytes([0x01, 0x00, 0xE4, 0x0C, 0x7B, 0x00, 0x00, 0x00]))

    assert 1 in daemon.node_last_seen


def test_handle_heartbeat_error_publishes_alert():
    handler = FakeSubscriptionHandler()

    subscriber = Subscriber()
    handler.handle_subscriber(subscriber)
    daemon = CanBusDaemon(handler)

    daemon._handle_heartbeat(1, bytes([0x01, 0x4F, 0xE4, 0x0C, 0x7B, 0x00, 0x00, 0x00]))

    event = subscriber.queue.get(timeout=1.0)
    assert isinstance(event.payload, AlertEvent)
    assert event.payload.code == "heartbeat_status_79"


def test_take_unknown_monitor_iteration_does_not_crash(monkeypatch):
    handler = FakeSubscriptionHandler()
    daemon = CanBusDaemon(handler)
    daemon._node_last_seen[1] = datetime.now()
    daemon._stop_event.set()
    monkeypatch.setattr("infrastructure.bus.can_daemon.time.sleep", lambda _: None)

    daemon._monitor_loop()

    assert 1 in daemon.node_last_seen
