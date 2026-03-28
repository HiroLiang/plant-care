from dataclasses import dataclass
from domain.mcu import MCU
from shared.store import ThreadSafeStore
from threading import RLock


class MCUManager:
    def __init__(self, store: ThreadSafeStore[int, MCU]):
        self._lock = RLock()
        self._store = store

    def apply_update(self, mcu_id: int, update: MCUUpdate):
        with self._lock:
            if not self._store.contains(mcu_id):
                raise KeyError(f"MCU id {mcu_id} not in store")

            mcu = self._store.retrieve(mcu_id)

            if update.temperature is DELETE:
                mcu.temperature = None
            else:
                mcu.temperature = update.temperature

            if update.humidity is DELETE:
                mcu.humidity = None
            else:
                mcu.humidity = update.humidity


class _Delete:
    pass


DELETE = _Delete()


@dataclass
class MCUUpdate:
    temperature: float | None | _Delete = None
    humidity: float | None | _Delete = None
