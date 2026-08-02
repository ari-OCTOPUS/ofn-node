---
type: architecture
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, integration, telegram, miniapp, obsidian, fugu, governor]
created: 2026-08-02
updated: 2026-08-02
created_by: agent
sources:
  - "[[06 - Architecture Maps/OCTOPUS-CURRENT-TRUTH]]"
  - "[[_ops/implementation_reports/MINIAPP-UI-COCKPIT-2026-08-02]]"
---

# OCTOPUS — Integration Status

<!-- BEGIN GENERATED: vault-docs lane, 2026-08-02. ویرایشِ انسانی زیرِ «Owner notes». -->

> **مقیاسِ وضعیت** (عمداً چهارتایی، نه دوتایی):
> **WIRED** = مسیرِ صداکننده تا انتها دنبال شد · **PARTIAL** = بخشی وصل، بخشی نه ·
> **ORPHAN** = کد هست، صداکننده نیست · **UNKNOWN** = نسنجیدم.
> «فلگ روشن» به‌تنهایی WIRED نیست. «تست سبز» هم نیست.

## Track A — ops runtime

| قطعه | مسیر | وضعیت | شاهد |
|---|---|---|---|
| موتورِ action | `_ops/agi2027_control/ops_actions.py` | **WIRED** | از `miniapp_gateway` (POST `/api/actions`) و `miniapp_state` صدا زده می‌شود |
| owner gate | همان، `OpsActionEngine.execute` | **WIRED** | `if not actor.get("is_owner"): DENIED owner_gate_failed` — اولین شرطِ تابع |
| allowlist ِ action | همان، `ALLOWED_ACTIONS` | **WIRED** | ۶ عضو: `lead.create, lead.add_note, lead.update_stage, task.create, task.done, value.record_event` |
| مسدودسازیِ اتوماسیونِ بیرونی | همان، `BLOCKED_PREFIXES` | **WIRED** | ۷ پیشوند، **قبل از** allowlist چک می‌شود (یعنی حتی اگر کسی اشتباهی allowlist کند، باز رد است) |
| idempotency | `_ops/agi2027_control/runtime.py::IdempotencyStore` | **WIRED** | `execute` قبل از هر نوشتن `begin(key)` می‌زند؛ `DUPLICATE` بی‌اثر برمی‌گردد |
| audit log | `runtime.py::AuditLog` → `ops-action-audit.jsonl` | **WIRED** | `execute` در پایان همیشه `append` می‌کند — «ثبت همیشه، گیت فقط روی تحویل» |
| DBِ محلی | `_ops/agi2027_runtime/octopus_ops.sqlite3` | **WIRED** | ۴ جدول: `leads, lead_notes, tasks, value_events` |
| فلگ‌های runtime | `_ops/agi2027_runtime/managed_flags.json` | **WIRED** | `OCTOPUS_WIRE_TG_CONTROL=1`, `..._LEAD_OUTBOUND_WAL=1`, `..._VALUE_LEDGER=1` |

**صادقانه:** فایل‌های `octopus_ops.sqlite3` و `ops-actions-idempotency.sqlite3` در
`git status` **untracked** اند. برای فایلِ داده این احتمالاً درست است (نباید کامیت شود)،
ولی هیچ `.gitignore` ای را برایشان نسنجیدم → UNKNOWN.

## Track B — 4D / brain

| قطعه | مسیر | وضعیت | شاهد |
|---|---|---|---|
| درِ واحدِ مدل | `_ops/cortex/model_router.py::ask` خطِ ۴۲۶ | **WIRED** | wrapperِ `_ask_impl` + ثبتِ سوخت؛ tierها از `TASK_TIERS` |
| ردهٔ پولی پشتِ دوقفله | همان، `paid_gate()` | **WIRED** | تاریخِ phase + `ACTIVATION-CORTEX-PAID.flag` |
| نگاشتِ کار→رده | همان، `TASK_TIERS` | **WIRED** | ۱۷ کلید؛ ناشناخته → `local` |
| ردهٔ واقعی | همان، `_TIER_ROLE` | **PARTIAL** | فقط `secondary→glm` و `primary→orchestr`. نقشِ `premium` (fugu-ultra) از `ask()` **دست‌نیافتنی** است. رده‌ای به نامِ `cyber` یا `ultra` وجود ندارد. |
| آداپتورِ حاکمیت | `_ops/budget/governor.py` | **ORPHAN (ولی حالا تست‌دار)** | صفر صداکنندهٔ **تولیدی**؛ تنها importکننده خودِ تستش است. `test_governor_routing.py` ۱۷/۱۷ سبز. هر دو فایل **untracked**، و تست در `run_all.py` **ثبت‌نشده** |
| ماژول‌های cortex | `_ops/cortex/*.py` | **UNKNOWN** | ۳۸ فایل؛ این جلسه فقط `model_router`, `wlos_bridge`, `fugu_quota` (نام) را باز کرد |
| ماژول‌های heart | `_ops/heart/*.py` | **UNKNOWN** | ۱۷ فایل؛ فقط `fuel_meter` غیرمستقیم از `model_router` دیده شد |

