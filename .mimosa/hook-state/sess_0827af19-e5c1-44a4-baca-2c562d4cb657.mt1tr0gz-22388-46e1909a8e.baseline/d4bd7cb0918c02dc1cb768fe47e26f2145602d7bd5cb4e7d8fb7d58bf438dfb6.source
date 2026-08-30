# HANDOFF — دکترِ اختاپوس، ۲۵ جولای ۲۰۲۶

مرجعِ کاملِ جلسه‌ای که حلقهٔ خودیادگیری و مغزهای پولی را تعمیر کرد.
ایجنتِ بعدی: **اول این را کامل بخوان، بعد دست به کد ببر.**

---

## ۰. یک‌خطی

ارگانیسم زنده است، سوئیت **۲۸۹/۲۸۹** سبز، ۱۰ فیکس روی دو کامیتِ برگشت‌پذیر
(`a05f74e` و `482048b`) نشسته و در بدنِ زنده تأیید شده. سه کارِ باقی‌مانده هست که
دو تایش طراحیِ آماده دارد و یکی‌اش رأیِ مالک می‌خواهد.

## ۱. وضعیتِ راستی‌آزمایی‌شده (ادعا نکن، اینها سنجیده شده‌اند)

* برنچِ زنده: `claude/octopus-event-bridge-aligned`. تگِ برگشتِ deploy: `pre-deploy-2026-07-25`.
* سه پروسه زنده: `organism.py` · `cortex/cortex.py` (پورت ۸۷۷۲) · `live/server.py` (پورت ۸۷۷۳).
* هر ۴ واچ‌داگ `Ready`. `_ops/STOP-ORGANISM` وجود ندارد (ارگانیسم مسلح است).
* **GLM و Fugu واقعاً کار می‌کنند** — نه ادعا، شاهدِ روی دیسک:
  `_ops/state/paid-calls.jsonl` → `tier=primary, model=fugu, tokens 102/18, ms=4265`
  و `_ops/state/fugu-quota.json` → `used_total: 1` از سقفِ ۶۰.
* مناظره دیگر stub نیست: ledger قبل `topic=seed-3, verdict=pass, stub=true` →
  بعد `topic=plan-0, verdict=kill, stub=false, tier=local`.
* ژورنالِ کورتکس دیگر خودش را نقض نمی‌کند: `jschema: cortex-journal.v2` با
  `aligned=True` کنارِ `align_reason="هم‌راستا بود"`.

## ۲. چه چیزی تعمیر شد (تا دوباره نکَنی‌اش)

| کد | نقص | فیکس |
|---|---|---|
| W1 | خاطره در `episodic` نوشته می‌شد ولی تنها خواننده (`lead_outcome_recorder.py:66`) فقط `semantic` را search می‌کند | مسیر از `learning_gate` رد می‌شود؛ فلگ `OCTOPUS_WIRE_LEARN_FROM_LEAD` (روشن) |
| W2 | `maturity_pct` روی ۷۵.۶ یخ‌زده (۱۷ از ۴۳ بند ساختاراً هرگز `Done` نمی‌شوند) | `improve.improvement_rate()` از `state/cortex/outcomes.jsonl` — الان ۴۵.۱٪ |
| W3 | ژورنال هر چرخه `aligned:false` کنارِ «هم‌راستا بود» می‌نوشت | `align_work_plan` دو واقعیتِ جدا برمی‌گرداند؛ رکوردهای نو با `jschema` تفکیک |
| W4 | مناظره ۶۳/۶۳ stub روی یک موضوعِ ثابت | transportِ مغزِ محلی + `topics.next_topic`؛ فلگ `OCTOPUS_WIRE_DEBATE_LOCAL` (روشن) |
| W6 | ادعای propose-only بودنِ C6 تست نداشت | `tests/test_c6_trigger_propose_only.py` |
| W7 | ۷۰ کارتِ RFC بی‌صدا مردند (`OCTOPUS_CB_SECRET` نیست → توکن mint نمی‌شود) | `DOCTOR_SUBMIT_BLOCKED` + هشدار + وضعیتِ `submitted-no-channel` که خودترمیم می‌شود |
| B2 | لِینِ «پولیِ» `llm_learn` را qwen جواب می‌داد | `synthesis` حالا `tier` می‌گیرد؛ `work_pump` صریحاً `primary` می‌فرستد |
| B4 | هیچ اثری از تماسِ پولی روی دیسک نبود + تستِ Fugu LIVE سبزِ دروغ بود | `state/paid-calls.jsonl` + `PAID_HTTP_TIMEOUT_S=45` + `PAID_ASK_BUDGET_S=90` + فیکسِ aliasِ کلید |
| C1 | بنچِ C6 خودش را تأیید می‌کرد (`baseline_ms=5.0` هاردکدِ خودِ فرضیه) | بنچِ جفت‌شدهٔ A/B، baselineِ اندازه‌گیری‌شده، gc خاموش، کنترلِ A/A، ادعای مکانیزمی |

