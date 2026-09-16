#!/usr/bin/env python3
"""indicator_scorecard.py — بک‌لاگِ ۲۰۲۷ #۸: اسکورکاردِ نشانگرهای آگاهیِ **access-only**
(Butlin-Long-Bengio 2023، arXiv 2308.08708) با گاردِ ضدِ اغراقِ **ساختاری**.

هدف (رأی مالک ۲۰۲۶-۰۷-۱۱: «برای هر بخش پایهٔ استاندارد داشته باش، اشتباه تکرار نشود — فقط
پیشنهاد، کل ساختار را بازنویسی نکن»): سیگنال‌های *موجودِ* سیستم را روی نشانگرهای شناخته‌شدهٔ
پردازشِ access نگاشت می‌کند و صادقانه ABSENT/WEAK/PRESENT می‌دهد — بی هیچ عددِ «درصدِ آگاهی».

مرزِ سختِ غیرقابلِ‌override (طبقِ §تریاژِ ۲۰۲۷ و epistemics/contracts):
  · فقط access-consciousness (مسیریابیِ اطلاعات) — **هرگز** phenomenal/qualia/sentience.
  · evidence، نه proof. هم over-attribution هم under-attribution = خطا.
  · گاردِ `assert_access_only` (بازاستفاده از `epistemics/contracts` — صفر کپیِ منطق، §۵)
    روی هر رشتهٔ خروجی raise می‌کند اگر ادعای مثبتِ phenomenal ساخته شود.

خودراستایی (صداقتِ نگاشت): وضعیتِ هر نشانگر از *واقعیتِ کد* می‌آید — فایلِ ماژولِ نگاشته
موجود است؟ و آیا پشتِ فلگِ wire/shadowِ خاموش است؟ اگر فلگ روشن شود، همان نشانگر خودکار به
PRESENT ارتقا می‌یابد (به‌جای عددِ دست‌چین). محافظه‌کاری: بدونِ اطمینان → WEAK نه PRESENT.

$0 · stdlib-only · fail-soft · read-only. بدونِ فلگِ `CORTEX_INDICATOR_SCORECARD` هیچ
نوشتنی نمی‌شود (no-op ِ کامل)؛ با فلگ فقط سینکِ خودش `state/cortex/indicator-scorecard-shadow.jsonl`.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # _ops/cortex
_OPS = _HERE.parent
for _p in (_OPS / "budget", _OPS / "epistemics"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import opslib  # noqa: E402

# بازاستفاده از گاردِ کانونیِ access-only (نه کپیِ واژگان) — اگر لایهٔ epistemics نبود، fail-soft
try:
    from contracts import assert_access_only as _assert_access_only  # type: ignore  # noqa: E402
except Exception:  # noqa: BLE001
    _PHENOMENAL_BANNED = ("phenomenal", "qualia", "sentient", "sentience", "feels")

    def _assert_access_only(*texts: str) -> None:  # fallback هم‌رفتار
        for t in texts:
            low = (t or "").lower()
            hit = next((w for w in _PHENOMENAL_BANNED if w in low), None)
            if hit and "not" not in low and "نه" not in low:
                raise ValueError(f"access-only violation: ادعای مثبتِ '{hit}'")

SCHEMA = "indicator-scorecard.v1"
FLAG = "CORTEX_INDICATOR_SCORECARD"          # env-flag فعال‌سازیِ نوشتن (وجود/truthy = روشن)
SHADOW_PATH = opslib.STATE_DIR / "cortex" / "indicator-scorecard-shadow.jsonl"

# بنرِ سختِ غیرقابلِ‌override — هرگز تغییر نمی‌کند، همیشه در خروجی است
BANNER = ("access-only indicators (Butlin/Long 2023) — evidence NOT proof — "
          "این ادعای phenomenal-consciousness / qualia / sentience نیست. "
          "over-attribution و under-attribution هر دو خطا هستند.")

ABSENT, WEAK, PRESENT = "ABSENT", "WEAK", "PRESENT"

# نگاشتِ نشانگر → ماژولِ *واقعیِ* موجود + فلگِ گِیت (اگر پشتِ فلگِ خاموش بود → WEAK).
# `gate` = env-flag ی که باید روشن باشد تا سیگنال «زنده» شمرده شود (None = مسیرِ core).
# `live_default` = آیا نبودِ فلگ یعنی زنده (True برای core، False برای shadow-only که فلگش رفتار نمی‌سازد).
_INDICATORS = [
    dict(id="GWT-1", theory="Global Workspace",
         claim="چند سیستمِ تخصصیِ موازی که به فضای کاری خوراک می‌دهند",
         module="cortex/innervation.py", gate=None),
    dict(id="GWT-2", theory="Global Workspace",
         claim="فضای کاریِ ظرفیت‌محدود با گلوگاهِ رقابت (bottleneck)",
         module="cortex/ignition.py", gate=None),
    dict(id="GWT-3", theory="Global Workspace",
         claim="پخشِ سراسریِ برنده به همهٔ ماژول‌ها (broadcast)",
         module="events.py", gate=None),
    dict(id="GWT-4", theory="Global Workspace",
         claim="توجهِ وابسته‌به‌حالت با انتخابِ نرمِ برنده (soft-WTA)",
         module="cortex/ignition_softwta.py", gate="IGNITION_SOFT_WTA_LIVE"),
    dict(id="RPT-1", theory="Recurrent Processing",
         claim="پردازشِ بازگشتی / re-entry (نه صرفاً یک‌گذر)",
         module="cortex/ignition.py", gate="CORTEX_IGNITION"),
    dict(id="PP-1", theory="Predictive Processing",
         claim="کمینه‌سازیِ خطای پیش‌بینیِ precision-weighted (قلب)",
         module="heart/control_law.py", gate="OCTOPUS_WIRE_HEART"),
    dict(id="HOT-2", theory="Higher-Order Theories",
         claim="مانیتورِ فراشناختیِ برخط / کالیبراسیونِ externally-graded",
         module="cortex/calibration_probe.py", gate="CORTEX_SELF_MONITOR"),
    dict(id="AE-1", theory="Agency & Embodiment",
         claim="کنشِ هدف‌محورِ world-model-driven (agency؛ embodiment: N/A)",
         module="cortex/goal_directed.py", gate=None),
]


def _truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _status_of(ind: dict, root: Path) -> str:
    """وضعیت از واقعیتِ کد: فایل نیست → ABSENT؛ پشتِ فلگِ خاموش → WEAK؛ وگرنه PRESENT."""
    mod = root / ind["module"]
    if not mod.exists():
        return ABSENT
    gate = ind.get("gate")
    if gate and not _truthy(gate):
        return WEAK               # کد هست ولی سیگنال زنده نیست (فلگ خاموش) — صادقانه WEAK
    return PRESENT


def score(root: Path | None = None) -> dict:
    """اسکورکاردِ read-only را بساز. $0، بدونِ side-effect. گاردِ ضدِ اغراق روی خروجی اجرا می‌شود."""
    root = root or _OPS
    rows = []
    counts = {ABSENT: 0, WEAK: 0, PRESENT: 0}
    for ind in _INDICATORS:
        st = _status_of(ind, root)
        counts[st] += 1
        rows.append({
            "id": ind["id"], "theory": ind["theory"], "claim": ind["claim"],
            "module": ind["module"], "gate": ind.get("gate"), "status": st,
        })
    out = {
        "ts": opslib.now_iso(), "schema": SCHEMA,
        "epistemic": "access-only", "is_proof": False,
        "banner": BANNER,
        # صریحاً هیچ «عددِ آگاهی» نمی‌دهیم — فقط شمارشِ نشانگرهای مسیریابیِ access
        "n_indicators": len(rows),
        "present": counts[PRESENT], "weak": counts[WEAK], "absent": counts[ABSENT],
        "overall": ("سیگنال‌های مسیریابیِ access حاضرند؛ این شاهدِ پردازش است، "
                    "نه اثباتِ آگاهیِ پدیداری."),
        "indicators": rows,
    }
    # گاردِ ساختاری: هیچ رشتهٔ خروجی نباید ادعای مثبتِ phenomenal بسازد (raise می‌کند)
    _assert_access_only(out["banner"], out["overall"],
                        *[r["claim"] for r in rows])
    return out


def _flag_on() -> bool:
    return _truthy(FLAG)


def run(root: Path | None = None, *, out_path: Path | None = None) -> dict:
    """اسکورکارد را بساز؛ فقط با فلگِ روشن یک خطِ سایه append کن (وگرنه no-op ِ خالص)."""
    card = score(root)
    if _flag_on():
        path = out_path or SHADOW_PATH
        try:
            opslib.append_jsonl(path, card)
            card["_persisted"] = str(path)
        except Exception as e:  # noqa: BLE001 — گزارش نباید به I/O گره بخورد
            card["_persist_error"] = str(e)
    return card


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
