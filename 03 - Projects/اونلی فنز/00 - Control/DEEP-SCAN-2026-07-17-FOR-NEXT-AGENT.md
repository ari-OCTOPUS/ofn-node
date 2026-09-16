---
type: control
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
created: 2026-07-17
created_by: deep-scan agent (ZCode)
tags: [project-f, deep-scan, handoff, read-first]
aliases: ["دیپ‌اسکن Project-F", "Deep Scan for Next Agent"]
purpose: "یک‌جا، خلاصهٔ فشردهٔ کل پروژه برای ایجنت بعدی — قبل از هر کاری این را بخوان."
---

# 🔭 DEEP SCAN — Project-F (اونلی فنز) — 2026-07-17

> **برای ایجنت بعدی.** این فایل خلاصهٔ راستی‌آزمایی‌شدهٔ کل پروژه است (کد + سند + state + git).
> **اول بخوان**، بعد بر اساس نقشِ مشخص‌شده‌ات در §۷ وارد کار شو.
> **قاعدهٔ containment همیشگی:** بیرون از این پوشه فقط «Project-F». صفر echo هویت/شهر/قومیت/محتوا. در این گزارش creator = **C**، operator = **A**.

---

## ۱. این پروژه چیست؟ (یک‌خطی + حقایق ثابت)

کسب‌وکار faceless محتوای **فقط‌پا** (غیر-explicit) با مدل درآمد از OnlyFans/Fansly، اجراشده از استرالیا، تیم دونفرهٔ **۵۰/۵۰**: **A** (ops/tech/marketing/finance) + **C** (تولید محتوا). فاز فعلی = **validation**.

**۸ قاعدهٔ قفل‌شده (immutable — تغییر فقط با verdict انسانی):**
1. فقط پا — بدون صورت/بدن/explicit.
2. geo-block کامل ایران در همهٔ لایه‌ها + بدون هدف‌گیری کاربر داخل ایران.
3. پرداخت فقط داخل‌پلتفرم — هرگز P2P/crypto/PayPal با خریدار.
4. بدون نقض ToS هیچ پلتفرمی.
5. privacy دوطرفه (creator + buyer).
6. بدون geo-fact شهری در کپی عمومی (فقط «Aussie»); سیگنال فرهنگی فارسی فقط بصری.
7. بیرون پوشه فقط «Project-F»; صفر echo هویت.
8. ۱۸+ با consent ثبت‌شده; مرزِ C (ردِ بدن) بر همهٔ پلن‌ها حاکم.

**مرجع ماشین‌خوان:** `PROJECT-F-CONTROL-MANIFEST.json` 🏆
**منشور (charter):** `CLAUDE.md`

---

## ۲. وضعیت واقعی همین امروز (هیچ‌چیز متورم نشده)

| محور | وضعیت |
|---|---|
| اجرای بیرونی (اکانت/پست/شوت/درآمد واقعی) | **صفر.** هیچ اکانتی ساخته نشده، هیچ پستی منتشر نشده، هیچ شوتی اجرا نشده، صفر درآمد. |
| کد ساخته‌شده | **همهٔ propose-only.** pipeline + studio + cockpit + brain + ۳ safety net + Layer-2 (Fan CRM, Vault, KPI, Octopus bridge, FAQ). |
| تست‌ها | **۱۴۸ تست سبز** (۱۲ فایل تست — `tests/` + `*/test_*.py`). |
| بلاکر ریشه‌ای | **GATE 0** (محل اقامت C ثبت نشده → Branch A/B) — **به‌صورت temporary-A فرضی حل‌شده ۲۰۲۶-۰۷-۱۶** ولی هنوز کامل ثبت/قفل نیست. |
| پلن لانچ | **۲۰۲۶-۰۷-۱۶:** «Full Aggressive با safety nets» تأیید شد (VERDICT PF-V5 = no→پلن کامل). LAUNCH-RUNBOOK ساخته شد. |
| Safety nets | ✅ ساخته‌شده: DM-HITL + Warmup-Guard + Warning-Kill (۳۸ تست، ۱۰۰/۱۰۰). |
| پوشهٔ پروژه در git | **۹ فایل dirty** (تمیز تقریباً). کل repo = ۳۰۵ فایل dirty (به‌خاطر `_ops` همزمان — تأیید شد). |
| branch | `master` در `F:/backup`. ۲۳ worktree در `.claude/worktrees/` (بعضی **stale** — همیشه با مسیر مطلق main-vault کار کن). |

