import threading
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class ThreadSafeStore(Generic[K, V]):
    def __init__(self):
        self._lock = threading.RLock()
        self._storage: dict[K, V] = {}

    def retrieve(self, key: K) -> V | None:
        with self._lock:
            return self._storage.get(key)

    def store(self, key: K, value: V) -> None:
        with self._lock:
            self._storage[key] = value

    def remove(self, key: K) -> None:
        with self._lock:
            self._storage.pop(key, None)

    def contains(self, key: K) -> bool:
        with self._lock:
            if key not in self._storage:
                return False
            return True

    def values(self) -> list[V]:
        with self._lock:
            return list(self._storage.values())
