# NEXT-STEPS-COMPLETE — سه قلم باقی‌ماندهٔ گام ۵ (اجرا شد 2026-09-18)

## ۱) gemini ۰/۲ — رفع شد: الان **۱۰/۱۰**
**ریشه (اندازه‌گیری‌شده، نه حدس):** مسیر provider سالم بود (probe خام: HTTP 200، finishReason=STOP، متن «OK»).
باگ در سقف بود: `_HttpBrain.answer` سقف ۱۲۸ توکن می‌دهد و **Gemini 3.x توکن‌های thinking را از همان سقف می‌خورد** →
متن قابل‌مشاهده فقط ۱۳ کاراکتر («fence + def») می‌شد و scorer رشتهٔ def add را پیدا نمی‌کرد.
**رفع:** thinkingBudget=0 در GeminiBrain._body + scorer حالا fenceهای مارک‌داون را strip می‌کند.
**اثبات:** اجرای کامل ۱۰ تسک → GEMINI TOTAL: 10.0/10 (قبلاً ۷/۱۰ با کد ۰/۲). رسید: 138:state/receipts/GEMINIFIX-*.json

## ۲) سوئیچ مصرف‌کننده‌های remote_brain به کارخانه — انجام شد
- دو محل ساخت واقعی: `ofn/assistant_update.py` و `ofn/run.py` (دو rung). چهار «فایل» دیگر مصرف‌کننده نبودند:
  config.py فقط یک ثابت دارد، trend_sources.py فقط در کامنت نامش آمده، و دو تست به مسیر قدیمی assert می‌کنند (دست نخوردند تا نشکنند).
- الگو: `_factory_brain(tier, pin)` + fallback به RemoteBrain قدیمی + ثبت هر فراخوانی در state/receipts/brainswitch.jsonl.
- **یافتهٔ مهم:** فکتوری برای tier استاندارد مغز محلی رایگان (qwen3-0.6b، امتیاز ۴/۱۰) را انتخاب می‌کرد —
  برای این دو مصرف‌کنندهٔ استدلالی ضعیف است؛ پس به **deepseek (۱۰/۱۰، ارزان‌ترین) پین شدند** و REMOTE_DEEP به tier «deep» واگذار شد.
  اثبات: `_factory_brain("standard", pin="deepseek")` → RemoteBrain deepseek-flash.
- رسیدها: BRAINSWITCH-*.json + BRAINSWITCH-CALLSITES-*.json + BRAINSWITCH-PIN-*.json

## ۳) تایمر برای cognition/durability — **تصمیم: تایمر ساخته نشد** (با دلیل)
- `cognition_factory.py` یک **CLI هر-وظیفه** است (main(argv)؛ پچ/canary می‌سازد) نه مغز دوره‌ای. از ۰۹-۱۵ کسی صدایش نزده؛
  مشکل «نداشتن caller» است نه «نداشتن تایمر». اقدام درست: وصل‌کردن مسیر پچ coding-worker/ops_agent به همین CLI، یا archive رسمی.
- `durable_jobs.py` یک **کتابخانه** است (lease/heartbeat/evaluate؛ بدون main) و مصرف‌کننده‌اش از ۰۹-۱۵ به fleet_jobs.jsonl منتقل شده (۱۴۴/۱۵۰ CLOSED)
  → **جانشین‌شده**، نه خواب. اقدام درست: تأیید مالکِ صف، بعد archive با pre-image.

## وضعیت پایان
| قلم | وضعیت |
|---|---|
| gemini 0/2 | FIXED_WITH_EVIDENCE (10/10) |
| سوئیچ مصرف‌کننده‌ها | DONE (۲ محل واقعی؛ ۴ فایل غیرمصرف‌کننده با دلیل) |
| تایمر cognition/durability | DECIDED_WITH_REASON (caller/archive لازم است، نه تایمر) |
| مسیر پول / شاهد ۱۸۲ / فلگ‌های wire | دست‌نخورده |
