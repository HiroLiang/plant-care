import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import grpc
from google.protobuf.timestamp_pb2 import Timestamp

from application.mcu_bus_command_client import MCUBusCommandClient
from domain.control import (
    ActuatorAction,
    CommandDispatchResult,
    CommandStatus,
    DeviceType,
    SensorType,
    ValueUnit,
)
from plant_core.generated.mcubus.v1 import commands_pb2, common_pb2

_DEVICE_TYPE_TO_PROTO = {
    DeviceType.PUMP: common_pb2.DEVICE_TYPE_PUMP,
    DeviceType.FAN: common_pb2.DEVICE_TYPE_FAN,
    DeviceType.LIGHT: common_pb2.DEVICE_TYPE_LIGHT,
}

_ACTUATOR_ACTION_TO_PROTO = {
    ActuatorAction.ON: common_pb2.ACTUATOR_OPERATION_TURN_ON,
    ActuatorAction.OFF: common_pb2.ACTUATOR_OPERATION_TURN_OFF,
    ActuatorAction.SET_LEVEL: common_pb2.ACTUATOR_OPERATION_SET_LEVEL,
}

_SENSOR_TYPE_TO_PROTO = {
    SensorType.TEMPERATURE: common_pb2.SENSOR_TYPE_TEMPERATURE,
    SensorType.HUMIDITY: common_pb2.SENSOR_TYPE_HUMIDITY,
    SensorType.SOIL_MOISTURE: common_pb2.SENSOR_TYPE_SOIL_MOISTURE,
    SensorType.LIGHT_LEVEL: common_pb2.SENSOR_TYPE_LIGHT_LEVEL,
    SensorType.WATER_LEVEL: common_pb2.SENSOR_TYPE_WATER_LEVEL,
    SensorType.PH: common_pb2.SENSOR_TYPE_PH,
}

_VALUE_UNIT_TO_PROTO = {
    ValueUnit.CELSIUS: common_pb2.VALUE_UNIT_CELSIUS,
    ValueUnit.PERCENT: common_pb2.VALUE_UNIT_PERCENT,
    ValueUnit.VOLT: common_pb2.VALUE_UNIT_VOLT,
    ValueUnit.RATIO: common_pb2.VALUE_UNIT_RATIO,
}

_PROTO_STATUS_TO_DOMAIN = {
    common_pb2.COMMAND_STATUS_ACCEPTED: CommandStatus.ACCEPTED,
    common_pb2.COMMAND_STATUS_SUCCEEDED: CommandStatus.SUCCEEDED,
    common_pb2.COMMAND_STATUS_REJECTED: CommandStatus.REJECTED,
    common_pb2.COMMAND_STATUS_INVALID_ARGUMENT: CommandStatus.INVALID_ARGUMENT,
    common_pb2.COMMAND_STATUS_UNSUPPORTED: CommandStatus.UNSUPPORTED,
    common_pb2.COMMAND_STATUS_FAILED: CommandStatus.FAILED,
    common_pb2.COMMAND_STATUS_UNSPECIFIED: CommandStatus.UNSPECIFIED,
}


class InvalidControlRequest(ValueError):
    pass


class UpstreamUnavailableError(RuntimeError):
    pass


class UpstreamRequestError(RuntimeError):
    pass


class ControlService:
    def __init__(self, command_client: MCUBusCommandClient):
        self._command_client = command_client

    async def set_actuator_state(
        self,
        *,
        node_id: int,
        device_type: DeviceType,
        action: ActuatorAction,
        level: float | None = None,
    ) -> CommandDispatchResult:
        command = self._build_base_command(
            node_id=node_id,
            command_type=common_pb2.COMMAND_TYPE_ACTUATOR,
        )
        command.actuator_command.CopyFrom(
            commands_pb2.ActuatorCommand(
                device_type=_DEVICE_TYPE_TO_PROTO[device_type],
                operation=_ACTUATOR_ACTION_TO_PROTO[action],
                level=level or 0.0,
            )
        )
        return await self._dispatch(command)

    async def request_telemetry(
        self,
        *,
        node_id: int,
        sensor_types: list[SensorType] | None = None,
    ) -> CommandDispatchResult:
        command = self._build_base_command(
            node_id=node_id,
            command_type=common_pb2.COMMAND_TYPE_REQUEST_TELEMETRY,
        )
        command.request_telemetry_command.CopyFrom(
            commands_pb2.RequestTelemetryCommand(
                sensor_types=[_SENSOR_TYPE_TO_PROTO[sensor_type] for sensor_type in (sensor_types or [])]
            )
        )
        return await self._dispatch(command)

    async def reset_node(
        self,
        *,
        node_id: int,
        reason: str | None = None,
    ) -> CommandDispatchResult:
        command = self._build_base_command(
            node_id=node_id,
            command_type=common_pb2.COMMAND_TYPE_RESET,
        )
        command.reset_command.CopyFrom(commands_pb2.ResetCommand(reason=reason or ""))
        return await self._dispatch(command)

    async def set_threshold(
        self,
        *,
        node_id: int,
        sensor_type: SensorType,
        value: float,
        unit: ValueUnit,
        channel: str | None = None,
    ) -> CommandDispatchResult:
        command = self._build_base_command(
            node_id=node_id,
            command_type=common_pb2.COMMAND_TYPE_SET_THRESHOLD,
        )
        command.set_threshold_command.CopyFrom(
            commands_pb2.SetThresholdCommand(
                sensor_type=_SENSOR_TYPE_TO_PROTO[sensor_type],
                value=value,
                unit=_VALUE_UNIT_TO_PROTO[unit],
                channel=channel or "",
            )
        )
        return await self._dispatch(command)

    def close(self) -> None:
        self._command_client.close()

    async def _dispatch(self, command: commands_pb2.McuCommand) -> CommandDispatchResult:
        try:
            reply = await asyncio.to_thread(self._command_client.dispatch_command, command)
        except grpc.RpcError as exc:
            if exc.code() == grpc.StatusCode.UNAVAILABLE:
                raise UpstreamUnavailableError("MCU bus daemon is unavailable") from exc
            raise UpstreamRequestError(f"MCU bus dispatch failed: {exc.code().name}") from exc

        accepted_at = reply.accepted_at.ToDatetime(tzinfo=UTC) if reply.HasField("accepted_at") else None
        return CommandDispatchResult(
            command_id=reply.command_id,
            accepted=reply.accepted,
            status=_PROTO_STATUS_TO_DOMAIN.get(reply.status, CommandStatus.UNSPECIFIED),
            message=reply.message,
            accepted_at=accepted_at,
            target_node_id=command.target.node_id,
        )

    def _build_base_command(self, *, node_id: int, command_type: int) -> commands_pb2.McuCommand:
        requested_at = datetime.now(UTC)
        timestamp = Timestamp()
        timestamp.FromDatetime(requested_at)
        return commands_pb2.McuCommand(
            command_id=str(uuid4()),
            target=common_pb2.McuNodeRef(node_id=node_id),
            issued_by="control-daemon",
            requested_at=timestamp,
            type=command_type,
        )
