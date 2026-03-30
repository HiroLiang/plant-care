from fastapi import APIRouter, Depends, Query

from application.monitor_service import MonitorService
from interface.http.dependencies import get_monitor_service

router = APIRouter(
    prefix="/monitors",
    tags=["monitors"],
)


@router.get("/all-status")
async def get_all_status(
    node_id: str | None = None,
    service: MonitorService = Depends(get_monitor_service),
):
    return await service.get_all_status(node_id=node_id)


@router.get("/device-states")
async def get_device_states(
    node_id: str | None = None,
    service: MonitorService = Depends(get_monitor_service),
):
    return {"device_states": await service.get_device_states(node_id=node_id)}


@router.get("/events")
async def get_events(
    node_id: str | None = None,
    command_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    service: MonitorService = Depends(get_monitor_service),
):
    return {"events": await service.get_event_history(node_id=node_id, command_id=command_id, limit=limit)}
