from fastapi import Request

from application.monitor_service import MonitorService
from bootstrap.bootstrap import AppContext


def get_monitor_service(request: Request) -> MonitorService:
    ctx: AppContext = request.app.state.ctx
    return ctx.services.monitor_service
