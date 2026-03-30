import logging
from threading import Event, Thread
from typing import Optional, Callable, Iterator

import grpc

from application.mcu_bus_client import MCUBusClient
from domain.mcu_bus_event import MCUBusEvent
from infrastructure.mcu.bus_event_adapter import to_domain

from plant_core.generated.mcubus.v1 import event_service_pb2_grpc, events_pb2

logger = logging.getLogger(__name__)


class GrpcMCUBusClient(MCUBusClient):
    def __init__(self, host: str, port: str):
        self._host = host
        self._port = port
        self._connected = False
        self._server_address: str = host + ":" + port
        self._stop_event = Event()
        self._subscription_thread: Optional[Thread] = None
        self._channel: Optional[grpc.Channel] = None
        self._stub: Optional[event_service_pb2_grpc.MCUBusEventServiceStub] = None

    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> None:
        """
        Connect to MCU Bus gRPC Server
        """
        if self._connected:
            logger.warning("Already connected")
            return

        try:
            self._channel = grpc.insecure_channel(self._server_address)
            self._stub = event_service_pb2_grpc.MCUBusEventServiceStub(self._channel)
            self._connected = True
            logger.info("Connected to MCU Bus Server at %s", self._server_address)
        except Exception as e:
            logger.error("Failed to connect: %s", e)
            raise

    def disconnect(self) -> None:
        """
        Disconnect from MCU Bus gRPC Server
        :return:
        """
        if not self._connected:
            return

        self._stop_event.set()

        if self._subscription_thread and self._subscription_thread.is_alive():
            self._subscription_thread.join(timeout=5.0)

        if self._channel:
            self._channel.close()
            self._channel = None

        self._connected = False
        logger.info("Disconnected from MCU Bus Server")

    def subscribe_events(
            self,
            on_event: Callable[[MCUBusEvent], None],
            on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        """
        Subscribe to MCU Bus events
        :param on_event: Method to call when event is received
        :param on_error: Method to call when error is received
        """
        if not self._connected:
            raise RuntimeError("Not connected to server")

        try:
            event_stream: Iterator[events_pb2.BusEvent] = self._stub.SubscribeBusEvents(
                events_pb2.SubscribeBusEventsRequest(include_system_events=True)
            )

            logger.info("Started subscribing to bus events")

            for proto_event in event_stream:
                if self._stop_event.is_set():
                    break

                # Convert event to domain
                domain_event = to_domain(proto_event)

                try:
                    on_event(domain_event)
                except Exception as e:
                    logger.error("Error in event callback: %s", e)
                    if on_error:
                        on_error(e)

        except grpc.RpcError as e:
            logger.error("gRPC error: %s - %s", e.code(), e.details())
            if on_error:
                on_error(e)
        except Exception as e:
            logger.error("Unexpected error: %s", e)
            if on_error:
                on_error(e)

    def subscribe_events_async(
            self,
            on_event: Callable[[MCUBusEvent], None],
            on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        """
        Subscribe to MCU Bus events asynchronously
        :param on_event: Method to call when event is received
        :param on_error: Method to call when error is received
        """
        if self._subscription_thread and self._subscription_thread.is_alive():
            logger.warning("MCU Bus subscription thread already running")
            return

        self._stop_event.clear()

        def _subscribe_loop():
            self.subscribe_events(on_event, on_error)

        self._subscription_thread = Thread(
            target=_subscribe_loop,
            daemon=True,
            name="MCUBusSubscription"
        )
        self._subscription_thread.start()
        logger.info("Started async subscription thread")
