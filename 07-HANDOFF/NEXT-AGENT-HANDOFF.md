---
type: handoff
created: 2026-08-15
mission: "بازیابی Vault طبق مگاپرامپت Senior Knowledge Architect / Systems Reconciliation Engineer"
agent: "ZCode (GLM-5.2)"
---

# NEXT-AGENT-HANDOFF — مأموریت بازیابی Vault (2026-08-15)

> **📌 الحاقیهٔ 2026-08-16 ~13:2x — DEEP-SEAMS EXECUTED:** [[../06-EVIDENCE/DEEP-SEAMS-2026-08-16|شواهد]] · C-027 deadline_cycles → recall-events **۹۰** · C-028 tip-commit · gauge ۰/۱۵ PASS. آزاد **C-029**. پوش فقط با کلمه.

> **📌 الحاقیهٔ 2026-08-16 ~13:1x — بستن ERRORHUNT + ماندگارسازی:** نوت [[../07 - Knowledge/شناخت-اختاپوس/49-NIGHT-CLOSE-ERRORHUNT-PERSIST-2026-08-16|۴۹]] · circuit orchestr روی دیسک **half_open** · Poisoning Watch LastResult=0 · سه تست ERRORHUNT در `run_all.py` · `OctopusLiveDataRefresh` هنوز FILE_NOT_FOUND. آزاد **C-027**. پوش فقط با کلمه.

> **📌 الحاقیهٔ 2026-08-16 عصر — HARD-TEST + OPS (نشست پنجم):** شش قابلیت با حمله آزموده شد — S5 خودترمیمی=REAL · S1-S4=PARTIAL · **S6 پیش‌بینیِ ثبت‌شده=METAPHOR** (۱/۱۶ زیرمجموعه؛ مدل بدتر از ثابت). صلیب‌چک مستقل (Sonnet 5) تأییدش کرد + **C-026** (approve/reject بی‌گیتِ enabled) + قید روزهای گذار برای VOTE 4. عملیات فرمانی: اولاما سبک شد (`flags` → 1.5b؛ VRAM 4216→163MiB؛ organism+cortex ری‌استارت با لانچر رسمی)؛ تحلیل بودجهٔ deepseek (کل تاریخ $0.35؛ سقف $20/w در ۱٫۲٪؛ پروب $0.008 معلق رأی). **صف رأی مالک:** پنج کارت HARD-TEST + C-026-fix + بودجه + ری‌استارت رسمی ۳ عضو env-قدیمی. **شناسهٔ آزاد بعدی: C-027.** نقشهٔ کامل روز: [[../00 - Inbox/2026-08-16 DAY-INDEX (MOC)|DAY-INDEX 2026-08-16]] · نشست: [[../00 - Inbox/2026-08-16 SESSION — Hard-Test + Ops + DeepSeek Budget|SESSION]]

> **الحاقیهٔ نشست چهارم (2026-08-15 شب — اجازه‌های تفویضی طبقه‌بندی‌شده):**
> ✅ طبقهٔ A اجرا شد: فلگ‌فایل رسمی `_ops/OCTOPUS-flags.cmd` کشف شد؛ `CORTEX_HYPOTHESIS=1` اضافه (بکاپ .prev) + `OCTOPUS_UNIFIED_CHAT=1` از قبل بود؛ ری‌استارت کنترل‌شدهٔ کامل با `RESTART-ALL.ps1` (cortex با یک تلاش مجدد)؛ **گیت پذیرش دستی PASS**: هر ۵ عضو PID جدید، هر دو فلگ در هر ۴ عضو برابر (336)، state تازه 17:31:08، beat پیشرونده، پورت‌ها 8771-8776 بالا · ✅ طبقهٔ C آماده شد: جفت‌کلید Ed25519 (خصوصی بیرون از repo در `~/.octopus-signing/`) + `_ops/D1-AUDIT-PACKAGE-2026-08-15/` (SCOPE + RUN-AUDIT.ps1 فقط-خواندنی + MANIFEST) — امضا و یافتن ممیز مستقل با مالک؛ D1 تا آن موقع NOT_STARTED می‌ماند
> ⚠️ ثبت برای نشست بعد: shortfall=4 فلگ در loader (pre-existing، برابر در همه) · گیت خودکار اسکریپت پنجرهٔ ۱۲۰s دارد ولی بوت ارگانیسم ~۳min — پیشنهاد: پنجره را به 300s ببرید · `OBSERVATORY` آداپتور ندارد (فاز ۳)

