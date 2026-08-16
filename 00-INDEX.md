---
type: vault-index
created: 2026-08-15
canonical_vault: "F:\\backup"
agent: "ZCode (GLM-5.2) — مأموریت بازیابی Vault طبق مگاپرامپت Senior Knowledge Architect"
owner_verdicts_2026_08_15:
  vault_canonical: "F:\\backup"
  nbb_cp: "«همش منم» — هر چهار نسخهٔ در گردش یک پروژه‌اند؛ هیچ‌کدام به‌تنهایی canonical نیست"
  structure_location: "ریشهٔ F:\\backup طبق مگاپرامپت"
rules:
  - "شواهد نه ادعا · بهبود نه بازنویسی · حذف ممنوع · نقل‌قول قبل از به‌روزرسانی"
  - "سلسلهٔ حقیقت: کد زنده/runtime > فایل مخزن/لجر > CHECKPOINT تازه > یادداشت قدیمی > (ممنوع) حافظهٔ ایجنت"
status_legend:
  verified: "از کد/runtime/فایل تأیید شد"
  likely: "تاریخ تازه و محتوا معقول، تأیید مستقیم نشده"
  stale: "قدیم یا مناقض با کد/وضعیت زنده"
  unknown: "قابل تأیید نیست"
  unverified: "عدد/ادعا بدون منبع قابل‌تأیید"
---

# 00-INDEX — نقشهٔ کامل Vault (F:\backup)

> **🤖 ایجنت خارجی؟** اول [[01-TRUTH/STATE-2026-08-15-NIGHT.md|STATE — اسنپ‌شات جامع (شب 2026-08-15)]] را بخوان — وضعیت زندهٔ هر دو مخزن + قواعد + کارِ باز. این ایندکس نقشهٔ کامل ساختار است.
> این فایل خروجی STEP 1 مگاپرامپت است: انventory کامل فقط-خواندنی.
> تاریخ ثبت: 2026-08-15. هیچ فایلی برای ساخت این ایندکس تغییر/حذف نشده.

> 🌙 **پایان شب 15↯16 اوت:** [[00 - Inbox/2026-08-15↯16 NIGHT — MASTER SUMMARY|MASTER SUMMARY]] — هر ۴ مگاپرامپت اجرا شد · M3 9.28→14.4% · HARDTEST: S5 REAL/S6 METAPHOR · C-019..C-026 · بازِ رأی: پوش·SELF_CODE·۵کارت·ممیز·PAT. آزاد بعدی: C-027.

## ۰. رأی‌های مالک (2026-08-15، این جلسه)

| موضوع | رأی مالک |
|-------|----------|
| Vault کانونیکال | `F:\backup` |
| NBB-CP | «همش منم» — هر ۴ نسخه یک پروژه‌اند؛ سند هر ۴ را با هم ثبت می‌کند |
| محل ساختار هدف | ریشهٔ `F:\backup` طبق مگاپرامپت |

## ۱. نمای کلی پوشه‌های Vault (تجمیعی)

