#!/usr/bin/env python3
"""test_fugu_quota_toctou.py — VQ-FUGU-TOCTOU-001 (۲۰۲۶-۰۸-۰۷).

`_mutate()` در fugu_quota.py قبلاً `except Exception: pass` داشت که هر خطای
داخلِ بلوکِ `with opslib.LockedJson(...)` را می‌بلعید و به یک fallbackِ
**بی‌قفل** می‌افتاد — شاملِ TimeoutError ِ واقعیِ قفلِ مشغول (دقیقاً همان
لحظه‌ای که فایل توسطِ پروسهٔ دیگری در حالِ نوشتن است). یعنی قراردادِ خودِ
تابع («شکستِ I/O = fail-closed») توسطِ خودِ کدش نقض می‌شد.

این تست با یک `opslib.LockedJson` جعلی که عمداً TimeoutError می‌دهد،
ثابت می‌کند: (۱) `_mutate` دیگر به fallbackِ بی‌قفل نمی‌افتد، (۲) نتیجه
None است (fail-closed)، (۳) فایلِ state دست‌نخورده می‌ماند.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("fugu-toctou")
OPS = Path(__file__).resolve().parent.parent
for _p in (OPS / "budget", OPS / "cortex"):
    sys.path.insert(0, str(_p))

import opslib  # noqa: E402
import fugu_quota as fq  # noqa: E402


class _FakeLockTimeout:
    """opslib.LockedJson ِ جعلی — شبیه‌سازیِ قفلِ واقعاً مشغول (opslib.py
    بعدِ ۵۰×۰.۱s تلاش، همین استثنا را raise می‌کند)."""
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        raise TimeoutError(f"lock busy: {self.path}")

    def __exit__(self, *a):
        return False


def t_a_lock_timeout_fails_closed_not_unlocked_fallback():
    """قفلِ مشغول → None (fail-closed)، نه نوشتنِ بی‌قفلِ فایل."""
    state_path = opslib.STATE_DIR / "fugu-quota.json"
    assert not state_path.exists(), "پیش‌شرط: فایل هنوز نباید وجود داشته باشد"

    orig_locked_json = opslib.LockedJson
    opslib.LockedJson = _FakeLockTimeout
    try:
        out = fq._mutate(lambda st: fq.Core.count_attempt(st, "primary:ARCHITECT_SYS"))
        assert out is None, f"قفلِ مشغول باید fail-closed (None) بدهد، نه: {out}"
        assert not state_path.exists(), (
            "‏TOCTOU: قفل مشغول بود ولی _mutate همچنان به fallbackِ بی‌قفل افتاد و فایل نوشت")
    finally:
        opslib.LockedJson = orig_locked_json


def t_b_write_failure_inside_lock_also_fails_closed():
    """شکستِ نوشتن *داخلِ* بلوکِ قفل‌شده (نه خودِ قفل) هم باید fail-closed شود،
    نه fallbackِ بی‌قفل."""
    state_path = opslib.STATE_DIR / "fugu-quota.json"

    class _FakeLockWriteFails:
        def __init__(self, path):
            self.path = path

        def __enter__(self):
            return self

        def read(self):
            return {}

        def write(self, st):
            raise OSError("simulated disk full mid-write")

        def __exit__(self, *a):
            return False

    orig_locked_json = opslib.LockedJson
    opslib.LockedJson = _FakeLockWriteFails
    try:
        out = fq._mutate(lambda st: fq.Core.count_attempt(st, "primary:ARCHITECT_SYS"))
        assert out is None, f"شکستِ نوشتنِ داخلِ قفل باید fail-closed بدهد، نه: {out}"
        assert not state_path.exists(), "شکستِ نوشتن نباید به fallbackِ بی‌قفل بیفتد"
    finally:
        opslib.LockedJson = orig_locked_json


def t_c_genuine_import_error_still_uses_single_process_fallback():
    """وقتی opslib واقعاً import نمی‌شود (نه اینکه import شد و بعد خطا داد)،
    fallbackِ تک‌پروسه باید همچنان کار کند — این مسیرِ ایمنِ تست/dev است.

    FUGU_QUOTA_BASE صریحاً ست می‌شود چون _base() هم خودش import opslib می‌کند؛
    وگرنه با import مسدودشده به مسیرِ واقعیِ _ops (بیرونِ sandbox) می‌افتد."""
    import builtins
    import os as _os
    import tempfile

    tmp = Path(tempfile.mkdtemp(prefix="fq-toctou-c-"))
    (tmp / "state").mkdir(parents=True, exist_ok=True)
    state_path = tmp / "state" / "fugu-quota.json"
    _saved_base = _os.environ.get("FUGU_QUOTA_BASE")
    _os.environ["FUGU_QUOTA_BASE"] = str(tmp)

    orig_import = builtins.__import__

    def _blocked_import(name, *a, **kw):
        if name == "opslib":
            raise ImportError("simulated: opslib genuinely not on sys.path")
        return orig_import(name, *a, **kw)

    builtins.__import__ = _blocked_import
    try:
        out = fq._mutate(lambda st: fq.Core.count_attempt(st, "primary:ARCHITECT_SYS"))
        assert out is not None, "‏ImportError واقعی باید همچنان fallbackِ تک‌پروسه بدهد"
        assert state_path.exists(), "fallbackِ تک‌پروسه باید فایل را بنویسد"
    finally:
        builtins.__import__ = orig_import
        if _saved_base is None:
            _os.environ.pop("FUGU_QUOTA_BASE", None)
        else:
            _os.environ["FUGU_QUOTA_BASE"] = _saved_base


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_fugu_quota_toctou: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
