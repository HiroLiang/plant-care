from dataclasses import dataclass

from bootstrap.clients import Clients
from bootstrap.services import Services
from infrastructure.persistence.datasource import DataSource


@dataclass
class AppContext:
    db: DataSource | None
    clients: Clients | None
    services: Services | None
