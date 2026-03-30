from typing import Protocol

from plant_core.generated.mcubus.v1.commands_pb2 import DispatchCommandReply, McuCommand


class MCUBusCommandClient(Protocol):
    def dispatch_command(self, command: McuCommand) -> DispatchCommandReply:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError
