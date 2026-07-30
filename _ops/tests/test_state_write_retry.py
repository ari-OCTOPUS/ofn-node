#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_state_write_retry — ریشهٔ VQ-STATE-WRITE-001: نوشتنِ اتمیکِ state.

الگوی شکستِ ثبت‌شده (00-REALITY-BASELINE ۰۷-۳۰): `os.replace` روی ویندوز با
WinError 5 (قفلِ گذرای AV/ایندکسر) می‌شکند ⇒ `.tmp` تازه، فایلِ اصلی کهنه،
هیچ زنگی. سه ادعای فیکس، هرکدام با سنجهٔ رفتاری:
  ۱) شکستِ گذرا با retry جذب می‌شود و فایل واقعاً به‌روز می‌شود.
  ۲) شکستِ دائمی fail-loud است (استثنا بالا می‌رود، بلعیده نمی‌شود) و محتوای
     قبلی دست‌نخورده می‌ماند.
  ۳) شکستِ دائمی breadcrumb ِ ماشین‌خوان کنارِ فایل می‌گذارد — کهنگی از این
     به بعد قابلِ تشخیصِ قطعی است نه حدسی.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
for p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import harness  # noqa: E402
import opslib  # noqa: E402

_TMP = Path(tempfile.mkdtemp(prefix="state-retry-"))


def _lj(name: str) -> "opslib.LockedJson":
    return opslib.LockedJson(_TMP / name)


class _FlakyReplace:
    """جانشینِ os.replace: n بارِ اول PermissionError، بعد واقعی."""

    def __init__(self, fail_times: int):
        self.left = fail_times
        self.calls = 0
        self.real = os.replace

    def __call__(self, src, dst):
        self.calls += 1
        if self.left > 0:
            self.left -= 1
            raise PermissionError(5, "Access is denied (simulated AV lock)")
        return self.real(src, dst)


def _no_sleep():
    real = opslib.time.sleep
    opslib.time.sleep = lambda *_: None
    return real


def t_a_transient_lock_is_absorbed_and_the_file_really_updates():
    lj = _lj("transient.json")
    with lj:
        lj.write({"v": 1})
    flaky = _FlakyReplace(fail_times=2)
    real_sleep = _no_sleep()
    opslib.os.replace = flaky
    try:
        with lj:
            lj.write({"v": 2})
    finally:
        opslib.os.replace = flaky.real
        opslib.time.sleep = real_sleep
    assert flaky.calls == 3, ("retry نکرد", flaky.calls)
    assert json.loads((_TMP / "transient.json").read_text("utf-8")) == {"v": 2}
    assert not (_TMP / "transient.json.replace-failed.json").exists(), \
        "موفقیت نباید breadcrumb بگذارد"


def t_a_permanent_failure_is_loud_and_leaves_the_old_state_intact():
    lj = _lj("permanent.json")
    with lj:
        lj.write({"v": "old"})
    flaky = _FlakyReplace(fail_times=99)
    real_sleep = _no_sleep()
    opslib.os.replace = flaky
    raised = False
    try:
        with lj:
            lj.write({"v": "new"})
    except PermissionError:
        raised = True
    finally:
        opslib.os.replace = flaky.real
        opslib.time.sleep = real_sleep
    assert raised, "شکستِ دائمی بی‌صدا بلعیده شد — همان باگِ اصلی!"
    assert json.loads((_TMP / "permanent.json").read_text("utf-8")) == \
        {"v": "old"}, "state ِ قبلی خراب شد"
    crumb = _TMP / "permanent.json.replace-failed.json"
    assert crumb.exists(), "breadcrumb ِ تشخیصِ کهنگی نوشته نشد"
    d = json.loads(crumb.read_text("utf-8"))
    assert d.get("error") and d.get("attempts") == 6, d
    assert (_TMP / "permanent.json.tmp").exists(), \
        ".tmp ِ تازه باید بماند (شاهدِ جرم)"


def t_the_happy_path_is_byte_identical_to_before_the_fix():
    lj = _lj("happy.json")
    with lj:
        lj.write({"a": 1, "b": "فارسی"})
    got = json.loads((_TMP / "happy.json").read_text("utf-8"))
    assert got == {"a": 1, "b": "فارسی"}, got
    assert not (_TMP / "happy.json.tmp").exists(), "tmp بعد از موفقیت ماند"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_state_write_retry: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
