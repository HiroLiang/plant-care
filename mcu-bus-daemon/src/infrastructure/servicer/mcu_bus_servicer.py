import logging
from datetime import UTC, datetime

from grpc import ServicerContext

from application.subscription_handler import SubscriptionHandler
from domain.subscription import Subscriber
from infrastructure.servicer.bus_enevt_adapter import to_proto
from mcubus.v1 import commands_pb2, common_pb2
from mcubus.v1.command_service_pb2_grpc import MCUBusCommandServiceServicer
from mcubus.v1.event_service_pb2_grpc import MCUBusEventServiceServicer

logger = logging.getLogger(__name__)


class MCUBusCommandServer(MCUBusCommandServiceServicer):
    def DispatchCommand(self, request, ctx: ServicerContext):
        accepted_at = datetime.now(UTC)
        reply = commands_pb2.DispatchCommandReply(
            command_id=request.command.command_id,
            accepted=False,
            status=common_pb2.COMMAND_STATUS_UNSUPPORTED,
            message="Command dispatch is defined in the shared protocol but not wired to CAN transport yet.",
        )
        reply.accepted_at.FromDatetime(accepted_at)
        return reply


class MCUBusEventServer(MCUBusEventServiceServicer):
    def __init__(self, subscription_handler: SubscriptionHandler):
        self._subscription_handler = subscription_handler

    def SubscribeBusEvents(self, request, ctx: ServicerContext):
        subscriber = Subscriber()
        self._subscription_handler.handle_subscriber(subscriber)
        ctx.add_callback(lambda: self._disconnect_subscriber(subscriber))

        try:
            while ctx.is_active():
                event = self._subscription_handler.take_event(subscriber.id)
                if _matches_subscription(event, request):
                    yield to_proto(event)

        except Exception as e:
            logger.exception("Subscriber %s stream terminated unexpectedly: %s", subscriber.id, e)
        finally:
            self._disconnect_subscriber(subscriber)

    def _disconnect_subscriber(self, subscriber: Subscriber) -> None:
        if self._subscription_handler.has_subscriber(subscriber.id):
            self._subscription_handler.remove_subscriber(subscriber.id)
            logger.info(
                "Subscriber %s disconnected, remaining: %d",
                subscriber.id,
                len(self._subscription_handler.subscribers),
            )


def _matches_subscription(event, request) -> bool:
    if request.node_ids and event.source_node_id not in request.node_ids:
        return False

    event_type = _event_type_for(event)
    if request.event_types and event_type not in request.event_types:
        return False

    system_event_types = {
        common_pb2.EVENT_TYPE_COMMAND_RESULT,
        common_pb2.EVENT_TYPE_ALERT,
    }
    if not request.include_system_events and event_type in system_event_types:
        return False

    return True


def _event_type_for(event) -> int:
    payload = event.payload
    payload_name = type(payload).__name__
    mapping = {
        "TelemetryEvent": common_pb2.EVENT_TYPE_TELEMETRY,
        "HeartbeatEvent": common_pb2.EVENT_TYPE_HEARTBEAT,
        "DeviceStateEvent": common_pb2.EVENT_TYPE_DEVICE_STATE,
        "CommandResultEvent": common_pb2.EVENT_TYPE_COMMAND_RESULT,
        "AlertEvent": common_pb2.EVENT_TYPE_ALERT,
    }
    return mapping.get(payload_name, common_pb2.EVENT_TYPE_UNSPECIFIED)