> **الحاقیهٔ نشست سوم (2026-08-15 عصر — اجرای تفویضی با تأیید چتی مالک):**
> ✅ راستی‌آزما 27/27 PASS (CRITICAL 3→0) · ✅ `--apply` موتور: پک ۱۷ فایله در `07 - Knowledge/OCTOPUS-TRUTH-2026-08-15/` + **ADR-041 نوشته شد** (C-005 resolved) + PHANTOM-DOCUMENTS · ✅ کامیت `e3e9d36` (begin_epoch + schema_version stamp + ۳ تست؛ سوئیت 320 passed) · ✅ تسک «OCTOPUS Observatory Hourly» (اولین اجرا 18:06) · ✅ allowlist **v2**: ردیف F=USGS (robots 404→allow طبق RFC 9309 §2.3.1.3) + G=hacker-news (robots صریح `Allow: /*.json$`) + اصلاحیهٔ PHASE-1 (n≥60 حفظ · پنجرهٔ ۳۰ روز) · ✅ سه‌عددی آرشیو: OCTOPUS-PRIME و _octopus **زنده‌اند — آرشیو نشدند** (تست PRE-0 وابسته است؛ _octopus امروز نوشته شده و import زنده دارد) — جزئیات: [[../02-DECISIONS/OPEN-VERDICTS|OPEN-VERDICTS نشست سوم]]
> بازِ مانده: جداسازی استراتژی از persistence · NBB-V2/V3/V4 · MP-O3/O4 · D1/D7/امضا · گیت‌های سه‌گانه (اقدام بیرونی)

## ۱. چی کردم (فایل‌های ایجادشده — هیچ فایل موجودی ویرایش/حذف نشد)

پوشه‌های جدید در ریشهٔ `F:\backup` + `00-INDEX.md` — همهٔ محتوا از شواهد ساخته شد، نه از حافظه:

