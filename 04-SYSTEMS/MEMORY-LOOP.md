---
type: systems-note
created: 2026-08-15 (شب — جاروی تست T1/T1b)
mission: C-012 فاز صفر Council Mesh — ترمیم حلقهٔ حافظه/یادگیری
level: A (همه با اجرای زنده)
related: "[[../01-TRUTH/CONTRADICTIONS|C-012]] · [[../08-PLANS/COUNCIL-MESH-v0.1|COUNCIL-MESH v0.1]] · [[../06-EVIDENCE/TEST-SWEEP-2026-08-16|TEST-SWEEP]]"
---

# MEMORY-LOOP — حلقهٔ حافظهٔ مغز 4d (C-012 فاز صفر)

## ۱. بیماری (تأییدشده)

`4d_system/brain/automation.py` حافظه را **write-only** می‌خواندنِش صفر بود:
- ۳ ارجاع نوشتن (`save_hypothesis` در create · `save_conclusions` در conclude · autoloop `save_experiment`)، صفر خواندن (`query_experiments`/`get_pending_hypotheses`/`search_vault` هرگز صدا نمی‌شدند)
- اثر زنده در DB: **۱۰۶۲ فرضیه، همهٔ pending (tested=0)، هیچ‌وقت مصرف‌نشده**؛ متن‌های تکراری تا **۲۹ بار** ثبت شده بودند
- `memory_read_patch.py` از ایجنت-معمار موازی موجود بود ولی **import نشده بود** (C-012)

## ۲. فیکس (فاز صفر — commit همین نشست)

| نقطه | کار | فایل |
|------|-----|------|
| introspect | خواندنِ تجربهٔ گذشته + آمار حافظه **قبل از** خودخوانی؛ خلاصهٔ «حافظه: N تجربهٔ گذشته» در رویداد | `automation.py::_job_introspect` |
| create | خواندنِ صفِ pending (≤۲۰۰) → **dedup** (شباهت ≥۰٫۹ با نرمال‌سازی نیم‌فاصله) → ثبت فقط اگر نو → **read-back از مسیر مصرف‌کننده** (`get_pending_hypotheses`) | `automation.py::_job_create` + `memory_read_patch.py` |
| conclude | جستجوی RAG در والت **قبل از** نتیجه‌گیری (bft وال: N قطعه در رویداد) | `automation.py::_job_conclude` |
| stale | تفکیک صف به کهنه/تازه با `transaction_time = ستونِ timestamp` (نگاشت صادقانه؛ شِما دست‌نخورده) — شمارش در رویداد create | `memory_read_patch.split_stale` |
| telemetry | هر خواندن → رویدادِ `memory.read`؛ هر read-back → `memory.readback`؛ هر دو در `trace_id` کارِ تصمیم | `memory_read_patch._emit_read/_emit_readback` + `events.py` (دو نامِ نو در VALID_EVENTS) |
| متریک‌ها | `telemetry_metrics(after_id)` از `dashboard_events` واقعی محاسبه می‌کند | `memory_read_patch.telemetry_metrics` |
| ضدِ نابودی | `__main__` دمو دیگر `clear_events()` پیش‌فرض نمی‌زند (۴۸ ردیفِ مانده از ۳۴۲۱۶، اثرِ clear های قبلی بود) — فقط با `DEMO_CLEAR_EVENTS=1` | `automation.py::__main__` |

## ۳. شاهد زنده (سطح A — 2026-08-15 ~20:0x)

اجرای ۴۸ تیکِ واقعیِ `AutomationController(use_llm=False, MOCK_MODE)` روی DB واقعی (بدون پاک‌کردن رویدادها، مارکر id=34216):

| متریک | هدف فاز صفر | نتیجهٔ زنده |
|-------|-------------|-------------|
| `memory_read_before_decision_ratio` | ≥ 0.95 | **1.0** (۱۸/۱۸ کارِ تصمیم: ۸ creative + ۳ conclude + ۷ introspect) |
| `memory_readback_success_ratio` | ≥ 0.99 | **1.0** (۱/۱ — dedup اجازهٔ فقط یک نوشتن داد؛ پوششِ بیشتر در تست‌ها) |
| dedup | — | از ۸ کارِ create فقط **۱** نوشت (۱۰۶۲→۱۰۶۳)؛ ۷ تکرار رد شد |
| خطا | — | ۴۸ تیک، صفر fail |
| هزینه | — | صفر تماس LLM (بودجهٔ 4d جابجا نشد؛ llm_budget.json همان 2026-07-12 ماند) |

فرمان بازتولید: `cd 4d_system && python -X utf8` + اسکریپتِ نشست (مارکر → ۴۸× `run_one()` → `memory_read_patch.telemetry_metrics(after_id=marker)`).

## ۴. تست‌ها (قانون: تست در همان commit)

- **نو:** `4d_system/tests/test_memory_loop_c012.py` — **۱۲/۱۲ سبز**؛ روی `AutomationController` واقعی با DB موقت (patch `memory.store.DB_PATH`): خواندن-قبل-از-تصمیم با trace مشترک، dedup (ثبتِ دوبارهٔ متنِ یکسان نمی‌کند)، read-back از مسیر مصرف‌کننده، stale با transaction_time، متریک‌ها از رویدادهای واقعی، و خواندنِ پس از تصمیم در ratio شمرده نمی‌شود
- **رگرسیون کل 4d:** `tests/run_all.py` → ۲۶۵ تست: ۲۶۱ سبز + **۴ شکستِ pre-existing** در `test_self_code_gate` (اثبات با git-stash: بدون تغییرات من هم همین چهار شکست) — ریشه: [[#۵]]

## ۵. تناقض‌های مرتبط

- **C-012 → resolved** با شاهد telemetry زندهٔ بالا (بند ۳)
- **C-013 (نو):** گاردِ self_code کلِ پروژه را TCB می‌بیند (REFERENCE_DIR → ریشه) — ۴ تستِ pre-existing را می‌شکند؛ جهت fail-closed امن است؛ فیکس پیشنهادی: fallback مسیر ناموجود `4D/` + رأی مالک

## ۶. چه ماند (رأی مالک)

1. **daemon مغز 4d روشن نیست** — آخرین اجرا 13:40 امروز با ۱ تیک. حلقهٔ حافظه حالا سالم است ولی daemon باید رسمی بالا بیاید تا telemetry پیوسته جاری شود (`python -m brain.daemon`؛ تصمیمِ اجرای ماهانهٔ مالک، بودجه‌دار). فیکس‌ها با ری‌استارت بعدی معتبر می‌شوند.
2. روشن‌کردنِ `OCTOPUS_CONSOLIDATION_DEDUP_FUZZY` (فلگ موجود، خاموش) برای گرفتنِ تکرارهای نزدیک‌به-یکسان در consolidation — فقط از `OCTOPUS-flags.cmd` + ری‌استارت رسمی.
3. صفِ ۱۰۶۲ فرضیهٔ pending: پاک‌سازی **ممنوع** (append-only)؛ pre-registration این‌بارها یا expiry سیاستی — رأی مالک.
