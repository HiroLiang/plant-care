from bootstrap.logging import setup_logging
import logging

logger = logging.getLogger("pytest.setup")


def pytest_configure():
    setup_logging(level=logging.DEBUG, json_output=False)
    logger.info("Logging configured")
