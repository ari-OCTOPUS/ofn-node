# برنامهٔ اجرایی یک‌جلسه‌ای برای ایجنت بعدی — C2 + C3 + مغزهای پولیِ تاریک

**تاریخ:** 2026-07-25  
**حکم مالک در پیام آخر:** ایجنت بعدی هر سه کار باقی‌مانده را در **یک جلسه** انجام دهد. این حکم اجازهٔ اعمال کدهای همین سند را می‌دهد؛ **اجازهٔ فعال‌سازی، ارسال بیرونی، مصرف سهمیه یا deploy نمی‌دهد**.

---

## 0) نتیجهٔ مطلوب جلسه

در یک نشست، به همین ترتیب:

1. **C2:** تولیدکنندهٔ صادقِ فرضیهٔ C6، رفع over-marking، id-backfill، reaper و پشتیبانی از `mechanism_count`.
2. **C3:** بستن جعل `OWNER_CONFIRMED` و `source=owner` بدون گواهیِ مالک؛ مسیر واقعی رأی مالک سالم بماند.
3. **مغزهای پولی:** مسیرهای router موجود را با تست قفل کن و چهار فلگ را در `OCTOPUS-flags.cmd` به‌صورت **صریحاً صفر** ثبت کن؛ هیچ‌کدام روشن نشود.
4. سه commit مستقل و قابل برگشت؛ پیش از **هر** commit کل suite با exit code صفر.

**انتظار شمار تست‌ها:** خط پایه 289 فایل است. با سه تست جدید این برنامه، انتظار نهایی **292 فایل تست سبز** است. اگر تعداد واقعی فرق کرد، شمار چاپ‌شدهٔ `run_all.py` و exit code حقیقت نهایی است؛ حدس نزن.

---

## 1) مرزهای غیرقابل مذاکره

- سه پروسهٔ زنده کد را از دیسک می‌خوانند؛ فقط یک نویسنده روی `F:\backup`.
- نوشتن سریالی؛ تشخیصِ read-only می‌تواند موازی باشد.
- حذف ممنوع؛ `git clean` ممنوع؛ فایل را فقط منتقل/آرشیو کن.
- هیچ restart/deploy/send/provider-call در این جلسه.
- هر رفتار جدید additive، پیش‌فرض خاموش و fail-soft؛ استثنا tick را نکشد.
- هرگز `_ops/ACTIVATION-C6-RESEARCH.flag` را نساز.
- هرگز `OCTOPUS_CB_SECRET` را نساز/تغییر نده.
- C6 باید propose-only بماند؛ `_ops/tests/test_c6_trigger_propose_only.py:1-82` مرز را قفل کرده است.
- `OCTOPUS-flags.cmd` توکن زنده دارد: **هرگز type/Get-Content/cat/dump/tail/echo نکن**. فقط `read_bytes/write_bytes`، بدون چاپ محتوا، با حفظ CRLF.
- چهار فلگ این جلسه باید صفر بمانند:
  - `OCTOPUS_WIRE_C6_PRODUCER=0`
  - `OCTOPUS_GOVERNOR_USE_ROUTER=0`
  - `OCTOPUS_HEART_DOCTOR_USE_ROUTER=0`
  - `OCTOPUS_DOCTOR_SELFKNOW_PAID=0`
- `OCTOPUS_WIRE_C6_RESEARCH` و هر activation موجود را دست نزن.

---

## 2) شاهدهای فعلی که باید پیش از ویرایش دوباره با `rg -n` ثبت شوند

1. صف C6 فقط مصرف می‌شود: `_ops/c6_trigger.py` پس از import مستقیم `_pop_next_hypothesis()` را می‌زند و در نبود ردیف `no-pending-hypothesis` می‌دهد؛ فعلاً producer ندارد.
2. فساد صف: `_ops/c6_trigger.py` در `_mark_hypothesis` شرط فعلی دارد:
   `d.get("id") == hid or d.get("status") == "RUNNING"`؛ پس RUNNING نامرتبط را می‌بندد.
3. **طراحی C2 نسبت به کد زنده کمی قدیمی است:**
   - طراحی، `_derive_fns` را دوخروجی فرض کرده؛ کد زنده پس از C1 سه خروجی می‌دهد: `experiment_fn, verifier_fn, box`.
   - طراحی، `_mark_hypothesis` را سه‌آرگومانی فرض کرده؛ کد زنده آرگومان چهارم `requeue=False` دارد.
   - بنابراین snippetها را کورکورانه paste نکن؛ C1 را حفظ کن.
