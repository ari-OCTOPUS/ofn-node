# GATE-0 MEGA-BUILD — 2026-08-19T12:30Z

## واقعیت زنده (runtime snapshot)

| مؤلفه | مقدار | شاهد |
|---|---|---|
| labels.json | 58 لیبل · sha `f3c3c407` | _ops/state/labels.json |
| LIVE4_SCORING | PRIMARY_V4_EXECUTED_CRITERION_NOT_MET_30V_13W (دانش منفی حفظ) | label + PRIMARY-V4-REPORT |
| LIVE4_PROTOCOL | V4_FROZEN (ratify شده) | PROTOCOL-V4-FREEZE.json |
| VARIANCE_ROBUSTNESS | VERIFIED_VOID_0PCT_20_SAMPLES (اولین قابلیت معیار) | voidrate20.json |
| DAEMON_PREDICTION_LOOP | LIVE_VERIFIED (705 pred / 691 outcome — در حال رشد) | predictions.db |
| MEMORY_LEARNING | MEMORY_LIVE_LEARNING_UNVERIFIED (درست — ۳۰/۲۰ پاس نشده) | LEARNING-VERDICT |
| وب‌اپ | 8771 (organism) · 8772 (cortex) · 8773 (cockpit) همگی LISTENING روی 127.0.0.1 | netstat |
| بکاپ بقا | owner-key.enc ✓ (144B) · مانیفست ۱۱ فایل · ۰ خرابی | MANIFEST.sha256 |
| دیمن 4d | زنده (ری‌استارت کنترل‌شده؛ stop path VERIFIED) | GATE-3 |

## جدول فرض / واقعیت / اثر (megaprompt §2.2)

| فرض مگاپرامپت | واقعیت زنده | اثر |
|---|---|---|
| «judge_unreadable گلوگاه است» | حل شد (V4a+fallback؛ VOID ۰٪) — گلوگاه جدید = ابطال فرضیهٔ حافظه | فاز ۲ باید ablation را اولویت کند |
| «داور ضعیف است» | باگ میدان‌ها بود (client content-only فیکس) + position-bias ۲۵٪ | طراحی جفت‌های swap-test در فاز ۵ |
| «داemon ۴d صفر prediction دارد» | ۷۰۵/۶۹۱ — حلقه زنده | فاز ۲ می‌تواند Brier دیمن را بسنجد |
| «وب‌اپ باید ساخته شود» | از قبل زنده است (cockpit 8773 + organism) | فاز ۵ = ارتقا/همگام‌سازی، نه ساخت از صفر |
| «تلگرام center نیاز به آپدیت دارد» | مرکز زنده (لاگ‌های telegram فعال) | فاز ۵: همگام‌سازی وضعیت در UI |

## طرح فاز ۱ (S1 core kernel) — گیت + تخمین

- **محتوا**: event bus typed با run_id + state machine ثبت‌گذار + رسید کامل هر عمل (budget_before/after) + heartbeat با status=OFF
- **گیت**: ۱۰ عمل نمونه با رسید کامل و budget_after ≥ 0
- **تخمین**: ۳–۴ چرخهٔ کاری (پیش از گیت ۲ سپتامبر)، ~۶ ساعت معادل
- **وابستگی**: به ماژول موجود `_ops/runtime/beat_lease.py` و `_ops/state/events.jsonl` وصل می‌شود (نه دوباره‌سازی)

## کشفیات این اسکن (برای تب CAPABILITIES/AUDIT)

۱. باگ میدان reasoning/content → فیکس (JUDGE_FIELD_SPLIT=VERIFIED) · ۲. position-bias ۲۵٪ (n=4) · ۳. قابلیت VOID-0% VERIFIED · ۴. ابطال صادقانهٔ V4 (۱۳/۳۰) · ۵. دیمن ۷۰۵/۶۹۱ با θ محافظه‌کارانه (کالیبراسیون ادعا نمی‌شود)