---

## ۳. مهم‌ترین تغییر ۲۰۲۶-۰۷-۱۶ (دیروز) — حتماً بدان

یک **چرخش استراتژیک** رخ داد که با تمام اسناد قبلی (HANDOFF-2026-07-12 که می‌گفت «contained propose-only») در تضاد است:

1. **VERDICT PF-V5:** از «فقط research/draft» به **«Full Aggressive Launch با safety nets»**.
2. **VERDICT PF-V1/V2:** GATE 0 به‌صورت **temporary-A** فرضی حل شد (محل اقامت مشخص، Branch A فرضی) — ولی توافق مکتوب **deferred** تا اولین درآمد (PF-V3).
3. **VERDICT PF-LAUNCH-SAFETY:** ۳ safety net ساخته شد.
4. **PF-STATE-RESET-V1:** `studio/drafts.json` از ۲۴۴ ردیفِ تستی به `[]` ریست شد (به `_Archive/studio-state-snapshots/` منتقل شد).
5. اسناد جدید: `LAUNCH-RUNBOOK-2026-07-16.md`، `LAUNCH-SAFETY-NETS-2026-07-16.md`، `LAYER2-ARCHITECTURE-2026-07-16.md`.

⚠️ **پس `HANDOFF-NEXT-AGENT.md` (۲۰۲۶-۰۷-۱۲) قدیمی/ناقص است** — می‌گوید «contained، منتظر G0» ولی تصمیم دیروز جلوتر رفته. همیشه تاریخ فایل‌ها را چک کن و جدیدتر را ملاک قرار بده.

---

## ۴. معماری کد (Inventory فشرده)

### DataSpine (Layer 2 — مرکز دادهٔ یکپارچه)
`brain/store.py` (۴۷۰ خط): `FanDB` + `VaultBank` + `KPIRollup` + `OctopusState`. State در `langar/{fan_db,vault,kpi,octopus}.json`. صفر PII (fan_id = sha1(alias)[:12]).

### مغز (`brain/`)
| فایل | خط | وضعیت | نقش |
|---|---|---|---|
| `dual_brain_v3.py` | ۴۱۸ | ✅ **فعال** | ۱۰ ThinkingBrain + ۷ CommBrain. به‌کار‌گرفته‌شده در orchestrator/langar/studio. |
| `acquisition.py` | ۳۲۱ | ✅ فعال | هوشِ اکتساب؛ `with_bandit()` اختیاری. |
| `acquisition_pipeline.py` | ۲۹۳ | ✅ فعال | صف propose-only: draft→approve→finalize. **`_SAFE_HOOKS` = ۵ هوکِ نمونه.** |
| `learning.py` | ۲۹۶ | ✅ فعال | ThompsonBandit + UCB1 — **باگِ greedy رفع شد**. |
| `dm_pipeline.py` | ۲۰۴ | ✅ فعال | صف DM HITL — **هیچ متد send/transmit ندارد**. |
| `guards.py` | ۲۸۷ | ✅ فعال | WarmupGuard + ChannelLocks (fail-closed). |
| `store.py` | ۴۷۰ | ✅ فعال | DataSpine. |
| `faq_engine.py` | ۱۳۸ | ✅ فعال | auto-draft برای DM ورودی (HITL). |
| `ab_tracker.py` | ۹۷ | ⚠️ **orphan** | A/B test — کاملاً ساخته، هیچ callerی. |
| `content_engine.py` | ۹۹ | ⚠️ orphan | ایده‌پردازی — seed = `random.Random(42)` (دترمینیستیک). |
| `lifecycle.py` | ۹۲ | ⚠️ orphan | churn prediction — هیچ callerی. |
| `kpi_dashboard.py` | ۷۶ | ⚠️ orphan | HTML renderer. |
| `project_f_brain.py` | ۲۴۸ | 🔴 **dead** | superseded توسط v3. هیچ importerی. |
| `dual_brain.py` | ۳۱۸ | 🔴 dead | superseded. |