| پوشه | تعداد md | بازهٔ تاریخ | نقش | دستهٔ هدف | وضعیت |
|------|----------|-------------|-----|-----------|-------|
| `00 - Inbox/` | 260 | 2026-07-03 … 2026-08-15 | دامپ نشست‌ها/گزارش‌ها | منبع (در جا می‌ماند) | mixed |
| `01 - Dashboard/` | 7 | 2026-07-18 … 2026-08-15 | داشبوردها | در جا | likely |
| `02 - Life OS/` | 2 | 2026-07-15 | زندگی شخصی | در جا | likely |
| `03 - Projects/` | 713 | 2026-06-29 … 2026-08-15 | ۶ پا + research-spec | منبع 05-BUSINESSES و 04-SYSTEMS | mixed |
| `04 - Architect System/` | 312 | 2026-06-13 … 2026-08-15 | مغز مادر/architect | منبع 02-DECISIONS | mixed |
| `05 - Agents/` | 8 | 2026-07-07 … 2026-07-20 | پرامپت ایجنت‌ها | منبع 07-HANDOFF | stale? |
| `06 - Architecture Maps/` | 63 | 2026-07-07 … 2026-08-13 | نقشه‌های معماری | منبع 04-SYSTEMS | likely |
| `07 - Knowledge/` | 477 | 2026-07-06 … 2026-08-15 | دانش (genome-system، شناخت-اختاپوس…) | منبع 06-EVIDENCE | mixed |
| `08 - Assets/` | 0 md | — | دارایی‌های باینری | در جا | — |
| `09 - People/` | 1 | 2026-07-15 | افراد | در جا | likely |
| `10 - Telegram processing/` | 13 | 2026-07-15 … 2026-08-11 | پردازش تلگرام | در جا | likely |
| `4D-Vault/` | 3055 | 2026-08-06 (همه در یک روز) | Vault پژوهشی 4D (MOC، ریاضی، SOG…) | در جا — سیستم مستقل | unknown |
| `OCTOPUS/` | 4 md + داشبورد HTML | 2026-07-13 … 2026-08-15 | قلب معماری + CURRENT-TRUTH | منبع 01-TRUTH | **verified** |
| `OCTOPUS-DOCTOR/` | Vault مستقل دکتر | 2026-07-29 … 2026-08-15 | پزشک ارگانیسم (10-قوانین…90-_meta) | در جا — زیرسیستم | mixed |
| `OCTOPUS-PRIME/` | 27 | 2026-07-23 | phase-0 قدیمی | **در جا — وابستگی زنده** (تست قانونی PRE-0 از آن لود می‌کند؛ سه‌عددی 2026-08-15) | active — آرشیو: خیر |
| `_memory/` | 1 (HEARTBEAT 145KB) | 2026-08-15 | حافظهٔ زندهٔ runtime | منبع 01-TRUTH | **verified** |
| `_Templates/` | 9 | 2026-07-10 … 2026-07-15 | قالب‌ها | در جا | likely |
| `architecture/` | 1 | 2026-08-12 | سند معماری | منبع 04-SYSTEMS | likely |
| `continuity/` | 17 | 2026-08-03 | رکوردهای تصمیم DR-* | منبع 06-EVIDENCE | verified (به‌عنوان فایل) |
| `docs/` | 1 | 2026-08-04 | مستندات | در جا | likely |
| `nervous-system/` | 9 md + کد | 2026-07-13 | سیستم عصبی (کد+spec) | منبع 04-SYSTEMS | mixed |
| `agent-prompts/` | 15 | 2026-07-11 … 2026-08-03 | پرامپت‌های ایجنت | منبع 07-HANDOFF | likely |
| `_octopus/` | 4 md (+غیرmd تا 2026-08-15) | تا 2026-08-15 | ساختار اجرایی | **در جا — زنده**: امروز نوشته شده؛ langar/Ziman/pf_os import می‌کنند | active — آرشیو: خیر |
| `PRE-0/` | 11 | 2026-07-06 … 2026-07-28 | نمونهٔ امن اسکن | در جا | likely |

| `07 - Knowledge/OCTOPUS-TRUTH-2026-08-15/` | 17 فایل | 2026-08-15 17:09 (موتور --apply) | پک حقیقت رصدخانه (16 یادداشت + PHANTOM-DOCUMENTS + گزارش نشست) | منبع 06-EVIDENCE/INTERNET-OBSERVATORY | **verified** (توسط موتور نوشته شد) |
| `07 - Knowledge/OCTOPUS-COUNCIL-2-2026-08-15/` | 6 فایل (۲ گزارش + سنتز + extract ۵۸۴خط + docx + README) | 2026-08-15 شب (`576c7fb`) | شورای دوم + سند جامع حسابرسی + فکت‌چک انتساب TCB | منبع 06-EVIDENCE / شناخت-اختاپوس نوت ۴۸ | **verified** |
| `architecture/observatory-allowlist.yaml` | — | 2026-08-15 (v2) | allowlist امضاشدهٔ ۷ دامنه‌ای | 06-EVIDENCE | verified |

| `04-SYSTEMS/HEARTS-TIME.md` + `GENOME-MEMORY.md` + `MINDS.md` + `OWNER-CONSOLE.md` + `LEGS-LIVE.md` + `UNCONSCIOUS.md` | ۶ یادداشت شناختِ عمیق | 2026-08-15 (شبِ طبیعت‌شناس، مرحله ۱-۶) | آناتومی درونی از state/ledger/ناخودآگاه — سطح A | 04-SYSTEMS | **verified** |

| `4d_system/config/trust-boundary.json` + `_ops/audit/bundles/AEB-20260816-000508.{json,txt}` | مرز اعتماد TCB + باندل شواهد حسابرسی (C-013/R19) | 2026-08-15/16 | امنیت/حسابرسی | 06-EVIDENCE | verified |
| `06-EVIDENCE/DEBT-SWEEP-2026-08-16.md` · `02-DECISIONS/DECISION-ARTIFACTS-2026-08-16/` (۵ مصنوع) · `agent-prompts/MEGAPROMPT-DEBT-SWEEP-2026-08-16.md` (v1.2) · `03 - Projects/Mining/02 - Code/PAT-SCRUB-READY-2026-08-16.md` | خروجی‌های جاروی بدهی R0a-R29 | 2026-08-16 ~00:0x | اجرا/تصمیم | 06-EVIDENCE + 02-DECISIONS | verified |

