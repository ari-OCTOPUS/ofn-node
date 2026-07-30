# ارزیابی وضعیت زنده زنجیره کنترل — ۲۰۲۶-۰۷-۳۰

بررسی فقط‌خواندنی بود؛ هیچ state/runtime/flag/process تغییر نکرد.

## حکم

`PARTIALLY_INTEGRATED`

## شواهد

### Cortex و قلب

- `cortex-state.json @ 15:57:46`، cycle=52، coherence=0.786.
- Cortex rhythm: 153.6s از `×2 heart-shadow(76.8s)`.
- `heart-shadow-latest.json @ 15:58:48`: period=51.25s، mode=shadow.
- `production_wire.open=false`.
- دلایل: delta_self_live منفی و hash قانون کنترل با SIM-REPORT ناهماهنگ.

نتیجه: قلب روی cadence مغز اثر دارد، ولی authority آن shadow است. رفتار باید صریحاً
`ADVISORY_SHADOW` نامیده شود، نه production authority.

### Self model و عصب‌کشی

- self-model آخرین بار 2026-07-29T15:26:56 نوشته شده.
- innervation @ 15:59:32: coverage=80%.
- dead spots: spine و self-model.
- ORGANISM-STATE در Cortex کهنه گزارش شده.

نتیجه: خودشناسی کدی گسترده است ولی snapshot لحظه‌ای تازه نیست.
`self_awareness_pct=99.7%` فقط پوشش docstring است، نه خودآگاهی phenomenological یا freshness.

### قطب‌نما و هدف

- prereg واقعی `2026-07-30#1:f7ceb1b7dd0e` موجود است.
- goal: attribution.claimed > 0.
- baseline=0، target=>0، direction به GOALS مالک لینک شده.
- actionهای ممنوع صریح: send/spend/merge/deploy/restart/arm/secret/delete.
- verdict مستقل هنوز وجود ندارد.

نتیجه: Direction→Goal→Prereg زنده است؛ Evaluation هنوز pending است.

### هدایت مالک

- API bounded وجود دارد: focus/think cadence/pause.
- `owner-guidance.jsonl` در snapshot فعلی وجود نداشت.
- هدایت فعلی روی فکر Cortex اثر می‌گذارد، نه مستقیم روی target منجمد.

نتیجه: هدایت طراحی شده ولی در snapshot فعلی directive فعالی مشاهده نشد.

### مأموریت و اقدام

- Mission Genome موجود است.
- Action Bridge ساخته و تست‌شده گزارش شده ولی caller زنده ندارد.
- SGC goal هنوز به Mission/Action/Receipt/Memory با trace مشترک وصل نیست.

نتیجه: حلقه ارزیابی هدف وجود دارد، حلقه کامل خودتکمیلی هنوز نه.

## شکاف‌های P0/P1

1. freshness خودمدل و ORGANISM-STATE.
2. authority صادق ریتم قلب سایه.
3. exact prereg → canonical mission.
4. mission → action request با mapping قطعی.
5. action → receipt.
6. receipt + metric → verdict مستقل.
7. outcome معتبر → memory.
8. trace مشترک در تمام مراحل.
9. هدایت چرخه جاری فقط bounded؛ تغییر هدف فقط چرخه بعد.

## چیزی که این پکیج اضافه کرد

- Snapshot با authority صریح.
- Compass واحد.
- سیاست ریتم shadow/production.
- سیاست هدایت و target freeze.
- ترجمه قطعی سه goal فعلی.
- Mission envelope مشترک.
- Action Request سازگار با Action Bridge.
- Link graph با trace و missing stages.
- runtime-safe seam که exact prereg را می‌گیرد.

وضعیت: `IMPLEMENTED_NOT_INTEGRATED`؛ هیچ ادعای LIVE نشده است.

---

## اجرای واقعیِ تست‌ها — ثبتِ ایجنتِ ارشدِ موازی، ۲۰۲۶-۰۷-۳۰

> این بخش را ایجنتِ ارشد اضافه کرد. سازندهٔ بسته صریح گفته بود
> `TESTS_NOT_EXECUTED_HERE` — این‌جا واقعاً اجرا شدند.

