# RFC RFC-acd327bf

**status:** drafted

## مسئله (bottleneck)
knob:CHRONO_NUDGE_EVERY_N_BEATS — بدونِ مقدارِ صریح (unset)

## فیکس پیشنهادی
knobِ `CHRONO_NUDGE_EVERY_N_BEATS` مقدارِ صریح ندارد. پیشنهاد: به میانهٔ کرانِ امن (780.0، بازهٔ [120,1440]) ست شود تا آهنگِ کاری صریح و قابلِ‌کنترل شود. اثرِ محدود و برگشت‌پذیر.

## lift موردِانتظار
خود-تنظیمیِ نرم در کرانِ امن (کنترلِ صریحِ آهنگِ کاری)

## rollback
ورودیِ CHRONO_NUDGE_EVERY_N_BEATS را از state/cortex/auto-knobs.json حذف کن

---
*rfc_hash: `7953c8d36cc345a002b464e5` · ledger_ref: `789dc5143739e01282abd563cf9c2d0eb06c27aa39e99b769f69aa0c1b4c9b4a`*