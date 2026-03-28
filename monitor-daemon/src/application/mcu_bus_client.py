import logging
from typing import Optional, Callable, Protocol

from domain.mcu_bus_event import MCUBusEvent

logger = logging.getLogger(__name__)


class MCUBusClient(Protocol):
    def is_connected(self) -> bool:
        ...

    def connect(self) -> None:
        ...

    def disconnect(self) -> None:
        ...

    def subscribe_events(
            self,
            on_event: Callable[[MCUBusEvent], None],
            on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        ...

    def subscribe_events_async(
            self,
            on_event: Callable[[MCUBusEvent], None],
            on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        ...