| فایل | تغییر | منبع شواهد | وضعیت |
|------|--------|-------------|--------|
| `00-INDEX.md` | ایجاد + به‌روزرسانی معوق‌ها | کشف فایل‌سیستم + git | ✅ |
| `01-TRUTH/CURRENT-TRUTH.md` | آینهٔ اعداد زنده: 0.95/36563/11/False/`9b6ed0c` | `OCTOPUS/CURRENT-TRUTH.md` بلوک auto 04:10Z | ✅ |
| `01-TRUTH/TEST-COUNT.md` | **اجراهای زندهٔ pytest** + برچسب‌ها | `py -m pytest` (فرمان‌ها ثبت شده) | ✅ |
| `01-TRUTH/SERVICE-STATUS.md` | پورت‌های 879x خاموش؛ دکتر outbox/dry_run | netstat/curl + doctor-vitals.json | ✅ |
| `01-TRUTH/CONTRADICTIONS.md` | **C-001…C-007** — هر دو مقدار هر تناقض، بدون حل | MANIFEST/BACKUP-README/CURRENT-TRUTH/ADR-039/pytest | ✅ |
| `02-DECISIONS/DECISIONS.md` | ایندکس D-01…D-37 + تداخل شماره‌گذاری Oها | architect/01-Project/DECISIONS.md (دست‌نخورده) | ✅ |
| `02-DECISIONS/OPEN-VERDICTS.md` | NBB-V1…V4 · MP-O3/O4 · D1/D7/امضا · NEW-1…4 | مگاپرامپت + CURRENT-TRUTH | ✅ |
| `03-GATES/GATES.md` | سه گیت نامبرده = unverified (هیچ‌جا نیامدند) | grep کل Vault | ✅ |
| `04-SYSTEMS/OCTOPUS.md` | ۶ پا + ۲ مغز + وضعیت زنده | README + CURRENT-TRUTH | ✅ |
| `04-SYSTEMS/NBB-CP.md` | ۴ نسخه + فازها + **H1 صریح** (SKELETON_HARDENING.md:28) + 171 زنده | MANIFEST/docs/pytest/DR | ✅ |
| `04-SYSTEMS/OFN-NODE.md` | دو ماشین + commits پل + ادعاهای unverified | مگاپرامپت 2026-08-13 + git log | ✅ |
| `04-SYSTEMS/HYPOTHESIS-ENGINE.md` | ADR-037 + **شکست زندهٔ collection** | pytest (خطا عیناً) | ✅ |
| `04-SYSTEMS/INTERNET-OBSERVATORY.md` | hypothesis — هیچ شاهدی نیست | جستجوی منفی | ✅ |
| `04-SYSTEMS/TYPED-EVENTS.md` | hypothesis + کاندیدها | جستجوی منفی | ✅ |
| `05-BUSINESSES/*.md` (۶) | هر پا: نقش/بلاکر/تصمیم مرتبط؛ اعداد=hypothesis | README + DECISIONS | ✅ |
| `06-EVIDENCE/ADR-{037,039,040,041}.md` + `MATH-ATLAS.md` | وضعیت هر سند؛ 041=missing | پوشهٔ adr + Inbox | ✅ |
| `07-HANDOFF/INTEGRATION-GUIDES.md` | قواعد CLAUDE.md (نقل) + نقشهٔ اتصال | CLAUDE.md ریشه | ✅ |
| `08-PLANS/*.md` (۳) و `09-DESIGN/*.md` (۲) | یادداشت‌های «غیاب مستند» + کاندیدها | جستجوی منفی | ✅ |

## ۲. چی ماند

- [ ] **NEW-1:** رأی مالک — معادل معتبر MEGA-PLAN-01/02، TYPED-EVENTS، DESIGN-DIRECTIVE، ARI-STUDIO-STEPS، UNIFIED-CHAT-MEGAPROMPT (کاندیدها در 00-INDEX §۳)
- [ ] **NEW-2:** رأی مالک — سرنوشت ADR-041 (C-005)
- [ ] صف راستی‌آزمایی کدِ DECISIONS (02-DECISIONS/DECISIONS.md — verified_in_code برای Dها)
- [ ] تست‌های اجرا‌نشده: `4d_system/src/nbb_cp` · `nbb-cp-kre` · اعداد پاها (۳۳/۲۱/۲۹/۸ از ۹)
- [ ] تأیید پورت‌ها/سرویس‌ها/۱۲۲۹ تست OFN از خودِ برد (دسترسی نداریم)
- [ ] پر کردن `01-TRUTH/TEST-COUNT.md` برای کل مخزن وقتی روش جمع‌زدن سالم پیدا شد (الان root collection: 15+2 errors)

## ۳. چی شکست (صادقانه)

1. سوئیت `hypothesis_engine` در این محیط **collection error** خورد: `ImportError: falsified_assists_at` (C-003) — تعمیر نشد (خارج از مرز). *پیشنهاد:* بررسی شود آیا `deceptive_grid.py` تابع را export می‌کند یا تست از API قدیمی است.
2. تست‌های epistemics پیدا/اجرا نشد؛ دو عدد متناقض (۱۳۳ در برابر ۶۵) هر دو unverify ماندند (C-007).
3. جمعِ تعداد تست کل مخزن از ریشه ممکن نشد (collect: 15+2 errors) → 414/408 هر دو unverified (C-006).
4. خروجی `pytest` معمولیِ NBB-CP خط خلاصه نداشت (پیکربندی پروژه) — با `-o addopts=` حل شد؛ برای ایجنت بعدی مستند شد.

