# RFC RFC-a08830ce

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
*rfc_hash: `748f0d202611bafc369d72d1` · ledger_ref: `b3ff8eb543c125a0e07bbaa522ccf0f3d67969b4ce7b5e2e1663edde1d0104c1`*