### کاکپیت/استودیو (`langar/` + `studio/`)
| فایل | خط | وضعیت | نقش |
|---|---|---|---|
| `langar/langar_bot.py` | ۹۱۶ | ✅ فعال | کاکپیت تلگرامی A. ~۴۶ دستور. `OpsecGuard` fail-closed، `CostMeter`، `SelfModel`. |
| `langar/{pf,dm,fan,vault}_admin.py` | ~۱۰۰ هرکدام | ✅ فعال | dispatcherهای دستورهای `/pf_* /dm_* /fan_* /vault_*`. |
| `studio/saba_studio.py` | ۵۰۳ | ✅ فعال | رابط تلگرامی C با inline-keyboard + cert-gate. |
| `studio/content_studio.py` | ۲۲۵ | ✅ فعال | موتورِ مدیریت درفت. |
| `studio/affirm.py` | ۶۷ | ✅ فعال | لایهٔ تحسینِ content-free. |
| `studio/studio_telegram.py` + `_v3.py` | ۲۳۹/۱۹۵ | 🔴 dead | superseded توسط `saba_studio.py`. |

### Orchestrator + Octopus Core
| فایل | وضعیت | نکتهٔ حیاتی |
|---|---|---|
| `orchestrator.py` (۱۷۰) | 🔴 **dead at runtime** | به ۶ ماژولِ `_ops/neural/` وابسته‌ست که در scope پروژه **وجود ندارند**. `_VAULT = _HERE.parent.parent` به `F:\backup` می‌رود. `/octopus_tick` fallback به «isolated heartbeat». |
| `octopus_core/*` | ⚠️ ساخته‌شده، **نیمه‌سیم‌شده** | `event_bus.py`, `actuator.py`, `capability_registry.py`, `telemetry.py`, `health.py`, `integration/langar_integration.py` — ولی `attach_to_langar()` در langar_bot **هرگز صدا زده نمی‌شود**. |

### قدم‌های «یک‌خطی» که سال‌ها ارزش می‌آورند (از ACTIVATION-REPORT)
- `pf_admin._default_pipe()` الان `vault=None` → **VaultBank سیم‌نشده‌ست** (pipeline به `_SAFE_HOOKS` fallback می‌کند). تزریقِ VaultBank = بانکِ واقعی جایگزینِ نمونه‌ها.
- `AcquisitionBrain(...)` → `AcquisitionBrain.with_bandit(...)`: بزرگ‌ترین ارتقای هوش (۱ خط).
- `langar_bot`: اضافه‌کردن `attach_to_langar(self)` = فعال‌سازی event_bus/telemetry/capability.

---

## ۵. تست‌ها — چه پوشش دارد، چه ندارد

**۱۴۸ تست سبز** در ۱۲ فایل:
| فایل | تعداد | پوشش |
|---|---|---|
| `tests/test_store.py` | ۲۴ | DataSpine + ۴ کلاس. |
| `tests/test_layer2_integration.py` | ۲۴ | fan/vault/faq/octopus/pipeline-vault. |
| `tests/test_dm_hitl.py` | ۱۴ | DM HITL + containment. |
| `tests/test_layer2_integration.py` | ۲۴ | integration. |
| `tests/test_langar_failclosed.py` | ۱۰ | fail-closed در langar. |
| `tests/test_warmup_guard.py` | ۱۱ | warm-up. |
| `tests/test_warning_kill.py` | ۱۳ | channel locks/full_stop. |
| `brain/test_acquisition_pipeline.py` | ۱۲ | pipeline. |
| `brain/test_learning.py` | ۱۱ | bandit/exploration/recency/eval. |
| `langar/test_langar.py` | ۹ | opsec/stranger-silence/kill/cost. |
| `langar/test_pf_admin.py` | ۷ | pf_admin. |
| `studio/test_saba_studio.py` | ۱۰ | submit/cert/capacity/halt. |
| `studio/test_affirm.py` | ۳ | affirm. |