## ۴. تصمیم‌های لازم از مالک

- NEW-1 و NEW-2 (بالا) + NBB-V1…V4 + MP-O3/O4 + D1/D7 + امضای Ed25519 — همه در [[../02-DECISIONS/OPEN-VERDICTS|OPEN-VERDICTS]]
- تعیین تکلیف ارجاع stale در `README.md` ریشه به `app/NBB-CP` (C-004) — **پیشنهاد:** فقط یک خط correction زیر جدول، بدون بازنویسی.

## ۶. الحاقیهٔ نشست دوم (2026-08-15، بعدازظهر) — رصدخانه و زنجیرهٔ hash

### ۶-۱. حکم قطعی تفسیر الف/ب: **ب درست بود — زنجیرهٔ شاهد مستقل قابل تأیید است**

بازتولید با فرمول عینِ سورس، روی دیتابیس‌های زنده (`mode=ro`): **۴/۴ ردیف منطبق** (۲ evidence + ۲ prediction). CRITICAL های راستی‌آزما ناشی از ناکافی‌بودن کاندیدها بود، نه نقص معماری.

فرمول‌های دقیق (از سورس working repo):
```
evidence  (src/nbb_cp/adapters/observatory/evidence_store.py:125-130):
  headers_canonical = canonical_json(json.loads(response_headers))   # sort_keys + compact + ensure_ascii=False
  body = f"{seq}|{evidence_id}|{url}|{method}|{occurred_at}|{recorded_at}|{status_code}|{headers_canonical}|{body_hash}|{body_size}|{prev_hash}"
  hash = sha256(body.encode("utf-8")).hexdigest()

prediction (src/nbb_cp/adapters/observatory/prediction_registry.py:91):
  body = f"{seq}|{event_type}|{prediction_id}|{canonical_json(json.loads(payload))}|{prev_hash}"
  hash = sha256(body.encode("utf-8")).hexdigest()

canonical_json = json.dumps(x, sort_keys=True, separators=(",",":"), ensure_ascii=False)
  (kernel/events.py:35 — نسخهٔ evidence_store یکسان است)
```
نکتهٔ کلیدی شکست کاندیدهای قبلی: (۱) `response_headers` در هیچ‌کدام از ۱۵ کاندید نبود؛ (۲) payload/headers باید از JSON ذخیره‌شده (که با جداکنندهٔ فاصله‌دار نوشته شده) parse و با جداکنندهٔ compact بازserialize شود.

### ۶-۲. پیشنهاد (propose-only) — کاندیدهای صحیح برای `verify_live_store.py`

```python
# evidence — جایگزین/تکمیلی evidence_hash_candidates:
hdrs_c = canonical(json.loads(row["response_headers"]))
cands.append((
    "src-formula: seq|eid|url|method|occ|rec|status|headers_c|body_hash|size|prev",
    "|".join([seq, eid, url, method, occ, rec, sc, hdrs_c, bh, bs, p]),
))

# prediction — جایگزین/تکمیلی prediction_hash_candidates:
cands.append((
    "src-formula: seq|event_type|pid|canonical(payload)|prev",
    "|".join([seq, et, pid, canonical(json.loads(payload)), p]),
))
```
تست‌شده توسط این ایجنت روی دادهٔ زنده: هر دو فرمول ۴/۴ بازتولید کردند. اعمال با مالک.

### ۶-۳. کشفیات مکمل

- **آستانه پیدا شد:** کد `n ≥ 60` در `src/nbb_cp/adapters/observatory/verifier.py:12` (+ خطوط 71 و 160) ↔ سند امضاشده `n ≥ 20` → ناسازگاری تأیید و مکان‌یابی شد (موتور sync در `_ops` می‌گشت و نمی‌دید).
- **پنجرهٔ ۱۴/۳۰ روز:** در کد مخزن نیست (`run_observatory.py` پنجره ندارد) — احتمالاً Task Scheduler بیرون از repo؛ باز.
- **ریشهٔ تساوی 0.80=0.80:** مدل سادهٔ فعلی در `run_observatory.py:120-135` همان سیگنال persistence (0.8/0.1) را برای OCTOPUS می‌گیرد.
- **دامنهٔ دوم در بودجه:** `hacker-news.firebaseio.com 0/50` (به‌جز USGS).
- working repo: ۸ vault ابسیدین روی درایو (طبق موتور)؛ من ۱۲ شمردم (با تودرتوها) — تفاوت تعریف شمارش.

