# مگاپرامپت: اشباعِ مغزِ گران + بستنِ دنباله‌های باز — ۲۰۲۶-۰۷-۲۷

> این سند خودبسنده است. ایجنتِ اجراکننده هیچ دسترسی به چتِ قبلی ندارد و نباید فرض کند دارد.

## هویت و زمین

تو یک ایجنتِ ارشد روی vault ِ ابسیدینِ `F:\backup` هستی — یک ارگانیسمِ نرم‌افزاریِ زنده در `_ops/` که برای یک اپراتورِ تنها (فارسی‌زبان، سیدنی) کار می‌کند. قانونِ اساسی: `F:\backup\_PROJECT_INSTRUCTIONS.md` — اول آن را بخوان. برنچِ کار: `claude/octopus-event-bridge-aligned`.

**قیودِ سختِ تخطی‌ناپذیر** (خلاصهٔ قانونِ اساسی + رأی‌های ثابتِ مالک):
- هرگز حذف نکن؛ فقط منتقل کن. هرگز `.git` ، `_code` ، فایل‌های secret.
- secret (کلید/توکن/سید/پسورد) هرگز در چت/نوت/لاگ/commit نوشته نمی‌شود. `OCTOPUS-flags.cmd` را هرگز چاپ نکن — فقط حضورِ یک کلیدِ غیرسری را می‌توانی grep کنی.
- رفتارِ نو = افزودنی + flag-gated + پیش‌فرض خاموش. مسلح‌کردن فقط با رأیِ مالک.
- `git add -A` در ریشه **ممنوع** — فایل‌های `STOP-*` باید untracked بمانند؛ فقط مسیرِ صریح stage کن.
- مسیرهای PII (`08 - Partner`، `Identity/*`، `_ops/state/OWNER-PROFILE*`) را هرگز باز نکن؛ ونچرِ محتوایی را فقط «the venture» بنام.
- هیچ trading/سیگنال/مشاورهٔ مالی.
- ارگانیسم زنده است: `run_all` را وقتی بالاست نزن (`test_tg_power` فایلِ زندهٔ `STOP-ORGANISM` می‌سازد). تستِ تکی آزاد است.
- ویرایشِ `.cmd/.bat` با ابزارِ Edit خط‌ها را LF می‌کند و cmd خراب می‌پارسد — فقط با بایت‌نویسیِ `\r\n` (الگو در همین سند).
- قفلِ آنتی‌ویروس روی `.git/objects`: هر `git add/commit` را در حلقهٔ retry (تا ۶ بار، sleep 2) بزن.

## وضعِ فعلی (اندازه‌گیری‌شده، نه ادعا — ۲۰۲۶-۰۷-۲۷ ~۱۲:۳۰)

- **قلب بیدار است**: `daily_beat_cap` از راهِ knob ِ مالک (`organ_dialogue.heart_set_apply`) ۲۸۸→۲۰۰۰ شد؛ تیک ~۴۳ ثانیه، ۲۴ ساعته. setpoint در `state/pulse/heart-setpoint-latest.json` (epoch_seq=29) و از ری‌استارت جان به‌در می‌برد.
- **مصرفِ Fugu** (پلنِ فلت، `state/paid-calls.jsonl`): تا ظهر ~۲۲/۶۰. مشتری‌ها: governor ِ ساعتی (`tokens_in` ثابتِ ۱۲۲۴۲) + `deep_think` (۴ بازه/روز) + از ری‌استارتِ بعدی: لایهٔ عمیقِ improve و حلقهٔ self_patch.
- **commitهای امروز**: `970601b` (deep_think + قلب) و `ef99317` (مغزِ دوسطحی + حلقهٔ self_patch). هر دو روی برنچ.
- **فلگ‌های مسلح‌شده در `OCTOPUS-flags.cmd`** (gitignored؛ فقط سرِ بوت خوانده می‌شود): `OCTOPUS_WIRE_DEEP_THINK=1`، `DEEP_THINK_SLOTS=4`، `CORTEX_IMPROVE_DEEP=1`، `CORTEX_IMPROVE_DEEP_DAILY=2`، `OCTOPUS_WIRE_SELF_PATCH=1`.
- **پروسه‌های زنده**: `organism.py` (تیکِ اصلی)، `cortex\cortex.py` (**از ۰۷-۲۶ بوت شده — فلگ‌های تازه را ندارد**)، `telegram_center\center.py`، `live\server.py`.
- **دو bat ِ LF-خراب**: `_ops/RUN-CORTEX.bat` و `_ops/telegram_center/RUN-TG-CENTER.bat` — هر دو الان زیرِ cmd ِ زنده‌اند (تعمیر فقط وقتی اجرا نمی‌شوند).
- در صفِ self_patch یک نقصِ CONFIRMED باز است: `sp-482568c63c12` — ‏`action_graph.action_for_intent` برای intent ناشناخته به‌جای fail-closed به `mission.next` می‌رود.

