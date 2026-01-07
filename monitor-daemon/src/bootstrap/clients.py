import os

from clients.control_daemon.http_client import ControlDaemonHttpClient
from clients.mcu.rs485_client import Rs485Client

CTRL_DAEMON_URL = os.getenv("CTRL_DAEMON_URL", "http://localhost:8000")


class Clients:
    def __init__(self, ctrl_client: ControlDaemonHttpClient, rs485_client: Rs485Client):
        self.ctrl_client = ctrl_client
        self.rs485_client = rs485_client

    async def close(self):
        await self.ctrl_client.close()
        await self.rs485_client.close()


async def init_clients() -> Clients:
    ctrl_client = ControlDaemonHttpClient(base_url=CTRL_DAEMON_URL)
    rs485_client = Rs485Client()

    return Clients(ctrl_client=ctrl_client, rs485_client=rs485_client)


async def shoutdown_clients(clients: Clients):
    await clients.close()
