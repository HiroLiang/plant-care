import grpc

from application.mcu_bus_command_client import MCUBusCommandClient
from plant_core.generated.mcubus.v1 import command_service_pb2_grpc, commands_pb2


class GrpcMCUBusCommandClient(MCUBusCommandClient):
    def __init__(self, host: str, port: str):
        self._server_address = f"{host}:{port}"
        self._channel = grpc.insecure_channel(self._server_address)
        self._stub = command_service_pb2_grpc.MCUBusCommandServiceStub(self._channel)

    def dispatch_command(self, command: commands_pb2.McuCommand) -> commands_pb2.DispatchCommandReply:
        request = commands_pb2.DispatchCommandRequest(command=command)
        return self._stub.DispatchCommand(request)

    def close(self) -> None:
        self._channel.close()
