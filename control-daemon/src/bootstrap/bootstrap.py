import logging

from bootstrap.context import AppContext

logger = logging.getLogger(__name__)


async def bootstrap() -> AppContext:
    from bootstrap.clients import init_clients
    from bootstrap.logging import setup_logging
    from bootstrap.services import init_services

    setup_logging(logging.INFO, False)

    clients = await init_clients()
    services = await init_services(clients)
    return AppContext(clients=clients, services=services)


async def shutdown(ctx: AppContext) -> None:
    from bootstrap.clients import shoutdown_clients
    from bootstrap.services import shutdown_services

    await shutdown_services(ctx.services)
    await shoutdown_clients(ctx.clients)