فلگ‌های افزوده‌شده به `_ops/OCTOPUS-flags.cmd`: `OCTOPUS_WIRE_LEARN_FROM_LEAD=1`،
`OCTOPUS_WIRE_DEBATE_LOCAL=1`، `OCTOPUS_WIRE_C6_RESEARCH=1`، `FUGU_DAILY_CALL_CAP=60`.

## ۳. کارِ باقی‌مانده — به ترتیبِ اولویت

### الف) C2 — تولیدکنندهٔ فرضیهٔ C6 (بزرگ‌ترین شکاف)
بدونش C6 **یک‌بارمصرف** است: `seed_default_hypothesis` بعد از اولین ردیف دیگر seed نمی‌کند و
هیچ‌جای ریپو به `state/c6/hypothesis-queue.jsonl` نمی‌نویسد → از روز دوم برای همیشه
`{"ran": false, "reason": "no-pending-hypothesis"}`.
**طراحیِ کاملِ آماده (لنگر + کد + تست):** `_program-deliverables/C6-substance-2026-07-25/C2-hypothesis-producer-DESIGN.md`
نکتهٔ صداقت که در طراحی هست و باید حفظ شود: صفِ خالی شرافتمندانه است؛ فرضیهٔ ساختگی همان
سبزِ دروغی است که این جلسه کَند.
همچنین باگِ `_mark_hypothesis` (هر ردیفِ `RUNNING` را می‌بندد نه فقط idِ منطبق) در همان سند فیکس شده.

### ب) C3 — جعلِ اعتمادِ مالک
`research_loop.py:363-373` ردیفِ outcome را **خودش** می‌نویسد و بعد
`trust: OWNER_CONFIRMED, source: owner` اعلام می‌کند بدونِ هیچ مالکی. امروز مهار شده چون
`namespace=semantic` به committerِ `scrub_salience_bar` می‌رود و trust را به `GRADED` تنزل می‌دهد —
ولی `memory/gate.py:168` می‌گوید `if source == "owner": return "OWNER_CONFIRMED"`، پس با تغییرِ
namespace به `procedural`/`owner_fact` قفل باز می‌شود.
**طراحیِ آماده:** `_program-deliverables/C6-substance-2026-07-25/C3-owner-trust-forgery-DESIGN.md`
هشدار: امضای `_verify_outcome` از ۲-تاپل به ۳-تاپل می‌رود؛ هر دو callerِ مشروع
(`verdict_recorder.py:165` و مسیرِ لید) باید هم‌زمان به‌روز شوند.

### ج) گاورنر به مغزِ پولی وصل نیست
لاگِ زنده: `governor llm epoch failed (fallback به dry): DEEPSEEK_API_KEY تنظیم نیست`.
`governor_epoch.py` مستقیم سراغِ DeepSeek می‌رود (کلید ندارد) به‌جای روتر. فلگِ
`OCTOPUS_GOVERNOR_USE_ROUTER` در کد هست ولی در `OCTOPUS-flags.cmd` نیست. همین برای
`OCTOPUS_HEART_DOCTOR_USE_ROUTER` و `OCTOPUS_DOCTOR_SELFKNOW_PAID` هم صادق است.
**این تصمیمِ مصرفِ سهمیه و خروجِ داده است — بدونِ رأیِ صریحِ مالک روشن نکن.**

