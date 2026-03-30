import os

from infrastructure.mcu.grpc_mcu_bus_command_client import GrpcMCUBusCommandClient

MCU_BUS_DAEMON_HOST = os.getenv("MCU_BUS_DAEMON_HOST", "localhost")
MCU_BUS_DAEMON_PORT = os.getenv("MCU_BUS_DAEMON_PORT", "50051")


class Clients:
    def __init__(self, mcu_bus_command_client: GrpcMCUBusCommandClient) -> None:
        self.mcu_bus_command_client = mcu_bus_command_client

    async def close(self) -> None:
        self.mcu_bus_command_client.close()


async def init_clients() -> Clients:
    return Clients(
        mcu_bus_command_client=GrpcMCUBusCommandClient(
            MCU_BUS_DAEMON_HOST,
            MCU_BUS_DAEMON_PORT,
        )
    )


async def shoutdown_clients(clients: Clients | None) -> None:
    if clients is None:
        return
    await clients.close()
