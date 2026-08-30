"""test_close_c025_family_key_20260816 — قفل دونرمال‌ساز C-025.

پایتون \\s+ را فشرده می‌کند؛ SQL فقط \\n/\\t. یکی‌سازی SQL = رأی جدا.
ثبت در run_all نشده (WORKLOCK).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "4d_system"))

from memory.hypothesis_policy import family_key  # noqa: E402


def _sql_norm(hypothesis: str) -> str:
    return hypothesis.lower().replace("\n", " ").replace("\t", " ")


def test_python_collapses_double_space_sql_does_not():
    twin_a = "hello  world"
    twin_b = "hello world"
    assert family_key("d", twin_a) == family_key("d", twin_b)
    assert _sql_norm(twin_a) != _sql_norm(twin_b)
    assert re.sub(r"\s+", " ", twin_a) == re.sub(r"\s+", " ", twin_b)
