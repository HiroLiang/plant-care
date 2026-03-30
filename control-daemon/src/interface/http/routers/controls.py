from fastapi import APIRouter, Depends

from application.control_service import ControlService
from interface.http.dependencies import get_control_service
from interface.http.schemas import (
    ActuatorControlRequest,
    CommandDispatchResponse,
    CommandTargetResponse,
    ResetNodeRequest,
    SetThresholdRequest,
    TelemetryRequestCommandRequest,
)

router = APIRouter(prefix="/controls", tags=["controls"])


@router.post("/actuators", response_model=CommandDispatchResponse)
async def set_actuator_state(
    request: ActuatorControlRequest,
    service: ControlService = Depends(get_control_service),
) -> CommandDispatchResponse:
    result = await service.set_actuator_state(
        node_id=request.node_id,
        device_type=request.device_type,
        action=request.action,
        level=request.level,
    )
    return _to_response(result)


@router.post("/telemetry-requests", response_model=CommandDispatchResponse)
async def request_telemetry(
    request: TelemetryRequestCommandRequest,
    service: ControlService = Depends(get_control_service),
) -> CommandDispatchResponse:
    result = await service.request_telemetry(
        node_id=request.node_id,
        sensor_types=request.sensor_types,
    )
    return _to_response(result)


@router.post("/resets", response_model=CommandDispatchResponse)
async def reset_node(
    request: ResetNodeRequest,
    service: ControlService = Depends(get_control_service),
) -> CommandDispatchResponse:
    result = await service.reset_node(node_id=request.node_id, reason=request.reason)
    return _to_response(result)


@router.post("/thresholds", response_model=CommandDispatchResponse)
async def set_threshold(
    request: SetThresholdRequest,
    service: ControlService = Depends(get_control_service),
) -> CommandDispatchResponse:
    result = await service.set_threshold(
        node_id=request.node_id,
        sensor_type=request.sensor_type,
        value=request.value,
        unit=request.unit,
        channel=request.channel,
    )
    return _to_response(result)


def _to_response(result) -> CommandDispatchResponse:
    return CommandDispatchResponse(
        command_id=result.command_id,
        accepted=result.accepted,
        status=result.status,
        message=result.message,
        accepted_at=result.accepted_at,
        target=CommandTargetResponse(node_id=result.target_node_id),
    )