### نتیجه

```text
test_authority_policies.py    OK 4
test_pipeline.py              OK 3
test_runtime_seam.py          OK 2
test_snapshot_compass.py      OK 3
test_translator_graph.py      OK 5
test_snapshot_staleness.py    OK 10   ← نو، توسط ایجنتِ ارشد
                              ─────
                              ۲۷ چک · ۴۹+ assert
```

خطای bootstrap ِ `sys.path` که سازنده گزارش کرده بود واقعاً برطرف شده بود —
هر پنج فایل از اولین اجرا سبز شدند.

### ⚠️ دو محافظتِ ادعاشده که تست نداشتند

جهشِ اجراشده (نه ادعاشده) روی `snapshot.py` **سبز ماند** در دو مورد:

```text
auth = "STALE" → "AUTHORITATIVE"                 ⇒ سوییت سبز ماند
حذفِ blockers.append("self-model-not-fresh")     ⇒ سوییت سبز ماند
```

یعنی هر دو محافظت واقعاً وجود داشتند ولی **هیچ‌کس نمی‌دیدشان**. علت:
`t_stale_self_model_degrades_compass` فقط `compass` را با یک dict ِ دست‌ساز
می‌سنجید؛ خودِ `snapshot._state()` — که کهنگی را محاسبه می‌کند — هرگز با
ورودیِ کنترل‌شده اجرا نمی‌شد، و تنها بندِ زنده‌اش شرطِ شلِ
`in ("ADVISORY_SHADOW","STALE","MISSING")` داشت که هر سه را می‌پذیرفت.

**درس:** «تست نوشته شد» و «محافظت سنجیده می‌شود» دو چیزند. تنها سنجه، جهشِ
واقعاً اجراشده است.

### فیکسِ کوچکِ testability

`_state()` روی هر مسیرِ بیرون از `OPS` با `relative_to` استثنا می‌داد، پس یک
تابعِ **خالص** بیرون از یک مسیرِ خاص اصلاً قابلِ‌سنجش نبود — و همین علتِ ریشه‌ایِ
نبودِ آن دو تست بود. مسیرِ نمایشی fail-soft شد (۲ خط). رفتارِ تولیدی
بایت‌به‌بایت دست‌نخورده: در تولید همیشه داخلِ `_ops` صدا زده می‌شود.

### جهش‌های اجراشده — همه قرمز پس از افزودنِ گارد

```text
STALE → AUTHORITATIVE            ⇒ 7/10
حذفِ بازدارندهٔ self-model        ⇒ 9/10
مرزِ SLA معکوس (> → >=)          ⇒ 9/10
shadow مقدم بر کهنگی             ⇒ 7/10
JSON خراب → معتبر                ⇒ 8/10
قلبِ shadow → authoritative      ⇒ AssertionError
هدفِ منجمد قابلِ بازنویسی         ⇒ AssertionError
متنِ روش → classification_hint   ⇒ AssertionError
```

### capability manifest

طبقِ شرطِ handoff («فقط پس از سبزیِ تست‌ها») اضافه شد:
`_ops/unified_control/capability-manifest.json`. هر دو رجیستری می‌بینندش —
`capability_registry.discover_manifests()` = ۴ و ممیزِ مستقلِ
`telegram_contract/validate_contract.py` هم = ۴.

### وضعیتِ به‌روزشده

```text
CODE_WRITTEN            → TESTS_EXECUTED_AND_GREEN
TESTS_NOT_EXECUTED_HERE → ۲۷ چک سبز، ۸ جهشِ قرمزکننده
IMPLEMENTED_NOT_INTEGRATED  (بدونِ تغییر — هنوز صفر صداکنندهٔ runtime)
NOT_LIVE                    (بدونِ تغییر)
```

اتصال به runtime همچنان مسدود است: `self-model` کهنه (VQ-STATE-WRITE-001) و
authority قلبِ shadow هنوز رأیِ مالک ندارد — دقیقاً همان دو پیش‌شرطی که خودِ
`INTEGRATION-PLAN.md` گذاشته.
