import logging

from bootstrap.clients import init_clients, shoutdown_clients
from bootstrap.context import AppContext
from bootstrap.database import init_database, shout_database
from bootstrap.logging import setup_logging
from bootstrap.services import init_services
from domain.mcu_bus_event import MCUBusEvent

logger = logging.getLogger(__name__)


def wire_mcu_bus_subscription(ctx: AppContext) -> None:
    if not ctx.clients or not ctx.services:
        return

    client = ctx.clients.mcu_bus_client
    service = ctx.services.monitor_service

    def on_event(event: MCUBusEvent) -> None:
        service.ingest_mcu_event(event)

    def on_error(error: Exception) -> None:
        logger.warning("MCU bus subscription error: %s", error)

    client.connect()
    client.subscribe_events_async(on_event=on_event, on_error=on_error)


async def bootstrap() -> AppContext:
    # Setup logging
    setup_logging(logging.INFO, False)

    # Initialize database
    db = await init_database()

    # Initialize clients
    clients = await init_clients()

    # Initialize services
    services = await init_services(clients)

    ctx = AppContext(
        db=db,
        clients=clients,
        services=services
    )
    wire_mcu_bus_subscription(ctx)
    return ctx


async def shutdown(ctx: AppContext) -> None:
    await shout_database(ctx.db)
    await shoutdown_clients(ctx.clients)