| `00 - Inbox/2026-08-16 DISCOVERY — Unwired & Dead Paths Catalog.md` · `06-EVIDENCE/UNWIRED-*-2026-08-16.md` · `07-HANDOFF/UNWIRED-REPORT-2026-08-16.md` | کشف کلاس ۹ بی‌فراخوان: ConsolidationCycle NEVER-WIRED · C-019/C-020 | 2026-08-16 11:4x | کشف | 06-EVIDENCE | verified |

| `00 - Inbox/2026-08-16 JUDGE — Architecture Judgment Report.md` · `00 - Inbox/2026-08-15 DISCOVERY — Hidden Capabilities Catalog.md` (+ `_scratch-dark.json`، gitleaks پاک) | قضاوت معماری (INV-4) + کاتالوگ پنهان‌ها: ۴۰۳ فلگ / ۱۵ DARK / ۱ orphan_armed / ~۴۵ پکیج نامرئی | 2026-08-16 00:1x | کشف/قضاوت | 06-EVIDENCE منبع | verified (فایل‌ها موجودند) |
| `02-DECISIONS/DECISION-ARTIFACTS-2026-08-16/DA-4-PEP-MESH-AND-ACTION-LEASES.md` + `DA-5-INTRINSIC-CONTROL-AND-ORGANISM-MANIFEST.md` | شبکهٔ ۶-PEP + lease تک‌مصرف · کنترل درونی + manifest ارگانیسم — تکمیل‌کنندهٔ DA-1..3 | 2026-08-16 | تصمیم | 02-DECISIONS | verified |

**خارج از شمارش یادداشت (کد/زیرساخت):** `_ops/`، `4d_system/`، `octopus-bridge/`، `node_modules/`، `.git/`، `.claude/`، `_build/`، `_portable-build/`، `_zip-verify/`، `_archive-binaries/`، `_Archive/`، `_Duplicates/` — ایندکس تک‌فایلی نمی‌شوند؛ فقط سندهای مرجعشان ثبت شده است.

## ۲. فایل‌های کلیدی (تک‌تک)

