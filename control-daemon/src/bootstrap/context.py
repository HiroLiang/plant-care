from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bootstrap.clients import Clients
    from bootstrap.services import Services


@dataclass
class AppContext:
    clients: "Clients | None"
    services: "Services | None"
