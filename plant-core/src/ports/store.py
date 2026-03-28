from typing import Protocol, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class Store(Protocol[K, V]):
    def retrieve(self, key: K) -> V | None:
        ...

    def store(self, key: K, value: V) -> None:
        ...

    def remove(self, key: K) -> None:
        ...

    def contains(self, key: K) -> bool:
        ...

    def values(self) -> list[V]:
        ...
