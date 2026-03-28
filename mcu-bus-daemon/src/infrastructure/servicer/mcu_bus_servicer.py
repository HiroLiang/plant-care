import logging

import grpc
from grpc import ServicerContext

from application.subscription_handler import SubscriptionHandler
from domain.subscription import Subscriber
from mcubus.v1.mcu_bus_pb2_grpc import MCUBusServiceServicer
from infrastructure.servicer.bus_enevt_adapter import to_proto

logger = logging.getLogger(__name__)


class MCUBusServer(MCUBusServiceServicer):
    def __init__(self, subscription_handler: SubscriptionHandler):
        self._subscription_handler = subscription_handler

    def Register(self, request, ctx: ServicerContext):
        ctx.abort(
            grpc.StatusCode.UNIMPLEMENTED,
            "Register is not implemented in bring-up mode; use SubscribeEvents for CAN validation.",
        )

    def UnRegister(self, request, ctx: ServicerContext):
        ctx.abort(
            grpc.StatusCode.UNIMPLEMENTED,
            "UnRegister is not implemented in bring-up mode; use SubscribeEvents for CAN validation.",
        )

    def SubscribeEvents(self, request, ctx: ServicerContext):
        """
        Override this method to receive events from subscribers.
        :param request: proto request
        :param ctx: gRPC context
        """

        # Add subscriber to handler
        subscriber = Subscriber()
        self._subscription_handler.handle_subscriber(subscriber)

        # Add callback method
        ctx.add_callback(lambda: self._disconnect_subscriber(subscriber))

        # Keep taking events from handler
        try:
            while ctx.is_active():
                event = self._subscription_handler.take_event(subscriber.id)
                yield to_proto(event)

        # gRPC errors
        except grpc.RpcError as e:
            logger.warning("Subscriber %s RPC error: %s", subscriber.id, e.code())

        except RuntimeError as e:
            logger.info("Subscriber %s stream closed: %s", subscriber.id, e)

        # Unexpected errors
        except Exception as e:
            logger.exception("Subscriber %s unexpected error: %s", subscriber.id, e)

        # Remove events subscriber
        finally:
            self._disconnect_subscriber(subscriber)

    def _disconnect_subscriber(self, subscriber: Subscriber) -> None:
        """
        Disconnects the subscriber from the bus handler.
        :param subscriber: event subscriber
        """
        if self._subscription_handler.has_subscriber(subscriber.id):
            self._subscription_handler.remove_subscriber(subscriber.id)
            logger.info(
                "Subscriber %s disconnected, remaining: %d",
                subscriber.id,
                len(self._subscription_handler.subscribers),
            )
