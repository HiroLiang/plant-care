from datetime import datetime, timezone

from google.protobuf.timestamp_pb2 import Timestamp
from plant_core.generated.mcubus.v1 import common_pb2, events_pb2

from infrastructure.mcu.grpc_mcu_bus_client import GrpcMCUBusClient


class FakeEventStub:
    def __init__(self, events):
        self._events = events
        self.last_request = None

    def SubscribeBusEvents(self, request):
        self.last_request = request
        return iter(self._events)


def test_subscribe_events_requests_system_events_and_maps_alert():
    ts = Timestamp()
    ts.FromDatetime(datetime(2026, 3, 18, tzinfo=timezone.utc))
    proto_event = events_pb2.BusEvent(
        event_id="evt-alert",
        source_node_id=2,
        emitted_at=ts,
        event_type=common_pb2.EVENT_TYPE_ALERT,
        alert=events_pb2.AlertEvent(
            severity=common_pb2.ALERT_SEVERITY_WARNING,
            code="node_hot",
            message="temperature rising",
        ),
    )
    stub = FakeEventStub([proto_event])
    client = GrpcMCUBusClient("localhost", "50051")
    client._connected = True
    client._stub = stub
    seen_events = []

    client.subscribe_events(on_event=seen_events.append)

    assert stub.last_request.include_system_events is True
    assert len(seen_events) == 1
    assert seen_events[0].payload.code == "node_hot"
    assert seen_events[0].payload.severity == "warning"
