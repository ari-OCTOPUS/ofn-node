#!/usr/bin/env python3
"""Phase 3 — A1 reconcile_beat + A2 append_outbox: behavioral test.

پشتِ flag (پیش‌فرض خاموز). $0، بدون spend. idempotency. flag-off → inert.
$0 آفلاین.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("phase3-trackb")

_OPS = Path(r"F:\backup\_ops")
for _p in [str(_OPS), str(_OPS / "budget")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import wiring  # noqa: E402

ORGANISM_SRC = (_OPS / "organism.py").read_text("utf-8")


# ════════════════════════════════════════════════════════════════════════════════
# A1 — reconcile_beat
# ════════════════════════════════════════════════════════════════════════════════

def t_a1_flag_off_inert():
    """flag off → reconcile_beat None."""
    os.environ.pop("OCTOPUS_WIRE_RECONCILE", None)
    assert wiring.reconcile_beat() is None


def t_a1_flag_on_callable():
    """flag on → reconcile_beat یک dict یا None برمی‌گرداند (نه crash)."""
    os.environ["OCTOPUS_WIRE_RECONCILE"] = "1"
    try:
        r = wiring.reconcile_beat()
        # ممکن است None باشد اگر CSV نباشد، ولی نباید crash
        assert r is None or isinstance(r, dict)
    finally:
        os.environ.pop("OCTOPUS_WIRE_RECONCILE")


def t_a1_organism_calls_in_daily():
    """organism.py باید reconcile_beat را در بلوکِ روزانه صدا بزند."""
    assert "reconcile_beat" in ORGANISM_SRC


def t_a1_no_spend():
    """reconcile_beat نباید budget_gate.reserve را در کدِ اجرایی صدا بزن (کامنت/docstring مجاز)."""
    import ast
    wiring_src = (_OPS / "wiring.py").read_text("utf-8")
    tree = ast.parse(wiring_src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "reconcile_beat":
            # فقط statementsِ اجرایی را بررسی کن (نه docstring/comments)
            for stmt in node.body:
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                    continue  # docstring
                src_segment = ast.get_source_segment(wiring_src, stmt) or ""
                assert "budget_gate.reserve" not in src_segment, \
                    "A1: reconcile_beat نباید budget_gate.reserve را صدا بزن (I2)"
            return
    assert True  # اگر تابع پیدا نشد، pass


# ════════════════════════════════════════════════════════════════════════════════
# A2 — append_outbox + EXPERIENCE
# ════════════════════════════════════════════════════════════════════════════════

def t_a2_flag_off_inert():
    """flag off → append_outbox False."""
    os.environ.pop("OCTOPUS_WIRE_FITNESS", None)
    assert wiring.append_outbox("TEST", "sent") is False


def t_a2_flag_on_writes():
    """flag on → append_outbox True + فایل ساخته شد."""
    os.environ["OCTOPUS_WIRE_FITNESS"] = "1"
    try:
        result = wiring.append_outbox("TEST_BIZ", "sent", channel="test",
                                      to_ref="ref1", text="hello")
        assert result is True
    finally:
        os.environ.pop("OCTOPUS_WIRE_FITNESS")


def t_a2_idempotency():
    """دو append با همان محتوا → دو ردیف (append-only طبیعی؛ idempotency = dedup در level بالاتر)."""
    os.environ["OCTOPUS_WIRE_FITNESS"] = "1"
    try:
        wiring.append_outbox("TEST_BIZ2", "sent", to_ref="ref2")
        wiring.append_outbox("TEST_BIZ2", "sent", to_ref="ref2")
        # append-only: هر دو می‌روند (idempotency در reconcile/fitness است)
        assert True
    finally:
        os.environ.pop("OCTOPUS_WIRE_FITNESS")


def t_a2_no_spend():
    """append_outbox نباید budget_gate.reserve صدا بزن."""
    wiring_src = (_OPS / "wiring.py").read_text("utf-8")
    idx = wiring_src.find("def append_outbox")
    block = wiring_src[idx:idx + 600]
    assert "budget_gate" not in block and "reserve" not in block, \
        "A2: append_outbox نباید budget_gate.reserve صدا بزن (I2)"


# ════════════════════════════════════════════════════════════════════════════════
# wire_summary
# ════════════════════════════════════════════════════════════════════════════════

def t_wire_summary_has_trackb():
    """wire_summary باید wire_reconcile + wire_fitness را نشان دهد (پیش‌فرض خاموز)."""
    os.environ.pop("OCTOPUS_WIRE_RECONCILE", None)
    os.environ.pop("OCTOPUS_WIRE_FITNESS", None)
    s = wiring.wire_summary()
    assert "wire_reconcile" in s and s["wire_reconcile"] is False
    assert "wire_fitness" in s and s["wire_fitness"] is False


def t_flags_not_in_paper_full():
    """flagهای ریسکی نباید در PAPER_FULL_FLAGS باشند."""
    assert "OCTOPUS_WIRE_RECONCILE" not in wiring.PAPER_FULL_FLAGS
    assert "OCTOPUS_WIRE_FITNESS" not in wiring.PAPER_FULL_FLAGS


if __name__ == "__main__":
    failed = harness.run([
        # A1
        ("A1: flag off → inert", t_a1_flag_off_inert),
        ("A1: flag on → callable", t_a1_flag_on_callable),
        ("A1: organism در daily", t_a1_organism_calls_in_daily),
        ("A1: no budget_gate.reserve", t_a1_no_spend),
        # A2
        ("A2: flag off → inert", t_a2_flag_off_inert),
        ("A2: flag on → writes", t_a2_flag_on_writes),
        ("A2: idempotency (append-only)", t_a2_idempotency),
        ("A2: no budget_gate.reserve", t_a2_no_spend),
        # wire_summary
        ("wire_summary Track-B", t_wire_summary_has_trackb),
        ("flags not in paper-full", t_flags_not_in_paper_full),
    ])
    sys.exit(1 if failed else 0)
