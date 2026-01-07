from fastapi import APIRouter, Depends

from application.monitor_service import MonitorService
from interface.http.dependencies import get_monitor_service

router = APIRouter(
    prefix="/monitors",
    tags=["monitors"],
)


@router.get("/all-status")
async def get_all_status(
        service: MonitorService = Depends(get_monitor_service),
):
    service.poll()
    return service.snapshot()