## آنچه ساخته شد (تا تکرارش نکنی)

| قطعه | فایل | تست |
|---|---|---|
| جلساتِ فکرِ عمیق (۴/روز، دو موضوعِ مالک: «خودت را بساز» / «نقاشی را بساز») | `_ops/deep_think.py` + صدازدن در `organism.py` | `test_deep_think` ۱۶/۱۶ |
| لایهٔ عمیقِ حلقهٔ خودارتقایی (صفِ واقعیِ گاف‌ها → Fugu، سقفِ داخلیِ ۲/روز) | `_ops/cortex/improve.py` (`_deep_synth`) | `test_improve_deep` ۱۰/۱۰ |
| حلقهٔ خودپچ‌زنی: مرورِ کدِ خود (۱ فایل/روز) → صفِ نقص → پچ + سوییتِ ایزوله → کارت | `_ops/self_patch.py` + `_ops/cortex/code_autonomy.py` | `test_self_patch` ۲۶/۲۶، `test_code_autonomy` ۱۳/۱۳ |

الگوهای تثبیت‌شده که باید حفظ شوند: **اسلات/ردیف قبل از تماسِ گران می‌سوزد**؛ **tier="primary" همیشه پین** (وگرنه `CORTEX_LOCAL_FIRST` بی‌صدا به مدلِ رایگان می‌برد)؛ **جوابِ خارج از قرارداد دور انداخته می‌شود، حدس زده نمی‌شود**؛ **متنِ هر جلسهٔ گران در دفترِ jsonl می‌ماند**.

## مأموریت‌ها (به ترتیب؛ هر کدام مستقل commit شود)

### M1 — تعمیرِ دو bat ِ خراب (پیش‌نیازِ ری‌استارتِ cortex)
فقط وقتی که پروسه‌اش پایین است. مراحل: (۱) از مالک بخواه cortex را بخواباند (فایلِ `_ops/STOP-CORTEX` بساز — خروجِ تمیزِ خودِ حلقه است — بعد cmd ِ والدِ RUN-CORTEX را ببندد)؛ (۲) CRLF را با بایت‌نویسی برگردان:
```python
from pathlib import Path
p = Path(r"F:\backup\_ops\RUN-CORTEX.bat")
raw = p.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
p.write_bytes(raw)
```
(۳) همین برای `telegram_center/RUN-TG-CENTER.bat` وقتی center پایین است؛ (۴) `STOP-CORTEX` را پاک کن و مالک دوباره بالا بیاورد. **تا bat تعمیر نشده، cortex فلگِ `CORTEX_IMPROVE_DEEP` را نمی‌بیند.**

### M2 — راستی‌آزماییِ سه حلقهٔ تازه بعد از ری‌استارت‌ها (اثر، نه فلگ)
با پنجرهٔ زمانی و فایلِ اثر بسنج، نه با grep ِ لاگِ سبز:
- `state/deep-think/sessions.jsonl` — جلسهٔ تازه بعد از بوت؟
- `state/cortex/deep-synth.jsonl` + کلیدِ `deep_thought` در `state/cortex/upgrades-digest.json`؟
- `state/self-patch/review-state.json` تاریخِ امروز + در صورتِ نقص، ردیفِ تازه در `defect-queue.jsonl`؟
- `state/fugu-quota.json` — `used_total` باید متناسب بالا برود (سقف ۶۰). اگر به ۵۰+ رسید، به مالک بگو سقف را بالا ببرد یا کادنس را کم کن — خودت سقف را عوض نکن.

