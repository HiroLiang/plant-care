from typing import Protocol


class BusDaemon(Protocol):
    def connect(self) -> bool:
        ...

    def disconnect(self) -> None:
        ...

    def start(self) -> bool:
        ...

    def stop(self) -> None:
        ...

    def run_forever(self) -> None:
        ...
