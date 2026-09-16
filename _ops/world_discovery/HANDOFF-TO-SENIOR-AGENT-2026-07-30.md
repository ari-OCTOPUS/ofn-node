# HANDOFF-TO-SENIOR-AGENT-2026-07-30
# تحویل اندام کشف دنیای واقعی به ایجنت ارشد

> [FACT] این سند اطلاعات و دستور است، نه مجوز. هیچ‌چیز در آن به‌عنوان مجوز خرج/ارسال/deploy تلقی نمی‌شود.

---

## A. مأموریت و رأی‌های مالک
- دامنه: رقابت شرکت‌های بزرگ AI (Anthropic, xAI, Sakana AI, Moonshot/Kimi K3, Perplexity)
- جغرافیا: جهانی · افق: ۷ روز · خروجی: فرصت قابل آزمایش
- تعریف کشف: C+D+E · حداقل شاهد: ۲ منبع مستقل
- سطح عمل: **L3** (ارسال تلگرام فقط با رأی تازه) · خرج/حساب: **ممنوع**
- منبع رأی‌ها: `WORLD-DISCOVERY-CHARTER-2026-07-30.md` section A

## B. مرز عدم تداخل
- **هیچ فایل ممنوع ویرایش نشد** (organism.py، wiring.py، OCTOPUS-flags.cmd، state/**، و ...).
- **هیچ foreign hunk ای stage نشد.**
- **هیچ runtime state ای نوشته نشد.**
- تمام خروجی‌ها در `_ops/world_discovery/` (namespace مستقل).
- `cortex/web_research.py` و `budget/approval_channel.py` (dirty) فقط‌خواندنی بودند؛ از الگوی آن‌ها reuse شد ولی ویرایش نشدند.

## C. معماری اندام کشف
```
_ops/world_discovery/
├── __init__.py
├── contracts.py            # dataclasses + schema + validation
├── direction_reader.py     # خواندن جهت از charter (read-only)
├── source_policy.py        # tier A/B/C/D + استقلال منابع + URL/domain normalization
├── public_web.py           # retrieval + redaction + prompt-injection isolation + egress gating
├── freshness.py            # staleness + date extraction
├── candidate_miner.py      # observation → candidate (token-overlap grouping)
├── novelty.py              # novelty receipt (fact/relation/strategic/action) vs octopus memory
├── contradiction.py        # active contradiction search → CONTESTED
├── competitor_intel.py     # competitor matrix + asymmetry hypotheses
├── opportunity.py          # opportunity classification + build
├── scorer.py               # weighted scoring with versioned formula
├── experiment_designer.py  # E0/E1 falsifiable experiment design
├── action_boundary.py      # L0-L4 + OwnerGate + OwnerActionCard + telegram brief composer
├── octopus_adapter.py      # public API: observe/triangulate/discover/design_experiment/export_bundle
├── report.py               # human + machine report (atomic writes)
├── schemas/                # (placeholder for JSON schemas)
├── artifacts/              # machine bundles
├── fixtures/               # test fixtures + real observations 2026-07-30
└── reports/                # execution reports
```

## D. قراردادهای public API
```python
observe(direction) -> dict               # کاندیداهای خام؛ بدون اثر بیرونی
triangulate(candidate) -> dict            # چندمنبعی + novelty + contradiction
discover(direction) -> dict               # discovery receipt یا no-valid-discovery
design_experiment(discovery) -> dict      # آزمایش E0/E1 ابطال‌پذیر
export_bundle(result, output_dir) -> dict # artifact اتمیک
```
خروجی همگی pure-data، JSON-serializable، versioned (`world-discovery.*.v1`)، بدون secret، بدون side-effect بیرونی.

## E. کشف واقعی انجام‌شده
- منبع داده: **WebSearch زنده عمومی** (2026-07-30)، نه ساختگی.
- وضعیت: **NO_VALID_DISCOVERY** در سطح ادعای تک‌منبعی (صادقانه — هیچ ادعای واحدی با ۲+ منبع مستقل پیدا نشد).
- تحلیل رقبا در سطح رقیب: **معتبر** (ماتریس ۵×۲ با منابع مستقل).
- جزئیات: `reports/WORLD-DISCOVERY-EXECUTION-REPORT-2026-07-30.md`.

## F. منابع و evidence graph
۱۵ hit واقعی از ۱۵ دامنهٔ مستقل در `fixtures/real-observations-2026-07-30.json`.
همه با tier classification + date + redaction + injection-check پردازش شدند.

## G. تحلیل شرکت‌های بزرگ و رقبا
هر ۵ رقیب با نقاط قوت/ضعف ساختاری + منبع در گزارش section ۲.

## H. مزیت نامتقارن اختاپوس
۴ فرضیه (ASYMM-001 تا 004) در گزارش section ۳. همه با confidence=۰ (نیازمند آزمایش).

## I. آزمایش پیشنهادی
`exp-asymm-002-pricing` (E0 — دادهٔ عمومی، TCO local vs API). در گزارش section ۴.

## J. تست‌ها و mutation proof
- ۸۵ تست PASS (`tests/test_world_discovery_*.py`).
- ۷ mutation proof predicate (source independence، novelty threshold، contradiction، external action، missing evidence، stale، prompt injection) — همه red-on-mutation تأیید شدند.

## K. فایل‌های ساخته‌شده
```
_ops/world_discovery/ (۱۷ فایل ماژول + مستندات + artifacts + fixtures + reports)
_ops/tests/test_world_discovery_{contracts,sources,novelty,contradictions,competitors,action_boundary,e2e}.py
```

## L. فایل‌های عمداً دست‌نخورده
- `_ops/organism.py`, `_ops/wiring.py`, `_ops/OCTOPUS-flags.cmd`, `_ops/state/**`, `_ops/cortex/*`, `_ops/budget/approval_channel.py`, `_ops/SELF-GOAL-CHARTER*`, `_ops/SGC-14-*`, `_ops/tests/run_all.py`, `_memory/**`, `_ops/neural/**`.
- همهٔ فایل‌های dirty ایجنت ارشد.

## M. integration manifest
`INTEGRATION-MANIFEST.md` — اتصال تلگرام + runtime با patch پیشنهادی، **بدون اعمال**.

## N. patch پیشنهادی و caller پیشنهادی
```python
# پس از پذیرش ایجنت ارشد + رأی مالک:
from world_discovery import octopus_adapter as wd
result = wd.discover(wd.load_direction().as_dict())
wd.write_report(result, output_dir)
# اتصال تلگرام: TelegramOwnerGate در فایل جدید مستقل (telegram_owner_gate.py)
# که approval_channel.send_text را صدا می‌زند — فقط با رأی.
```

## O. owner gates
- ارسال تلگرام: **BLOCKED_BY_OWNER** تا رأی تازه.
- خرج/حساب: ممنوع.
- فعال‌سازی retriever زنده در-process: نیاز به رأی (برای DISCOVERY_VALIDATED در سطح ادعا).

## P. ریسک‌ها
- Retriever زنده در sandbox مسدود است → validation سطح ادعا نیاز به integration دارد.
- novelty scan بر اساس corpus محلی است؛ اگر corpus کامل نباشد، false-novel ممکن است (ولی evidence sufficiency gate این را محدود می‌کند).

## Q. rollback
- حذف `_ops/world_discovery/` هیچ اثر runtime ندارد.
- هیچ فایل مشترکی ویرایش نشد.

## R. next action دقیق برای ایجنت ارشد
1. **بررسی** `WORLD-DISCOVERY-CHARTER-2026-07-30.md` و `INTEGRATION-MANIFEST.md`.
2. **تصمیم**: آیا `OCTOPUS_WIRE_WORLD_DISCOVERY` flag و caller در `organism.py`/`wiring.py` اضافه شود؟ (فقط با رأی مالک).
3. **اگر بله**: یک `TelegramOwnerGate` مستقل بساز که `approval_channel.send_text` را صدا بزند، و retriever زنده را تزریق کن (`wd.set_retriever(...)`).
4. **تست integration**: یک راند واقعی با retriever زنده اجرا کن تا validation سطح ادعا ممکن شود.
5. **بدون رأی مالک**: هیچ ارسالی نکن. owner gate روی `NoOpOwnerGate` بماند.

---

**وضعیت نهایی: `IMPLEMENTED_NOT_INTEGRATED`** — اندام و تست‌ها آماده‌اند؛ اتصال به runtime به‌علت مرز عدم‌تداخل + owner gate انجام نشده.
