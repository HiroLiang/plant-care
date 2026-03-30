from dataclasses import dataclass

from plant_core.infrastructure.persistence.sqlite import SQLiteDatasource
from plant_core.infrastructure.persistence.sqlite import (
    SQLiteCommandLogRepository,
)
from plant_core.infrastructure.persistence.sqlite.repositories.sqlite_device_state_repository import (
    SQLiteDeviceStateRepository,
)
from plant_core.infrastructure.persistence.sqlite.repositories.sqlite_event_log_repository import (
    SQLiteEventLogRepository,
)
from plant_core.infrastructure.persistence.sqlite.repositories.sqlite_node_repository import SQLiteNodeRepository
from plant_core.infrastructure.persistence.sqlite.repositories.sqlite_sensor_reading_repository import (
    SQLiteSensorReadingRepository,
)
from plant_core.infrastructure.persistence.sqlite.repositories.sqlite_sensor_repository import SQLiteSensorRepository


@dataclass(frozen=True)
class SQLiteRepositoryBundle:
    nodes: SQLiteNodeRepository
    device_states: SQLiteDeviceStateRepository
    sensors: SQLiteSensorRepository
    sensor_readings: SQLiteSensorReadingRepository
    command_logs: SQLiteCommandLogRepository
    event_logs: SQLiteEventLogRepository

    @classmethod
    def from_datasource(cls, datasource: SQLiteDatasource) -> "SQLiteRepositoryBundle":
        connection = datasource.raw_connection
        return cls(
            nodes=SQLiteNodeRepository(connection),
            device_states=SQLiteDeviceStateRepository(connection),
            sensors=SQLiteSensorRepository(connection),
            sensor_readings=SQLiteSensorReadingRepository(connection),
            command_logs=SQLiteCommandLogRepository(connection),
            event_logs=SQLiteEventLogRepository(connection),
        )
