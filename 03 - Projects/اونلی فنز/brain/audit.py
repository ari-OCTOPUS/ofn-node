#!/usr/bin/env python3
"""audit.py — Project-F · لاگِ append-onlyِ تأییدهای انسانی (2026-07-20).

هر approve/finalize/dm-approve یک خط JSON در ``langar/approvals.jsonl`` می‌نویسد
تا مسیرِ HITL قابل‌ممیزی باشد (چه کسی، کی، روی چه آیتمی). فقط متادیتای
content-free: هرگز متنِ hook/caption/body کامل ثبت نمی‌شود — فقط id/status/actor.

stdlib-only · fail-soft (audit هرگز pipeline را نمی‌شکند) · thread-safe.
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # brain/
_PROJECT_ROOT = _HERE.parent                     # Project-F/
# قابل‌انحراف با PF_AUDIT_FILE (تست/harness) — مثل PF_BRAIN_DIR در orchestrator
DEFAULT_AUDIT_FILE = Path(os.environ.get("PF_AUDIT_FILE")
                          or (_PROJECT_ROOT / "langar" / "approvals.jsonl"))

_LOCK = threading.RLock()

# ── مهرِ منشأ (2026-07-25) ──────────────────────────────────────────────────
# راستی‌آزماییِ متخاصم نشان داد سوئیتِ خودِ ونچر ۵۰ ردیف در همین فایلِ **تولیدیِ**
# حسابرسیِ تأییدِ انسانی نوشته بود، که ۱۴ تای آن `actor: owner` بود. امروز ضرری
# ندارد (فایل gitignore و بی‌خواننده است) ولی ضررش مؤخر و جدی است: در سیستمی که
# جدولِ رأیِ واقعی (`rfc_decision`) **صفر ردیف** دارد، این فایل تنها جایی است که
# شبیهِ «مدرکِ تأییدِ مالک» به‌نظر می‌رسد — و ۱۴ ردیفش جعلی است.
#
# دو لایه: (۱) conftest مسیر را برای تست‌ها به tmp می‌برد؛ (۲) همین مهر، که حتی اگر
# لایهٔ اول دور زده شود، ردیفِ ساختگی **ساختاراً** از ردیفِ واقعی قابلِ تفکیک باشد.
# تشخیص صریح است (env) با یک fallbackِ خودکار — نه جادو، و هرگز fail-open:
# اگر شک باشد، `test` مهر می‌خورد نه `live`.
ORIGIN_ENV = "PF_AUDIT_ORIGIN"
_TEST_RUNNER_MODULES = ("pytest", "_pytest", "unittest")


def _entry_looks_like_test() -> bool:
    """اسکریپتِ ورودی خودش تست است؟

    لازم است چون `run_all.py` هر تست را به‌صورتِ پروسهٔ جدا با `python test_x.py`
    می‌دود — در آن حالت نه pytest و نه unittest در `sys.modules` نیست، پس تشخیصِ
    ماژول‌محور به‌تنهایی به `live` می‌افتد. (خودِ همین نقص را تستِ
    `test_audit_origin_guard.py::T2/T3` گرفت.)"""
    import sys as _s
    cands = [_s.argv[0] if _s.argv else ""]
    main = _s.modules.get("__main__")
    cands.append(str(getattr(main, "__file__", "") or ""))
    for c in cands:
        if not c:
            continue
        norm = str(c).replace("\\", "/").lower()
        base = norm.rsplit("/", 1)[-1]
        if base.startswith("test_") or base.endswith("_test.py"):
            return True
        if "/tests/" in norm or norm.endswith("/run_all.py") or base == "run_all.py":
            return True
    return False


def _origin() -> str:
    """`live` | `test`. صریح برنده است؛ وگرنه تشخیصِ بافتِ تست.

    **هرگز fail-open نیست:** هر مقدارِ ناشناختهٔ env نادیده گرفته می‌شود و به
    تشخیص می‌افتد، و شک هرگز به‌نفعِ «واقعی» تفسیر نمی‌شود. دلیل: ردیفِ ساختگیِ
    مهرخوردهٔ `live` بدتر از نبودِ ردیف است — در سیستمی که جدولِ رأیِ واقعی صفر
    ردیف دارد، این فایل تنها چیزی است که شبیهِ مدرکِ تأییدِ مالک به‌نظر می‌رسد."""
    v = str(os.environ.get(ORIGIN_ENV, "")).strip().lower()
    if v in ("live", "test"):
        return v
    import sys as _s
    if any(m in _s.modules for m in _TEST_RUNNER_MODULES) or _entry_looks_like_test():
        return "test"
    return "live"


def audit_append(event: str, payload: dict, path: str | Path | None = None) -> bool:
    """یک رویدادِ تأیید را append می‌کند. True=نوشته شد، False=خطای بی‌صدا.

    payload باید content-free باشد (id/actor/status/channel) — caller مسئول است؛
    این‌جا هم به‌عنوان کمربندِ دوم فقط کلیدهای امن عبور داده می‌شوند.

    هر ردیف `origin` می‌گیرد. ردیفِ بی‌`origin` = نوشته‌شده قبل از ۲۰۲۵-۰۷-۲۵ ⇒
    منشأ نامعلوم ⇒ **مدرکِ تأییدِ انسانی حساب نمی‌شود.**"""
    safe_keys = ("id", "actor", "status", "channel", "kind", "ok", "reason",
                 "link_code", "duplicate")
    row = {"ts": time.time(), "event": str(event)[:40], "origin": _origin()}
    for k in safe_keys:
        if k in payload:
            row[k] = payload[k] if isinstance(payload[k], (bool, int, float)) \
                else str(payload[k])[:80]
    target = Path(path) if path else DEFAULT_AUDIT_FILE
    try:
        with _LOCK:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False
