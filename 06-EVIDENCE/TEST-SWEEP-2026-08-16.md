---
type: evidence-note
created: 2026-08-16 (session start ~19:5x local 2026-08-15 night continued)
mission: جاروی تست جامع — MEGAPROMPT-TEST-SWEEP-2026-08-16
agent: ZCode (GLM-5.3) — Test Engineer
rule: هر عدد با فرمان/فایل منبع‌دار · سطح A/B/C
---

# TEST-SWEEP 2026-08-16 — دفتر شواهد جلسهٔ جاروی تست

## STEP 0 — تصویر اولیه (سطح A — همه با اجرای زنده 2026-08-15 ~19:50 local)

### سلامت ارگانیسم
- **beat 36878 · halted=null/false · stop_organism=false · conflicts=[]** — منبع: `_ops/state/ORGANISM-STATE.json` (ts=2026-08-15T19:47:00)
- coherence: **0.979** · members 11 · beat 36850 — منبع: `OCTOPUS/CURRENT-TRUTH.md` بلوک auto (auto-generated 2026-08-15T09:20:41Z — قدیمی‌تر از state json؛ beat پیشرونده سازگار: 36850→36878)
- ۵ پروسهٔ python عضو (همهٔ PID تازه از ری‌استارت 19:16-19:20): organism.py=15036 (8771+8777) · cortex=3524 (8772) · live/server.py=19680 (8773) · miniapp_gateway=15880 (8774) · telegram_center=19288 (8776) — منبع: `Get-CimInstance Win32_Process` + `netstat -ano`
- دو پروسهٔ جانبی غیرعضو: `http.server 8765` (PID 5780، از 14/08) و `_ops/octopus_mcp/server.py` (PID 688، از 11:46) — رصد شد، دست نخورد

### baseline تست‌ها (STEP 0-2)

| مجموعه | ادعای مگاپرامپت | نتیجهٔ زنده (سطح A) | فرمان | وضعیت |
|--------|----------------|---------------------|-------|-------|
| NBB-CP | 171 | **171 passed in 2.49s** | `cd "03 - Projects/NBB-Control-Plane" && python -m pytest -o addopts= -q` | ✅ مطابق |
| hypothesis | 23 | **23 passed in 1.78s** | `cd _ops/hypothesis_engine && python -m pytest -o addopts= -q` | ✅ مطابق |
| suite working | 320 | **320 passed in 10.47s** | `cd Desktop\nbb-control-plane && python -m pytest -o addopts= -q` | ✅ مطابق |
| bayes | 21 | **21 passed in 0.26s** | `python -m pytest _ops/observatory/tests/test_bayesian.py -o addopts= -q` | ✅ مطابق |
| observatory(working) | 115 | **116 passed in 1.07s** | `python -m pytest _ops/observatory/tests/ -o addopts= -q` | ⚠️ +۱ نسبت به ادعا (TEST-COUNT قدیمی‌تر: 93) — احتمالاً تستی بعد از نگارش مگاپرامپت اضافه شده؛ ردیف کامل در TEST-COUNT |

### یافتهٔ جانبی STEP 0
- `_ops/tests/test_epistemic_bayes.py` (مخزن F:\backup): **صفر تابع تست** (`grep -c "def test_" → 0`) — فایل docstring+import دارد ولی بدنه‌ای ندارد؛ مرتبط با T3/C-007 (سوئیت epistemics واقعی کجاست؟)

## T1 — ترمیم حلقهٔ حافظه (C-012 فاز صفر) — ✅ کامل با شاهد زنده

**تغییرات:** `4d_system/brain/memory_read_patch.py` (بازنویسیِ کاملِ patchِ وصل‌نشده — خواننده‌ها + dedup + stale + read-back + telemetry) · `automation.py` (سه نقطهٔ تصمیم خواندن قبل از تصمیم + trace_id + عدمِ پاک‌کردنِ رویدادها در دمو) · `events.py` (دو نامِ نو در VALID_EVENTS) · تست نو: `4d_system/tests/test_memory_loop_c012.py`.