4. جعل C3 در `_ops/outcomes/research_loop.py:362-373`: outcome خودنوشته و سپس `trust="OWNER_CONFIRMED"`, `source="owner"`.
5. اعطای اعتماد از رشته در `_ops/memory/gate.py:164-171`: `source == "owner"` مستقیماً commitِ `OWNER_CONFIRMED` می‌دهد.
6. گواهی canonical رأی واقعی از قبل وجود دارد: `_ops/outcomes/verdict_recorder.py:76-81` ردیف را با `verdict="measurement"` و `payload.owner_verdict_raw` می‌نویسد.
7. `OutcomeStore` هر دو ستون لازم را ذخیره می‌کند: `_ops/outcomes/outcome_store.py:76-105` شامل `verdict` و `payload_json` است.
8. سه مسیر پولی از قبل در کد آماده‌اند:
   - Governor: `_ops/budget/governor_epoch.py`، شاخهٔ `OCTOPUS_GOVERNOR_USE_ROUTER` داخل `allocate_llm`.
   - Heart doctor: `_ops/heart/doctor_setpoint.py`، شاخهٔ `OCTOPUS_HEART_DOCTOR_USE_ROUTER` داخل `llm_refine`.
   - Doctor self-knowledge: `_ops/doctor/self_knowledge.py:34-36` و `_ask_llm`؛ `OCTOPUS_DOCTOR_SELFKNOW_PAID` فقط task را از `think` به `synthesize` می‌برد.
9. تست موجود self-knowledge رفتار تاریک را اثبات می‌کند: `_ops/tests/test_doctor_selfknowledge.py` در `t_ask_llm_local_by_default`، نبود فلگ=`think` و مقدار 1=`synthesize`.

فرمان‌های تشخیص پیشنهادی (فقط کد؛ نه فایل flags):

```powershell
rg -n "_pop_next_hypothesis|_derive_fns|_mark_hypothesis|seed_default_hypothesis" F:\backup\_ops\c6_trigger.py
rg -n "OWNER_CONFIRMED|source.*owner|_verify_outcome|learn_from_outcome" F:\backup\_ops\outcomes F:\backup\_ops\memory F:\backup\_ops\wiring.py
rg -n "OCTOPUS_GOVERNOR_USE_ROUTER|OCTOPUS_HEART_DOCTOR_USE_ROUTER|OCTOPUS_DOCTOR_SELFKNOW_PAID" F:\backup\_ops --glob "*.py"
```

---

## 3) فاز صفر — تریاژ و baseline

1. کامل بخوان:
   - `F:\backup\SESSION-HANDOFF-2026-07-25-octopus-doctor.md`
   - `...\C2-hypothesis-producer-DESIGN.md`
   - `...\C3-owner-trust-forgery-DESIGN.md`
   - همین سند.
2. `git status --short --branch` و `git log -5 --oneline`؛ انتظار commitهای مبنا `a05f74e` و `482048b` در ancestry.
3. اگر تغییر ناشناخته در فایل‌های scope وجود داشت، **توقف و سؤال**؛ stash/reset/clean ممنوع.
4. سلامت پروسه‌ها و پورت‌های 8772/8773 را ثبت کن، بدون restart.
5. baseline کامل:

```powershell
python -X utf8 "F:\backup\_ops\tests\run_all.py"
$LASTEXITCODE
```

معیار شروع: چاپ صریح `✅ همهٔ 289 فایل تست سبز` و exit code `0`. نبودن `❌` مدرک نیست.

---

# 4) فاز C2 — تولیدکنندهٔ فرضیهٔ C6

مرجع اصلی: `C2-hypothesis-producer-DESIGN.md`. شش فایل آن طراحی را بساز/ویرایش کن، اما ادغام با C1 مطابق این بخش باشد.

## 4.1 فایل جدید `_ops/c6_probes.py`

- رجیستری probeهای read-only، آفلاین، $0 و شمارشی.
- `measure() -> {count:int, detail:str}`.
- خطا یا عدم قطعیت = `count=-1`؛ هرگز hypothesis نسازد.
- فقط `count > floor` نقص واقعی است.
- دو probe طراحی را پیاده کن:
  - `self_audit_redundant_reads`
  - `rfc_duplicate_surplus`
- wrapperهای `_read/_grep` در `finally` برگردند و زیر lock باشند.
- علامت `+` ابتدای خط docstring در متن طراحی diff-marker است؛ آن را وارد فایل نکن.
- هیچ network/subprocess/effect primitive.