| فایل | به‌روزرسانی | منبع | دستهٔ هدف | وضعیت |
|------|-------------|------|-----------|-------|
| `OCTOPUS/CURRENT-TRUTH.md` | 2026-08-15 (auto 04:10Z) | runtime ارگانیسم | 01-TRUTH | **verified** — coherence 0.95 · beat 36563 · members 11 · halted False · HEAD `9b6ed0c` |
| `_memory/HEARTBEAT.md` | 2026-08-15 | runtime | 01-TRUTH (منبع SERVICE-STATUS) | verified (وجود + runtime-written) |
| `OCTOPUS-DOCTOR/90-_meta/state/doctor-vitals.json` | 2026-08-15 | runtime دکتر | 01-TRUTH | verified (وجود) |
| `_ops/OCTOPUS-HONESTY.md` | — (ارجاع در CURRENT-TRUTH) | _ops | 01-TRUTH | verified (وجود) |
| `_ops/docs/MONEY-CLAIM-VS-CONFIRM.md` | — (ارجاع در CURRENT-TRUTH) | _ops | 01-TRUTH | verified (وجود) |
| `CLAUDE.md` (ریشه) | 2026-08-03 | مخزن | 07-HANDOFF | likely |
| `README.md` (ریشه) | 2026-08-10 | مخزن | 04-SYSTEMS/OCTOPUS | **stale** — به `app/NBB-CP` حذف‌شده اشاره می‌کند ⚠️ |
| `04 - Architect System/architect/01-Project/DECISIONS.md` | 2026-07-09 | owner-authored | 02-DECISIONS | likely — D-01…D-37 + باز O-01…O-04 |
| `03 - Projects/NBB-Control-Plane/MANIFEST.yaml` | 2026-07-11 | مخزن | 04-SYSTEMS/NBB-CP | ⚠️ ادعا: ۲۰۷ تست (C-001) |
| `03 - Projects/NBB-Control-Plane/BACKUP-README.txt` | 2026-07-11 | مخزن | 04-SYSTEMS/NBB-CP | ⚠️ ادعا: ۱۷۱ تست، Head `02561ea` (C-001) |
| `03 - Projects/NBB-Control-Plane/CLAUDE.md` | — | مخزن | 04-SYSTEMS/NBB-CP | likely |
| `4d_system/nbb-cp-kre/` | — | مخزن | 04-SYSTEMS/NBB-CP | verified (به‌عنوان فایل) — `VERIFIED_SAFE_READONLY_TOOL` طبق `continuity/DR-NBB-CP-KRE-VERIFY-20260803.md` |
| `4d_system/src/nbb_cp/` | — | مخزن | 04-SYSTEMS/NBB-CP | unknown (بسته بودن تست‌ها بررسی نشد) |
| `app/NBB-CP` | حذف 2026-08-03 | تاریخچهٔ git (کامیت `ea69126`) | 04-SYSTEMS/NBB-CP | **stale/حذف‌شده** — فقط در اسنپ‌شات‌ها (backup-SAFE-2026-07-19) |
| `03 - Projects/research-spec-compiler/adr/` | — | مخزن | 06-EVIDENCE | verified (وجود) — **ADR-001…023، 033…040، 042، 043**؛ شماره‌های 024–032 و **041 غایب‌اند** |
| `_ops/hypothesis_engine/` | — (ارجاع CURRENT-TRUTH 2026-08-13) | _ops | 04-SYSTEMS/HYPOTHESIS-ENGINE | likely — ADR-037 |
| `_ops/epistemics/` | — (ارجاع CURRENT-TRUTH) | _ops | 06-EVIDENCE/ADR-039 | likely — «تست‌ها ۴۵/۴۵ + ۲۰/۲۰ سبز» هنوز unverified |
| `_ops/conversation_hub/` | — (ارجاع CURRENT-TRUTH) | _ops | 06-EVIDENCE/ADR-040 | likely — `OCTOPUS_UNIFIED_CHAT=0` (خاموش) |
| `00 - Inbox/2026-08-11 MATH-ATLAS — Equations Hidden in Octopus.md` | 2026-08-11 | نشست | 06-EVIDENCE/MATH-ATLAS | likely |
| `00 - Inbox/2026-08-12 RECONCILIATION-REPORT — Math Atlas Runtime Truth.md` | 2026-08-12 | نشست | 06-EVIDENCE/MATH-ATLAS | likely |
| `00 - Inbox/2026-08-13 SELF-CONTAINED — Math Atlas Complete for Research.md` | 2026-08-13 | نشست | 06-EVIDENCE/MATH-ATLAS | likely |
| `07 - Knowledge/شناخت-اختاپوس/40-MATH-EQUATIONS-RESEARCH-ARCHITECTURE-COMPARISON-2026-08-11.md` | 2026-08-11 | نشست | 06-EVIDENCE/MATH-ATLAS | likely |
| `continuity/DR-NBB-CP-KRE-VERIFY-20260803.md` | 2026-08-03 | DR رسمی | 06-EVIDENCE | verified (به‌عنوان فایل) |
| `continuity/PHASE0-STATUS-2026-08-03.md` | 2026-08-03 | DR رسمی | 06-EVIDENCE | verified (به‌عنوان فایل) |
| `OCTOPUS/ARCHITECTURE-BIBLE.md` | — | مخزن | 04-SYSTEMS/OCTOPUS | likely |

## ۳. سندهای phantom — هفت نام که در گفتگو تولید شدند، نه در مخزن

**رأی مالک (NEW-1، 2026-08-15):** این هفت نام هیچ معادل تعیین‌شده‌ای ندارند و ندارند؛ نگاشتشان به اسناد موجود = ثبت حدس به‌عنوان واقعیت (همان مکانیزمی که C-001…C-007 را ساخت). ثبت رسمی در `PHANTOM-DOCUMENTS.md` است که موتور `octopus_sync` در `--apply` می‌نویسد. جدول کاندیدهای قبلی این بخش حذف شد.

| نام | وضعیت | نکتهٔ تازه |
|-----|-------|------------|
| MEGA-PLAN-01 / MEGA-PLAN-02 | phantom | — |
| TYPED-EVENTS | phantom | — |
| DESIGN-DIRECTIVE / ARI-STUDIO-STEPS | phantom | — |
| UNIFIED-CHAT-MEGAPROMPT | phantom | معماری واقعی چت: ADR-040 (موجود) |
| ADR-041 | **✅ نوشته شد (17:09 توسط --apply):** `03 - Projects/research-spec-compiler/adr/ADR-041-internet-observatory.md` — پرش ۰۴۰→۰۴۲ بسته شد → C-005 resolved | موضوعش واقعی و زنده است (کد + ۹۳ تست) |
| CHECKPOINT.md (نود میدانی) | phantom در این مخزن | اگر روی برد باشد، نسخه‌ای این‌جا نبوده |

