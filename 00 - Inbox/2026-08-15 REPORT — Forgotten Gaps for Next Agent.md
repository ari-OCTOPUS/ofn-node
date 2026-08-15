---
type: knowledge
kind: forgotten-gaps-report
status: active
created: 2026-08-15
updated: 2026-08-15
created_by: agent
audience: next-agent
tags: [octopus, forgotten, handoff, stale-docs, council]
sources:
  - "[[01-TRUTH/STATE-2026-08-15-NIGHT]]"
  - "[[01-TRUTH/CONTRADICTIONS]]"
  - "[[07 - Knowledge/OCTOPUS-COUNCIL-2-2026-08-15/01-FORGOTTEN-GAPS]]"
  - "[[00 - Inbox/2026-08-15 SELF-CONTAINED — Architecture Deep-Scan for External Agents]]"
  - "[[00 - Inbox/2026-08-15 MEGAPROMPT — Hidden Capabilities Discovery]]"
  - "[[agent-prompts/MEGAPROMPT-DEBT-SWEEP-2026-08-16]]"
---

# گزارش شکاف‌های فراموش‌شده — برای ایجنت بعدی (2026-08-15 ~23:25)

> سه اسکن موازی + تطبیق زنده (HEAD، تسک‌های زمان‌بندی، CONTRADICTIONS).
> این فایل **بر** STATE-NIGHT و CONTRADICTIONS و flags last-wins سوار است.
> `OPEN-VERDICTS` / `NEXT-AGENT-HANDOFF` §۱–۴ / `00-INDEX` §۲ / پک `OCTOPUS-TRUTH` تا ۱۷:۰۹ را **اسنپ‌شات صبح/عصر** بگیر، نه SoT شب.

**HEAD زنده:** `6fc0f4b` — `fix(C-013/R13): trust-boundary manifest + TCB hash-checks…` (۲۲:۴۸)  
**git:** `master...germline/master` **ahead 23** (مگاپرامپت هنوز «۱۹+» می‌گوید)  
**شناسهٔ آزاد تناقض: C-016** (STATE §۸ و TEST-SWEEP هنوز C-013/C-015 می‌گویند — دروغ)

---

## ۰. ترتیب خواندن — اگر فقط پنج چیز

1. این فایل
2. `01-TRUTH/CONTRADICTIONS.md` (YAML بعضی‌جا کهنه است؛ نثر پایین‌تر را هم بخوان)
3. `_ops/OCTOPUS-flags.cmd` last-wins (~خط ۱۴۷۰)
4. `agent-prompts/MEGAPROMPT-DEBT-SWEEP-2026-08-16.md` **v1.2**
5. Architecture Deep-Scan + Hidden Capabilities MEGAPROMPT (هر دو Inbox امروز)

اگر تعارض دیدی: **کد + flags + این گزارش > STATE §۸ > OPEN-VERDICTS > HANDOFF پایین‌صفحه > نوت ۱۷:۰۹**.

---

## ۱. دوباره نکن — کار انجام شده، دفتر دروغ می‌گوید

| موضوع | دفتر هنوز می‌گوید | حقیقت زنده (سطح A همین نشست) | اگر دوباره کنی |
|---|---|---|---|
| **C-013 TCB** | CONTRADICTIONS: `open — owner_action`، «فیکس هنوز اعمال نشده» | کامیت `6fc0f4b` در HEAD؛ `settings.py::_resolve_reference_dir` به `SYSTEM_ROOT/'4D'` (ناموجود) fallback می‌کند | بازنویسی TCB بدون رأی بستن |
| **C-014 رصدخانه دوتایی** | هر دو تسک **فعال**؛ R3 = Disable قدیمی | `Get-ScheduledTask`: `OCTOPUS-Observatory` = **Disabled**؛ `OCTOPUS Observatory Hourly` = Ready | **Hourly را خاموش نکن** — همان چشم زنده است |
| **C-012 حافظه 4d** | COUNCIL-MESH بدنه: patch import نشده | `8a5e98b` + telemetry 1.0؛ C-015 = سند کهنه | دوباره وصل کردن پچ |
| **C-003 hypothesis** | NEXT-AGENT §۳: ImportError | NEW-4 stash؛ **23 passed** | stash دوباره / «تعمیر» deceptive_grid |
| **C-005 ADR-041** | OPEN-VERDICTS NEW-2 و 00-INDEX §۲: غایب | فایل ADR روی دیسک؛ C-005 resolved | نوشتن دوباره ADR-041 |
| **C-006 / C-007 تست** | ۴۱۴/۴۰۸ و ۱۳۳/۶۵ unverified | `run_all` ۲۴۰ فایل / ۲۹۳۱ چک؛ epistemics ۱۷۷ | pytest از ریشه به‌عنوان شمارنده |
| **C-009 رأی دکتر** | YAML هنوز `open` | نثر: ۷ رأی واقعی؛ پل `3156316` | ساختن پل دوم |
| **استراتژی بیزی** | OPEN-VERDICTS «کار آتی» | working repo `18fd88a`؛ watch امشب n بیزی=۱ | کپی persistence به‌جای bayes-v1 |
| **UNIFIED_CHAT / HYPOTHESIS / EPISTEMIC** | چند سند =0 / «نه wired» | flags last-wins **=1** | خاموش کردن برای «تطابق با ADR-037 روی کاغذ» |
| **امضای D1** | بعضی ردیف‌ها: چت ≠ Ed25519 (درست برای لَب) | `_ops/D1-AUDIT-PACKAGE` دارای `MANIFEST.sig` Verified | ساختن کلید دوم؛ دادن کلید خصوصی به ممیز |

