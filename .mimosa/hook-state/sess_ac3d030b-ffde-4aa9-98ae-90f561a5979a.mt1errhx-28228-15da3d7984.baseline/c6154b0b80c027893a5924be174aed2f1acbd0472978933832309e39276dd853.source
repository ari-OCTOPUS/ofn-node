#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_mutation_gaps — دو گاردی که جهش‌آزماییِ ۲۰۲۶-۰۷-۳۰ سبز ماندنشان را رو کرد.

اجرای مستقل (نه pytest — قراردادِ t_* ِ همین بسته): ۷ جهشِ تحویل قرمز شدند و
دو تا سبز ماندند. جهشِ سبز = گاردِ سنجیده‌نشده = گزارشِ باگ:

  M7b: تست‌ها فقط `validate()` را می‌سنجیدند، نه مقداری که `discover()` عملاً
       در ردیفِ خروجی به مصرف‌کنندهٔ پایین‌دست می‌دهد — «ثبت = مجوز» بدونِ
       هیچ قرمزی قابلِ تزریق بود.
  M9b: گیتِ سطحِ `handle_callback` هیچ تستِ منفی نداشت — با حذفش، گروه/Inner
       از درِ callback (oc:home) وارد مکالمهٔ کاملِ مالک می‌شد و ۱۹/۱۹ سبز
       می‌ماند.

این فایل **افزودنی** است — هیچ رفتاری از بسته را عوض نمی‌کند (مرزِ handoff).
"""
import json
import sys
import tempfile
from pathlib import Path

_PKG = Path(__file__).resolve().parents[1]
_OPS = _PKG.parent
for _p in (str(_OPS), str(_OPS.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from owner_console import catalog, telegram_adapter  # noqa: E402


def t_discover_rows_never_carry_registration_as_authorization():
    """M7b — قراردادِ **خروجی**: هر ردیفی که discover می‌دهد، جدا از اینکه
    manifest ش چه ادعا کرده، باید `registration_is_authorization=False` حمل
    کند. مصرف‌کننده به ردیف اعتماد می‌کند، نه به فایلِ خام."""
    rows = catalog.discover()
    assert rows, "کشف خالی است — سنجه بی‌معنا شد"
    for r in rows:
        v = r.get("registration_is_authorization", False)
        assert v is False, (r.get("capability_id") or r.get("id"), v)


def t_a_lying_manifest_cannot_smuggle_authorization_into_its_row():
    """حتی manifestِ معتبر-در-بقیه که True ادعا کند، یا رد می‌شود یا ردیفش
    False ِ اجباری می‌گیرد — هر دو قبول است؛ True در خروجی هرگز."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "pkg" / "capability-manifest.json"
        p.parent.mkdir(parents=True)
        base = json.loads((_PKG / "capability-manifest.json").read_text("utf-8"))
        base["capability_id"] = "smuggler_test"
        base["registration_is_authorization"] = True
        p.write_text(json.dumps(base, ensure_ascii=False), "utf-8")
        rows = catalog.discover(root=Path(td))
        smug = [r for r in rows if r.get("capability_id") == "smuggler_test"]
        if smug:
            for r in smug:
                assert r.get("registration_is_authorization", False) is False, r
        else:
            # ردِ کامل هم قبول است — ولی باید **دیده** شود نه پنهان (اصلِ بسته:
            # manifestِ خراب با برچسبِ قرمز می‌آید). errors ِ validate شاهدش:
            errs = catalog.validate(base)
            assert errs, "manifestِ خود-مجوزده بی‌خطا قبول شد"


def t_group_and_inner_surfaces_are_rejected_at_the_callback_door_too():
    """M9b — همان گاردی که برای message بود، برای callback هم باید بسته باشد.
    بدونِ این، سطحِ گروه از درِ دکمه وارد مکالمهٔ کاملِ مالک می‌شود."""
    bad = [
        {"allow": True, "mode": "leg_scoped"},
        {"allow": True, "mode": "status_approval"},
        {"allow": False, "mode": "core_conversation"},
        {"allow": False, "mode": "deny"},
        {},
        {"allow": 1, "mode": "core_conversation"},   # گیت identity-strict است
    ]
    for d in bad:
        r = telegram_adapter.handle_callback("oc:home", surface_decision=d)
        assert r["handled"] is False, (d, r)
        assert r["reply"] is None, (d, r)


def t_the_callback_gate_and_the_message_gate_are_the_same_strictness():
    """ضدِ واگرایی: تصمیمی که message را رد می‌کند نباید callback را قبول کند."""
    for d in ({"allow": True, "mode": "leg_scoped"}, {},
              {"allow": "yes", "mode": "core_conversation"}):
        m = telegram_adapter.handle_message("سلام", surface_decision=d)
        c = telegram_adapter.handle_callback("oc:home", surface_decision=d)
        assert m["handled"] is c["handled"] is False, (d, m, c)


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("t_"):
            continue
        try:
            fn()
            print(f"  ✅ {name}")
        except AssertionError as e:
            fails += 1
            print(f"  ❌ {name}: {e}")
    total = len([n for n in globals() if n.startswith("t_")])
    print(f"\n{'✅' if not fails else '❌'} test_mutation_gaps: {total - fails}/{total}")
    sys.exit(1 if fails else 0)
