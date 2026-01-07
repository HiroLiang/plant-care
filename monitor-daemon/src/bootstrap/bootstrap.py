import logging

from bootstrap.clients import init_clients, shoutdown_clients
from bootstrap.context import AppContext
from bootstrap.database import init_database, shout_database
from bootstrap.logging import setup_logging
from bootstrap.services import init_services


async def bootstrap() -> AppContext:
    # Setup logging
    setup_logging(logging.INFO)

    # Initialize database
    db = await init_database()

    # Initialize clients
    clients = await init_clients()

    # Initialize services
    services = await init_services()

    return AppContext(
        db=db,
        clients=clients,
        services=services
    )


async def shutdown(ctx: AppContext) -> None:
    await shout_database(ctx.db)
    await shoutdown_clients(ctx.clients)