### ۶-۴. کارهای اجراشده به دستور مالک در این نشست

| کار | نتیجه |
|-----|-------|
| NEW-4: `git stash push` مسیر-مشخص روی `deceptive_grid.py` (F:\backup) | `stash@{0}` ثبت شد — ویرایش آرشیو شد، حذف نشد |
| اجرای مجدد تست‌های hypothesis_engine | **`23 passed in 1.53s`** → C-003 resolved |
| بازتولید hash زنجیره‌ها | ۴/۴ ✅ (سطح A) |
| خواندن `PHASE-1-DECISIONS.md` | NBB-V1=A، ADR-037=A، USGS موقت — همه با امضای owner (سطح A) |

### ۶-۵. منتظر مالک

1. اعمال کاندیدهای §۶-۲ در راستی‌آزما و اجرای مجدد → انتظار: CRITICAL→PASS
2. `--apply` موتور (پس از تأیید فرمول‌ها — شرط شما برآورده شد): PHANTOM-DOCUMENTS + ADR-041 + پک (۱۶ یادداشتهٔ اولیه؛ اکنون ۲۱ فایل — سطح A شمارش 2026-08-15 شب)
3. آستانهٔ n (60↔20) و پنجره (14↔30): تصمیم و یکسان‌سازی
4. `repo root` FAIL موتور (`.git` یک سطح بالاتر) — صاحب موتور گفت اصلاح می‌کند

## ۵. قواعد رعایت‌شده (خود-گزارشی، قابل‌رسی)

- هیچ فایلی حذف نشد (`rm` اجرا نشد) · هیچ فایل موجودی بازنویسی نشد (فایل‌های زنده فقط quot شدند)
- هیچ رازی خوانده/echo نشد (`.env` باز نشد؛ توکن دکتر از قبل redacted بود)
- هیچ فلگی روشن نشد · هیچ چیزی به بیرون ارسال نشد (حتی curl ساب‌دامنه‌ها اجرا نشد)
- `99-ARCHIVE/` خالی ماند — طبق رأی مالک NEW-3 (سه عدد لازم قبل از هر انتقال)
- فارسی حفظ شد؛ شناسه‌ها/مسیرها لاتین
- نشست دوم: دیتابیس‌های زنده فقط با `mode=ro` باز شدند؛ بازگردانی deceptive_grid با stash انجام شد نه حذف؛ کد راستی‌آزما تغییر داده نشد (فقط پیشنهاد §۶-۲)

> **الحاقیهٔ نشست پنجم (2026-08-15 شب‌هنگام — «همهٔ قفل‌ها»):** صدای دکتر وصل شد (۳ متغیر env، mode=direct، اثبات در پروسه؛ vitals در سیکل بعد دکتر تازه می‌شود) · کشف: vault-RAG از قبل وصل بود (flags.cmd:1217) · 4d=قفل ORANGE طبق ADR-008 (رأی فقط از کانال رسمی تلگرام مالک) · brain_core: شاهد علیه promote (missing_old=3473) · تک‌پا = طراحی D-35 نه قفل · پیشنهادهای باز: پنجرهٔ گیت پذیرش 120s→300s · بررسی shortfall=4

> **الحاقیهٔ نهایی شب (کارت‌های اجازه):** سه کارت مجوز با دکمه به تلگرام مالک رفت (ok×3): امضای D1 · رأی ORANGE 4d · قضاوت n≥60. رصد روزانهٔ ۱۹:۰۰×۵روز مسلح شد. پس از رأی مالک: (۱) امضا با openssl از ~/.octopus-signing (۲) ثبت ORANGE در ADR-008 addendum (۳) گزارش روزانه خودکار از cron نشست.

