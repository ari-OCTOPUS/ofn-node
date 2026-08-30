#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_effector_registry — پایداریِ ساختاریِ رجیستریِ sensor→actuator.

این رجیستری «نقشهٔ بیماریِ sensor-rich/actuator-poor» است. تستِ آن تضمین می‌کند:
· هر ورودی فیلدهای الزامی را دارد.
· status فقط از مقادیرِ مجاز است.
· هر wired یک actuatorِ غیرnull دارد.
· هر dead-output/display-only شاهدِ متنی دارد (evidence).
· شمارش‌ها سازگارند.

این تست نمی‌گوید «چند حس باید وصل باشد» — آن تصمیمِ مالک است. فقط می‌گوید
«اگر کسی چیزی اضافه کرد، قراردادِ رجیستر را نقض نکند.»"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

import effector_registry as er  # noqa: E402

_VALID_STATUS = {"wired", "display-only", "dead-output", "shadow"}
_REQUIRED_FIELDS = {"produced_by", "field", "actuator", "gate",
                    "status", "propose_only", "verified_at", "evidence"}


def _run(label, fn):
    try:
        fn()
        print(f"  ✅ {label}")
        return True
    except AssertionError as e:
        print(f"  ❌ {label}: {e}")
        return False


def t_every_entry_has_required_fields():
    for name, e in er.EFFECTORS.items():
        missing = _REQUIRED_FIELDS - set(e.keys())
        assert not missing, f"{name}: missing {missing}"


def t_status_values_are_valid():
    for name, e in er.EFFECTORS.items():
        assert e["status"] in _VALID_STATUS, f"{name}: bad status {e['status']!r}"


def t_wired_has_real_actuator():
    for name, e in er.EFFECTORS.items():
        if e["status"] == "wired":
            assert e["actuator"], f"{name}: wired but actuator is None/empty"


def t_dead_and_display_have_evidence():
    for name, e in er.EFFECTORS.items():
        if e["status"] in ("dead-output", "display-only"):
            assert e["evidence"] and len(e["evidence"]) > 10, \
                f"{name}: {e['status']} needs evidence text"


def t_shadow_can_have_null_actuator():
    # shadow = observation-only by design; actuator may be None
    for name, e in er.EFFECTORS.items():
        if e["status"] == "shadow":
            assert "actuator" in e, f"{name}: shadow needs actuator key (None ok)"


def t_counts_are_consistent():
    counts = er.status_counts()
    total = counts["total"]
    categorized = sum(v for k, v in counts.items() if k != "total")
    assert total == categorized, f"counts: total={total} but categorized={categorized}"
    assert total == len(er.EFFECTORS), "total != len(EFFECTORS)"


def t_helper_lists_match_status():
    assert set(er.dead_outputs()) == {n for n, e in er.EFFECTORS.items()
                                      if e["status"] == "dead-output"}
    assert set(er.display_only()) == {n for n, e in er.EFFECTORS.items()
                                      if e["status"] == "display-only"}
    assert set(er.wired()) == {n for n, e in er.EFFECTORS.items()
                               if e["status"] == "wired"}


def t_evidence_mentions_real_paths():
    # شاهدِ متنی باید مسیرِ فایلِ واقعی داشته باشد (نه فقط توصیفِ مبهم)
    for name, e in er.EFFECTORS.items():
        ev = e.get("evidence", "")
        assert (".py" in ev or ".json" in ev or ".jsonl" in ev or ".db" in ev), \
            f"{name}: evidence should reference a real file path"


if __name__ == "__main__":
    tests = [
        ("every entry has required fields", t_every_entry_has_required_fields),
        ("status values are valid", t_status_values_are_valid),
        ("wired has real actuator", t_wired_has_real_actuator),
        ("dead/display have evidence", t_dead_and_display_have_evidence),
        ("shadow can have null actuator", t_shadow_can_have_null_actuator),
        ("counts are consistent", t_counts_are_consistent),
        ("helper lists match status", t_helper_lists_match_status),
        ("evidence mentions real paths", t_evidence_mentions_real_paths),
    ]
    passed = 0
    for label, fn in tests:
        if _run(label, fn):
            passed += 1
    print(f"\n{'✅' if passed == len(tests) else '❌'} test_effector_registry: {passed}/{len(tests)}")
    sys.exit(0 if passed == len(tests) else 1)
