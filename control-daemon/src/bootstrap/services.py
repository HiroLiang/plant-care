from application.control_service import ControlService
from bootstrap.clients import Clients


class Services:
    def __init__(self, control_service: ControlService):
        self.control_service = control_service


async def init_services(clients: Clients) -> Services:
    return Services(control_service=ControlService(clients.mcu_bus_command_client))


async def shutdown_services(services: Services | None) -> None:
    if services is None:
        return
    services.control_service.close()
