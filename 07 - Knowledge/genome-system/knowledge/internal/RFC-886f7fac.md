# RFC RFC-886f7fac

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
*rfc_hash: `4543eeadb2492ef28b70e83b` · ledger_ref: `3baecc40e712e33714c8e4b3c9d4e899642d6266e7cbacc1a8652cf1e96de781`*