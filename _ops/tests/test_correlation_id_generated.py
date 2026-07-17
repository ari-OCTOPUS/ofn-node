"""test_correlation_id_generated.py — P1 (2026-07-15): emit بدونِ correlation_id →
mint ِ خودکارِ oct-YYYYMMDD-hex6 (خوانندهٔ consolidate.py:116 دیگر کور نیست)؛
با correlation_id ِ صریح → دست‌نخورده؛ هر رویداد یکتا."""
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("correlation_id")

import events as ev  # noqa: E402


def t_a_minted_when_empty():
    e = ev.emit("task.completed", "x", summary="s")
    assert re.fullmatch(r"oct-\d{8}-[0-9a-f]{6}", e["correlation_id"]), e["correlation_id"]


def t_b_explicit_preserved():
    e = ev.emit("task.completed", "x", correlation_id="my-corr-1")
    assert e["correlation_id"] == "my-corr-1"


def t_c_unique_per_event():
    a = ev.emit("task.completed", "x")["correlation_id"]
    b = ev.emit("task.completed", "x")["correlation_id"]
    assert a != b


if __name__ == "__main__":
    for f in (t_a_minted_when_empty, t_b_explicit_preserved, t_c_unique_per_event):
        f()
        print("ok", f.__name__)
    print("PASS test_correlation_id_generated")