## 4.2 فایل جدید `_ops/c6_producer.py`

- فلگ `OCTOPUS_WIRE_C6_PRODUCER`، default OFF.
- قبل از هر measurement، سقف pending و row را بسنج.
- id محتوامحور: `sha256(probe|subject)`؛ با **تمام** ردیف‌ها dedupe، شامل DONE/ABANDONED.
- فقط producer append می‌کند؛ lifecycle فعلی C6 برای تغییر status همان فایل را بازنویسی می‌کند—ادعای append-only را فقط دربارهٔ تولید ردیف تازه بنویس، نه کل queue.
- schema کامل برای `research_contract.make_contract(c6._build_contract(row))`.
- queue خالی نتیجهٔ سالم است؛ هیچ fallback فرضیه‌ای تولید نکن.
- هر خطا alert + خروج نرم، بدون raise.

## 4.3 ادغام دقیق در `_ops/c6_trigger.py`

### الف) pop/reaper/id

- `calendar` و `hashlib` اضافه شود.
- `RUNNING` قدیمی‌تر از `C6_RUNNING_STALE_H` (default 48h) → `ABANDONED`، بدون `verdict`.
- UTC را با `calendar.timegm` بخوان؛ ساعت سیستم سیدنی است.
- PENDING بی‌id هنگام pop، id محتوامحور بگیرد.
- malformed line حفظ شود.

### ب) producer

- در `c6_research_beat`، پس از importهای اصلی و **پیش از pop**، `c6_producer.produce(queue=QUEUE)` داخل try/except fail-soft.
- producer فقط به فلگ خودش پاسخ دهد؛ C6 همچنان env + activation file را لازم دارد.

### ج) early close

- contract-invalid و run-failed ردیف همان id را ببندند.
- هیچ RUNNING نامرتبط لمس نشود.

### د) `_mark_hypothesis`

- امضای فعلی چهارآرگومانی و منطق `requeue/MAX_ATTEMPTS` را حفظ کن.
- تنها شرط مجاز: `if hid and d.get("id") == hid:`.
- fallback به contract id حذف شود چون pop اکنون id را تضمین می‌کند.

### هـ) `mechanism_count` با حفظ C1

**این مهم‌ترین adaptation نسبت به طراحی قدیمی است.** `_derive_fns` باید همچنان سه خروجی برگرداند.

- شاخهٔ `mechanism_count` باید برگرداند:
  `experiment_fn, verifier_fn, box`.
- experiment همان probe ثبت‌شده را دوباره می‌سنجد و `box["bench"]` را پر می‌کند.
- verifier:
  - `measured > floor` → defect reproduced / supported.
  - `measured <= floor` و `measured >= 0` → falsified.
  - `measured < 0` → unsupported **و inconclusive**؛ `box["accept"]` طوری پر شود که requeue فعلی تا `MAX_ATTEMPTS` کار کند.
- `benchmark_gain` را برخلاف snippet قدیمی count خام نگذار. C1 در `_ops/c6_trigger.py` gain را عمداً بی‌بعد و 0..1 کرده است. برای mechanism count از نسبت کران‌دار استفاده کن، مثلاً:
  `max(0, min(1, (measured-floor)/max(measured,1)))`.
- risk حداقل 0.1 بماند.
- `_summarize` برای `kind=mechanism_count` صریح بگوید «نقص بازتولید شد/نشد»، baseline count، measured count، floor، unit و detail؛ آن را «بهبود انجام‌شده» معرفی نکند.
- شاخهٔ `micro_benchmark` و تمام معیارهای C1 بایت‌معنا حفظ شوند.

### و) seed

- وقتی `OCTOPUS_WIRE_C6_PRODUCER` روشن است، `seed_default_hypothesis()` باید `False` بدهد و هیچ seed نسازد.
- وقتی فلگ خاموش است رفتار فعلی unchanged.
- فایل activation را این جلسه نساز و فلگ را 1 نکن.

## 4.4 تست C2

فایل جدید `_ops/tests/test_c6_hypothesis_producer.py` مطابق طراحی، با این اصلاح‌ها:

- سه‌خروجی: `_ef, _vf, _box = c6._derive_fns(...)`.
- تست inconclusiveِ `measured=-1` و پرشدن box/requeue semantics.
- تست gain در بازهٔ `[0,1]`.
- تست `_mark_hypothesis` با آرگومان `requeue` و حفظ رفتار retry.
- هیچ probe واقعی در suite اجرا نشود.
- `test_c6_trigger_propose_only.py` اسکن دو فایل جدید را هم شامل شود.
- در `run_all.py` ثبت شود.