> **الحاقیهٔ ششم — ادغام ربات‌ها (2026-08-15 ~18:4x):** دکتر به outbox برگشت، توکن مستقیم حذف شد (فلگ‌ها 339→338) — صدای واحد = ربات center از طریق doctor_link (فلگش از قبل روشن بود؛ باگ «نادیده» ترتیب هندلرها بود که پلِ 3156316 اصلاح کرد). تست تک‌صدا: کارت فقط از center آمد (cursor: pos 8728، day_count 5). دبل‌چک پایانی: coherence **0.977** (بالا از 0.942) · beat 36803 · رصدخانه 6/6 · همهٔ کامیت‌ها ثبت.

> **الحاقیهٔ هفتم — شورای دوم (2026-08-15 دیرشب):** اسناد در [[../07 - Knowledge/OCTOPUS-COUNCIL-2-2026-08-15/README|OCTOPUS-COUNCIL-2]] (`576c7fb`). مالک NO-GO دقیق‌تر را پذیرفت. فکت‌چک: ویرایش TCB = ایجنت جاروی تست (`8a5e98b`) نه مالک؛ `check_invariants` هش ندارد. مگاپرامپت بعدی v1.1.

---

## الحاقیه 2026-08-16 (~00:1x) — جاروی بدهی EXECUTED (مگاپرامپت v1.1، تفویض کامل مالک)

**ورودی نشست بعد:** `06-EVIDENCE/DEBT-SWEEP-2026-08-16.md` (جدول کامل R1..R29 + §R3 اثبات C-014) · `02-DECISIONS/DECISION-ARTIFACTS-2026-08-16/` (DA-1/2/3 + سیاست R16 + طرح R18).

خلاصهٔ وضعیت:
- ✅ اجرا شد: R0a/R13 (manifest مرز اعتماد + هش‌چک TCB؛ C-013 resolved) · R3/C-014 (containment اثبات‌شده) · R2 (germline@bb2d859، unpushed=0) · R19 (AEB + باندل نهایی) · R4-R14 (۱۵ شکست بسته + باگ تولیدی def callback) · R20/R16(قدم صفر)/R18 مصنوع · R21(بسته)+R22/R23/R24/R25/R26/R27.
- ⏳ دستِ مالک: R1 چرخش PAT (پچ آماده در `03 - Projects/Mining/02 - Code/PAT-SCRUB-READY-2026-08-16.md`) · **امضای Ed25519**: `4d_system/config/trust-boundary.json` + `_ops/audit/bundles/AEB-*.txt` (فرمان‌ها در سربرگ مولدها) · بعدش روشن‌کردن `OCTOPUS_TCB_MANIFEST_ENFORCE` با ری‌استارت رسمی · R21 انتخاب ممیز بیرونی · رأی‌های سیاست صف (R16 v1) و DA-1/DA-2/DA-3.
- ⏸ تعلیقِ مستند (نردبان شورا): R15 daemon (بعد از DA-2) · R17 فلگ (پنجرهٔ بعدی) · R28/R29 (فاز ۵، هرگز هم‌زمان).
- شناسهٔ آزاد تناقض: **C-016**. سوئیت‌های نو در run_all: `test_flag_shortfall_smtp_exemption.py` · `test_ask_reasoning_preamble_strip.py`؛ تست‌های 4d: `test_trust_boundary_c013.py`.

### تکمیل 2026-08-16 ~00:5x — دو مأموریت اسکن

