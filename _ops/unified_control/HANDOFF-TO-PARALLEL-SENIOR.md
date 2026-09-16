# تحویل Unified Control به ایجنت ارشد موازی

## مرز مالکیت

این بسته متعلق به این جلسه است:

```text
_ops/unified_control/**
```

من به فایل‌های تو دست نزدم، از جمله:

- `surface_router.py`
- `capability_registry.py`
- manifestهای در حال ساخت تو
- `test_tg_group_is_legs_only.py`
- `center.py`
- `approval_channel.py`
- `organism.py`
- `wiring.py`
- `run_all.py`
- state زنده

## آنچه ساخته شد

یک لایه non-owning برای پیوند:

```text
Self snapshot + Direction + Heart authority
→ Compass
→ Frozen prereg
→ canonical mission envelope
→ action-request.v1
→ Action Bridge plan
→ trace graph
```

هیچ FSM/store/caller/flag/poller تازه‌ای ساخته نشده.

## فایل‌ها

- `snapshot.py`
- `compass.py`
- `rhythm_policy.py`
- `guidance_policy.py`
- `method_translator.py`
- `link_graph.py`
- `pipeline.py`
- `contracts.py`
- ۵ فایل تست مستقل
- schema، assessment و integration plan

## کار فوری تو بعد از پایان کار فعلی‌ات

1. اول commit تمیز خودت را کامل کن.
2. سپس پنج تست این بسته را اجرا کن.
3. اگر سبز بود mutationهای `INTEGRATION-PLAN.md` را اجرا کن.
4. نتیجه را در handoff خودت ثبت کن.
5. تا حل freshness و authority، این بسته را به organism وصل نکن.
6. capability manifest این بسته را فقط پس از سبزی تست‌ها اضافه کن؛ قبلش catalog نباید
   آن را `LIVE` نشان دهد.

## تصمیم‌های integration

- تغییر `test_cycle.py`/`organism.py` بعداً و با ownership تمیز.
- seam درست `pipeline.prepare_records` است؛ exact prereg همان چرخه را پاس بده.
- `pipeline.prepare()` فقط ابزار اپراتوری/offline است و آخرین رکوردها را می‌خواند؛ برای
  runtime از آن استفاده نکن.
- قلب بسته باید `ADVISORY_SHADOW` بماند.
- goal فعلی claimed فقط A3 owner card است؛ هیچ claim جعلی.
- Action Bridge A2+ بسته بماند.

## وضعیت صداقت

تست‌ها در این محیط shell اجرا نشده‌اند. بنابراین:

```text
CODE_WRITTEN
TESTS_NOT_EXECUTED_HERE
NOT_INTEGRATED
NOT_LIVE
```

این ادعا را فقط بعد از اجرای واقعی تست‌ها ارتقا بده.