**تست‌ها (سطح A):**
- تست نو: **12 passed** (`cd 4d_system && python -m pytest tests/test_memory_loop_c012.py -o addopts= -q`)
- رگرسیون کل 4d: `python tests/run_all.py` → **265 tests: 261 pass + 4 pre-existing failures** (همه در test_self_code_gate؛ اثبات با git-stash که بدون تغییرات من هم همان‌ها می‌شکند → ریشه = C-013)
- یافتهٔ جانبی: این سوئیت ۲۶۵تایی در TEST-COUNT ثبت نشده بود — ثبت شد

**اجرای زنده (پذیرش معمار ارشد — سطح A، 2026-08-15 ~20:0x):**
- ۴۸ تیکِ واقعیِ AutomationController(use_llm=False, MOCK_MODE=true) روی DB واقعی، مارکر id=34216
- **memory_read_before_decision_ratio = 1.0** (۱۸/۱۸: ۸ creative + ۳ conclude + ۷ introspect) ≥ 0.95 ✅
- **memory_readback_success_ratio = 1.0** (۱/۱) ≥ 0.99 ✅ — n کوچک چون dedup فقط ۱ نوشتن را گذاشت؛ پوششِ بیشتر در تست‌ها
- **dedup زنده:** از ۸ create فقط ۱ ثبت (hypotheses: 1062→1063)؛ ۷ تکرار رد شد
- ۰ fail در ۴۸ تیک · ۰ تماس LLM (llm_budget.json همان 2026-07-12 ماند)

## T1b — ریشه‌یابی consolidation گیرکرده — ✅ ریشه + فیکس + تست

**ریشه (سطح A):** مگاپرامپت می‌گفت «insight یکسان در همهٔ cycleها». کالبدشکافی ۶۲۵ ردیف: ۳۱ مجموعهٔ متمایز؛ عصرِ asmr (۷۹ ردیف) قدیمی است؛ تکرارِ جاری «فیکس‌های تأییدشده: 3 · آگاهیِ میانگین: 0.73» ×۲۰ ردیفِ پیاپی (08-12→08-15). زنجیرهٔ علت:
1. منابعِ ورودی کند-تغییرند (mean آگاهیِ شبکهٔ ۴۰خانه‌ای: 0.71→0.73 طی روزها؛ پنجرهٔ verdict ثابت روی 3) — دادهٔ صادقانه
2. از سیکل ۵۳۷ (2026-07-28) `OCTOPUS_WIRE_LATENT_PERSIST=1` (flags.cmd:732) به هر ردیف بردار می‌دهد (۸۹/۸۹ ردیفِ پس از آن غنی)
3. شرطِ «مقصدِ fold نباید latent_vector داشته باشد» در تنها-گاردِ فعالِ dedup (مسیرِ بدون‌فلگ) → همیشه رد → هیچ تاشدنی → انفجارِ ردیف

**فیکس:** شرطِ مذکور از مسیرِ بدون‌فلگ برداشته شد (fold به ردیفِ غنی مجاز؛ بردار حفظ؛ sync_latent از طریق تطبیقِ last_cycle بردارِ تازه می‌نویسد — پوششِ خودِ کد برای ردیفِ تا‌شده). مسیرِ compress (فلگ‌دار) دست‌نخورده. فایل: `_ops/neural/consolidation.py` + تست نو `_ops/tests/test_consolidation_fold_rich.py`.

**تست‌ها:** نو ۴/۴ (pytest و اسکریپتی) · رگرسیون ۷ فایلِ consolidation/عصبی همه سبز (`test_consolidation_{compress_and_recall,fuzzy_dedup,wiring,latent,fold_rich}` + `test_neural` + `test_canonical_consolidation`).

**نکتهٔ استقرار:** پروسه‌های زنده کدِ قدیمی را تا ری‌استارتِ بعدی دارند؛ فیکس با ری‌استارت رسمی بعدی معتبر می‌شود. پیشنهاد جدی: روشن‌کردنِ `OCTOPUS_CONSOLIDATION_DEDUP_FUZZY` (فلگِ موجودِ خاموش) در همان پنجرهٔ فلگ — رأی مالک.

## C-registry این مرحله
- **C-012 → resolved** (شرط telemetry زنده برآورده شد)
- **C-013 ثبت شد** (گاردِ self_code: REFERENCE_DIR→ریشه، همه TCB؛ ۴ شکستِ pre-existing؛ فیکس پیشنهادی مستند، اعمال نشد — رأی مالک) — آزاد بعدی: **C-014**
