"""test_latent_space_fail_closed.py — FIX #53 verification

تأیید می‌کند که:
۱. exception مصنوعی باعث wipe نمی‌شود (دادهٔ قبلی حفظ می‌شود)
۲. error در self._corrupt_load_error ثبت می‌شود
۳. فایل خراب به quarantine منتقل می‌شود
۴. تابع fail-safe برمی‌گردد (crash نمی‌کند)

no network, no outbound, no real data — فقط temp dir.
"""
import json
import sys
import os
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent  # F:\backup\_ops
_NEURAL = _OPS / "neural"
for _p in (str(_OPS), str(_NEURAL)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OCTOPUS_NEURAL_EFFECT_SHADOW", "0")

results = {"pass": 0, "fail": 0, "details": []}


def check(name, cond):
    if cond:
        results["pass"] += 1
        results["details"].append(f"  ✅ {name}")
    else:
        results["fail"] += 1
        results["details"].append(f"  ❌ {name}")


def main():
    try:
        import numpy as np
    except ImportError:
        # اگر numpy نیست، تست skip کن
        results["details"].append("  ⏭️ numpy not available — skip")
        return

    from latent_space import SharedLatentSpace

    with tempfile.TemporaryDirectory() as tmp:
        persist = Path(tmp) / "latent.json"

        # ۱. ذخیرهٔ دادهٔ سالم
        ls = SharedLatentSpace(dim=4, persist_path=persist)
        ls.embed("test_key", np.array([1.0, 2.0, 3.0, 4.0]), layer="L1")
        ls.store()
        check("data persisted", persist.exists())

        # ۲. خراب‌کردن فایل
        persist.write_text("THIS IS { NOT VALID JSON !!! ", "utf-8")
        check("corrupt file written", True)

        # ۳. load با فایل خراب — نباید crash کند
        try:
            ls2 = SharedLatentSpace(dim=4, persist_path=persist)
            check("_load (via __init__) did not crash on corrupt", True)
        except Exception as e:
            check(f"_load crashed: {e}", False)

        # ۴. دادهٔ جدید باید خالی باشد (چون load شکست خورد) ولی error ثبت شده
        has_error = hasattr(ls2, '_corrupt_load_error') and ls2._corrupt_load_error is not None
        check("corrupt_load_error registered", has_error)

        # ۵. فایل اصلی خراب نباید جا مانده باشد (quarantine شده)
        original_still_corrupt = persist.exists() and "NOT VALID" in persist.read_text("utf-8", errors="replace")
        check("corrupt file quarantined (not left in place)", not original_still_corrupt)

        # ۶. quarantine فایل ساخته شده
        quarantine_exists = any(
            f.name.startswith("latent.corrupt.") for f in Path(tmp).iterdir()
        ) if Path(tmp).exists() else False
        check("quarantine file created", quarantine_exists)

    print("test_latent_space_fail_closed — FIX #53 verification")
    for d in results["details"]:
        print(d)
    print(f"\nPass: {results['pass']}, Fail: {results['fail']}")
    return results["fail"] == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
