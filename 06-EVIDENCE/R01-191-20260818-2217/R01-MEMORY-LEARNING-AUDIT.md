# R01-MEMORY-LEARNING-AUDIT — raw → episode → retrieval → validation → canonical

run: R01-191-20260818-2217 · سؤال محوری مالک: «یادگیری واقعی رخ می‌دهد یا فقط ذخیره/بازیابی؟»

## ۱. لایه‌های موجود (OBSERVED)

| لایه | شیء | نویسنده | خواننده | وضعیت |
|---|---|---|---|---|
| Raw event | `_ops/state/events.jsonl` (۴٬۶۷۵ رویداد یکتا) + `events.archive.jsonl` | حلقه‌های organism/cortex/live | UNVERIFIED — مصرف‌کنندهٔ مستقیم در این پاس دیده نشد | ACTIVE-WRITE |
| Chrono substrate | `chrono.db` — heartbeat 40,713 · checkpoint 40,712 · experience_meter 40,266 · anticipation ۶ · gated_effect **۰** | `_ops/chrono.py` | automation/دمون (فعلاً پایین) | ACTIVE |
| Long-term memory | `_ops/state/memory/memory.db` — ۴۸۳ سطر + FTS + confidence | `4d_system/memory/store.py` (save_experiment / save_hypothesis / claim_hypothesis / save_reflection / conversations) | query/load functions موجود | ACTIVE-SUSPECT: نوشته می‌شود؛ «خواندهشدن در تصمیم بعدی» اثبات نشد |
| Ingest خام | `_ops/state/memory/self-loop-ingest.jsonl` (۹۹۴KB، فعال 21:28) | `_ops/memory/self_loop_ingest.py` + cortex/improve.py | **یافت نشد** | **WRITE-ONLY SUSPECT** — دقیقاً الگوی «حافظهٔ write-only» |
| Research ingest | `research-ingest.jsonl` (۳۲KB، Aug 16) | research pipeline | UNVERIFIED | STALE |
| Hypothesis queue | c6/hypothesis-queue.jsonl (۴۳) + registry | hypothesis_engine | claim_hypothesis تست‌شده ولی **صداکننده wired نیست** (02-DECISIONS/CLAIM-HYPOTHESIS-WIRING-PROPOSAL) | PRESENT_UNWIRED |

## ۲. زنجیرهٔ یادگیری — داوری

```text
Observation → events.jsonl → (بازیافت به episode؟) → memory.db → بازخورد به تصمیم بعدی
                                  ▲                       │
                self-loop-ingest ─┘ (گیت admission: NOT FOUND)  └─→ اثر قابل مشاهده: NOT FOUND
```

- **ذخیره‌سازی: قوی.** چند لایه فعال با حجم و تازگی.
- **Validation/admission: غایب در مسیر ingest.** هیچ قراردادی (evidence-check، contradiction-search، تأیید) پیش از ورود محتوای مدل به فایل‌های ingest دیده نشد — خروجی LLM می‌تواند بی‌गیت بنشیند (اگرچه ورود به memory.db هنوز از store API می‌گذرد؛ عمق دقیق = F3).
- **Retrieval: confidence دارد؛ provenance و expiry ندارد** (store.py:67,140 — فقط confidence).
- **بازخورد: اثبات نشد.** `gated_effect=0` در chrono (هیچ اثر گیت‌شده‌ای ثبت نشده) و انتظار (anticipation) فقط ۶ ردیف؛ اسناد watch (کامیت 03c3bf0) خودشان می‌گویند «همهٔ y=1، calibration در ≥5.0 تست نشده».
- **حافظهٔ منفی: ABSENT** به‌عنوان لایهٔ مجزا (شکست‌ها/ردشدتن‌ها جای ساختاریافته ندارند — فایل‌های `_unwired_*` صفربایتی و پرچم‌ها نزدیک‌ترین چیزها هستند).

## ۳. نتیجهٔ ممیزی

**در وضعیت فعلی: سیستم «یاد می‌گیرد» به معنای انباشتن تجربه است، نه تغییر رفتار مبتنی بر آن.** حلقهٔ کامل (پیش‌بینی منجمد → outcome → امتیازدهی → تغییر سیاست) neither wired nor evidenced است. این دقیقاً همان چیزی است که F3 (قرارداد admission + evidence) و F5 (حلقهٔ عمودی کوچک) برنامهٔ بنیاد برایش طراحی شده‌اند.

## ۴. ورودی مستقیم برای F3

1. EVIDENCE_CONTRACT باید فیلدهای provenance/timestamp/confidence/expiry را برای هر رکورد حافظه اجباری کند (الان فقط confidence).
2. MEMORY_ADMISSION_RULE باید مسیر self-loop-ingest را یا ببندد یا از گیت عبور دهد؛ ورود متن مدل به هر فایلِ بدون گیت = نقض.
3. claim_hypothesis باید صداکننده بگیرد (پروپوزال موجود در 02-DECISIONS) — پیش‌نیاز «فرضیهٔ آزموده‌شده».
4. حافظهٔ منفی به‌عنوان لایهٔ پنجم (طرح شورای ۴) — پیشنهاد پذیرش در طراحی F3.