**ماژول‌های بدون تست مستقیم:** `dual_brain_v3.py` (مغزِ فعال!), `project_f_brain.py` (dead), `dual_brain.py` (dead), `ab_tracker.py`, `content_engine.py`, `lifecycle.py`, `kpi_dashboard.py`, `dm_pipeline.py` (تست غیرمستقیم), `faq_engine.py`, `dm_admin.py`, `fan_admin.py`, `vault_admin.py`, `orchestrator.py` (dead).

---

## ۶. تعارض‌های باز + Verdictهای معلق (برای A)

### جدول تعارض‌ها (باید reconcile شوند قبل از اجرا)
| # | موضوع | نسخهٔ A | نسخهٔ B | وضعیت |
|---|---|---|---|---|
| ۱ | ساعتِ C | ~۳۰h/hفته (master-ref) | ~۳–۵h (MASTER-BUILD) → **۳h تأییدشده ۲۰۲۶-۰۷-۱۰** | ✅ بسته (۳h) |
| ۲ | نام برند | **Anar Soles** (تأییدیهٔ ۰۷-۰۵، صفر-collision) | Arch & Amber / Yalda Arch | ⚠️ منتظر verdict نهایی |
| ۳ | نردبان قیمت | MASTER-BUILD VIP $۳۵ | Playbook VIP $۲۰ / EXT-04 $۳-۵/۸-۱۵/۱۵-۳۰ | ⚠️ ۳ نسخه — یکی قفل شود |
| ۴ | نقش Fansly | mirror-of-OF (Playbook) | equal-weight-day-1 (MONETIZATION) | ⚠️ منتظر verdict |
| ۵ | «Persian»/«Sydney» در کپی | تحقیق بیرونی توصیه می‌کند | ۲ قاعدهٔ قفل‌شده ممنوع + Playbook خودم نقض دارد | ⚠️ OPEN (P0-opsec) |
| ۶ | body expansion | production plan دارد | C رد کرده → freeze/remove؟ | ⚠️ OPEN |

### Verdictهای معلق (VERDICT_QUEUE + OpenQuestions)
- **PF-STRUCT-V2:** اجرای MIGRATION-MAP (dedup + filing اسناد به 00–09) — **OPEN**.
- **PF-CODE-REFACTOR-V1:** rename شناسه‌های حاوی نام C در `studio/` (opsec) — **deferred** (PII در git نیست، فقط hygiene).
- ۱۱ verdict انسانی قدیمی‌تر در `THREAD-CLOSURE-D §۹` + OpenQuestions #۱–#۲۰ (برخی بسته‌شده).
- **GATE 0:** temporary-A، کامل نشده. توافق مکتوب (PF-V3) deferred.

---

## ۷. نقش‌های ممکن برای ایجنت بعدی + نقطهٔ شروع هرکدام

سه پرامپت/مسیر فعال وجود دارد. **اول مشخص کن کدام نقش توست**:

### مسیر الف — لانچِ Project-F (مدیریت کسب‌وکار)
- **پرامپت فعال:** `LAUNCH-RUNBOOK-2026-07-16.md` (موج ۲) + `PROMPT-NEXT-AGENT.md` (truthful cockpit).
- **نقطهٔ شروع:** مرحلهٔ ۵ ROADMAP (بانکِ کپیِ واقعی + سیم‌کردنِ VaultBank و LearningBridge — **بی‌نیاز به GATE 0**).
- **نکته:** هرگز به worktree‌های stale فکر نکن؛ روی main-vault با مسیر مطلق کار کن.

