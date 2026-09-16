# Unified Control Link

وضعیت: `IMPLEMENTED_NOT_INTEGRATED`

این پکیج یک FSM یا store تازه نیست. مالکیت هیچ state کانونی را نمی‌گیرد؛ فقط رکوردهای
موجود را با یک trace مشترک پیوند می‌دهد و شکاف‌ها را صریح می‌کند:

```text
Self snapshot + Owner direction + Heart authority
                    ↓
              Unified Compass
                    ↓
Frozen Prereg → Canonical Mission → Action Request → Action Bridge Plan
                    ↓
       Receipt → Independent Verdict → Memory
```

## اجزا

- `snapshot.py`: تصویر فقط‌خواندنی با authority صریح.
- `compass.py`: جهت معنایی از مالک/پیش‌ثبت؛ قلب فقط تنظیم‌کننده ریتم.
- `rhythm_policy.py`: قلب سایه هرگز production جا زده نمی‌شود.
- `guidance_policy.py`: هدایت مالک نمی‌تواند target منجمد را وسط چرخه عوض کند.
- `method_translator.py`: ترجمه قطعی goal candidate به mission/action؛ بدون LLM.
- `link_graph.py`: یک trace برای direction→goal→mission→action→receipt→verdict→memory.
- `pipeline.py`: آماده‌سازی read-only و dry-run مستقل.

## اصول سخت

1. Self-model تازه نبود ⇒ readiness پایین می‌آید.
2. Heart `production_wire.open=false` ⇒ `ADVISORY_SHADOW`، حتی اگر فایل تازه باشد.
3. قلب cadence/risk را تنظیم می‌کند؛ جهت معنایی را نه.
4. هدف/target از prereg می‌آید و immutable می‌ماند.
5. متن method هیچ کلاس عمل یا مجوزی تعیین نمی‌کند.
6. goal ناشناخته بدون mapping بازبینی‌شده BLOCK می‌شود.
7. claimed هرگز با lead/claim جعلی تکمیل نمی‌شود؛ فقط owner card برای lead واقعی.
8. این پکیج caller زنده، فلگ، poller، network یا spend ندارد.

## وضعیت فعلی بدن در زمان طراحی

- قلب تازه ولی shadow-only و production wire بسته.
- Cortex ریتم خود را از قلب سایه گرفته بود.
- innervation حدود ۸۰٪؛ spine و self-model نقطه مرده.
- self-model بیش از SLA کهنه.
- هدف claimed پیش‌ثبت شده؛ هنوز verdict مستقل نداشت.
- Action Bridge ساخته ولی runtime caller نداشت.

## اجرای آینده

```bash
python -X utf8 F:\backup\_ops\unified_control\tests\test_snapshot_compass.py
python -X utf8 F:\backup\_ops\unified_control\tests\test_authority_policies.py
python -X utf8 F:\backup\_ops\unified_control\tests\test_translator_graph.py
python -X utf8 F:\backup\_ops\unified_control\tests\test_runtime_seam.py
python -X utf8 F:\backup\_ops\unified_control\tests\test_pipeline.py
```

در این محیط shell در اختیار این ایجنت نبود؛ فایل‌های تست نوشته شده‌اند اما اجرای آن‌ها
باید توسط ایجنت ارشد/موازی انجام و نتیجه ثبت شود. تا آن زمان ادعای TESTED یا LIVE ممنوع.
