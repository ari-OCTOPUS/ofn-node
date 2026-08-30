#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_action_schema_drift — دو کپیِ مستقلِ اعتبارسنجِ action-request.v1.

واقعیتِ ثبت‌شده: `unified_control.contracts.validate_action_request` کپیِ
دستیِ `action_bridge.contracts.validate_request` است (رشتهٔ schema هم literal
تکرار شده، import نشده). این dual-write ِ قرارداد است — اگر یکی عوض شود و
دیگری نه، درخواستی که یک لایه قبول می‌کند لایهٔ بعد رد می‌کند (یا بدتر:
برعکس). تا زمانی که یکی‌سازی رأی نگرفته، این تست drift را قرمز می‌کند.
"""
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
for p in (str(_OPS), str(_OPS / "action_bridge"), str(_OPS / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import harness  # noqa: E402
import contracts as ab  # noqa: E402  (action_bridge — sibling import ِ عمدی)
from unified_control import contracts as uc  # noqa: E402


def _valid_request() -> dict:
    return {"schema": "action-request.v1", "action_id": "act:drift-0001",
            "prereg_id": "2026-07-31#1:kx", "source_component": "test",
            "intent": "درخواستِ آزمونِ drift", "action_type": "observe_metric",
            "target": "state/neural/recall-trend.jsonl",
            "expected_effect": "read-only observation",
            "allowed_scope": ["state/**"], "external_effect": False,
            "estimated_cost": 0, "rollback": "none-needed (read-only)",
            "falsifier": "metric file unreadable"}


def t_the_schema_string_is_identical_in_both_packages():
    assert ab.REQUEST_SCHEMA == uc.ACTION_REQUEST_SCHEMA, (
        ab.REQUEST_SCHEMA, uc.ACTION_REQUEST_SCHEMA)


def t_a_valid_request_passes_both_validators():
    req = _valid_request()
    a = ab.validate_request(req)
    u = uc.validate_action_request(req)
    assert a["ok"], a
    assert u["ok"], u


def t_every_required_field_is_required_by_both():
    """حذفِ هر میدانِ اجباری باید **هر دو** را قرمز کند — اگر فقط یکی قرمز شد،
    drift شروع شده."""
    for field in ab._REQUEST_REQUIRED:
        req = _valid_request()
        req.pop(field, None)
        a = ab.validate_request(req)
        u = uc.validate_action_request(req)
        assert not a["ok"], f"action_bridge حذفِ {field} را قبول کرد"
        assert not u["ok"], f"unified_control حذفِ {field} را قبول کرد"


def t_known_deliberate_difference_is_pinned_not_hidden():
    """uc سخت‌گیرتر است: allowed_scope ِ خالی را رد می‌کند، ab قبول می‌کند
    (ab در classifier ِ خودش می‌بندد). این تفاوت **عمدی و ثبت‌شده** است — این
    بند پینش می‌کند تا تغییرِ بی‌صدا در هر جهت دیده شود."""
    req = _valid_request()
    req["allowed_scope"] = []
    a = ab.validate_request(req)
    u = uc.validate_action_request(req)
    assert a["ok"], ("ab حالا scope ِ خالی را رد می‌کند — تفاوتِ عمدی عوض شد؛ "
                     "این تست و سندش را آگاهانه به‌روز کن", a)
    assert not u["ok"], ("uc حالا scope ِ خالی را قبول می‌کند — گاردِ سخت‌گیر "
                         "شل شد", u)


def t_hostile_shapes_are_rejected_by_both():
    for mutate in (
        lambda r: r.update(external_effect="false"),      # str نه bool
        lambda r: r.update(estimated_cost=True),           # bool نه عدد
        lambda r: r.update(action_id="x"),                 # کوتاه‌تر از حد
        lambda r: r.update(schema="action-request.v2"),    # نسخهٔ ناشناخته
    ):
        req = _valid_request()
        mutate(req)
        assert not ab.validate_request(req)["ok"], req
        assert not uc.validate_action_request(req)["ok"], req


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_action_schema_drift: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
