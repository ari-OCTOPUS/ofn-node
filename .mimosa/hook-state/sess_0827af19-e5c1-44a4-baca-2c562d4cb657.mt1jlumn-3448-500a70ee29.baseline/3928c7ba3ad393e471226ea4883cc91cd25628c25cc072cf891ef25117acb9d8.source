#!/usr/bin/env python3
"""depth_guard.py — گاردِ ناوردیِ ضدِ جعبه‌سیاه (anti-black-box invariant guard).

رأی مالک/ناوردیِ ارگانیسم: هیچ‌چیز نباید در جعبه‌سیاه گم شود —
  (۱) عمقِ واگذاری (delegation) هرگز از ۲ عبور نکند (زنجیرهٔ بی‌انتهای ایجنت→ایجنت ممنوع)؛
  (۲) هیچ نوشتنی بدونِ یک رویدادِ متناظر رخ ندهد (write باید همیشه رد پای event داشته باشد).

مدل: این ماژول **فقط مشاهده‌ای/SHADOW** است — نه block می‌کند، نه mutate. صرفاً می‌سنجد و
اگر ناوردی نقض شده باشد، برای هر نقض دقیقاً یک `opslib.alert` (fail-soft) می‌فرستد تا در
governor-alerts دیده شود. هیچ اقدامِ مخرب، هیچ نوشتنِ دیسک، هیچ تغییرِ state.

containment: هیچ رشتهٔ ممنوع (هویتِ Project-F) در alert/violation echo نمی‌شود
(scrub با _BANNED_ECHO — parity با registry_scan.scrub).

$0 · stdlib · read-only · fail-soft · بدونِ side-effectِ import.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

# ناوردیِ عمقِ واگذاری: root → A → B مجاز است (عمق ۲)؛ سطحِ سوم = جعبه‌سیاه.
MAX_DEPTH = 2

# containment (parity با registry_scan.scrub) — هیچ‌کدام هرگز از این ماژول بیرون نمی‌رود.
_BANNED_ECHO = ("اونلی", "onlyfans", "صبا")


def _scrub(s: str, cap: int = 160) -> str:
    """هر رشتهٔ حاوی echo ِ ممنوع → کاملاً redact (parity با registry_scan.scrub)."""
    v = str(s or "")[:cap]
    low = v.lower()
    if any(b in low or b in v for b in _BANNED_ECHO):
        return "(redacted:containment)"
    return v


def _depth_of(chain) -> int:
    """عمقِ واگذاری از ورودی. list/tuple → طولِ زنجیره؛ int → عمقِ مستقیم.
    bool زیرکلاسِ int است ولی زنجیره نیست → ۰. هر چیزِ دیگر (نامفهوم) → ۰ (fail-soft)."""
    if isinstance(chain, bool):
        return 0
    if isinstance(chain, int):
        return chain if chain > 0 else 0
    if isinstance(chain, (list, tuple)):
        return len(chain)
    return 0


def check_delegation(chain) -> dict:
    """عمقِ زنجیرهٔ واگذاری را می‌سنجد (ناوردی: depth <= MAX_DEPTH).

    chain: list/tuple = زنجیرهٔ واگذاری (طولش = عمق) یا int = عمقِ مستقیم.
    خروجی: {depth, ok, reason}. fail-soft: ورودیِ نامفهوم/خطا → depth 0 / ok=True
    (هرگز caller را نمی‌شکند؛ مشاهده‌ای است، پیش‌فرضِ امن = بی‌نقض)."""
    try:
        depth = _depth_of(chain)
    except Exception:  # noqa: BLE001
        return {"depth": 0, "ok": True, "reason": "unknown-chain (fail-soft)"}
    ok = depth <= MAX_DEPTH
    reason = "ok" if ok else f"delegation depth {depth} > {MAX_DEPTH}"
    return {"depth": depth, "ok": ok, "reason": reason}


def warn_if_violation(chain, wrote_without_event: bool = False) -> dict:
    """ناوردی‌ها را چک کن؛ برای هر نقض دقیقاً یک `opslib.alert` (SHADOW/مشاهده‌ای).

    این تابع **هرگز block/mutate نمی‌کند** — فقط warn. دو نقضِ ممکن:
      · depth > MAX_DEPTH  → violation "delegation-depth"
      · wrote_without_event → violation "write-without-event"
    خروجی: {violations:[...]}. fail-soft: اگر خودِ alert بشکند، جریان ادامه می‌یابد."""
    violations: list[dict] = []

    d = check_delegation(chain)
    if not d.get("ok", True):
        violations.append({"kind": "delegation-depth",
                           "depth": d.get("depth", 0),
                           "detail": d.get("reason", "")})
    if wrote_without_event:
        violations.append({"kind": "write-without-event",
                           "detail": "write performed without an emitted event"})

    for v in violations:
        try:
            # فقط رشته‌های تولیدِ داخلی (kind/detail) — با اینحال از scrub رد می‌شوند (دفاعِ عمقی)
            opslib.alert([_scrub(f"[depth-guard] {v['kind']}: {v.get('detail', '')}")])
        except Exception:  # noqa: BLE001
            pass  # مشاهده‌ای است؛ شکستِ alert هرگز نباید caller را بشکند

    return {"ok": not violations, "violations": violations}


if __name__ == "__main__":
    import json
    # فقط check_delegation (خالص، بدون alert) — نمایشِ read-only، مثلِ __main__ ِ stress/innervation
    demo = {
        "clean_depth2": check_delegation(2),
        "clean_chain_2": check_delegation(["root", "A"]),
        "violation_depth3": check_delegation(3),
        "violation_chain_3": check_delegation(["root", "A", "B"]),
    }
    print(json.dumps(demo, ensure_ascii=False, indent=2))