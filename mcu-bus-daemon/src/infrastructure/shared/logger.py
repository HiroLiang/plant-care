import logging

try:
    from pythonjsonlogger.json import JsonFormatter
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal bring-up images
    JsonFormatter = None


def setup_logging(level: int = logging.INFO, json_output: bool = True):
    handler = logging.StreamHandler()

    if json_output and JsonFormatter is not None:
        formatter = JsonFormatter(
            "%(levelname)s %(asctime)s [%(name)s] %(message)s"
        )
    else:
        formatter = logging.Formatter(
            "%(levelname)s: %(asctime)s [%(name)s] %(message)s"
        )

    handler.setFormatter(formatter)

    logging.basicConfig(
        level=level,
        handlers=[handler]
    )
