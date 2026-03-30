from fastapi import Request

from application.control_service import ControlService
from bootstrap.context import AppContext


def get_control_service(request: Request) -> ControlService:
    ctx: AppContext = request.app.state.ctx
    assert ctx.services is not None
    return ctx.services.control_service
