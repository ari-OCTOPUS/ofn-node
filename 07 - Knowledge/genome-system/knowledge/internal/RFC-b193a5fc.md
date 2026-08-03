# RFC RFC-b193a5fc

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
*rfc_hash: `3d2c493897b7f8e717ddb0d6` · ledger_ref: `fd890d80a50e53b702aa17e02f55887d914a0041f91547d246a9fb4ed65f3b28`*