## 4.5 راستی‌آزمایی و commit C2

```powershell
python -X utf8 "F:\backup\_ops\tests\test_c6_hypothesis_producer.py"
python -X utf8 "F:\backup\_ops\tests\test_c6_trigger_propose_only.py"
python -X utf8 "F:\backup\_ops\tests\test_c6_bench_honesty.py"
python -X utf8 "F:\backup\_ops\tests\run_all.py"
$LASTEXITCODE
```

انتظار full suite: **290/290، exit 0**. سپس فقط فایل‌های C2 را stage و commit:

`fix(c6): add honest hypothesis producer and id-safe queue lifecycle`

---

# 5) فاز C3 — جلوگیری از جعل اعتماد مالک

مرجع اصلی: `C3-owner-trust-forgery-DESIGN.md`.

## 5.1 `_ops/outcomes/learning_gate.py`

- ثابت‌ها:
  - `_OWNER_ATTEST_KEY = "owner_verdict_raw"`
  - `_OWNER_ATTEST_VERDICT = "measurement"`
  - `_UNATTESTED_SOURCE = "unattested_owner_claim"`
- `_owner_attested(row)` فقط وقتی true باشد که:
  - event type=`accepted-measurement`
  - ستون verdict=`measurement`
  - payload JSON دارای owner_verdict_raw غیرخالی باشد.
- `_verify_outcome` از 2-tuple به `(ok, owner_attested, why)` تغییر کند و SELECT سه ستون بزند.
- **تمام unpackerهای واقعی `_verify_outcome` را با `rg -n` پیدا و هم‌زمان اصلاح کن**؛ به شمارِ نوشته‌شده در طراحی اعتماد نکن.
- در `learn_from_outcome`:
  - trust ادعایی را `declared_trust` نگه دار.
  - بدون attestation، `OWNER_CONFIRMED` را به `GRADED` cap کن.
  - بدون attestation، `source=owner` را به `unattested_owner_claim` تبدیل کن.
  - receipt، trust اعطاشدهٔ gate و claim اولیه را جدا ثبت کند.
  - خروجی telemetry شامل `trust`, `trust_declared`, `owner_claim_unattested` باشد.
- fail-soft/fail-closed فعلی حفظ شود.

## 5.2 `_ops/memory/gate.py`

- defense-in-depth طراحی را اضافه کن: `_OWNER_PRODUCERS` و `_owner_source_ok`.
- producer خودکار با `source=owner` نتواند owner-only namespace را commit کند.
- سازگاری legacy بدون producer مطابق طراحی حفظ شود؛ این لایه authentication رمزنگاری‌شده نیست و در گزارش نهایی چنین ادعایی نکن.

## 5.3 `_ops/outcomes/research_loop.py`

- outcome خودنوشته را با payload صادقانه علامت بزن:
  `self_run=True`, `measurement_only=True`, verifier و held-out.
- signal را به:
  - `trust="GRADED"`
  - `source="research_loop"`
  - `producer="research_loop"`
  تغییر بده.
- namespace فعلاً `semantic` بماند؛ انتقال به `self_claim` خارج از رأی این جلسه است.

## 5.4 callerهای مشروع

با `rg -n "learn_from_outcome\("` تمام callerها را audit کن:

- رأی واقعی مالک در `verdict_recorder.py` باید همان ردیف canonical دارای attestation را مصرف کند و همچنان در owner-only test، `OWNER_CONFIRMED` بگیرد.
- مسیر lead که `DETERMINISTIC`/delivered ادعا می‌کند نباید owner attestation لازم داشته باشد.
- هیچ caller خودکاری نباید `source=owner` بفرستد.

## 5.5 تست C3

- فایل جدید `_ops/tests/test_c3_owner_trust_forgery.py` از طراحی ساخته شود.
- fixture `_ops/tests/test_learning_loop.py` به جای outcome دستی جعلی، از `verdict_recorder.record_owner_verdict` استفاده کند.
- تست‌های الزامی:
  1. research_loop با source/trust جعلی owner_fact نمی‌سازد.
  2. claim بی‌گواهی در semantic به GRADED cap و در receipt ممیزی می‌شود.
  3. مسیر واقعی owner tap در owner_fact همچنان OWNER_CONFIRMED است.
  4. کلید attestation در کد production تنها یک writer canonical دارد.
  5. defense-in-depth مستقیم: `producer=research_loop, source=owner, namespace=owner_fact` در `MemoryGate` commit نمی‌شود.
