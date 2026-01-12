import threading

from abc import ABC, abstractmethod
from typing import Dict

from domain.mcu_bus import Subscriber, BusEvent


class BusHandler(ABC):
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

    def take_event(self, subscriber_id: str) -> BusEvent:
        with self._lock:
            subscriber = self.subscribers.get(subscriber_id)

        if not subscriber:
            raise KeyError(subscriber_id)

        return self._take_event_for(subscriber)

    def publish(self, event: BusEvent) -> None:
        with self._lock:
            subscribers = list(self.subscribers.values())

        for subscriber in subscribers:
            subscriber.queue.put(event)

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
