from plant_core.generated.mcubus.v1 import event_service_pb2_grpc, events_pb2
from plant_core.infrastructure.persistence.sqlite.bundle import SQLiteRepositoryBundle


def test_monitor_can_import_plant_core_packages():
    assert events_pb2.BusEvent is not None
    assert event_service_pb2_grpc.MCUBusEventServiceStub is not None
    assert SQLiteRepositoryBundle is not None
