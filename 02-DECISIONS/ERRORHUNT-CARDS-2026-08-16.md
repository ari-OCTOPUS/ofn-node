---
type: decision-artifact
id: ERRORHUNT-CARDS-2026-08-16
created: 2026-08-16
status: کارت ۲ انجام شد (Watch) — ۴ رأی باز + بازماندهٔ LiveDataRefresh
parent: ERRORHUNT forensics
---

# کارت‌های رأی — شکار خطا 2026-08-16

کارت ۲ را نشست پایانی شب اجرا کرد (python.exe مطلق). چهارتای دیگر رأی می‌خواهند. اسنپ‌شات circuit روی دیسک دیگر دروغ نمی‌گوید (`half_open`).

| # | موضوع | اگر تأیید شود | اگر رد شود |
|---|---|---|---|
| 1 | پروب orchestr/Fugu | مدار را از مسیر زنده خارج کن یا سهمیه/کلید را درست کن — ۴۹× 429 در ۷ روز؛ `last_ok` ارکستر = 08-12 | بک‌آف 3600s؛ دیسک حالا half_open است (C-022 contained) |
| 2 | ~~Poisoning Watch FILE_NOT_FOUND~~ **انجام شد 13:04** | — | Watch LastResult=0. **بازمانده:** `OctopusLiveDataRefresh` = 2147942402؛ Execute Desktop درهم؛ bat = `F:\backup\nervous-system\refresh-live-data.bat` |
| 3 | سقف سوکت `reason` | `PAID_ASK_BUDGET_S_*` را با max_tokens فعلی هم‌تراز کن — ۳۶ هشدار reason تا 06:01 امروز | هشدار ادامه می‌یابد؛ تماس ممکن است بریده شود |
| 4 | `HF_TOKEN` | توکن اختیاری هاب برای دیمون (نام کلید فقط) تا هشدار unauth هر بوت نیاید | نویز INFO/WARNING هر بار بارگذاری MiniLM |
| 5 | هش کرنل body_bridge | manifest مورخ 2026-07-14 را برای `SENSITIVITY-LADDER.md` + `GEOMETRY.md` تازه کن، یا `integrity_ok=false` را به‌عنوان review دائمی بپذیر | daemon_state.kernel.integrity_ok=false می‌ماند (rsc.py و CLAIMS_LEDGER سالم‌اند) |
