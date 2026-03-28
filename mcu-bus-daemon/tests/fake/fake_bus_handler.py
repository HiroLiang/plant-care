from application.subscription_handler import SubscriptionHandler
from domain.mcu_bus import BusEvent
from domain.subscription import Subscriber


class FakeSubscriptionHandler(SubscriptionHandler):
    def __init__(self):
        super().__init__()

    def _on_subscriber_added(self, subscriber: Subscriber) -> None:
        subscriber.active = True

    def _on_subscriber_removed(self, subscriber: Subscriber) -> None:
        subscriber.active = False
        subscriber.queue.put_nowait(None)

    def _take_event_for(self, subscriber: Subscriber) -> BusEvent:
        event = subscriber.queue.get(timeout=1.0)
        if event is None:
            raise RuntimeError(f"Subscriber {subscriber.id} closed")
        return event
