import time
from queue import Queue

import can
import logging

from datetime import datetime
from enum import Enum
from typing import Optional, Callable, Dict
from threading import Event, Thread

from application.bus_daemon import BusDaemon
from application.subscription_handler import SubscriptionHandler
from domain.mcu_bus import AlertEvent, BusEvent, SensorDataEvent
from infrastructure.bus.can_protocol import DataType, parse_can_id, HeartbeatData, ErrorCode, TempHumData

logger = logging.getLogger(__name__)


class BusState(Enum):
    DISCONNECTED = 0
    CONNECTED = 1


class CanBusDaemon(BusDaemon):
    def __init__(
            self,
            rpc_handler: SubscriptionHandler,
            channel: str = 'can0',
            bitrate: int = 500000,
    ):

        # Bus Subscriber handler
        self._rpc_handler = rpc_handler

        # CAN Bus
        self.bus: Optional[can.Bus] = None
        self.channel: str = channel
        self.bitrate: int = bitrate

        # Daemon process control
        self._stop_event = Event()
        self._rx_thread: Optional[Thread] = None
        self._monitor_thread: Optional[Thread] = None

        # Text queue
        self._tx_queue: Queue = Queue()

        # Message handler
        self._handlers: Dict[int, Callable] = {}

        # Init default handlers
        self._register_default_handlers()

        self._node_last_seen: Dict[int, datetime] = {}

    @property
    def node_last_seen(self) -> dict[int, datetime]:
        return dict(self._node_last_seen)

    def _new_event_id(self, node_id: int) -> str:
        return f"{node_id}-{time.time_ns()}"

    def register_handler(self, data_type: int, handler: Callable) -> None:
        """
        Register message handler
        :param data_type: DataType int
        :param handler: Callable
        """
        self._handlers[data_type] = handler

    def connect(self) -> bool:
        """
        Connect to the can bus device
        :return: is success
        """
        if self.bus:
            return True

        try:
            self.bus = can.Bus(
                channel=self.channel,
                bitrate=self.bitrate,
                interface='socketcan',
            )
            logger.info("Connected to %s @ %s bps", self.channel, self.bitrate)
            return True
        except can.CanError as e:
            logger.error(f"Failed to connect to CAN bus: {e}")
            return False

    def disconnect(self) -> None:
        """
        Disconnect from the CAN bus
        """
        if self.bus:
            self.bus.shutdown()
            self.bus = None
            logger.info("Disconnected from CAN bus")

    def start(self) -> bool:
        """
        Start the bus daemon loop threads
        :return:Is start success
        """
        if not self.connect():
            return False

        self._stop_event.clear()

        # Start RX thread
        self._rx_thread = Thread(target=self._rx_loop, daemon=True)
        self._rx_thread.start()

        # Start monitor thread
        self._monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

        logger.info("CAN bus daemon started")
        return True

    def stop(self) -> None:
        """
        Stop the bus daemon loop threads
        """
        logger.info("Stopping CAN bus daemon")
        self._stop_event.set()

        if self._rx_thread:
            self._rx_thread.join(timeout=5)

        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

        self.disconnect()
        logger.info("CAN bus daemon stopped")

    def run_forever(self) -> None:
        """
        Process until stop signal is received
        """
        if not self.start():
            return

        try:
            while not self._stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.stop()

    def _rx_loop(self):
        """
        Receive loop: Receive and handle messages
        """
        logger.info("RX thread started")

        while not self._stop_event.is_set():
            try:
                if self.bus is None:
                    continue

                msg = self.bus.recv(timeout=1.0)
                if msg is None:
                    continue

                # Analyze CAN ID
                node_id, data_type = parse_can_id(msg.arbitration_id)

                # Log receive data
                logger.debug(
                    f"RX: ID=0x{msg.arbitration_id:03X} "
                    f"Node={node_id} Type=0x{data_type:02X} "
                    f"Data={msg.data.hex()}"
                )

                # Call handler
                if data_type in self._handlers:
                    handler = self._handlers[data_type]
                    handler(node_id, bytes(msg.data))
                else:
                    logger.debug("Unhandled CAN data type: 0x%02X from node %s", data_type, node_id)

            except Exception as e:
                if not self._stop_event.is_set():
                    logger.error(f"RX loop error: {e}")

        logger.info("RX thread stopped")

    def _monitor_loop(self):
        """
        Monitor loop: Check nodes
        """
        logger.info("Monitor thread started")

        while not self._stop_event.is_set():
            time.sleep(10)

            now = datetime.now()
            for node_id, last_seen in self._node_last_seen.items():
                offline_seconds = (now - last_seen).total_seconds()
                if offline_seconds > 30:
                    logger.warning(f"Node {node_id} offline for {offline_seconds:.0f}s")

        logger.info("Monitor thread stopped")

    # Message handlers
    def _register_default_handlers(self) -> None:
        """
        Register the default handler functions
        """
        self.register_handler(DataType.HEARTBEAT, self._handle_heartbeat)
        self.register_handler(DataType.TEMP_HUM, self._handle_temp_hum)

    def _handle_heartbeat(self, node_id: int, data: bytes) -> None:
        """
        Handle heartbeat data
        :param node_id: MCU node id
        :param data: Heartbeat data bytes
        """
        try:
            heartbeat = HeartbeatData.from_bytes(data)
            logger.debug(f"Heartbeat: {heartbeat}")

            # update last seen
            self._node_last_seen[node_id] = datetime.now()

            # Record heartbeat in database
            if heartbeat.status != ErrorCode.NONE:
                logger.error(f"Heartbeat: {heartbeat.status}")
                self._rpc_handler.publish(BusEvent(
                    event_id=self._new_event_id(node_id),
                    module_id=str(node_id),
                    timestamp=datetime.now(),
                    payload=AlertEvent(
                        severity="error",
                        code=f"heartbeat_status_{heartbeat.status}",
                        message=str(heartbeat),
                    ),
                ))

        except Exception as e:
            logger.error(f"Error handling heartbeat: {e}")

    def _handle_temp_hum(self, node_id: int, data: bytes) -> None:
        """
        Handle temperature and humidity data
        :param node_id: MCU node id
        :param data: Hybrid data bytes
        """
        try:
            temp_hum = TempHumData.from_bytes(data)
            logger.info(f"Node {node_id}: {temp_hum}")
            self._node_last_seen[node_id] = datetime.now()

            # Send data through gRPC
            self._rpc_handler.publish(BusEvent(
                event_id=self._new_event_id(node_id),
                module_id=str(node_id),
                timestamp=datetime.now(),
                payload=SensorDataEvent(
                    temperature=temp_hum.temperature,
                    humidity=temp_hum.humidity,
                )
            ))

        except Exception as e:
            logger.error(f"Error handling temp/hum data: {e}")
