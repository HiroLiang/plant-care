import sys
from pathlib import Path

from bootstrap.logging import setup_logging
import logging

logger = logging.getLogger("pytest.setup")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLANT_CORE_SRC = PROJECT_ROOT / "plant-core" / "src"
PLANT_CORE_GENERATED = PLANT_CORE_SRC / "generated"

for path in (PLANT_CORE_SRC, PLANT_CORE_GENERATED):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


def pytest_configure():
    setup_logging(level=logging.DEBUG, json_output=False)
    logger.info("Logging configured")
