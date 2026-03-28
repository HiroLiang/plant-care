from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bootstrap.clients import Clients
    from bootstrap.services import Services
    from infrastructure.persistence.datasource import DataSource


@dataclass
class AppContext:
    db: "DataSource | None"
    clients: "Clients | None"
    services: "Services | None"
