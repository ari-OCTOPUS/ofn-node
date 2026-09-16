# tests/conftest.py — مسیرِ impl/ را روی sys.path می‌گذارد تا import‌های flat
# (from hypothesis_brain import ...) در تست‌ها کار کنند.
import sys
from pathlib import Path

IMPL_DIR = Path(__file__).resolve().parent.parent / "impl"
if str(IMPL_DIR) not in sys.path:
    sys.path.insert(0, str(IMPL_DIR))
