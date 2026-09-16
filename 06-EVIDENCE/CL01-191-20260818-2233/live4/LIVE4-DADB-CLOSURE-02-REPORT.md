# LIVE4 D-A/D-B CLOSURE-02 — گزارش نهایی این بلوک (2026-08-19 ~12:0x +10:00)
## D-A (FIXED_VERIFIED)
ریشه (طبقه‌بندی از شواهد paid-calls/pairs): ROUTE_DENIED-کلاس — ask_fugu بدون tier → TASK_TIERS→local؛
۷ شکست = ردِ گیت کیفیتِ local، نه provider. رفع: tier="primary" صریح. شاهد: در دو اجرای ۴تاییِ اخیر
baseline_arm_failure=0 (8/8 بازوی baseline با deepseek کامل شد) · صفر local-scoring · رسیدها COMPLETE.
## D-B (V2 + re-ask — هنوز 3/4)
قرارداد JSON سخت‌گیرانه + هشت تست سبز (A/B/TIE/نثر/کلیدمفقود/مقدارنامعتبر/JSONخراب/ترتیب‌جابجا).
دو اصلاح مسیر: (۱) .format با آکولادهای JSON می‌شکست → replace-templating؛ (۲) انتظار hex64 از مدل
غیرواقعی → rationale_hash = توکن کوتاه مدل، شاهدِ ضدجعلِ ما raw_output_sha256. + یک re-ask رسیددار
(JUDGE_REASK) برای UNREADABLE — بدون حدس برنده.
نتیجهٔ گیت ۴تایی (هر بار شناسه‌های تازه): 3/4 valid · judge_unreadable=1/4 → گیت ۴/۴سبز نشد؛ batch اصلی اجرا نشد.
## شواهد چهار تریس آخر
valid×3 (verdictهای B/A/B؛ یکی از مسیر re-ask) · void×1 (judge) · spent=$0.0007 · هزینه هر جفت معتبر≈$0.0002
## شرط دقیق شروعِ primary-30
چهار‌جفتِ پیاپیِ معتبر (judge_unreadable=0, baseline_arm_failure=0) + انجماد LIVE4-PROTOCOL-V2.
## اهرم بعدی (نشست بعد)
داور را به GLM بده (کلید موجود، keys_present glm=True) — هم compliance بالاتر احتمالی، هم رفعِ
JUDGE_INDEPENDENCE_LIMITED (داور از خانوادهٔ مدلِ بازوها خارج می‌شود)؛ در صورت نیاز re-ask دوم.
