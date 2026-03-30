import logging
import queue
import threading

from abc import ABC, abstractmethod
from typing import Dict

from domain.mcu_bus import BusEvent
from domain.subscription import Subscriber, Event

logger = logging.getLogger(__name__)


class SubscriptionHandler(ABC):
    def __init__(self):
        self._lock = threading.RLock()
        self.subscribers: Dict[str, Subscriber] = {}

    def handle_subscriber(self, subscriber: Subscriber) -> None:
        with self._lock:
            self.subscribers[subscriber.id] = subscriber
            self._on_subscriber_added(subscriber)

    def remove_subscriber(self, subscriber_id: str) -> None:
        with self._lock:
            subscriber = self.subscribers.pop(subscriber_id, None)
            if subscriber:
                self._on_subscriber_removed(subscriber)

    def has_subscriber(self, subscriber_id: str) -> bool:
        with self._lock:
            return subscriber_id in self.subscribers

    def take_event(self, subscriber_id: str) -> Event:
        """
        Get an event from the subscriber.
        Raises:
            KeyError: Subscriber not found
            RuntimeError: Subscriber is inactive or unsubscribed
        :param subscriber_id: id of the subscriber
        :return: BusEvent
        """
        with self._lock:
            subscriber = self.subscribers.get(subscriber_id)

        if not subscriber:
            raise KeyError(f"Subscriber {subscriber_id} not found")

        return self._take_event_for(subscriber)

    def publish(self, event: BusEvent) -> None:
        with self._lock:
            subscribers = list(self.subscribers.values())

        logger.info(
            "Publishing bus event %s (%s) from node %s to %d subscriber(s)",
            event.event_id,
            type(event.payload).__name__,
            event.source_node_id,
            len(subscribers),
        )

        for subscriber in subscribers:
            try:
                subscriber.queue.put_nowait(event)
            except queue.Full:
                logger.warning("Subscriber %s queue full, dropping event", subscriber.id)

    # ---- hooks ----
    @abstractmethod
    def _on_subscriber_added(self, subscriber: Subscriber) -> None:
        ...

    @abstractmethod
    def _on_subscriber_removed(self, subscriber: Subscriber) -> None:
        ...

    @abstractmethod
    def _take_event_for(self, subscriber: Subscriber) -> BusEvent:
        ...
