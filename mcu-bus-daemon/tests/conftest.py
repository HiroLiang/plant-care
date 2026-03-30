import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
PLANT_CORE_SRC = PROJECT_ROOT / "plant-core" / "src"

for path in (SRC_ROOT, PLANT_CORE_SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from fake.fake_bus_handler import FakeSubscriptionHandler


@pytest.fixture
def bus():
    return FakeSubscriptionHandler()