**C-013 و C-014 هنوز در YAML بازند** چون قاعده می‌گوید فقط رأی مالک می‌بندد. کد/تسک جلوتر از دفتر است. کار تو: **تأیید بستن از مالک**، نه پیاده‌سازی دوباره.

برای C-014 بستن واقعی = صبر تا ردیف `:36` بعدی در evidence نیاید. تسک قدیمی از قبل Disabled است.

---

## ۲. دست مالک — ایجنت نمی‌تواند

1. **R1** چرخش PAT گیتهاب (+ کلیدهای شکل‌دار همان فایل scout). مسیر: `03 - Projects/Mining/02 - Code/Robo-data/scout_all_in_one.py:38` — رشتهٔ `github_pat_` **هنوز هست**. چاپ/کامیت/پوش نکن. بعد از چرخش، ایجنت می‌تواند خط را پاک کند.
2. **R2** push به `germline/master` — **ahead 23**. `git add -A` هرگز.
3. **بستن رسمی C-013** روی `6fc0f4b` (قبول یا رد سیاست hash-check).
4. **بستن رسمی C-014** بعد از اثبات نبودِ `:36`. Hourly را لمس نکن.
5. **ترتیب R2 در برابر R13** اگر به آن‌ها رسیدی (سنتز شورا ≠ ماتریس v2.0).
6. **R21 ممیز مستقل D1** — `MANIFEST.sig` ≠ PASS شخص ثالث. خروجی `AUDIT-OUTPUT-*.txt` در بسته **نیست**. Waiver چت لَب ≠ این بسته.
7. **لَب OD-001 / OD-003** (نوت ۴۷). OD-002 «کلید ساخته نشده» **کهنه** است — کلید ارگانیسم وجود دارد؛ کلید لَب جداست.
8. **Gate 0 برد:** `OCTOPUS_BOARD_CONTROL_URL` + Bearer. فلگ `OCTOPUS_BOARD_CP` در flags.cmd حتی `set` نشده (پیش‌فرض کد = 0).
9. **واردات شورای چهارم** (Downloads ~۲۰:۰۹، Fable 5 + Sol) — در vault نیست. پوشهٔ **جدا** نه داخل COUNCIL-2.
10. **سه فایل غایب شورا** (فقط ریموت/پیوست چت): `octopus-architecture-briefing.md` · `octopus-updated-briefing.md` · `paste.txt`. اختراع نکن.
11. **قضاوت n≥60** — watch فقط **روز ۱** (۱۹:۰۰؛ bayes n=1/60). روزهای ۲–۵ نساخته.
12. **BFG / پاکسازی تاریخ** PAT.

---

## ۳. ایجنت بعدی می‌تواند (بدون فلگ‌آرم)

مأموریت تعریف‌شده: **DEBT-SWEEP v1.2** — اول `06-EVIDENCE/DEBT-SWEEP-2026-08-16.md` را بساز (STEP 2؛ هنوز **وجود ندارد**).

سپس R4–R14 بدهی تست (تصمیم صریح: تست به قرارداد امروز یا کد؛ هر کدام با تست در همان کامیت). WORKLOCK: `run_all.py` / `wiring.py` / `center.py` / `orphan_scan.py` را خودت ثبت نکن.

کشف پنهان: مگاپرامپت Inbox امروز — کاشف نه مسلح‌کننده؛ حداکثر ۵ کارت رأی.

بعد از رأی مالک: به‌روز کردن YAML تناقض‌ها برای C-013/C-014 تا با ماشین یکی شود.

---

## ۴. تله‌هایی که امشب در پین‌ها جا ماند

### ۴.۱ آرشیو نکن