> استثنای مهم: موضوعِ «رصدخانهٔ اینترنت» روی phantom نیست — کد کامل آن در مخزن کاری Desktop مستقر است (۹۳ تست سبز) → [[04-SYSTEMS/INTERNET-OBSERVATORY|INTERNET-OBSERVATORY]]

## ۴. Vaultهای دیگر (خارج از canonical — دست نخورده)

`F:\backup-Archive\مغز دوم` · `F:\backup-deploy-lab` · `F:\backup-SAFE-2026-07-19` · `F:\backup-snapshot-20260723-121256` · `F:\octopus-phase0-A-halt` · `F:\octopus-phase0-isolated` · `F:\romajan` · `F:\_______Black Box` · `C:\Users\Armin\Documents\Obsidian Vault`

**Vaultهای تودرتو داخل خود F:\backup** (کشف 2026-08-15): `OCTOPUS-DOCTOR/.obsidian` · `04 - Architect System/architect/.obsidian` — هر دو زیرسیستم فعال‌اند و دست نخورده باقی ماندند.

## ۴-ب. ساختار بازیابی ساخته‌شده در همین مأموریت (2026-08-15)

`00-INDEX.md` (همین فایل) · `01-TRUTH/` (CURRENT-TRUTH · TEST-COUNT · SERVICE-STATUS · CONTRADICTIONS با C-001…C-007) · `02-DECISIONS/` (DECISIONS · OPEN-VERDICTS) · `03-GATES/GATES.md` · `04-SYSTEMS/` (OCTOPUS · NBB-CP · OFN-NODE · HYPOTHESIS-ENGINE · INTERNET-OBSERVATORY · TYPED-EVENTS) · `05-BUSINESSES/` (۶ پا) · `06-EVIDENCE/` (ADR-037 · 039 · 040 · 041 · MATH-ATLAS) · `07-HANDOFF/` (NEXT-AGENT-HANDOFF · INTEGRATION-GUIDES) · `08-PLANS/` (۳ یادداشت غیاب) · `09-DESIGN/` (۲ یادداشت غیاب) · `99-ARCHIVE/` (خالی — هیچ فایلی archive-worthy از این_pass پیدا نشد؛ حذف هم نشد)

## ۵. موارد معوق این ایندکس

- [x] تناقض C-001: تست NBB-CP ۲۰۷/۱۷۱ → ثبت + اجرای زنده: **171 passed** (likely: ۱۷۱، status: open)
- [x] تناقض C-002: اعداد مگاپرامپت در برابر CURRENT-TRUTH زنده → ثبت شد
- [x] **NEW-1 (رأی مالک 2026-08-15):** هفت نام = phantom، بدون معادل؛ کاندیدها از این ایندکس حذف شد؛ ثبت رسمی در PHANTOM-DOCUMENTS.md (با `--apply`)
- [x] **NEW-2:** ADR-041 در پروژهٔ Perplexity موجود؛ با `--apply` در vault نوشته می‌شود → C-005 → owner_decided_pending_apply
- [x] **NEW-3:** هیچ انتقالی به 99-ARCHIVE بدون سه عدد (آخرین تغییر/ارجاع ورودی/import زنده) → `99-ARCHIVE/` خالی ماند
- [x] **NEW-4:** stash مسیر-مشخص deceptive_grid.py → تست‌ها **23 passed** → C-003 resolved
- [x] اجرای تست‌ها: NBB-CP ✅ 171 · رصدخانه ✅ 93 · hypothesis-engine ✅ 23 (بعد از بازگردانی) · epistemics ⚠️ C-007 · کل مخزن ⚠️ C-006
- [x] پورت‌های 8791–8794 → از دسکتاپ گوش نمی‌دهند؛ ادعای میدانی unverified
- [x] `--apply` موتور — **اجرا شد (17:09)**: پک ۱۶ یادداشته + ADR-041 + PHANTOM-DOCUMENTS + allowlist/policy ✅
- [x] آستانهٔ n — **حفظ ۶۰ در کد** + اصلاحیهٔ تاریخ‌دار (قبل از اولین resolution) ✅ · پنجره — **۳۰ روز** ✅
- [x] تسک «OCTOPUS Observatory Hourly» ساخته شد (اولین اجرا 18:06) + ریست روزانهٔ بودجه (کامیت e3e9d36) ✅
- [ ] جداسازی استراتژی OCTOPUS از persistence (کار مدل‌سازی آتی — ریشه مستند شد: run_observatory.py:120-135)
- [ ] تست‌های 4d_system/src/nbb_cp و nbb-cp-kre و اعداد README پاها (۳۳/۲۱/۲۹/۸ از ۹) — جلسهٔ بعد

