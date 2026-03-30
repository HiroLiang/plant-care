import asyncio
import logging

from bootstrap.context import AppContext
from domain.mcu_bus_event import MCUBusEvent

logger = logging.getLogger(__name__)


def wire_mcu_bus_subscription(ctx: AppContext, loop: asyncio.AbstractEventLoop) -> None:
    if not ctx.clients or not ctx.services:
        return

    client = ctx.clients.mcu_bus_client
    service = ctx.services.monitor_service

    def on_event(event: MCUBusEvent) -> None:
        future = asyncio.run_coroutine_threadsafe(service.ingest_mcu_event(event), loop)
        future.add_done_callback(_log_background_failure)

    def on_error(error: Exception) -> None:
        logger.warning("MCU bus subscription error: %s", error)

    client.connect()
    client.subscribe_events_async(on_event=on_event, on_error=on_error)


async def bootstrap() -> AppContext:
    from bootstrap.clients import init_clients
    from bootstrap.database import init_database
    from bootstrap.logging import setup_logging
    from bootstrap.services import init_services

    # Setup logging
    setup_logging(logging.INFO, False)

    # Initialize database
    database = await init_database()

    # Initialize clients
    clients = await init_clients()

    # Initialize services
    services = await init_services(database.repositories, clients)
    await services.monitor_service.refresh_local_modules()

    ctx = AppContext(
        db=database.db,
        repositories=database.repositories,
        clients=clients,
        services=services
    )
    loop = asyncio.get_running_loop()
    services.start_polling(loop)
    wire_mcu_bus_subscription(ctx, loop)
    return ctx


async def shutdown(ctx: AppContext) -> None:
    from bootstrap.clients import shoutdown_clients
    from bootstrap.database import shout_database
    from bootstrap.services import shutdown_services

    await shoutdown_clients(ctx.clients)
    await shutdown_services(ctx.services)
    await shout_database(ctx.db)


def _log_background_failure(future) -> None:
    try:
        future.result()
    except Exception:
        logger.exception("Background ingestion failed")
