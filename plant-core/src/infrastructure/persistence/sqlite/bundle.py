from dataclasses import dataclass

from infrastructure.persistence.sqlite.datasource import SQLiteDatasource
from infrastructure.persistence.sqlite.repositories.sqlite_command_log_repository import (
    SQLiteCommandLogRepository,
)
from infrastructure.persistence.sqlite.repositories.sqlite_device_state_repository import (
    SQLiteDeviceStateRepository,
)
from infrastructure.persistence.sqlite.repositories.sqlite_event_log_repository import (
    SQLiteEventLogRepository,
)
from infrastructure.persistence.sqlite.repositories.sqlite_node_repository import SQLiteNodeRepository
from infrastructure.persistence.sqlite.repositories.sqlite_sensor_reading_repository import (
    SQLiteSensorReadingRepository,
)
from infrastructure.persistence.sqlite.repositories.sqlite_sensor_repository import SQLiteSensorRepository


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
