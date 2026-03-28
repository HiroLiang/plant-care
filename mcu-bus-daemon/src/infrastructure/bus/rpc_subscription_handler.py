import logging
import queue

from application.subscription_handler import SubscriptionHandler
from domain.mcu_bus import BusEvent
from domain.subscription import Subscriber

logger = logging.getLogger(__name__)


class RpcSubscriptionHandler(SubscriptionHandler):
    """
    Can Bus Handler implements business
    """

    def _on_subscriber_added(self, subscriber: Subscriber) -> None:
        """
        Activate when subscriber was added
        :param subscriber: Subscriber
        """
        subscriber.active = True
        logger.info("Subscriber %s activated", subscriber.id)

    def _on_subscriber_removed(self, subscriber: Subscriber) -> None:
        """
        Deactivate when subscriber was removed
        :param subscriber: Subscriber
        """
        subscriber.active = False
        try:
            subscriber.queue.put_nowait(None)
        except queue.Full:

            # If queue is full, wait for clear
            try:
                while True:
                    subscriber.queue.get_nowait()
            except queue.Empty:
                pass
            subscriber.queue.put_nowait(None)

        logger.info("Subscriber %s deactivated", subscriber.id)

    def _take_event_for(self, subscriber: Subscriber) -> BusEvent:
        """
        Take event for subscriber
        :param subscriber: Subscriber
        :return: BusEvent
        """
        while subscriber.active:
            try:

                # Use timeout prevent stuck
                event = subscriber.queue.get(timeout=1.0)

                # Check stop signal
                if event is None:
                    raise RuntimeError(f"Subscriber {subscriber.id} closed")

                return event
            except queue.Empty:

                # Check active after timeout
                if not subscriber.active:
                    raise RuntimeError(f"Subscriber {subscriber.id} inactive")
                continue

        raise RuntimeError(f"Subscriber {subscriber.id} inactive")
