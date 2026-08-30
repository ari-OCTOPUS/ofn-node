#!/usr/bin/env python3
"""test_margin_m_v1.py — پذیرش m v1 (رأی مالک: ۴گانه + m_min=0.1).

هر خانواده + مینیمم‌گیری + fail-closed + لاگ سایه‌ای. $0 آفلاین."""
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

import harness
ENV = harness.setup("margin-m-v1")

from margin import margin as M
from margin import shadow_log as SL


def t_budget():
    assert abs(M.budget_headroom(50, 100) - 0.5) < 1e-9
    assert M.budget_headroom(100, 100) == 0.0
    assert M.budget_headroom(-1, 100) == 0.0, "منفی = نامعلوم ⇒ 0"
    assert M.budget_headroom(50, 0) == 0.0


def t_guard():
    assert M.guard_headroom(0.5, 0.0, 1.0) == 1.0, "وسط = بیشترین فاصله"
    assert M.guard_headroom(0.0, 0.0, 1.0) == 0.0, "روی مرز"
    assert M.guard_headroom(-0.1, 0.0, 1.0) == 0.0, "بیرون"
    assert abs(M.guard_headroom(0.75, 0.0, 1.0) - 0.5) < 1e-9


def t_breaker():
    assert M.breaker_headroom(0, 5) == 1.0
    assert abs(M.breaker_headroom(4, 5) - 0.2) < 1e-9
    assert M.breaker_headroom(5, 5) == 0.0
    assert M.breaker_headroom(3, 0) == 0.0


def t_suite():
    assert M.suite_headroom(100, 100) == 1.0
    assert M.suite_headroom(75, 100) == 0.5
    assert M.suite_headroom(50, 100) == 0.0, "نصف سبز = مرز"
    assert M.suite_headroom(0, 0) == 0.0


def t_m_of_and_gate():
    assert M.m_of(0.9, 0.4, 0.7) == 0.4
    assert M.m_of() == 0.0, "خالی = fail-closed"
    assert M.gate_ok(0.4) and not M.gate_ok(0.05)
    assert M.gate_ok(0.1) and not M.gate_ok(0.099), "مرزِ دقیق 0.1"


def t_shadow_log():
    with tempfile.TemporaryDirectory() as td:
        SL.LOG = Path(td) / "m.jsonl"
        assert SL.log_m("test", 0.42, family="budget") is True
        line = SL.LOG.read_text(encoding="utf-8").strip().splitlines()[-1]
        rec = __import__("json").loads(line)
        assert rec["m"] == 0.42 and rec["source"] == "test"


if __name__ == "__main__":
    failed = 0
    for name, fn in [("budget", t_budget), ("guard", t_guard), ("breaker", t_breaker),
                     ("suite", t_suite), ("m_of+gate", t_m_of_and_gate), ("shadow_log", t_shadow_log)]:
        try:
            fn(); print(f"  ✅ {name}")
        except AssertionError as e:
            print(f"  ❌ {name}: {e}"); failed += 1
    print(f"\n{'✅' if not failed else '❌'} test_margin_m_v1: {6 - failed}/6")
    sys.exit(1 if failed else 0)
