# DEAD-CODE — کد مرده/بی‌فراخوان (با فایل:خط)

> Branch: `audit/zcode-20260828` · Date: 2026-08-28

## مخزن `langar` (تمام موارد verify شده با جستجوی فراخوان)

| Item | Location | Evidence |
|---|---|---|
| `_verify/` کپی‌های سایه | `langar/_verify/{db,migrations,config_fresh,proclient_fresh,budget_fresh}.py` | db.py در schema v3 گیر کرده (اصلی v8)؛ رفتار واگرا در experiment_report (`_verify/db.py:439` گارد `rv is not None` دارد که `db.py:626` ندارد) — اعتمادِ کاذب تولید می‌کند |
| BrainRouter | `brain/brain_router.py` (89 خط) | کامل، صفر فراخوان در تولید (فقط test_upgrades) |
| ACELoop | `core/ace.py` (133 خط) | کامل، صفر فراخوان (reflect_and_improve از SelfImprover مستقیم می‌رود) |
| CoachAgent | `agents/coach_agent.py` | در main.py:49 ساخته می‌شود ولی domains=[] ⇒ هیچ‌وقت انتخاب نمی‌شود؛ متدهایش مرده |
| MemorySystem.search_semantic | `core/memory.py:87` | ساخته+تست شده، در pipeline تولید صدا زده نمی‌شود |
| Contract.allows/must_ask | `core/contract.py` | فقط /contract برای نمایش؛ منطق اجازه اجرا نمی‌شود |
| tracer decorator | `observability/tracer.py` | sink وصل شده (main.py:100) ولی @trace روی هیچ تابعی نیست |
| ai.py fallback | `ai.py` | فقط وقتی _CORE=None اجرا می‌شود که در main.py هرگز رخ نمی‌دهد |
| world_model._weather | `core/world_model.py:74-77` | همیشه None (stub) |
| research_wiring_example.py | ریشه | خودش می‌گوید «not imported» |
| LocalBrain | langar ندارد — OFN دارد | see below |

## مخزن `ofn-node`

| Item | Location | Evidence |
|---|---|---|
| `hmac_variants()` | `kernel/auth.py:118-158` | خودِ docstring: «TEMPORARY — delete once a golden vector exists»؛ جامانده |
| LocalBrain wiring | `adapters/remote_brain.py:132` + `run.py build_brains` | کلاس هست، هیچ‌وقت instantiate نمی‌شود (rung LOCAL عمداً خالی — مستند ولی مرده) |
| Sender پشت outbox | `adapters/outbox.py` | طراحیِ عمدی: صف پر می‌شود، فرستنده نیست (README §6) — ثبت به‌عنوان تصمیم، نه باگ |
| `__version__` drift | `ofn/__init__.py:5` = 0.1.0 | مستندات v0.8.0 — شمارش تست هم در 4 سند 4 عدد متفاوت (377/492/536/1229) |

## درخت زندهٔ والت (F:\backup) — نمونه‌های کلیدی

| Item | Evidence |
|---|---|
| ConsolidationCycle NEVER-WIRED | کشف 2026-08-16، UNWIRED catalog کلاس ۹ (C-019) |
| retired control-brain | `_launchpad/second-brain-live/control-brain` — قرنطینه PII + 409 (2026-07-24) |
| 8 بات خواب از 10 | `_ops/BOTS-REGISTRY.md` — Ziman/Saba/Painting/Accounting/ControlBrain/LangarBot/4D/WLOS |
| پوشه‌های فانتوم | PHANTOM-DOCUMENTS.md (MEGA-PLAN-01/02، TYPED-EVENTS، …) |
| `FAIL, gate_e2e(...)` فایل‌های صفربایتی با نام خطا در ریشهٔ والت | دو فایل literal از خروجی تستِ کپی‌شده در شل — پاک‌سازی‌نشده |

> پیشنهاد: هیچ‌کدام را حذف نکنید (قاعدهٔ حذف‌ممنوع والت) — فقط MOVE به _Archive یا برچسب DEAD در رجیستری؛ برای مخازن گیت‌هاب حذف در PR پس از تأیید مالک مجاز است.
