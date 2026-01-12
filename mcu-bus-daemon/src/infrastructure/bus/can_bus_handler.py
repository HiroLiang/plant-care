from application.bus_handler import BusHandler
from domain.mcu_bus import BusEvent, Subscriber


class CanBusHandler(BusHandler):

    def _on_subscriber_added(self, subscriber: Subscriber) -> None:
        subscriber.active = True

    def _on_subscriber_removed(self, subscriber: Subscriber) -> None:
        subscriber.active = False
        subscriber.queue.put(None)

    def _take_event_for(self, subscriber: Subscriber) -> BusEvent:
        while subscriber.active:
            event = subscriber.queue.get()
            if event is None:
                raise RuntimeError("Subscriber closed")
            return event

        raise RuntimeError("Subscriber inactive")
