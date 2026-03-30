import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
src_root_str = str(SRC_ROOT)
if src_root_str not in sys.path:
    sys.path.insert(0, src_root_str)
