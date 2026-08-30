#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ops_actions_notif_mark_read — عملِ notif.mark_read در OpsActionEngine
(تبِ هفتمِ مینی‌اپ، ۲۰۲۶-۰۸-۰۷).

ادعاها:
  ۱) notif.mark_read در ALLOWED_ACTIONS هست.
  ۲) نه ids نه all=True → BLOCKED، هیچ چیزی خوانده‌شده علامت نمی‌خورد.
  ۳) all=True → همه‌چیز خوانده‌شده می‌شود.
  ۴) ids=[...] → فقط همان‌ها.
  ۵) دوباره‌صدازدن (idempotency) دومی را دوباره اجرا نمی‌کند (نتیجهٔ اولی برمی‌گردد).
"""
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_HERE), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402

ENV = harness.setup("ops-actions-notif")

OWNER = {"is_owner": True}


def _sandbox():
    d = Path(tempfile.mkdtemp(prefix="ops-notif-"))
    rt = d / "rt"
    rt.mkdir()
    for k, v in (("OCTOPUS_OPS_RUNTIME_DIR", str(rt)),
                 ("OCTOPUS_OPS_DB_PATH", str(rt / "o.sqlite3")),
                 ("OCTOPUS_OPS_AUDIT_PATH", str(rt / "a.jsonl")),
                 ("OCTOPUS_OPS_IDEMPOTENCY_PATH", str(rt / "i.sqlite3"))):
        os.environ[k] = v
    from agi2027_control.ops_actions import OpsActionEngine, ALLOWED_ACTIONS
    import notif_inbox as _ni
    try:
        _ni._STORE_PATH.unlink()
    except OSError:
        pass
    return OpsActionEngine(root=d), _ni, ALLOWED_ACTIONS


def t_action_is_allowlisted():
    _, _, allowed = _sandbox()
    assert "notif.mark_read" in allowed, allowed


def t_missing_ids_and_all_is_blocked():
    eng, ni, _ = _sandbox()
    ni.push("needs", "x")
    r = eng.execute("notif.mark_read", {}, OWNER, action_id="n1")
    assert r["ok"] is False and r.get("status") in ("BLOCKED", "DUPLICATE"), r
    assert ni.unread_count() == 1, "نباید چیزی خوانده‌شده علامت بخورد"


def t_all_true_marks_everything():
    eng, ni, _ = _sandbox()
    ni.push("needs", "x")
    ni.push("needs", "y")
    r = eng.execute("notif.mark_read", {"all": True}, OWNER, action_id="n2")
    assert r["ok"] is True and r["marked"] == 2, r
    assert ni.unread_count() == 0


def t_specific_ids_only():
    eng, ni, _ = _sandbox()
    id1 = ni.push("needs", "x")
    ni.push("needs", "y")
    r = eng.execute("notif.mark_read", {"ids": [id1]}, OWNER, action_id="n3")
    assert r["ok"] is True and r["marked"] == 1, r
    assert ni.unread_count() == 1


def t_not_owner_is_denied():
    eng, ni, _ = _sandbox()
    ni.push("needs", "x")
    r = eng.execute("notif.mark_read", {"all": True}, {"is_owner": False}, action_id="n4")
    assert r["ok"] is False and r["status"] == "DENIED", r
    assert ni.unread_count() == 1


def t_double_call_is_idempotent_not_double_marked():
    eng, ni, _ = _sandbox()
    ni.push("needs", "x")
    r1 = eng.execute("notif.mark_read", {"all": True}, OWNER, action_id="n5")
    r2 = eng.execute("notif.mark_read", {"all": True}, OWNER, action_id="n5")
    assert r1["ok"] is True and r1["marked"] == 1, r1
    assert r2["status"] == "DUPLICATE", r2


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_ops_actions_notif_mark_read: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