### M3 — سرنوشتِ نقصِ بازِ صف
`drive` خودش آن را برمی‌دارد (بعد از ری‌استارتِ organism). کارِ تو فقط ممیزی است: پچِ تولیدشده در `state/self-patch/sp-482568c63c12.json` را بخوان، diff را با چشمِ خودت با ادعا مطابقت بده، و اگر سبز و درست بود مطمئن شو کارتش به مالک رسیده (لاگِ `tg_send_log`). **خودت پچ را اعمال نکن** — اعمال کلیکِ مالک است.

### M4 — مصرف‌کنندهٔ جوابِ جلسات (حلقه را ببند)
سه دفترِ گران (`deep-think/sessions.jsonl`، `cortex/deep-synth.jsonl`، کارت‌های Fugu) الان فقط نوشته می‌شوند. یک قدمِ کوچکِ propose-only بساز: خواندنِ آخرین جلسه‌ها → اگر جوابِ جلسه یک نقصِ فایل‌دارِ داخلِ allowlist ِ `code_autonomy.allowed_target` را نام برد، آن را (با قراردادِ سختِ JSON، مثلِ `review_and_queue`) واردِ `defect-queue.jsonl` کن. flag ِ جدید، پیش‌فرض خاموش، تستِ متخاصم با کاناری. **هیچ اجرای خودکاری از متنِ جلسه ساخته نمی‌شود** — فقط صف.

### M5 — پیشنهادِ up-1363aae4df (رأیِ خودِ Fugu)
جلسهٔ عمیقِ اول با استدلالِ درست گفت: «اول متر — `measured_lift._default_eval` از stub به سنجشِ واقعیِ suite-delta در sandbox ارتقا یابد — بعد شیرِ merge». این را به‌عنوانِ کارِ کدِ عادی (نه از راهِ self_patch؛ فایلش خارج از allowlist است) انجام بده: eval واقعی + تستِ گلدن (تغییرِ خنثی → delta≈0، رگرسیونِ عمدی → delta<0). propose-only، flag-gated.

## گوچاهای عملیاتیِ گران‌قیمت
- `model_router.ask(task, prompt, ...)` — ‏`task` پوزیشنالِ اول است؛ keyword-call ِ اشتباه TypeError ِ «مغزِ خراب‌نما» می‌دهد.
- تست‌ها یک-پروسه-هرکدام؛ دو `run_all` موازی flaky. تستِ جدید را با پیشوندِ درستِ فایلش جمع کن (`t_*` در فایل‌های harness ِ این سبک؛ `test_*` جمع نمی‌شود).
- `REAL_VAULT` پیش‌فرض = درختِ زنده؛ در تست همیشه `harness.setup()`.
- خروجیِ grep-شده حکم نیست — exit code یا شمارِ صریحِ pass/fail بگیر.
- `ORGANISM-STATE.json` کلیدِ `started` را با تأخیر می‌نویسد؛ بوتِ واقعی را از `Get-Process` بگیر نه از state.
- بوتِ ارگانیسم ~۴ دقیقه طول می‌کشد؛ سکوتِ اولِ بعد از ری‌استارت خرابی نیست.

## معیارِ پایان
هر ۵ مأموریت commit-شده (پیام‌ها انگلیسی و روایت‌گر، مثلِ `ef99317`)، سوییت‌های لمس‌شده exit=0، هیچ فلگی بدونِ رأیِ مالک مسلح نشده، و یک گزارشِ فارسیِ کوتاه برای مالک: چه شد، چه اثری اندازه‌گیری شد، چه تصمیم‌هایی مانده.