- **قاضی معماری ✅:** `00 - Inbox/2026-08-16 JUDGE — Architecture Judgment Report.md` — NO-GO تأیید + تشدید INV-4؛ DA-4 (شبکهٔ PEP) پاسخِ ساختاریِ کوچک‌ترین پچِ مؤثرش است. توجه: قاضی از snapshot 23:05 قضاوت کرد — هش‌چک TCB الان پیاده است (6fc0f4b).
- **کشف پنهان‌ها ✅:** `00 - Inbox/2026-08-15 DISCOVERY — Hidden Capabilities Catalog.md` — ۸ کلاس، اعداد زندهٔ امشب (نه 08-11)، ۵ کارت رأی برای مالک (کارت ۵ = حذف DOCTOR_USE_CENTRAL_ROUTER از flags.cmd — رأی مالک، ایجنت حذف نکرد). Scratch: `_scratch-dark.json`.
- ماتریس v2.0 جاافتاده‌ها: R20a-e کامل شد (DA-4 اضافه شد) · ترتیب R2/R13 در OPEN-VERDICTS با یادداشت اجرا ثبت شد (پیش‌فرض آینده = ماتریس تا رأی مالک).

## الحاقیه PHASE01 — 2026-08-16 (~0x:xx)

مگاپرامپت PHASE01 v2.0 اجرا شد: `06-EVIDENCE/PHASE01-2026-08-16.md`.
- **سه پیش‌فرض مگاپرامپت کهنه بود** (STEP1-1 ویرایش TCB، 4-2، بخشی از 4-4) — رد با شواهد؛ **C-018** ثبت. ایجنت بعد: قبل از هر STEP مگاپرامپت، پیش‌فرضش را با درخت زنده فکت‌چک کن (درسِ C-015/C-018).
- **R16 اعمال شد:** صف فرضیه 1063→382 فعال (681 dedup، صفر حذف، بکاپ+rollback). سقف ورود 10/روز در `save_hypothesis`.
- **کرنل شوراها سایه** در `4d_system/councils/` (+PEP سایه DA-4-P1) — ۱۸ تست پذیرش؛ فعال‌سازی فقط با گیت‌های COUNCIL-MESH.
- RESTART-CORTEX `-Force` (ریشهٔ تلاش دوم: نشانگر فقط در بالای سیکل دیده می‌شود).
- شناسهٔ آزاد تناقض: **C-019**.

## الحاقیه PHASE02 — 2026-08-16 (~06:0x)
- شواهد کامل: 06-EVIDENCE/PHASE02-2026-08-16.md. برجسته‌ها: هولداوت L1 (ACL مالک) → یافتهٔ gaming-beats-model؛ PEP سایه دو گلوگاه (tg_api._call_post · approval._url_json_post) — لاگ state/telegram-pep-shadow.jsonl از ری‌استارت بعدی پروسه‌ها پر می‌شود؛ readback الان نمای R16 را می‌فهمد.
- بازِ رأی مالک: فعال‌سازی PEP-P1 (پس از ≥۷ روز سایه) · DA-6 گزینه‌ها · DA-1 L2/L3 · نام ممیز D1 · چرخش PAT.

### الحاقیهٔ پایانی شب 2026-08-16 (~13:2x) — هر چهار مگاپرامپت اجرا شد

ورودی ایجنت بعد: `00 - Inbox/2026-08-15↯16 NIGHT — MASTER SUMMARY` + STATE §8.
- همهٔ شواهد در 06-EVIDENCE (DEEP-TEST · PHASE01 · PHASE02 · ERRORHUNT · CAPABILITY-HARDTEST · CROSSCHECK · RECALL · UNWIRED).
- پروتکل پوش (C-023): کامیت آزاد؛ **push فقط با کلمهٔ صریح مالک** — کامیت‌های معلق را در گزارش بالا بیاور.
- تسک پایش تعمیر شد (python.exe مطلق؛ ریشه: py per-user). تسک گرم‌کنندهٔ recall هم جدید است — هر دو را دست‌نخورده بگذار مگر خراب شوند.
- قاعدهٔ لانچر (درس C-024/دیپ‌تست): env پروسه‌ها از دو منبع واگرا می‌آید (flags.cmd برای _ops · 4d_system/.env برای مغز) — هر لانچر/تست باید منبع درست را صریح بخواند.
