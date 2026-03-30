from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from create_app import create_app
from domain.control import CommandDispatchResult, CommandStatus


@pytest.fixture
def service_stub():
    stub = type("ControlServiceStub", (), {})()
    stub.set_actuator_state = AsyncMock(return_value=CommandDispatchResult(
        command_id="cmd-123",
        accepted=False,
        status=CommandStatus.UNSUPPORTED,
        message="Not wired yet",
        accepted_at=None,
        target_node_id=7,
    ))
    stub.request_telemetry = AsyncMock(return_value=CommandDispatchResult(
        command_id="cmd-telemetry",
        accepted=True,
        status=CommandStatus.ACCEPTED,
        message="Accepted",
        accepted_at=None,
        target_node_id=7,
    ))
    stub.reset_node = AsyncMock(return_value=CommandDispatchResult(
        command_id="cmd-reset",
        accepted=True,
        status=CommandStatus.ACCEPTED,
        message="Accepted",
        accepted_at=None,
        target_node_id=7,
    ))
    stub.set_threshold = AsyncMock(return_value=CommandDispatchResult(
        command_id="cmd-threshold",
        accepted=True,
        status=CommandStatus.ACCEPTED,
        message="Accepted",
        accepted_at=None,
        target_node_id=7,
    ))
    return stub


@pytest.fixture
def app_with_stub(service_stub, monkeypatch):
    async def fake_bootstrap():
        return type(
            "Ctx",
            (),
            {"services": type("Services", (), {"control_service": service_stub})(), "clients": None},
        )()

    async def fake_shutdown(_):
        return None

    monkeypatch.setattr("create_app.bootstrap", fake_bootstrap)
    monkeypatch.setattr("create_app.shutdown", fake_shutdown)
    app = create_app()
    return app


@pytest.fixture
def client(app_with_stub):
    with TestClient(app_with_stub) as test_client:
        yield test_client