- در `run_all.py` ثبت شود.

## 5.6 راستی‌آزمایی و commit C3

```powershell
$tests = @(
  'test_c3_owner_trust_forgery.py','test_learning_loop.py','test_research_loop.py',
  'test_memory_gate.py','test_lead_learning_wire.py','test_verdict_outcome.py',
  'test_paper_lead_mvo_e2e.py'
)
$tests | ForEach-Object {
  python -X utf8 (Join-Path 'F:\backup\_ops\tests' $_)
  if ($LASTEXITCODE -ne 0) { throw "failed: $_" }
}
python -X utf8 "F:\backup\_ops\tests\run_all.py"
$LASTEXITCODE
```

انتظار full suite: **291/291، exit 0**. سپس فقط فایل‌های C3 را stage و commit:

`fix(memory): derive owner trust from durable attestation`

---

# 6) فاز مغزهای پولی — آماده ولی خاموش

## 6.1 اصل کار

شاخه‌های router از قبل وجود دارند؛ آن‌ها را دوباره طراحی نکن. کار این فاز:

1. reachability و fail-soft را با تست hermetic قفل کن.
2. فلگ‌ها را به‌صورت صریح 0 ثبت کن.
3. هیچ live provider test نزن.

## 6.2 تست جدید `_ops/tests/test_paid_router_dark_config.py`

تست باید آفلاین و بدون شبکه باشد:

- **Governor**
  - با live gate بسته، `allocate_llm` → `None` و router صدا نخورد.
  - با gate تستی باز + `OCTOPUS_GOVERNOR_USE_ROUTER=1` + `model_router/client` جعلی، فقط router صدا بخورد؛ DeepSeek client instantiate/complete نشود.
  - router error → `None`، بدون raise.
- **Heart doctor**
  - gate بسته → `None`.
  - gate تستی باز + `OCTOPUS_HEART_DOCTOR_USE_ROUTER=1` + router جعلی → suggestion parse شود؛ مسیر direct صدا نخورد.
  - router error → deterministic fallback (`None`) بدون raise.
- **Doctor self-knowledge**
  - نبود/صفر paid flag → task=`think`.
  - 1 فقط در تست با router جعلی → task=`synthesize`.
- **ساختاری**
  - هر سه نام فلگ در sourceهای مربوط حاضر باشند.
  - `OCTOPUS-flags.cmd` فقط به‌صورت bytes خوانده شود؛ محتوا چاپ نشود؛ چهار کلید هدف دقیقاً مقدار 0 داشته باشند.
  - CRLF invariant: هیچ lone-LF ایجاد نشده باشد.
- تست را در `run_all.py` ثبت کن.

## 6.3 ویرایش امن `OCTOPUS-flags.cmd`

فقط یک بار، پس از آماده‌شدن تست، با Python byte script:

1. `read_bytes()`.
2. hash/size و وجود CRLF را در متغیر نگه دار؛ **هیچ line/value دیگری چاپ نکن**.
3. فقط چهار key هدف را scan کن.
4. اگر هر key از قبل مقدار 1 یا مقدار غیرمنتظره دارد، توقف و از مالک بپرس؛ آن را بی‌اجازه خاموش/بازنویسی نکن.
5. keyهای غایب را با style موجود و CRLF اضافه کن، همه `=0`.
6. `write_bytes()`.
7. دوباره assert کن:
   - چهار key دقیقاً یک بار؛
   - همه 0؛
   - no lone-LF؛
   - هیچ بایت نامرتبط تغییر نکرده جز بلوک افزوده/خط هدف.
8. در خروجی فقط status نام چهار key، byte count و CRLF check را چاپ کن؛ نه فایل را.

**هیچ‌کدام را 1 نکن.** وجود `ACTIVATION-HEART-DOCTOR.flag` یا `ACTIVATION-GOVERNOR-LLM.flag` اجازهٔ router/paid نیست؛ فلگ 0 باید مسیر جدید را تاریک نگه دارد.

## 6.4 راستی‌آزمایی و commit سوم

```powershell
python -X utf8 "F:\backup\_ops\tests\test_paid_router_dark_config.py"
python -X utf8 "F:\backup\_ops\tests\test_epoch.py"
python -X utf8 "F:\backup\_ops\tests\test_doctor_selfknowledge.py"
python -X utf8 "F:\backup\_ops\tests\test_heart_control.py"
python -X utf8 "F:\backup\_ops\tests\run_all.py"
$LASTEXITCODE
```