### د) دو کلیدی که فقط مالک می‌زند (ایجنت هرگز)
1. `_ops/ACTIVATION-C6-RESEARCH.flag` — گیتِ دومِ C6. تا ساخته نشود `flag_on()` همیشه `False`.
2. `OCTOPUS_CB_SECRET` — بدونش هیچ کارتِ دکمه‌داری mint نمی‌شود و **هیچ رأیی وارد سیستم نمی‌شود**
   (`rfc_decision` هنوز صفر ردیف دارد). راز را ایجنت نه می‌سازد نه می‌نویسد.

## ۴. قوانینِ سختِ این ریپو

* **درختِ زنده است.** سه پروسهٔ در حالِ اجرا کد را از دیسک می‌خوانند. نوشتنِ موازیِ چند ایجنت روی
  `F:\backup` ممنوع. تشخیص را موازی بفرست، اعمال را خودت سریالی بزن.
* هر رفتارِ نو: **additive، flag-gated (پیش‌فرض خاموش)، fail-soft** — استثنا هرگز تیک را نکشد.
  `flag(name)` یعنی `os.environ.get(name, "0") == "1"` (`wiring.py:30`).
* `OCTOPUS-flags.cmd` **توکنِ زنده دارد**: هرگز dump/tail/echo نکن. فقط بایت‌محور و با حفظِ CRLF
  ویرایش کن (ابزارِ Edit فایلِ `.cmd` را به LF می‌برد و batch را خراب می‌کند).
* هرگز حذف نکن؛ منتقل کن (`_Duplicates` / `_Archive`). `git clean` ممنوع.
* ارسالِ بیرونی و اعمالِ کد **owner-gated** است. C6 ساختاراً propose-only است و تست قفلش کرده —
  نشکنش.
* سوئیت: `python -X utf8 F:\backup\_ops\tests\run_all.py` (هر فایل یک پروسه). قبل از commit سبز باشد.

## ۵. گوچاهایی که این جلسه هزینه داد

* **«نبودِ ❌» یعنی سبز نیست.** یک‌بار گزارش دادم دو فایل «کاملاً سبز شد» در حالی که پچ اصلاً اجرا
  نشده بود و `ModuleNotFoundError` خورده بود. همیشه شمارِ صریحِ pass/fail یا exit code بگیر.
* **ادعای «unwired» را با reachability بسنج، نه grep در چند فایلِ منتخب.** ادعای من که
  `learning_gate` وصل نیست غلط بود؛ وصل بود و فقط تقاضا صفر بود.
* **`cost_usd` در پلنِ فلت ساختاراً صفر است** (`subscription: max` ⇒ `est_worst_case()=0`). پس
  «خرجِ صفر» هرگز مدرکِ «استفاده نشده» نیست. شاهدِ واقعی: `paid-calls.jsonl` و `fugu-quota.json`.
* **ساعتِ ledger ‏UTC است و ساعتِ سیستم ‎+10:00 سیدنی.** قبل از «کهنه است» ۱۰ ساعت اختلاف را بسنج.
* گاردهای متنیِ «ابتداییِ ممنوع» باید مرزِ واژه داشته باشند وگرنه `held_out_eval(` را `eval(` می‌خوانند.
* قفلِ آنتی‌ویروس روی `.git/objects` برمی‌گردد؛ `git add/commit` را در حلقهٔ retry بزن.
* تست‌های wiring درختِ **زنده** را می‌خوانند: با حضورِ `STOP-ORGANISM` قرمز می‌شوند. آن قرمزی
  رگرسیون نیست.

## ۶. راستی‌آزمایی که باید بعد از هر تغییر بزنی

```powershell
python -X utf8 "F:\backup\_ops\tests\run_all.py"                      # باید 289/289 یا بیشتر باشد
Get-Content "F:\backup\_ops\state\paid-calls.jsonl" -Tail 3           # مغزِ پولی واقعاً کار کرد؟
Get-Content "F:\backup\07 - Knowledge\genome-system\ledger\ledger.jsonl" -Tail 5
Get-Content "F:\backup\_ops\governor\governor-alerts.md" -Tail 5      # ارگانیسم از چه می‌نالد؟
```
