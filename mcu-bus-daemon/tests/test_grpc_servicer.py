from datetime import datetime, timezone

import pytest

from domain.mcu_bus import AlertEvent, BusEvent, TelemetryEvent, TelemetryReading
from infrastructure.servicer.mcu_bus_servicer import MCUBusCommandServer, MCUBusEventServer
from fake.fake_bus_handler import FakeSubscriptionHandler
from plant_core.generated.mcubus.v1 import commands_pb2, common_pb2, events_pb2


class PreloadedSubscriptionHandler(FakeSubscriptionHandler):
    def __init__(self, event: BusEvent):
        super().__init__()
        self._event = event

    def _on_subscriber_added(self, subscriber):
        super()._on_subscriber_added(subscriber)
        subscriber.queue.put_nowait(self._event)


class FakeContext:
    def __init__(self):
        self._callbacks = []
        self._is_active_calls = 0

    def add_callback(self, callback):
        self._callbacks.append(callback)
        return True

    def is_active(self):
        self._is_active_calls += 1
        return self._is_active_calls == 1


def test_subscribe_bus_events_yields_proto_event():
    event = BusEvent(
        event_id="1-123",
        source_node_id=1,
        emitted_at=datetime.now(timezone.utc),
        payload=TelemetryEvent(
            readings=[
                TelemetryReading(sensor_type="temperature", value=25.34, unit="celsius"),
                TelemetryReading(sensor_type="humidity", value=60.27, unit="percent"),
            ]
        ),
    )
    handler = PreloadedSubscriptionHandler(event)
    server = MCUBusEventServer(handler)
    ctx = FakeContext()

    proto_event = next(server.SubscribeBusEvents(events_pb2.SubscribeBusEventsRequest(), ctx))

    assert proto_event.source_node_id == 1
    assert proto_event.telemetry.readings[0].value == pytest.approx(25.34)
    assert proto_event.telemetry.readings[1].value == pytest.approx(60.27)


def test_subscribe_bus_events_applies_filters():
    event = BusEvent(
        event_id="1-123",
        source_node_id=1,
        emitted_at=datetime.now(timezone.utc),
        payload=TelemetryEvent(
            readings=[TelemetryReading(sensor_type="temperature", value=25.34, unit="celsius")]
        ),
    )
    handler = PreloadedSubscriptionHandler(event)
    server = MCUBusEventServer(handler)
    ctx = FakeContext()

    stream = server.SubscribeBusEvents(
        events_pb2.SubscribeBusEventsRequest(node_ids=[2]),
        ctx,
    )

    with pytest.raises(StopIteration):
        next(stream)


def test_subscribe_bus_events_excludes_system_events_by_default():
    event = BusEvent(
        event_id="1-124",
        source_node_id=1,
        emitted_at=datetime.now(timezone.utc),
        payload=AlertEvent(
            severity="error",
            code="heartbeat_status_79",
            message="boom",
        ),
    )
    handler = PreloadedSubscriptionHandler(event)
    server = MCUBusEventServer(handler)
    ctx = FakeContext()

    stream = server.SubscribeBusEvents(events_pb2.SubscribeBusEventsRequest(), ctx)

    with pytest.raises(StopIteration):
        next(stream)


def test_subscribe_bus_events_includes_system_events_when_requested():
    event = BusEvent(
        event_id="1-125",
        source_node_id=1,
        emitted_at=datetime.now(timezone.utc),
        payload=AlertEvent(
            severity="warning",
            code="node_hot",
            message="hot",
        ),
    )
    handler = PreloadedSubscriptionHandler(event)
    server = MCUBusEventServer(handler)
    ctx = FakeContext()

    proto_event = next(
        server.SubscribeBusEvents(
            events_pb2.SubscribeBusEventsRequest(include_system_events=True),
            ctx,
        )
    )

    assert proto_event.event_type == common_pb2.EVENT_TYPE_ALERT
    assert proto_event.alert.code == "node_hot"


def test_dispatch_command_returns_structured_reply():
    server = MCUBusCommandServer()
    request = commands_pb2.DispatchCommandRequest(
        command=commands_pb2.McuCommand(
            command_id="cmd-1",
            issued_by="control-daemon",
            type=common_pb2.COMMAND_TYPE_RESET,
        )
    )

    reply = server.DispatchCommand(request, None)

    assert reply.command_id == "cmd-1"
    assert reply.accepted is False
    assert reply.status == common_pb2.COMMAND_STATUS_UNSUPPORTED