**خطرِ ردهٔ ۱:** `_ops/budget/governor.py` (۱۹KB، کامل، با contract و تصمیم و ثبت) در git
نیست. یک `git clean` یا یک worktree switch آن را می‌بَرد. → `OCTOPUS-RISK-REGISTER` R-1.

## Telegram UI

| قطعه | مسیر | وضعیت | شاهد |
|---|---|---|---|
| هوکِ کنترل‌پلین در بات | `_ops/telegram_center/center.py::_handle_message` | **WIRED** | `from agi2027_control.integration import try_handle_control` داخلِ همان تابع |
| فرمان‌های کنترل | `_ops/agi2027_control/integration.py::CONTROL_COMMANDS` | **WIRED** | ۱۱ فرمان: `/ops /repair /impact /fugu /outbound /projectf /ui /open /truth /legs /approvals` |
| fallthrough سالم | همان | **WIRED** | فرمانِ غیرکنترلی → `None` ⇒ `/now /lead /deal` دست‌نخورده |
| فلگِ کنترل | `managed_flags.json` یا `OCTOPUS_WIRE_TG_CONTROL=1` | **WIRED** | در فایل `="1"` است |
| دکمهٔ داشبورد در خانه | `center.py::_home_keyboard` | **PARTIAL** | فقط با `OCTOPUS_TG_MINIAPP=1` **و** فایلِ URL؛ الان URL نیست ⇒ دکمه وجود ندارد |
| gateway ِ HTTP | `_ops/telegram_center/miniapp_gateway.py` | **PARTIAL** | routeها هستند؛ اجرای زنده روی پورت سنجیده نشد |
| تب‌های cockpit | `_ops/telegram_center/miniapp/index.html` | **WIRED (۸ تب)** | `home, studio, outbound, approvals, legs, value, registry, truth` — هر ۸ تا renderer دارند |
| `X-Tg-Init-Data` در frontend | `miniapp/app.js::tgHeaders` | **WIRED** | روی هر `api()` و `apiPost()` سوار می‌شود |
| اعتبارسنجیِ initData در backend | `miniapp_gateway.py` → `validate_init_data` | **WIRED** | بدونِ token/owner **یا** initDataِ نامعتبر → `403` |
| رفتار در گروه در برابر DM | — | **UNKNOWN** | نسنجیدم. سابقهٔ ثبت‌شدهٔ این سیستم: پلِ فرمان و سیاستِ ورودیِ گروه دو لایهٔ **مستقل**اند و منوی مسلح می‌تواند به گروه نرسد. فرض نکن. |

**گپِ اصلیِ باز:** `/api/ops` هیچ بخشِ `brain` / `governor` / `obsidian` / `next_steps` ندارد و
هیچ زیرـendpointی (`/api/ops/...`) وجود ندارد. سنجیده شد با فراخوانیِ مستقیمِ
`get_ops_state()` → کلیدها فقط `status, leads_total, lead_stages, tasks_total, task_status,
value_events_total, value_events_per_leg, actions`. **lane دیگری همین حالا روی این است**؛
قبل از دست‌زدن دوباره بسنج.

## Obsidian