### مسیر ب — ارگانیسمِ اختاپوس (architecture/perception/security)
- **پرامپت فعال:** `04 - Architect System/octopus-build-prompts/NEXT-AGENT-PROMPT-2026-07-16-security.md` (بستنِ ۳ High از طریق ۱ auth-gate).
- **خوراک:** `ACTIVATION-REPORT-2026-07-16.md` (repo root — نقشهٔ فعال‌سازی) + `optimization/*.md`.
- **اولویت‌ها:** S1 (httpauth ~۴۰ خط)، S2 (_write_env non-destructive)، S3 (watchdog split-brain).

### مسیر ج — حسابداری (PocketSmith double-entry)
- **پرامپت فعال:** `MEGAPROMPT--accounting-upgrade-for-next-agent.md` (repo root).
- **موضوع:** ارتقای single-entry → double-entry ledger + COA + REA model. **پول = سنتِ integer.**

---

## ۸. ⚠️ خطرات و تله‌ها (حتماً بخوان)

1. **PII در `langar/langar_config.json`:** نام واقعی، شمارهٔ تلفن، آدرسِ کامل A ذخیره شده. فایل در commit `26a1955` **untrack شد و در `.gitignore`** قرار گرفت — ولی اگر قبلاً push شده، باید rotate شود. این **بزرگ‌ترین opsec ریسک** است.
2. **`docs/` و `research/` آینهٔ stale‌اند** — همیشه نسخهٔ root را بخوان (تأیید md5 در CARTOGRAPHY).
3. **`studio/drafts.json`** حالا `[]` است (ریست ۰۷-۱۶) — دیگر fixture تستی نیست.
4. **commit با pathspec:** این tree ~۳۰۵ فایل dirty از `_ops` دارد. `git commit` بدون pathspec کل index را می‌گیرد. همیشه `git commit -- <files>`.
5. **آنتی‌ویروس:** `git add` گاهی Permission denied `.git/objects` می‌دهد → retry با sleep.
6. **۲۳ worktree** در `.claude/worktrees/` — بعضی detached/stale. با `git worktree list` چک کن و فقط روی main-vault کار کن.
7. **`orchestrator.py` dead:** آن را standalone اجرا نکن؛ کرش می‌کند (وابسته به `_ops/neural`).
8. **استعارهٔ اختاپوس تزئینی نیست ولی ناقص:** observability/truth-cards زنده‌اند، **actuation فلج** است (هیچ motor cortex واقعی). `octopus_core` ساخته‌شده ولی نیمه‌سیم.
9. **verdict منفی = موفقیت:** اگر چیزی non-executable است، صریحاً بگو؛ نتایج را متورم نکن (سابقهٔ «گزارشِ مطمئنِ غلط» در vault هست).
10. **هرگز حذف؛ فقط انتقال** به `_Archive`/`_Duplicates`.

---

## ۹. ترتیب لود (در اولین جلسه)

۱) این فایل → ۲) `_memory/onlyfans-project-memory-2026-07-05.md` → ۳) `PROJECT-F-CONTROL-MANIFEST.json` → ۴) `CLAUDE.md` → ۵) `PROJECT.md` (Active Context) → ۶) جدیدترین فایل‌های ۲۰۲۶-۰۷-۱۶ (LAUNCH-RUNBOOK، LAYER2، SAFETY-NETS) → ۷) بسته به نقش‌ات، پرامپتِ مرتبط در §۷.

---

> **یک‌خطی:** پروژه‌ای که ۱۰۰٪ برنامه‌ریزی/کد شده، ۰٪ اجرا، ۱۴۸ تست سبز، ۳ safety net، **دیروز (۰۷-۱۶) تصمیم بر لانچِ کامل گرفته شد** — حالا تو باید یا لانچ را جلو ببری، یا ارگانیسمِ اختاپوس را سیم‌کنی، یا حسابداری را ارتقا دهی. اول نقش‌ات را مشخص کن.
