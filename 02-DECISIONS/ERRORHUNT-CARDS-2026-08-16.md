---
type: decision-artifact
id: ERRORHUNT-CARDS-2026-08-16
created: 2026-08-16
status: آمادهٔ رأی — حداکثر ۵ کارت
parent: ERRORHUNT forensics
---

# کارت‌های رأی — شکار خطا 2026-08-16

هیچ‌کدام در این نشست اجرا نشد (فلگ/تسک/راز).

| # | موضوع | اگر تأیید شود | اگر رد شود |
|---|---|---|---|
| 1 | پروب orchestr/Fugu | مدار را از مسیر زنده خارج کن یا سهمیه/کلید را درست کن — ۴۹× 429 در ۷ روز؛ `last_ok` ارکستر = 08-12 | همان بک‌آف 3600s؛ اسنپ‌شات دیگر دروغ نمی‌گوید (C-022) |
| 2 | Poisoning Watch FILE_NOT_FOUND | فرمان تسک را به مسیر مطلق `py.exe` (درس flags.cmd / دیمون-بی‌سلاح) عوض کن | مانیتور ۶ساعته گاهی نمی‌دود؛ شواهد کهنه می‌ماند |
| 3 | سقف سوکت `reason` | `PAID_ASK_BUDGET_S_*` را با max_tokens فعلی هم‌تراز کن — ۳۶ هشدار reason تا 06:01 امروز | هشدار ادامه می‌یابد؛ تماس ممکن است بریده شود |
| 4 | `HF_TOKEN` | توکن اختیاری هاب برای دیمون (نام کلید فقط) تا هشدار unauth هر بوت نیاید | نویز INFO/WARNING هر بار بارگذاری MiniLM |
| 5 | هش کرنل body_bridge | manifest مورخ 2026-07-14 را برای `SENSITIVITY-LADDER.md` + `GEOMETRY.md` تازه کن، یا `integrity_ok=false` را به‌عنوان review دائمی بپذیر | daemon_state.kernel.integrity_ok=false می‌ماند (rsc.py و CLAIMS_LEDGER سالم‌اند) |
