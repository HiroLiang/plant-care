import logging
import os

from client.control_daemon.http_client import ControlDaemonHttpClient
from application.mcu_bus_client import MCUBusClient
from client.mcu.rs485_client import Rs485Client
from infrastructure.mcu.grpc_mcu_bus_client import GrpcMCUBusClient

logger = logging.getLogger(__name__)

CTRL_DAEMON_URL = os.getenv("CTRL_DAEMON_URL", "http://localhost:8000")

MCU_BUS_DAEMON_HOST = os.getenv("MCU_BUS_DAEMON_HOST", "localhost")
MCU_BUS_DAEMON_PORT = os.getenv("MCU_BUS_DAEMON_PORT", "50051")


class Clients:
    def __init__(self,
                 ctrl_client: ControlDaemonHttpClient,
                 rs485_client: Rs485Client,
                 mcu_bus_client: MCUBusClient) -> None:
        self.ctrl_client = ctrl_client
        self.rs485_client = rs485_client
        self.mcu_bus_client = mcu_bus_client

    async def close(self):
        await self.ctrl_client.close()
        await self.rs485_client.close()
        self.mcu_bus_client.disconnect()


async def init_clients() -> Clients:
    ctrl_client = ControlDaemonHttpClient(base_url=CTRL_DAEMON_URL)
    rs485_client = Rs485Client()

    mcu_bus_client = GrpcMCUBusClient(MCU_BUS_DAEMON_HOST, MCU_BUS_DAEMON_PORT)

    return Clients(
        ctrl_client=ctrl_client,
        rs485_client=rs485_client,
        mcu_bus_client=mcu_bus_client
    )


async def shoutdown_clients(clients: Clients):
    await clients.close()