| سطح | چرا |
|---|---|
| `_octopus/` | صف MCP + import زندهٔ langar/Ziman/pf_os. نوت ۰۸-۰۳ «مرده» دروغ است. NEW-3: انتقال ممنوع. |
| `OCTOPUS-PRIME/` | تست قانونی PRE-0 از آن لود می‌کند. |
| `nervous-system/` ریشه | extractors زنده‌اند؛ رجیستری مسیر غلط `OCTOPUS/nervous-system` می‌دهد. |
| `genome-system/ledger/ledger.jsonl` | در حال append؛ telemetry می‌خواند. |
| لَب v2 `…T084249` | لجر آلوده ۲۴۰ ردیف — append-only. v3 `…T110641` تمیز است نه ارتقای رسمی. |

`_octopus/state/octopus_state.json` از ۲۰۲۶-۰۷-۱۸ `self_awareness=green` یخ‌زده — **سلامت ارگانیسم نیست** (صفر writer/reader).

### ۴.۲ سه چیز به نام 4d

- `4d_system/` — مغز پژوهش؛ ADR-038 **observe-only** (mtime `daemon_state.json`).
- `4D-Vault/` — ۳۰۵۵ نوت بازسازی‌شده از Chroma (۰۸-۰۶)؛ هدف observe نیست.
- ADR-038 — پروب. attach / `index_vault` / daemon بدون رأی نکن. brain_core را با 4d هم‌زمان live نکن.

رصدخانهٔ ساعتی روی **Desktop working repo** است نه روی کپی `4d_system/src/nbb_cp` (تست‌هایش اجرا نشده). پچ observatory را در vault NBB نزن.

### ۴.۳ اسپم دکتر ≠ ۷۲ باگ

`OCTOPUS-DOCTOR/60-یافته‌ها/F-AUTO-ALERT-*` ~۷۲ فایل. چند امضا، تکرار ×۵۴…۳۴۶ (`doctor_digest_beat` ValueError روی `'م`، paid-brain fail، …). جاروی تست این‌ها را defect نو نگیرد.

### ۴.۴ retraction ریاضی / بیز / ADR-042-043

بخوان: `00 - Inbox/2026-08-13 RETRACTION — bayes production + ADR-042-043.md`  
`bayes.py` `production_caller: NOT_FOUND`. ADR-042 Phase 0 = فقط لاگ سایت ارسال. ADR-043 ساعت‌ها مستقل معنا ندارند. پین HANDOFF ۰۸-۱۲ «۱۳۳ سبز / APPLY» را تولید نگیر.

### ۴.۵ `.prev-*` را ویرایش نکن

دو درخت کامل: `07 - Knowledge/OCTOPUS-TRUTH-2026-08-15.prev-20260815-183729` و `…184507`.  
`ADR-041*.prev-*` · `INTEGRATION-GUIDE.md.prev-*` · `OCTOPUS-flags.cmd.prev-*`.  
SoT بعد از ۱۷:۰۹ = STATE-NIGHT + این فایل + flags.

### ۴.۶ پل برد

`octopus-bridge/` در ریشه = دو فایل stub، بدون I/O. Ziman آداپتور جدا دارد. پورت‌های OFN 8791–8794 از این ماشین unverified. POST به برد نکن. `test_board_cp.py` و `test_legs_status_reader.py` در `run_all` نیستند.

### ۴.۷ spine / intel_spine

فلگ‌ها ON. glob این workspace روی `_ops/state/intel_spine/` و `spine.db` **صفر** (احتمالاً gitignore/قفل). اختراع دیتابیس نکن. ADR-043 را SoT n=2907 نگیر بدون دیدن فایل.

### ۴.۸ Studio / Project-F

`STUDIO_LLM_CLOUD_VIA_ROUTER=0` عمدی. «همه چی فعال بشه» شامل Studio نیست. هویت بیرون از پوشهٔ Project-F ممنوع.

---

## ۵. اسناد کانونی‌نما که فردا گمراه می‌کنند

شروع نکن از:

