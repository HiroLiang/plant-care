import asyncio
from datetime import UTC, datetime

import grpc
import pytest

from application.control_service import ControlService, UpstreamRequestError, UpstreamUnavailableError
from domain.control import ActuatorAction, DeviceType, SensorType, ValueUnit
from plant_core.generated.mcubus.v1 import commands_pb2, common_pb2


class RecordingClient:
    def __init__(self, reply=None, error=None):
        self.reply = reply
        self.error = error
        self.seen_command = None

    def dispatch_command(self, command):
        self.seen_command = command
        if self.error is not None:
            raise self.error
        return self.reply

    def close(self):
        return None


class FakeRpcError(grpc.RpcError):
    def __init__(self, status_code):
        super().__init__()
        self._status_code = status_code

    def code(self):
        return self._status_code


def make_reply(
    *,
    command_id: str = "cmd-1",
    accepted: bool = True,
    status: int = common_pb2.COMMAND_STATUS_ACCEPTED,
    message: str = "Accepted",
) -> commands_pb2.DispatchCommandReply:
    reply = commands_pb2.DispatchCommandReply(
        command_id=command_id,
        accepted=accepted,
        status=status,
        message=message,
    )
    reply.accepted_at.FromDatetime(datetime(2026, 3, 30, tzinfo=UTC))
    return reply


def test_set_actuator_state_builds_turn_on_command():
    client = RecordingClient(reply=make_reply())
    service = ControlService(client)

    result = asyncio.run(
        service.set_actuator_state(
            node_id=9,
            device_type=DeviceType.PUMP,
            action=ActuatorAction.ON,
        )
    )

    assert result.command_id == "cmd-1"
    assert result.target_node_id == 9
    assert client.seen_command.type == common_pb2.COMMAND_TYPE_ACTUATOR
    assert client.seen_command.target.node_id == 9
    assert client.seen_command.issued_by == "control-daemon"
    assert client.seen_command.actuator_command.device_type == common_pb2.DEVICE_TYPE_PUMP
    assert client.seen_command.actuator_command.operation == common_pb2.ACTUATOR_OPERATION_TURN_ON


def test_set_actuator_state_builds_set_level_command():
    client = RecordingClient(reply=make_reply())
    service = ControlService(client)

    asyncio.run(
        service.set_actuator_state(
            node_id=3,
            device_type=DeviceType.LIGHT,
            action=ActuatorAction.SET_LEVEL,
            level=0.75,
        )
    )

    assert client.seen_command.actuator_command.operation == common_pb2.ACTUATOR_OPERATION_SET_LEVEL
    assert client.seen_command.actuator_command.level == pytest.approx(0.75)


def test_request_telemetry_maps_sensor_types():
    client = RecordingClient(reply=make_reply())
    service = ControlService(client)

    asyncio.run(
        service.request_telemetry(
            node_id=5,
            sensor_types=[SensorType.TEMPERATURE, SensorType.HUMIDITY],
        )
    )

    assert client.seen_command.type == common_pb2.COMMAND_TYPE_REQUEST_TELEMETRY
    assert list(client.seen_command.request_telemetry_command.sensor_types) == [
        common_pb2.SENSOR_TYPE_TEMPERATURE,
        common_pb2.SENSOR_TYPE_HUMIDITY,
    ]


def test_set_threshold_maps_payload():
    client = RecordingClient(reply=make_reply())
    service = ControlService(client)

    asyncio.run(
        service.set_threshold(
            node_id=4,
            sensor_type=SensorType.SOIL_MOISTURE,
            value=48.5,
            unit=ValueUnit.PERCENT,
            channel="zone-a",
        )
    )

    assert client.seen_command.type == common_pb2.COMMAND_TYPE_SET_THRESHOLD
    assert client.seen_command.set_threshold_command.sensor_type == common_pb2.SENSOR_TYPE_SOIL_MOISTURE
    assert client.seen_command.set_threshold_command.value == pytest.approx(48.5)
    assert client.seen_command.set_threshold_command.unit == common_pb2.VALUE_UNIT_PERCENT
    assert client.seen_command.set_threshold_command.channel == "zone-a"


def test_dispatch_raises_unavailable_for_unavailable_grpc():
    service = ControlService(RecordingClient(error=FakeRpcError(grpc.StatusCode.UNAVAILABLE)))

    with pytest.raises(UpstreamUnavailableError):
        asyncio.run(service.reset_node(node_id=1, reason="reboot"))


def test_dispatch_raises_bad_gateway_for_other_grpc_errors():
    service = ControlService(RecordingClient(error=FakeRpcError(grpc.StatusCode.UNKNOWN)))

    with pytest.raises(UpstreamRequestError):
        asyncio.run(service.reset_node(node_id=1, reason="reboot"))
