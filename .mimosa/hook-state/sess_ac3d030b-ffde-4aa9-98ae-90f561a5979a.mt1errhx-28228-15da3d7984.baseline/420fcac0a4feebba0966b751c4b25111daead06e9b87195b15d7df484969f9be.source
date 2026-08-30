"""pytest hook — همان bootstrapِ unittest را فعال می‌کند."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests import _bootstrap  # noqa: F401,E402