| قطعه | مسیر | وضعیت | شاهد |
|---|---|---|---|
| validatorِ فرانت‌متر | `04 - Architect System/scripts/validate_frontmatter.py` | **WIRED** | اجرا شد: ۳۹۷ نوت، ۲ خطای از پیش موجود |
| validatorِ لینک | `04 - Architect System/scripts/find_broken_links.py` | **WIRED** | اجرا شد: ۲۰۰۴ نوت، ۸ شکسته در لایهٔ دست‌چین |
| لایهٔ حقیقت داخلِ vault | `06 - Architecture Maps/*` (همین سندها) | **WIRED (سند)** | طبقِ حکمِ مالک: vault، نه `docs/` |
| خواندنِ truth توسطِ cockpit | `miniapp_state.py::_TRUTH` و `runtime.py` `/truth` | **PARTIAL — به vault وصل نیست** | هر دو `OCTOPUS-CURRENT-TRUTH-2026-08-02.md` در **ریشهٔ repo** را hardcode کرده‌اند |
| نوشتنِ خودکار در vault | — | **UNKNOWN** | `06 - Architecture Maps/VAULT-UPDATER-spec.md` یک **spec** است؛ پیاده‌سازیِ زنده‌ای پیدا نکردم |
| merge strategy | `.gitattributes` | **WIRED** | `*.md merge=union` — به همین دلیل سندهای مشترک با append تکراری می‌شوند |

## Fugu / Governor

| قطعه | مسیر | وضعیت | شاهد |
|---|---|---|---|
| قراردادِ فراخوانی (۱۰ فیلد) | `_ops/budget/governor.py::normalize` | **پیاده، ولی ORPHAN** | دقیقاً `task_id, brain, purpose, expected_artifact, risk, importance, contains_secrets, allow_ultra, is_write, cache_key` |
| هستهٔ تصمیم | همان، `decide()` | **پیاده، تابعِ خالص** | اجرا شد؛ ۷ قاعده به ترتیب |
| گاردِ secret | همان، قاعدهٔ ۲ + گاردِ دومِ تحویل در `ask()` | **پیاده (دولایه)** | `contains_secrets` ⇒ `local` + `redact`؛ و در `ask` اگر tier راه‌دور شد ⇒ رد |
| گاردِ نوشتن | همان، قاعدهٔ ۱ | **پیاده** | `is_write` ⇒ `route="approval_gate"`، حاکم خودش مجوز نمی‌دهد |
| کش | همان، `_CACHE` (فقط حافظه، LRU ۱۲۸) | **پیاده** | hit ⇒ صفر تماسِ مدل |
| ثبتِ تصمیم | همان، `record()` → `state/governor/decisions.jsonl` | **پیاده** | محتوا-آزاد؛ `cache_key` هش می‌شود |
| فلگ | `OCTOPUS_WIRE_GOVERNOR` | **خاموش، بیرونِ `PAPER_FULL_FLAGS`** | خانه‌قاعده رعایت شده |
| **صداکنندهٔ تولیدی** | — | **هیچ** | grep: صفر. هیچ کدِ تولیدی `governor.ask` را صدا نمی‌زند؛ تنها importکننده خودِ تست است |
| **تست** | `_ops/tests/test_governor_routing.py` | **هست — ۱۷/۱۷ سبز** | اجرا شد. هر دو قفلِ secret را **جداگانه** می‌سنجد (وگرنه جهش روی هرکدام را آن‌یکی می‌پوشاند). ⚠️ `test_governor_contract.py` و `test_governor_lapsed_deadline.py` ماژولِ **دیگری** (`governor_epoch.py`) را می‌سنجند — نامِ مشابه، پوششِ صفر |
| **git** | — | **untracked (هر دو فایل)** | `?? _ops/budget/governor.py` و `?? _ops/tests/test_governor_routing.py`؛ تست در `run_all.py` هم ثبت نشده |
| سهمیهٔ fugu | `_ops/cortex/fugu_quota.py` | **WIRED** | `model_router._ask_paid` آن را `reserve/ok/fail` می‌کند |

قراردادِ کامل + قواعدِ مسیریابی: [[06 - Architecture Maps/FUGU-CALL-CONTRACT|FUGU-CALL-CONTRACT]].

## Next

1. **N-1** — دو خواننده‌ی truth را به این vault بِبَر.
2. **N-2/N-3** — `governor.py` را track کن، تست بده، یک صداکنندهٔ واقعی پشتِ فلگِ خاموش.
3. **N-4** — بخش‌های `brain/governor/obsidian/next_steps` در `/api/ops` (lane دیگر).
4. **N-5** — mojibake ِ `app.js`.
5. **N-6** — رفتارِ گروه در برابر DM را بسنج.

کاملش: [[06 - Architecture Maps/OCTOPUS-NEXT-ACTIONS|OCTOPUS-NEXT-ACTIONS]].

<!-- END GENERATED -->

## Owner notes

<!-- دستِ مالک. ایجنت این‌جا را بازنویسی نمی‌کند. -->
