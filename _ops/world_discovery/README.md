# World Discovery Organ — اندام کشف دنیای واقعی

> [FACT] namespace مستقل. side-effect بیرونی ندارد. بدون اتصال runtime تا پذیرش ایجنت ارشد.

این اندام حلقهٔ زیر را کامل می‌کند:

```
جهت مالک → مشاهدهٔ تازه از وب → کاندیداهای کشف → تأیید چندمنبعی + novelty + contradiction
→ تحلیل رقابتی → فرصت/تهدید سنجش‌پذیر → آزمایش کم‌خطر → شاهد بیرونی → تصمیم مالک
```

## معماری

```
world_discovery/
├── __init__.py
├── contracts.py            # dataclasses: Direction, Source, Observation, Discovery, Opportunity, Experiment, OwnerAction
├── direction_reader.py     # خواندن جهت مالک از charter/goals (read-only)
├── source_policy.py        # tiering A/B/C/D + استقلال منابع + URL/domain normalization
├── public_web.py           # retrieval از وب عمومی (retriever قابل‌تزریق) + redaction + injection-isolation
├── freshness.py            # staleness / oldest-newest source date
├── candidate_miner.py      # ساخت کاندیداهای خام از observations
├── novelty.py              # novelty receipt (fact/relation/strategic/action) vs octopus memory
├── contradiction.py        # contradiction search فعال → CONTESTED
├── competitor_intel.py     # ماتریس رقابت + مزیت نامتقارن
├── opportunity.py          # ساخت فرصت از تقاطع سیگنال‌ها
├── scorer.py               # امتیاز فرصت با فرمول نسخه‌دار
├── experiment_designer.py  # آزمایش E0/E1 ابطال‌پذیر
├── action_boundary.py      # L0–L4 + Owner Action Card + BLOCKED_BY_OWNER
├── octopus_adapter.py      # public API: observe/triangulate/discover/design_experiment/export_bundle
├── report.py               # report انسان‌خوان + bundle ماشین‌خوان
├── schemas/                # JSON schema v1
├── artifacts/              # bundleهای آزمایش (محلی، latest)
├── fixtures/               # test fixtures
└── reports/                # گزارش‌های اجرا
```

## استفادهٔ پایه

```python
from world_discovery import octopus_adapter as wd

direction = wd.load_direction()                      # از charter
observed  = wd.observe(direction)                    # کاندیداهای خام
verified  = wd.triangulate(top_candidate)            # چندمنبعی + novelty + contradiction
result    = wd.discover(direction)                   # یک discovery receipt یا no-valid-discovery
exp       = wd.design_experiment(result["discovery"])
bundle    = wd.export_bundle(result, output_dir)     # artifact اتمیک
```

## مرزها

- هیچ فایل ممنوع (بند E.1 charter) ویرایش نمی‌شود.
- ارسال تلگرام: فقط از طریق سوکت مستقل + Owner Action Card + رأی تازه.
- خرج = ۰. حساب = ممنوع. اطلاعات شخصی = ممنوع.

## تست

```
python _ops/tests/test_world_discovery_*.py
```

(نام‌های اختصاصی؛ `run_all.py` تغییر نمی‌کند.)

## وضعیت integration

`IMPLEMENTED_NOT_INTEGRATED` تا پذیرش ایجنت ارشد. see `INTEGRATION-MANIFEST.md`.