- `07-HANDOFF/NEXT-AGENT-HANDOFF.md` §۱–۴ (صبح بازیابی؛ C-003…C-007 را باز می‌داند)
- `02-DECISIONS/OPEN-VERDICTS.md` جدول‌های بالایی (NEW-2 غایب، HYPOTHESIS=0، NEW-4 دو معنی: 879x و deceptive_grid)
- `00-INDEX.md` §۲ (ADR-041 غایب، UNIFIED_CHAT=0)
- `06-EVIDENCE/ADR-04{0,1,7,9}.md` (pending_apply / flag=0)
- `04-SYSTEMS/INTERNET-OBSERVATORY.md` فرانت‌متر «ADR نیست» + allowlist v1 پنج دامنه (زنده v2 هفت دامنه)
- `07 - Knowledge/OCTOPUS-TRUTH-2026-08-15/09-OPEN-WORK.md` (هفت کار بالای لیست انجام شده)
- `شناخت-اختاپوس/00-README` هنوز «نقطهٔ ورود = سند ۲۰ / DEBT-SWEEP v1.1»
- MEGAPROMPT v1.2 هنوز در ROLE «شورای سه‌مدلی» می‌گوید (شورا ۲ = دو مدل) و STEP 2 یک‌جا C-015
- `_ops/ORGANISM-SPEC.md` «یک پروسه»
- `_ops/owner_console/__init__.py` `IMPLEMENTED_NOT_WIRED` — collaborator به center وصل است
- `OCTOPUS/CURRENT-TRUTH.md` بلوک **human** (UNIFIED_CHAT=0، epistemics نه wired) در برابر auto + flags
- `01-TRUTH/CURRENT-TRUTH.md` آینهٔ منجمد صبح (HEAD `9b6ed0c`)

هنوز **واقعاً باز** (این‌ها را «درست نکن»): NBB-V2/V3/V4 · MP-O3/O4 · D7/production · آداپتور observation.v1 · ممیز مستقل D1 · C-001 YAML (۲۰۷ در برابر ۱۷۱؛ زنده ۱۷۱) · C-015 سند COUNCIL-MESH.

---

## ۶. تسک‌های زمان‌بندی زنده (نمونهٔ همین نشست)

| Task | State |
|---|---|
| OCTOPUS Observatory Hourly | Ready / Enabled |
| OCTOPUS-Observatory | **Disabled** |
| Watchdogها (Cortex/Live/MiniApp/TG-Center) | Ready |
| OCTOPUS-Cockpit-Brain · OCTOPUS-doctor-day · OctopusLiveDataRefresh | Ready |

`OctopusLiveDataRefresh` نویسندهٔ CURRENT-TRUTH **نیست** (درس نوت ۱۵). خاموشش نکن مگر مالکش بگوید.

---

## ۷. درخت کثیف — commit نکن مگر بپرسند

`git status`: حدود **۲۱۱ modified + ۸۷ deleted + ۱۴۳ untracked**. بخش بزرگ runtime `_ops/state` و vitals دکتر. قانون: `git add -A` هرگز. اگر checkpoint خواستند، انتخابی و بدون state/sqlite/WAL.

پرچم: `_ops/backup/GITWRITE-FAILED.flag` (قفل git-write ۰۳:۵۰).

تست‌های روی دیسک و **بیرون** `run_all.py`: `test_board_cp.py` · `test_legs_status_reader.py` · `test_doctor_vote_bridge.py` (۵/۵، committed) · چند untracked در hypothesis.

---

## ۸. خروجی‌های همین جلسه (گم نشوند)

| فایل | برای کی |
|---|---|
| `00 - Inbox/2026-08-15 SELF-CONTAINED — Architecture Deep-Scan for External Agents.md` | قاضی معماری (کپی کامل) |
| `00 - Inbox/2026-08-15 MEGAPROMPT — Hidden Capabilities Discovery.md` | کاشف پنهان (نه مسلح) |
| **همین فایل** | ایجنت عملیاتی بعدی |
| `agent-prompts/MEGAPROMPT-DEBT-SWEEP-2026-08-16.md` v1.2 | مأموریت اصلی بدهی |

شورای دوم: `07 - Knowledge/OCTOPUS-COUNCIL-2-2026-08-15/` — NO-GO دقیق‌تر پذیرفته. جدول V را قاطی نکن (Gemini V1 ≠ Sol V1).

---

## ۹. یک‌خطی برای چسباندن بالای جلسهٔ بعد

```
SoT شب: گزارش شکاف فراموش‌شده 2026-08-15 ~23:25 + CONTRADICTIONS + flags last-wins.
HEAD 6fc0f4b = C-013 کد اعمال شده؛ تسک قدیمی رصدخانه Disabled — هیچ‌کدام را دوباره نکن.
C-016 آزاد است. DEBT-SWEEP v1.2 را اجرا کن؛ اول 06-EVIDENCE/DEBT-SWEEP-2026-08-16.md را بساز.
_octopus و OCTOPUS-PRIME را آرشیو نکن. 4D-Vault ≠ 4d_system. Hourly رصدخانه را خاموش نکن.
PAT را چاپ نکن. push دست مالک. HYPOTHESIS=1 تنش با شوراست نه باگ برای خاموش کردن.
```
