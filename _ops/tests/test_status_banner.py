#!/usr/bin/env python3
"""test_status_banner.py — بنرِ وضعیتِ چت (صداقتِ چت، TASK 4).

تستِ منطقِ خالص با ورودیِ کنترل‌شده (ops_dir موقت + quota تزریق‌شده).
هیچ پرچمِ زنده‌ای یا فایلِ state واقعی نمی‌خواند.
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
if str(_OPS / "owner_console") not in sys.path:
    sys.path.insert(0, str(_OPS / "owner_console"))

from status_banner import status_banner  # noqa: E402

FAILED = 0


def check(name: str, cond: bool, detail: str = ""):
    global FAILED
    if cond:
        print(f"  OK {name}")
    else:
        FAILED += 1
        print(f"  FAIL {name}: {detail}")


def _quota(remaining=10, cap=30, used=20, killed=False):
    return {"remaining": remaining, "cap": cap, "used_total": used, "killed": killed}


# ============================================================================
def t_healthy_empty():
    with tempfile.TemporaryDirectory() as d:
        r = status_banner(ops_dir=d, quota=_quota())
    check("healthy → ok/empty", r["level"] == "ok" and r["text"] == "", r)


def t_halt_all_flag():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "HALT-ALL").touch()
        r = status_banner(ops_dir=d, quota=_quota())
    check("HALT-ALL → halt", r["level"] == "halt" and r["halted"] is True, r)
    check("halt text mentions stop", "متوقف" in r["text"] and "HALT-ALL" in r["text"], r)


def t_stop_organism_flag():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "STOP-ORGANISM").touch()
        r = status_banner(ops_dir=d, quota=_quota())
    check("STOP-ORGANISM → halt", r["level"] == "halt" and r["halt_reason"] == "STOP-ORGANISM", r)


def t_stop_cortex_flag():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "STOP-CORTEX").touch()
        r = status_banner(ops_dir=d, quota=_quota())
    check("STOP-CORTEX → halt", r["level"] == "halt" and r["halt_reason"] == "STOP-CORTEX", r)


def t_halt_priority_hal_all_first():
    # هر دو پرچم → HALT-ALL (اولویتِ اول) گزارش شود.
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "STOP-ORGANISM").touch()
        (Path(d) / "HALT-ALL").touch()
        r = status_banner(ops_dir=d, quota=_quota())
    check("HALT-ALL wins priority", r["halt_reason"] == "HALT-ALL", r)


def t_quota_exhausted_warn():
    with tempfile.TemporaryDirectory() as d:
        r = status_banner(ops_dir=d, quota=_quota(remaining=0, cap=30, used=30))
    check("quota exhausted → warn", r["level"] == "warn", r)
    check("quota text", "سهمیه" in r["text"] and "30/30" in r["text"], r)


def t_quota_killed_warn():
    with tempfile.TemporaryDirectory() as d:
        r = status_banner(ops_dir=d, quota=_quota(remaining=5, cap=30, used=25, killed=True))
    check("quota killed → warn", r["level"] == "warn" and "سهمیه" in r["text"], r)


def t_quota_healthy_no_warn():
    with tempfile.TemporaryDirectory() as d:
        r = status_banner(ops_dir=d, quota=_quota(remaining=5, cap=30, used=25, killed=False))
    check("quota not exhausted → no warn", r["level"] == "ok" and r["text"] == "", r)


def t_halt_and_quota_both():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "HALT-ALL").touch()
        r = status_banner(ops_dir=d, quota=_quota(remaining=0, cap=30, used=30))
    check("halt+quota → level halt (highest)", r["level"] == "halt", r)
    check("both parts present", "متوقف" in r["text"] and "سهمیه" in r["text"], r)


def t_since_mtime_shown():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "STOP-ORGANISM"
        p.touch()
        old = time.time() - 7200  # 2 ساعت پیش
        os.utime(p, (old, old))
        r = status_banner(ops_dir=d, quota=_quota(), now=time.time())
    check("since-mtime in text", "2h" in r["text"] and "از" in r["text"], r)


def t_no_quota_injected_reads_best_effort_none():
    # وقتی quota=None و fugu_quota در دسترس نیست، banner نباید شکست بخورد.
    with tempfile.TemporaryDirectory() as d:
        r = status_banner(ops_dir=d, quota=None)
    # ممکن است quota واقعی بخواند یا None؛ مهم این است که level در نهایت ok باشد (چون پرچمی نیست).
    check("no flag + quota-None → no crash, ok", r["level"] == "ok", r)


# ============================================================================
# TASK 3 path ب — runtime_truth حالا بنرِ halt/quota را در خطِ اول می‌آورد.
def t_runtime_truth_surfaces_halt_banner():
    import status as _st   # owner_console روی sys.path است
    out = _st.runtime_truth(banner={"level": "halt", "text": "🔴 ارگانیسم متوقف است (HALT-ALL)"})
    check("runtime_truth prepends halt banner",
          "متوقف" in out and out.index("متوقف") < out.index("حقیقت runtime"), out)


def t_runtime_truth_no_banner_when_healthy():
    import status as _st
    out = _st.runtime_truth(banner={"level": "ok", "text": ""})
    check("runtime_truth omits banner when healthy",
          "🫀 حقیقت runtime" in out and "متوقف" not in out, out)


# ============================================================================
def main():
    tests = sorted((n, f) for n, f in globals().items() if n.startswith("t_"))
    for name, fn in tests:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            global FAILED
            FAILED += 1
            print(f"  CRASH {name}: {type(exc).__name__}: {exc}")
    total = len(tests)
    print(f"\n{'OK' if not FAILED else 'FAIL'} test_status_banner: "
          f"{total - FAILED}/{total} (failed={FAILED})")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
