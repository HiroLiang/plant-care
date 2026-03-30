import asyncio
import sqlite3

from bootstrap.database import init_database
from plant_core.infrastructure.persistence.sqlite.bundle import SQLiteRepositoryBundle
from plant_core.infrastructure.persistence.sqlite.datasource import SQLiteDatasource


def test_init_database_uses_plant_core_sqlite(tmp_path, monkeypatch):
    async def scenario() -> None:
        db_path = tmp_path / "monitor.sqlite3"
        monkeypatch.setenv("DB_PATH", str(db_path))

        resources = await init_database()
        try:
            assert isinstance(resources.db, SQLiteDatasource)
            assert isinstance(resources.repositories, SQLiteRepositoryBundle)

            rows = await resources.db.raw_connection.execute_fetchall(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
            tables = {row[0] for row in rows}
            assert {"nodes", "sensors", "sensor_readings", "latest_sensor_readings"} <= tables
        finally:
            await resources.db.close()

        with sqlite3.connect(db_path) as connection:
            persisted_tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
        assert {"nodes", "sensors", "sensor_readings", "latest_sensor_readings"} <= persisted_tables

    asyncio.run(scenario())
