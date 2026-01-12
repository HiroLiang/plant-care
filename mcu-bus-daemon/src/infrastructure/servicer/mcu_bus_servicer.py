import logging
import queue

import grpc
from grpc import ServicerContext

from application.bus_handler import BusHandler
from domain.mcu_bus import Subscriber
from generated.mcubus.v1.mcu_bus_pb2_grpc import MCUBusServiceServicer
from infrastructure.servicer.bus_enevt_adapter import to_proto

logger = logging.getLogger(__name__)


class MCUBusServer(MCUBusServiceServicer):
    def __init__(self, bus_handler: BusHandler):
        self._bus_handler = bus_handler

    def SubscribeEvents(self, request, ctx: ServicerContext):
        """
        Override this method to receive events from subscribers.
        :param request: proto request
        :param ctx: gRPC context
        """

        # Add subscriber to handler
        subscriber = Subscriber()
        self._bus_handler.handle_subscriber(subscriber)

        # Add callback method
        ctx.add_callback(lambda: self._disconnect_subscriber(subscriber))

        # Keep taking events from handler
        try:
            while ctx.is_active():
                event = self._bus_handler.take_event(subscriber.id)
                yield to_proto(event)

        # gRPC errors
        except grpc.RpcError as e:
            logger.warning("Subscriber %s RPC error: %s", subscriber.id, e.code())

        # Unexpect errors
        except Exception as e:
            logger.error("Subscriber %s unexpected error: %s", subscriber.id, e)

        # Remove events subscriber
        finally:
            self._disconnect_subscriber(subscriber)

    def _disconnect_subscriber(self, subscriber: Subscriber) -> None:
        """
        Disconnects the subscriber from the bus handler.
        :param subscriber: event subscriber
        """
        if self._bus_handler.has_subscriber(subscriber.id):
            self._bus_handler.remove_subscriber(subscriber.id)
            logger.info(
                "Subscriber %s disconnected, remaining: %d",
                subscriber.id,
                len(self._bus_handler.subscribers),
            )
