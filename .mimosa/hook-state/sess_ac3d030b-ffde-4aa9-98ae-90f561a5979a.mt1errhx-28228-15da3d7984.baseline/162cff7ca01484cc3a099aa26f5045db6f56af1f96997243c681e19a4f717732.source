#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_state_write_loudness — VQ-STATE-WRITE-001: شکستِ نوشتنِ خودمدل دیگر بی‌صدا نیست.

پیش از این فیکس، `self_model.run_and_persist` روی خطای نوشتن فقط
`{"ok": False}` برمی‌گردانْد؛ نه آلارمی، نه رویدادی، نه نشانگری — و `cortex`
هم `ok` را نمی‌خوانْد. نتیجهٔ عملی: heartbeat زنده، `self-model.json` شش روز
کهنه، هیچ زنگی (شاهد: ts=2026-07-25 روی درختِ ce35f61 در 2026-07-31).

سنجه‌ها رفتاری‌اند و روی خودِ تابع جاسوسی می‌کنند (درسِ «دفاعِ لایه‌ای
بی‌سنجه بی‌صدا می‌پوسد»): آلارم باید *صدا خورده باشد*، نشانگر باید *روی دیسک
باشد*، و موفقیت باید نشانگر را *پاک کند*. هیچ فایلِ زنده‌ای لمس نمی‌شود:
STATE_DIR قبل از هر import به tmpdir پین می‌شود.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="state-loud-")).resolve()
# opslib فقط ORG_ROOT/OPS_DIR را می‌خواند (پیش‌فرضِ ORG_ROOT = درختِ زنده!) —
# هر سه پین می‌شوند، قبل از هر import (درسِ «هر مسیرِ تحتِ آزمون را ایزوله کن»).
os.environ["ORG_ROOT"] = str(_TMP)
os.environ["OPS_DIR"] = str(_TMP / "_ops")
os.environ["OCTOPUS_STATE_DIR"] = str(_TMP / "_ops" / "state")
(_TMP / "_ops" / "state").mkdir(parents=True, exist_ok=True)

_HERE = Path(__file__).resolve().parent                  # _ops/tests
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib        # noqa: E402
import self_model    # noqa: E402

assert str(opslib.STATE_DIR).startswith(str(_TMP)), (
    "ایزوله نشد: STATE_DIR به tmp پین نیست — تست را ادامه نده", opslib.STATE_DIR)
assert str(self_model.MODEL_PATH).startswith(str(_TMP)), self_model.MODEL_PATH


def _tiny_root() -> Path:
    """یک ریشهٔ کوچک برای build_model تا اسکنِ کلِ _ops لازم نشود."""
    r = _TMP / "tinyroot"
    r.mkdir(parents=True, exist_ok=True)
    (r / "mod_a.py").write_text('"""ماژولِ نمونه."""\ndef f():\n    return 1\n', "utf-8")
    return r


class _AlertSpy:
    def __init__(self):
        self.calls = []

    def __call__(self, lines):
        self.calls.append(list(lines))


def t_a_write_failure_alerts_and_drops_marker():
    """شکستِ نوشتن ⇒ (۱) opslib.alert صدا می‌خورد (۲) نشانگرِ شکست روی دیسک."""
    spy = _AlertSpy()
    old_alert, old_model, old_marker = (opslib.alert, self_model.MODEL_PATH,
                                        self_model.WRITE_FAILURE_PATH)
    blocked = _TMP / "blocked-parent"
    blocked.write_text("این یک فایل است نه پوشه", "utf-8")   # mkdir(parents) شکست می‌خورد
    try:
        opslib.alert = spy
        self_model.MODEL_PATH = blocked / "self-model.json"
        self_model.WRITE_FAILURE_PATH = _TMP / "sm.write-failure.json"
        r = self_model.run_and_persist(_tiny_root())
        assert r.get("ok") is False, r
        assert spy.calls, "آلارم صدا نخورد — شکست هنوز بی‌صداست"
        assert any("self_model write FAILED" in " ".join(c) for c in spy.calls), spy.calls
        m = self_model.WRITE_FAILURE_PATH
        assert m.exists(), "نشانگرِ شکست نوشته نشد"
        d = json.loads(m.read_text("utf-8"))
        assert d.get("schema") == "state-write-failure.v1" and d.get("error"), d
    finally:
        opslib.alert, self_model.MODEL_PATH = old_alert, old_model
        self_model.WRITE_FAILURE_PATH = old_marker


