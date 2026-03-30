from plant_core.generated.mcubus.v1 import (
    command_service_pb2_grpc,
    commands_pb2,
    event_service_pb2_grpc,
    events_pb2,
)


def test_mcu_bus_can_import_plant_core_generated_modules():
    assert event_service_pb2_grpc.MCUBusEventServiceServicer is not None
    assert command_service_pb2_grpc.MCUBusCommandServiceServicer is not None
    assert events_pb2.BusEvent is not None
    assert commands_pb2.DispatchCommandRequest is not None
