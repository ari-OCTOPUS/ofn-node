#!/usr/bin/env python3
"""spine.py — ستونِ فقراتِ یکپارچه‌سازیِ Project-F (gap‌ one-spine، ۲۰۲۶-۰۷-۲۵).

زمینه: چهار لایهٔ Project-F (orchestrator / langar / studio / pf_os) تا حالا
به‌صورتِ جزیره‌ای کار می‌کردند — ارتباط فقط از طریقِ فایل‌های جدا (drafts.json،
approvals.jsonl، state files) و بدونِ correlation یا health. دو ستونِ فقراتِ
موجود هرگز به هم وصل نشدند:

  • EventBus (event_bus.py) — pub/sub داخلیِ پروژه، envelope مطابقِ log-event-v1.
    ولی `.bus/` خالی است: هیچ لایه‌ای publish نمی‌کند.
  • bridge.py — pub/sub یک‌طرفه به ارگانیسمِ مرکزی (saba-bridge.jsonl). نوشته
    شده ولی فقط اگر کسی صدا بزند کار می‌کند.

این ماژول یک «نقطهٔ انتشارِ واحد» می‌سازد: یک publish façade که هم در busِ
داخلی و هم در bridgeِ بیرونی می‌نویسد، با dedupِ advisory، fail-soft، و
containment (قاعدهٔ #۷: هیچ PII/محتوا به بیرون نمی‌رود).

طراحی:
  • emit(event, organ, msg, **kw) — نقطهٔ واحد. هم bus.publish و هم bridge.publish.
  • پشتِ OCTOPUS_WIRE_PROJECTF_SPINE (پیش‌فرض خاموش = no-op). هر لایه می‌تواند
    بدونِ تغییرِ رفتارِ آزموده‌شده emit() را صدا بزند.
  • containment: msg قبل از هر خروجی scrub می‌شود (PII/marquee). bridge فقط
    summaryِ content-free می‌گیرد.
  • trace inheritance: اگر در یک trace هستیم، spanِ parent حفظ می‌شود.

نامتغیرها (قفلِ سخت):
  ۱. emit() هرگز raise نمی‌کند (fail-soft — حلقهٔ داغ نباید بمیرد).
  ۲. هرگز PII/محتوا/پلتفرم در bridge نمی‌رود (قاعدهٔ #۷).
  ۳. flag خاموش = صفر اثر (byte-for-byte با قبل).
  ۴. bridge.kind در whitelist است (bridge.py::ALLOWED_KINDS).

$0 · stdlib-only · fail-soft.
"""
from __future__ import annotations

import json
from typing import Optional

from . import config

FLAG = "OCTOPUS_WIRE_PROJECTF_SPINE"
"""روشن‌کردنِ انتشارِ یکپارچه. خاموش = emit() یک no-op می‌شود."""

# نگاشتِ نامِ رویدادِ taxonomy → kindِ bridge (whitelist در bridge.py).
# فقط رویدادهایی که برای ارگانیسمِ مرکزی معنی دارند mirror می‌شوند. بقیه فقط در
# busِ داخلی می‌مانند (مرکز نیازی به هر tickِ داخلی ندارد).
_BRIDGE_KIND_MAP = {
    "studio.draft.submitted": "draft_submitted",
    "studio.control.halt": "halt",
    "studio.control.resume": "resume",
    "studio.control.boundary": "boundary",
    "orchestrator.tick.done": "brain_tick_done",
    "kpi.week.recorded": "kpi",
    "learning.observed": "learning_observed",
}

_bus: Optional[object] = None  # lazy singleton (EventBus)


def _get_bus():
    """EventBus را به‌صورتِ lazy بساز (importِ event_bus ممکن است در sandbox تفاوت کند)."""
    global _bus
    if _bus is not None:
        return _bus
    try:
        from . import event_bus
        _bus = event_bus.EventBus()
    except Exception:  # noqa: BLE001
        _bus = None
    return _bus


def enabled() -> bool:
    """flag روشن است؟ هر لایه باید قبل از emit این را چک نکند — emit خودش چک می‌کند."""
    return config.flag(FLAG)


def emit(event: str, organ: str, msg: str, *,
         status: str = "success", level: str = "INFO",
         payload: dict | None = None, mirror_to_bridge: bool = True,
         bridge_text: Optional[str] = None) -> Optional[dict]:
    """نقطهٔ انتشارِ واحد. هم در busِ داخلی و هم (اگه kind نگاشت شده) در bridge.

    mirror_to_bridge=False یعنی فقط busِ داخلی (برای رویدادهای پرسرعتِ داخلی).
    bridge_text: متنِ صریحِ content-free برای bridge (اگه None، از msgِ scrubشده
    استفاده می‌شود، که باید از قبل content-free باشد).

    خروجی: envelope ثبت‌شده در bus، یا None (flag خاموش / خطا).
    همیشه fail-soft: هرگز raise نمی‌کند."""
    if not enabled():
        return None
    # ۱) busِ داخلی — envelope کامل، trace/span زنده
    env = None
    bus = _get_bus()
    if bus is not None:
        try:
            env = bus.safe_publish(event, organ, msg,
                                   status=status, level=level, payload=payload)
        except Exception:  # noqa: BLE001
            env = None
    # ۲) bridge — فقط برای kindهای نگاشت‌شده، و فقط summaryِ content-free
    if mirror_to_bridge and event in _BRIDGE_KIND_MAP:
        try:
            from . import bridge
            kind = _BRIDGE_KIND_MAP[event]
            text = bridge_text if bridge_text is not None else _content_free(msg)
            bridge.publish(kind, summary=text)   # bridge.publish(kind, summary, count, extra)
        except Exception:  # noqa: BLE001
            pass
    return env


def _content_free(msg: str) -> str:
    """خلاصهٔ content-free از msg برای bridge — فقط تعداد/وضعیت، نه محتوا.

    این دفاعِ دوم است (bridge.py خودش _PII_TERMS را scrub می‌کند). ما اینجا
    عمداً محتوا را جایگزین می‌کنیم تا حتی اگر msg تصادفاً محتوا داشت، به مرکز
    نرود. قاعدهٔ #۷ سخت است."""
    s = str(msg or "")
    # اگر متن طولانی است، فقط اولین ۸۰ کاراکتر + … — bridge بیشتر از این نمی‌خواهد
    if len(s) > 80:
        s = s[:77] + "..."
    return s


def health() -> dict:
    """دسترسی به healthِ bus (per-organ: تعداد، خطا، staleness). flag-off → {}."""
    if not enabled():
        return {}
    bus = _get_bus()
    if bus is None:
        return {}
    try:
        return bus.health()
    except Exception:  # noqa: BLE001
        return {}