def t_b_successful_write_clears_the_marker():
    """موفقیت = نشانگرِ شکستِ قبلی پاک می‌شود (نشانگرِ کهنه دروغِ معکوس است)."""
    old_model, old_marker = self_model.MODEL_PATH, self_model.WRITE_FAILURE_PATH
    try:
        self_model.MODEL_PATH = _TMP / "ok" / "self-model.json"
        self_model.WRITE_FAILURE_PATH = _TMP / "ok" / "sm.write-failure.json"
        self_model.WRITE_FAILURE_PATH.parent.mkdir(parents=True, exist_ok=True)
        self_model.WRITE_FAILURE_PATH.write_text("{}", "utf-8")   # شکستِ قبلی
        r = self_model.run_and_persist(_tiny_root())
        assert r.get("ok") is True, r
        assert self_model.MODEL_PATH.exists(), "مدل نوشته نشد"
        assert not self_model.WRITE_FAILURE_PATH.exists(), "نشانگرِ کهنه پاک نشد"
    finally:
        self_model.MODEL_PATH, self_model.WRITE_FAILURE_PATH = old_model, old_marker


def t_c_source_contract_cortex_checks_ok_and_alerts():
    """cortex دیگر ok=False را بی‌خوانده دفن نمی‌کند. سنجهٔ منبع + سنجهٔ رفتاری
    روی همان بلوکِ except-محافظ (importِ کاملِ cortex در تست سنگین/ناایزوله است)."""
    src = (_OPS / "cortex" / "cortex.py").read_text("utf-8")
    i = src.find("def self_model_refresh")
    assert i >= 0, "self_model_refresh غایب"
    body = src[i:i + 900]
    assert 'r.get("ok"' in body, "cortex هنوز ok را نمی‌خواند"
    assert "persist FAILED" in body, "شاخهٔ ok=False آلارم ندارد"


def t_d_observability_blocks_on_stale_self_model():
    """گاردِ GAAT حالا خودمدل را هم می‌سنجد: کهنه ⇒ خود-تغییری می‌ایستد."""
    import improve
    old_state = improve.STATE
    box = _TMP / "obs1"
    (box / "cortex").mkdir(parents=True, exist_ok=True)
    now = time.time()
    org = box / "ORGANISM-STATE.json"
    org.write_text("{}", "utf-8")
    os.utime(org, (now, now))                                    # تازه
    sm = box / "cortex" / "self-model.json"
    sm.write_text("{}", "utf-8")
    os.utime(sm, (now - 7 * 86400, now - 7 * 86400))             # ۷ روز کهنه
    try:
        improve.STATE = box
        ok, why = improve.observability_ok()
        assert ok is False, (ok, why)
        assert "self-model" in why, why
    finally:
        improve.STATE = old_state


def t_e_observability_blocks_on_failure_marker():
    import improve
    old_state = improve.STATE
    box = _TMP / "obs2"
    (box / "cortex").mkdir(parents=True, exist_ok=True)
    now = time.time()
    for name in ("ORGANISM-STATE.json", "cortex/self-model.json"):
        p = box / name
        p.write_text("{}", "utf-8")
        os.utime(p, (now, now))
    (box / "cortex" / "self-model.write-failure.json").write_text("{}", "utf-8")
    try:
        improve.STATE = box
        ok, why = improve.observability_ok()
        assert ok is False, (ok, why)
        assert "write-failure" in why, why
    finally:
        improve.STATE = old_state


def t_f_observability_green_when_both_fresh_and_no_marker():
    """جهتِ امن: فیکس نباید مشاهدهٔ سالم را قرمز کند."""
    import improve
    old_state = improve.STATE
    box = _TMP / "obs3"
    (box / "cortex").mkdir(parents=True, exist_ok=True)
    now = time.time()
    for name in ("ORGANISM-STATE.json", "cortex/self-model.json"):
        p = box / name
        p.write_text("{}", "utf-8")
        os.utime(p, (now, now))
    try:
        improve.STATE = box
        ok, why = improve.observability_ok()
        assert ok is True, (ok, why)
    finally:
        improve.STATE = old_state


if __name__ == "__main__":
    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith("t_")]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  ✅ {name}")
        except AssertionError as e:
            failed += 1
            print(f"  ❌ {name}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  💥 {name}: {type(e).__name__}: {e}")
    print(f"\n{'✅' if not failed else '❌'} test_state_write_loudness: "
          f"{len(tests) - failed}/{len(tests)} passed, {failed} failed")
    sys.exit(1 if failed else 0)