انتظار full suite: **292/292، exit 0**. سپس commit:

`chore(llm): lock router paths behind explicit dark flags`

این commit فقط تست، ثبت run_all و byte-safe تغییر flags را داشته باشد؛ اگر کد production router واقعاً به اصلاح لازم نداشت، برای بزرگ‌کردن diff دستش نزن.

---

# 7) بازبینی نهایی همان جلسه

1. `git status --short`؛ فقط تغییرات مورد انتظار یا clean.
2. `git log -3 --oneline`؛ سه commit مستقل.
3. `git diff <base>..HEAD --check`.
4. دوباره مرز propose-only:

```powershell
python -X utf8 "F:\backup\_ops\tests\test_c6_trigger_propose_only.py"
```

5. اثبات تاریکی بدون خواندن فایل flags:
   - خروجی تست `test_paid_router_dark_config.py`؛
   - چهار key هدف =0؛
   - activation C6 ساخته نشده؛
   - secret ساخته نشده.
6. سلامت سه پروسه و پورت‌ها را دوباره ثبت کن؛ restart نکن.
7. اگر ledger تماس پولی را مشاهده کردی، فقط با `_ops/state/paid-calls.jsonl` و `fugu-quota.json` و با اختلاف UTC/+10 تحلیل کن؛ `cost_usd=0` مدرکِ عدم تماس نیست. به‌علت هم‌زمانی ارگانیسم، call تازه را بدون correlation به تغییرات این جلسه نسبت نده.
8. rollback آماده، اجرا نشود:

```powershell
git revert <router-dark-commit>
git revert <c3-commit>
git revert <c2-commit>
```

هر revert نیز پیش از commitِ خودش suite کامل می‌خواهد.

---

# 8) شروط توقف فوری

ایجنت باید توقف کند و سؤال بپرسد اگر:

- baseline کامل سبز نیست یا exit code نامعلوم است.
- فایل‌های scope تغییرات ناشناخته/هم‌زمان دارند.
- هر یک از چهار فلگ هدف از قبل 1 است.
- برای تست مجبور به network/provider واقعی می‌شود.
- نیاز به ساخت activation C6 یا secret احساس می‌کند.
- C2 بدون دست‌زدن به C1 قابل ادغام نیست؛ ابتدا conflict را با شاهد گزارش کند، نه اینکه معیار صداقت را ضعیف کند.
- C3 مسیر واقعی رأی مالک را می‌شکند.
- propose-only test قرمز می‌شود.
- شمار suite با متن PASSها نمی‌خواند یا import crash رخ می‌دهد.

---

# 9) Definition of Done و قالب گزارش نهایی

جلسه فقط وقتی تمام است که:

- C2: صفر defect → صفر row؛ defect واقعی → row کامل؛ idempotent؛ صف bounded؛ stale RUNNING بدون verdict → ABANDONED؛ mark فقط same-id؛ seed با producer روشن خاموش؛ C1 سالم.
- C3: automated caller نمی‌تواند owner trust بسازد؛ claim بی‌گواهی قابل ممیزی است؛ owner tap واقعی سالم است؛ attestation single-writer تست دارد.
- Paid/router: هر سه مسیر hermetic تست شده؛ چهار فلگ صریحاً 0؛ هیچ live call/activation/deploy.
- suite نهایی شمار صریح و exit code 0 دارد.
- سه commit قابل برگشت ثبت شده‌اند.

گزارش نهایی کوتاه ولی شاهددار:

```text
C2 — DONE
- files:line ...
- targeted: PASS (exit 0)
- full suite: 290/290 (exit 0)
- commit: ...

C3 — DONE
- files:line ...
- targeted: PASS (exit 0)
- full suite: 291/291 (exit 0)
- commit: ...

Router dark prep — DONE, NOT ACTIVATED
- four flags: explicit 0 (byte/CRLF check PASS; no file dump)
- hermetic router tests: PASS
- full suite: 292/292 (exit 0)
- commit: ...

Live body
- processes/ports: ...
- no restart/deploy/send
- C6 activation not created; CB secret untouched
```

هر عدد یا ادعای نهایی باید از خروجی فرمان یا `file:line` بیاید؛ پیش‌بینی‌های این سند را به‌جای نتیجهٔ اجرا گزارش نکن.
