from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bootstrap.clients import Clients
    from bootstrap.services import Services
    from plant_core.infrastructure.persistence.sqlite.bundle import SQLiteRepositoryBundle
    from plant_core.ports.datasource import DataSource


@dataclass
class AppContext:
    db: "DataSource | None"
    repositories: "SQLiteRepositoryBundle | None"
    clients: "Clients | None"
    services: "Services | None"
