#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ops_actions_diagnostics_noop — عملِ diagnostics.noop در OpsActionEngine
(رأیِ مالک، مگاپرامپتِ تناقضات، آیتمِ الف-۳، ۲۰۲۶-۰۸-۰۹).

ادعاها:
  ۱) diagnostics.noop در ALLOWED_ACTIONS هست.
  ۲) اجرا با owner واقعی → APPLIED + noop_id، ردیف در soak_test_noop نشسته.
  ۳) هیچ جدولِ بیزینسی (leads/tasks/value_events) لمس نمی‌شود — صفر ردیف قبل و بعد.
  ۴) بدونِ owner → DENIED، هیچ ردیفی نوشته نمی‌شود.
  ۵) idempotency: همان action_id دوباره → DUPLICATE، دو ردیف نوشته نمی‌شود.
"""
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402

ENV = harness.setup("ops-actions-diagnostics-noop")

OWNER = {"is_owner": True}
NOT_OWNER = {"is_owner": False}


def _sandbox():
    d = Path(tempfile.mkdtemp(prefix="ops-noop-"))
    rt = d / "rt"
    rt.mkdir()
    for k, v in (("OCTOPUS_OPS_RUNTIME_DIR", str(rt)),
                 ("OCTOPUS_OPS_DB_PATH", str(rt / "o.sqlite3")),
                 ("OCTOPUS_OPS_AUDIT_PATH", str(rt / "a.jsonl")),
                 ("OCTOPUS_OPS_IDEMPOTENCY_PATH", str(rt / "i.sqlite3"))):
        os.environ[k] = v
    from agi2027_control.ops_actions import OpsActionEngine, ALLOWED_ACTIONS
    eng = OpsActionEngine(root=d)
    return eng, ALLOWED_ACTIONS


def _counts(eng):
    c = eng.db.conn
    return {
        "leads": c.execute("SELECT COUNT(*) FROM leads").fetchone()[0],
        "tasks": c.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],
        "value_events": c.execute("SELECT COUNT(*) FROM value_events").fetchone()[0],
        "soak_test_noop": c.execute("SELECT COUNT(*) FROM soak_test_noop").fetchone()[0],
    }


def t_action_is_allowlisted():
    _, allowed = _sandbox()
    assert "diagnostics.noop" in allowed, allowed


def t_owner_call_applies_and_writes_only_noop_table():
    eng, _ = _sandbox()
    before = _counts(eng)
    assert before == {"leads": 0, "tasks": 0, "value_events": 0, "soak_test_noop": 0}, before
    r = eng.execute("diagnostics.noop", {"note": "soak-test"}, OWNER)
    assert r.get("ok") is True and r.get("status") == "APPLIED", r
    assert r.get("noop_id"), r
    after = _counts(eng)
    assert after == {"leads": 0, "tasks": 0, "value_events": 0, "soak_test_noop": 1}, (
        "diagnostics.noop باید فقط soak_test_noop را عوض کند: " + str(after))


def t_non_owner_is_denied_and_writes_nothing():
    eng, _ = _sandbox()
    r = eng.execute("diagnostics.noop", {"note": "x"}, NOT_OWNER)
    assert r.get("ok") is False and r.get("status") == "DENIED", r
    assert _counts(eng)["soak_test_noop"] == 0, "denied یعنی صفر نوشتن"


def t_idempotent_same_action_id_does_not_double_write():
    eng, _ = _sandbox()
    r1 = eng.execute("diagnostics.noop", {"note": "same"}, OWNER, action_id="noop-fixed-1")
    r2 = eng.execute("diagnostics.noop", {"note": "same"}, OWNER, action_id="noop-fixed-1")
    assert r1.get("ok") is True, r1
    assert r2.get("status") == "DUPLICATE", r2
    assert _counts(eng)["soak_test_noop"] == 1, "action_id تکراری نباید دو ردیف بسازد"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_") and callable(v)]
    fails = []
    for t in tests:
        try:
            t()
            print("  ✅", t.__name__)
        except Exception as e:  # noqa: BLE001
            fails.append((t.__name__, e))
            print("  ❌", t.__name__, "-", e)
    print(("PASS" if not fails else "FAIL"), f"— test_ops_actions_diagnostics_noop — {len(fails)} failures")
    sys.exit(1 if fails else 0)
