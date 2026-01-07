import logging

from pythonjsonlogger.json import JsonFormatter


def setup_logging(level: int = logging.INFO, json_output: bool = True):
    handler = logging.StreamHandler()

    if json_output:
        formatter = JsonFormatter(
            "%(levelname)s %(asctime)s [%(name)s] %(message)s"
        )
    else:
        formatter = logging.Formatter(
            "%(levelname)s %(asctime)s [%(name)s] %(message)s"
        )

    handler.setFormatter(formatter)

    logging.basicConfig(
        level=level,
        handlers=[handler]
    )
