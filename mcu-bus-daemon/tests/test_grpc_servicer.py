from datetime import datetime, timezone

import grpc
import pytest

from domain.mcu_bus import BusEvent, SensorDataEvent
from mcubus.v1 import messages_pb2
from infrastructure.servicer.mcu_bus_servicer import MCUBusServer
from fake.fake_bus_handler import FakeSubscriptionHandler


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


class AbortCalled(Exception):
    def __init__(self, code, details):
        super().__init__(details)
        self.code = code
        self.details = details


class FakeUnaryContext:
    def abort(self, code, details):
        raise AbortCalled(code, details)


def test_subscribe_events_yields_proto_event():
    event = BusEvent(
        event_id="1-123",
        module_id="1",
        timestamp=datetime.now(timezone.utc),
        payload=SensorDataEvent(
            temperature=25.34,
            humidity=60.27,
        ),
    )
    handler = PreloadedSubscriptionHandler(event)
    server = MCUBusServer(handler)
    ctx = FakeContext()

    proto_event = next(server.SubscribeEvents(messages_pb2.SubscribeRequest(), ctx))

    assert proto_event.module_id == "1"
    assert proto_event.sensor_data.temperature == pytest.approx(25.34)
    assert proto_event.sensor_data.humidity == pytest.approx(60.27)


def test_subscribe_events_normal_close_does_not_raise():
    event = BusEvent(
        event_id="1-123",
        module_id="1",
        timestamp=datetime.now(timezone.utc),
        payload=SensorDataEvent(
            temperature=25.34,
            humidity=60.27,
        ),
    )
    handler = PreloadedSubscriptionHandler(event)
    server = MCUBusServer(handler)
    ctx = FakeContext()

    stream = server.SubscribeEvents(messages_pb2.SubscribeRequest(), ctx)
    next(stream)

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize(
    ("method_name", "rpc_request"),
    [
        ("Register", messages_pb2.RegisterRequest()),
        ("UnRegister", messages_pb2.UnSubscribeRequest(module_id="1")),
    ],
)
def test_unary_methods_return_unimplemented(method_name, rpc_request):
    handler = FakeSubscriptionHandler()
    server = MCUBusServer(handler)
    ctx = FakeUnaryContext()

    with pytest.raises(AbortCalled) as exc_info:
        getattr(server, method_name)(rpc_request, ctx)

    assert exc_info.value.code == grpc.StatusCode.UNIMPLEMENTED
    assert "bring-up mode" in exc_info.value.details
