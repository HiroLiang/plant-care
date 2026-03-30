from plant_core.generated.mcubus.v1 import command_service_pb2_grpc, commands_pb2

from create_app import create_app


def test_create_app_registers_control_routes():
    app = create_app()
    paths = {route.path for route in app.router.routes}

    assert "/daemon/health" in paths
    assert "/controls/actuators" in paths
    assert "/controls/telemetry-requests" in paths
    assert "/controls/resets" in paths
    assert "/controls/thresholds" in paths
    assert command_service_pb2_grpc.MCUBusCommandServiceStub is not None
    assert commands_pb2.DispatchCommandReply is not None
