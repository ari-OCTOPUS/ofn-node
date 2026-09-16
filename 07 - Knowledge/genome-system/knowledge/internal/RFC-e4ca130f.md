# RFC RFC-e4ca130f

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
*rfc_hash: `16fd5ac0229f19d76bf5febc` · ledger_ref: `9a02515dffc8f5c310685f2af21598cd55deefabb712a0d64c6b666acf8229a6`*