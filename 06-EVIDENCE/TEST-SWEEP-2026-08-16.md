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

## T3 — سوئیت واقعی epistemics (C-007) — ✅ حل با اجرای زنده

**کشف کلیدی:** تست‌های `_ops` ساختارِ «اسکریپتِ خوداعتبارسنج» دارند (تابع‌های چک + گزارشگرِ خودشان، بدون `def test_`) — برای همین pytest از آن‌ها صفر collect می‌کرد و «سوئیت پیدا نشد» به نظر می‌رسید. اجرای درست = هر فایل جدا به‌عنوان پروسه.

**نتایج (سطح A — همه exit 0):**

| فایل | نتیجه |
|------|-------|
| test_epistemic_schemas | **45/45** ← منبعِ ادعای «۴۵/۴۵» |
| test_epistemics_receipt_chain | **20/20** ← منبعِ ادعای «۲۰/۲۰» |
| test_epistemic_benchmark | 6/6 |
| test_epistemic_c6c7 | 9/9 |
| test_epistemic_compose_build | 8/8 |
| test_epistemic_invariants | 19/19 |
| test_epistemic_runner | 11/11 |
| test_epistemic_selector_metrics | 24/24 |
| test_epistemic_bayes | 14/14 |
| test_phase4_epistemics | 13 ✅ |
| test_phase5_epistemics_wiring | 8 ✅ |
| **جمعِ هسته** | **۱۷۷ چکِ سبز · صفر شکست** |
| + مجاور (baseline 9 · held_out 9 · phase_gate 14 · adversarial 5) | ۳۷ → **جمع ۲۱۴** |

**داوری C-007:** هیچ‌کدام از ۶۵ و ۱۳۳ عددِ زنده نبود — ۶۵ فقط دو فایلِ نام‌برده بود؛ ۱۳۳ به هیچ فایلِ فعلی نگاشت نشد (تاریخی). **C-007 → resolved با فکتِ زنده = ۱۷۷.**

فرمان بازتولید: `cd _ops/tests && python -X utf8 <file>.py` برای هر فایل؛ یا مجموع در لاگِ run_all همین نشست.

## T2 — نخستین اجرای کاملِ رسمیِ run_all.py — ✅ انجام + C-006 بسته شد

- فرمان: `cd _ops/tests && python -X utf8 run_all.py` (لاگ کامل: `_baselines/run-all-output-20260815-sweep.log`) · ~۲۳ دقیقه · exit=1 (به‌خاطر ۱۶ فایلِ شکست)
- **۲۵۶ فایل در رانر → ۲۴۰ سبز (۲۹۳۱/۲۹۳۱ چکِ خودگزارشی) · ۱۶ شکست فایلی**
- از ۱۶: ۱ مورد (test_consolidation_latent) قراردادِ قدیمیِ fold را قفل کرده بود که T1b عمداً وارونه‌اش کرد → تست به قرارداد جدید به‌روزرسانی شد (تاریخ‌گذاری 2026-08-15 در خود تست) → **در اجرای مجدد سبز**
- ۱۵ شکستِ باقی‌مانده = **pre-existing** (هیچ‌کدام فایل‌های تغییرِ این نشست را import نمی‌کنند):
  - دریفِ تست↔کدِ زنده ×۹: miniapp_lifecycle_view (allowlist از ۵ به ۱۰ endpoint رشد کرده) · phantom_guards (۱۴ فلگِ بی‌اعلانِ نو) · llm_call_inventory (caller نو: owner_console/collab_model_adapter) · tg_callback_emitter_parity (کارتِ مردهٔ verb «approval») · miniapp_look_locked (۳ endpoint بدون مصرف‌کنندهٔ UI) · miniapp_ops_readmodel (نقش orchestr از ask() غیرقابل‌دسترس — یافتهٔ واقعی) · cortex_circuit_breaker (orchestr=open زنده — هم‌خوان با 429) · hebbian_eventclock (شکلِ خروجیِ دروازهٔ ADR-035) · collab_components (گاردِ live-state به‌درستی نوشتنِ تست را روی state زنده بست)
  - API drift تست↔ماژول ×۴: telemetry (snapshot/read_genome غایب) · discoveries (mark_nudged بدون high_water) · ti_collab_security + ti_redteam_injection (collaborator.callback حذف‌شده)
  - محیط ×۲: llm_routing_smoke (**429 واقعی از Fugu LIVE**) + همانِ circuit_breaker
- ریشهٔ «INTERNALERROR از ریشه»: تست‌های _ops اسکریپتِ خوداعتبارسنج‌اند — pytest-from-root ابزارِ درستِ جمع‌زدنِ این سوئیت نیست (مستند شد)
- **C-006 → resolved**: نه ۴14 نه ۴08 — فکتِ زنده = ۲۴۰ فایل سبز/۲۹۳۱ چک + ۱۵ دریف pre-existing

## T4 — shortfall=4 فلگ — ✅ سند (فیکس لازم ندارد)

- ۴ فلگِ غایب در هر ۵ عضو (snapshotهای flags-loaded-*.json): `OCTOPUS_SMTP_{FROM,HOST,PORT,USER}`
- ریشه (سطح A): در flags.cmd دو مرحلهٔ عمدی — خطوط ۱۲۹۰-۱۲۹۶ `set ...=1` (بخش arm) و سپس خطوط ۱۴۶۵-۱۴۶۸ مقدار را **خالی** می‌کنند («SMTP poison keys stay empty» — چون cred واقعی SMTP نیست) و cmd متغیرِ خالی را حذف می‌کند. پارسرِ فایل تعریف‌ها را می‌بیند، env نمی‌گیرد → shortfall=4 یکنواخت. **عمدی و بی‌خطر** — شمارنده کارش را درست کرده.

## T6 — حلقهٔ کامل رأی دکتر — ✅ e2e با voter مالک

- مسیر: کارتِ واقعیِ pending از outbox (mission=voice-test-single-20260815, gate=test) → شبیه‌سازی‌گر callback با **voter=TELEGRAM_OWNER_CHAT_ID** (بارگذاری .env در پروسه؛ مقدار هرگز چاپ نشد) از همان seam زنده (`doctor_link.handle_callback` → زیرپروسهٔ `doctor/cli.py votes`) → **ثبت در tg-inbox.jsonl** (callback_id=sim-t6-*؛ صادقانه قابلِ تفکیک) → **verdict(mission,test)=True** از inbox واقعی (pending عملکردیًت حل شد؛ شمارندهٔ vitals روزانه است و در سیکل بعد تازه می‌شود)
- نکتهٔ یافته‌شده: شبیه‌سازی‌گر باید فلگِ `OCTOPUS_WIRE_DOCTOR_TG=1` را هم می‌گیرد — در شلِ عادی هست وگرنه handle_callback بی‌صدا False می‌دهد
- رگرسیون تک‌صدا: نامِ `OCTOPUS_DOCTOR_BOT_TOKEN` در .env **وجود ندارد** (توکن مستقیم حذف‌شده ✓) · doctor_link فقط از `center._route_send` می‌فرستد ✓ · test_doctor_vote_bridge ۵/۵ (exit=0) ✓
- ۷ رأی واقعی مالکِ امشب + این e2e = حلقهٔ کامل از هر دو سو

## T8 — اعداد پاها در README ریشه — ✅ شمرده/اجرا شد

| ادعای README | نتیجهٔ زنده | وضعیت |
|---|---|---|
| Brushline ۸/۹ | **12 passed** (`cd "...brushline/60_code" && python -m pytest tests -o addopts= -q`) | رشد از ۸/۹ — عدد کهنه |
| کاریابی ۳۳ تست | **دقیقاً ۳۳ تابع تست** (شمارش ایستا 3+5+17+4+4)؛ اجرا بلاک: `sqlmodel` در پایتون اصلی نصب نیست |.inventory درست؛ اجرا نیازمند محیط |
| Ziman ۲۱ تست | **76 passed** (`cd "03 - Projects/Ziman Galerry/control-brain" && python -m pytest tests -o addopts= -q`) — run_tests.py خودش خراب است (به test_secrets حذف‌شده ارجاع می‌دهد) | رشد از ۲۱ — عدد کهسته |
| Project-F ۲۹ | **۶۸ چکِ ✅** (test_project_f 21 + test_deep_pf 26 + test_pf_full 21) | رشد از ۲۹ |

پیشنهاد (propose-only): جدولِ README با اعداد زنده به‌روزرسانی شود + اصلاح تک‌خطیِ ارجاع stale طبق C-004.

## T10 — معمای evidence#4 حل + مدل وظیفهٔ سخت پیش‌ثبت شد — ✅

- **evidence#4 (17:36:31):** مبدأ = شلیکِ سومِ تسکِ قدیمیِ «OCTOPUS-Observatory» (ساخته 15:36:27 امروز) — تسکِ جدیدِ امشب هم‌زمان مانده → fetch دوتایی ساعتی. ثبت: **C-014**؛ پیشنهاد: غیرفعال‌کردن یکی (رأی مالک)
- **مدل وظیفهٔ سخت (پیش‌ثبت → اجرا):** اسکریپتِ نو `_ops/observatory/scripts/backtest_hardtask.py` (working repo) — وظیفه: P(≥1 زلزلهٔ ≥6.0 در پنجرهٔ ۷روزه)؛ نامزد: base-rateِ چرخشی با lookback 90 روزِ strictly-گذشته. نتیجه روی ۳۵۱ روزِ واقعی (cache محلی، بدون شبکه): **Brier نامزد 0.0978** در برابر prior ثابت **0.4535** → معیارِ پیش‌ثبت برآورده (BEAT)؛ کالیبراسیون: p̄=0.8999 در برابر نرخ واقعی 0.9088. یادآوری صادقانه: 0.2097ِ سند قبلی روی وظیفهٔ متفاوت بود — مقایسهٔ مستقیم معنا ندارد (در خروجی اسکریپت هم نوشته شده).

## T12 — متر بودجه دیپ‌سیک — ✅ عین فرمول

- ۱۱۷ تراکنشِ آخرِ deepseek در paid-calls.jsonl بازمحاسبه شد: `tokens_in/1M×0.14 + tokens_out/1M×0.28` — **۱۱۷/۱۱۷ منطبق، صفر مغایرت** (نمونهٔ زنده: 1760/699 → 0.00044212 عین رکورد)
- قیمت‌ها عین budgets.yaml (econ/reason هر دو 0.14/0.28 — VERIFIED برچسب‌دار در خود فایل)

## T7 — چت یکپارچه سرتاسری — ✅ e2e کامل + یک باگ واقعی فیکس شد

- **owner-auth (مسیرش):** هدرِ `X-Tg-Init-Data` — HMAC-SHA256 عین پروتکل MiniApp تلگرام با کلیدِ مشتق از توکنِ ربات center؛ ولیدیشن: مالک‌بودنِ user.id + تازگی auth_date. گیت روی دیوارِ `/api/*` برقرار است.
- **نتیجهٔ زنده (HTTP واقعی به 127.0.0.1:8774):** بدون auth → **403 owner_auth_required** ✓ · با auth → نوبت ۱: **200/route=mcp** (جواب صادقِ خالی: «چیزی در repo نیافتم») · نوبت ۲: **200/route=runtime** — وضعیت زندهٔ واقعی ارگانیسم (قلب ADVISORY_SHADOW · خودمدل STALE age≈17450s · عصب‌کشی 100% · prereg=24/journal=24/verdict=22 · قطب‌نما DEGRADED · «نیمه‌یکپار»). `external_effect=False` هر دو نوبت ✓ (چت هرگز اجرا نمی‌کند)
- **باگ واقعی پیدا و فیکس شد:** POST بدونِ `message_id` در ترافیک واقعی (`now=None`) → `int(None)` → **500**. تست واحدِ قبلی `now` پاس می‌داد و این را نمی‌دید. فیکس: None-safe در `miniapp_gateway.py` + تست رگرسیون نو → **test_octopus_chat_endpoint: 6/6** (قانونِ تست-در-همان-کامیت). مستقر شدن فیکس: با همین ری‌استارت اثباتی T5.

## T9 — تست‌های هرگز-اجراشده — ✅ اجرا/تهیه

- **`4d_system/nbb-cp-kre`:** **21 passed in 30.68s** — نخستین اجرای ثبت‌شده (قبلاً «unknown/only-readonly») · فرمان: `cd 4d_system/nbb-cp-kre && python -m pytest tests -o addopts= -q`
- **`4d_system/src/nbb_cp`:** خودش فایل تستی ندارد؛ پوشش از `4d_system/tests/{l0_kernel,l1_adapters,l2_replay}` می‌آید که در سوئیت رسمیِ ۴d سبز اجرا شدند (۲۶۱/۲۶۵ با ۴ شکستِ pre-existingِ C-013). نکتهٔ محیطی: pytest مستقیم روی زیرپوشه‌ها خطای import می‌دهد چون `nbb_cp` به نسخهٔ Desktop (working repo) shadow می‌شود — رانر رسمی (`tests/run_all.py` با bootstrap) درست resolve می‌کند؛ ریشهٔ دیگرِ «چرا pytest از ریشه کار نمی‌کند» (مکملِ C-006)

## T11 — تمرین kill-switch/rollback — ✅ دریل سندباکسی + اثبات وجود در زنده

- **اثباتِ وجود در زنده (فقط-خواندن):** فایل STOP (`_ops/STOP-ORGANISM`) غایب ✓ · `halted()=None` ✓ · kill.switch رصدخانه غایب ✓ — هر سه مکانیزم موجود و درگیرنشده
- **دریل سندباکسی (ORG_ROOT/OPS_DIR ایزوله — هیچ لمسِ زنده):**
  - K1 `HALT-ALL` (مرز پنیک): engage → `halted()="HALT-ALL"` · release → None ✓
  - K2 `STOP-ORGANISM`: engage → گاردِ حلقه honor کرد (`consolidation_beat → None`) · release → ادامه ✓
  - K3 `kill.switch` رصدخانه: engage → `engaged()=True` · release → False ✓ (+ تست‌های اختصاصی‌اش test_kill_switch_blocks_all_requests/release در baseline سبزِ ۱۱۶)
- **یافته + اصلاح صادقانه:** «درزِ کیل‌سوییچ» — `halted()` فایل STOP-ORGANISM را **نمی‌بیند** (فقط STOP معمار/METABOLIC/DEBATE)؛ افکتورها مستقیم چک می‌کنند ولی مسیرِ رزرو پولی از `halted()` رد می‌شود. گارد افزودنی `kill_seam_denies()` پشت `OCTOPUS_WIRE_KILL_SEAM` است. **اصلاح 2026-08-15 ~21:3x:** دریل سندباکسیِ من بدونِ فلگ‌ها بود و درز را باز دید؛ در flags.cmd:689 `OCTOPUS_WIRE_KILL_SEAM=1` است — یعنی در پروسه‌های زنده **مسلح** و درز بسته است. قفل شد در test_no_go_envelope.py
- **rollback:** فیکس‌های این نشست همه additive و git-revertable؛ بکاپِ فلگ با قرارداد .prev- فقط هنگامِ تغییرِ فلگ (امشب فلگی عوض نشد)

## T5 — پنجرهٔ گیت پذیرش 120s→300s + ری‌استارت اثباتی — ✅

- تغییر: `_ops/RESTART-ALL.ps1` حلقهٔ state تازه از ۲۴×۵s (120s) به ۶۰×۵s (300s) · سینتکس OK · تست خودِ اسکریپت: **test_restart_preflight 8/8**
- **ری‌استارت اثباتی (فرمان رسمی، 20:52-20:58):** هر ۵ عضو PID تازه (organism 15036→16584 · cortex 3524→4176 · center 19288→18060 · gateway 15880→15080 · live 19680→1632) · پورت‌ها 8771-8777 بالا ✓ · فلگ‌ها برابر (۳۳۸ در هر ۴) ✓ · **state تازه در ۲دقیقه‌۴۱ثانیهٔ گیت رسید — پنجرهٔ قدیمیِ 120s همین‌جا fail می‌شد؛ پنجرهٔ نو در اولین اجرا خودش را اثبات کرد** · beat پیشرونده 36937→36945 ✓ · halted=None · stop_organism=False ✓
- تنها FAIL باقی‌ماندهٔ گیت = «missing 4 flags» (SMTP poison — همان T4؛ pre-existing و مستند). پیشنهاد: گیت، ۴ کلیدِ عمدیِ poison را از شمارشِ shortfall معاف کند — رأی مالک
- **استقرار فیکس‌ها با همین ری‌استارت اثبات شد:** POST چت بدون message_id حالا **200** می‌دهد (پیش از ری‌استارت: 500) — روی پروسهٔ زندهٔ تازه
- مشاهدهٔ جانبی (کیفیت، نه شکست): جوابِ مسیر ask گاهی پیش‌متنِ استدلال مدل را برمی‌گرداند («The user is asking me…») — کاندید بررسیٔ آیندهٔ لایهٔ collab

## الحاقیهٔ ۲۱:۳۰ — آشتی‌داریِ دو-ایجنت + رأی شورا → فکت‌چک و قیدِ مکانیکی

### برخوردِ memory_read_patch (سشن موازی vs این نشست) — حلِ خوش
- سشنِ موازی `4665d0f` (20:10:50) **همان نسخهٔ این نشست را، تعمیرشده** کامیت کرد: ۳۴۸ خط، ۱۷ تابع، عین درختِ فعلی (diff صفر). تعمیرشان واقعی بود: پایِ RAG (فراخوانیِ langchain StructuredTool مرده) + telemetry همیشه-سبز + تفکیکِ خطا از خالی.
- کامیتِ این نشست `8a5e98b` (20:17) سیم‌کشیِ automation را برد (۳ نقطه + trace) — چون 4665d0f پیش از آن نشسته بود، فایل در 8a5e98b بدون‌تغییر ماند.
- **اعتبارسنجیِ مجدد پس از تعمیر:** تست 12/12 · اجرای زندهٔ ۳۲ تیک: **read-before-decision = 1.0 (12/12)** · صفر شکست · ۵/۵ create توسط dedup رد شد (readback=0 چون نوشته‌ای لازم نبود — رفتارِ مطلوب) · RAG این بار retrievalِ واقعی از والت برگرداند.
- خطِ کهنهٔ «حلقه باز / C-012 open» در `07 - Knowledge/Architecture/CURRENT-REALITY.md` (سندِ canonical!) اصلاح شد — ادعای سشنِ موازی مالِ پیش از 20:17 بود.
- جمعِ هر دو اجرای زنده (پیش و پس از تعمیر): **30/30 کارِ تصمیم با خواندنِ پیشین = 1.0** · readback 1/1.

### فکت‌چکِ ۴ اقدامِ فوریِ شورا (شورا briefing خوانده بود، نه درختِ زنده)
| موردِ شورا | واقعیتِ درختِ زنده (سطح A) |
|---|---|
| C1: «git init اجرا نشده» | **از قبل انجام شده** — رپوی زنده با HEAD 768ba50؛ ریموت germline (E:/germline/octopus.git) موجود؛ ۱۷+ کامیت push نشده (رأی مالک) |
| C2: «gitleaks نصب شود» | **از قبل نصب بود** — اجرا شد (۱۵۱۰ کامیت / ۸۳۴MB / ۱۵.۵min): **۷۸۱ یافته در تاریخ** (نمونه‌ها در دامپ‌های دادهٔ lunarcrush؛ رازها redact شد) · **`.env` در گیت نیست ✓** (فقط .env.example) · چرخشِ کلیدها + پاک‌سازیِ تاریخ = دستِ مالک |
| C16: «سقفِ بودجهٔ Fugu نیست» | **هست** — budgets.yaml: `cap_monthly: 100 AUD` + `human_gated: true` برای ultra + quota-guard زنده (۵۹ امروز، صفر تماسِ پولیِ fugu)؛ چرخشِ کلید = مالک |
| P0-5: «رأیِ NO-GO → قیدِ اجرایی» | **تبدیل به تست شد:** `_ops/tests/test_no_go_envelope.py` — ۹/۹ سبز (SELF_CODE خاموش · EVOLVE_REQUIRE_APPROVAL=1 · KILL_SEAM=1 · فهرستِ سختِ autonomy_matrix · HARD-STOP انسانیِ decision_gate · gitleaks حاضر) + به run_all رسمی اضافه شد. نکته: پاکتِ رأی‌شدهٔ مالک (free-class 2026-07-16 + گیتِ 51/49) عمداً محترم شمرده شد — تست فقط مرزِ فراتر از پاکت را قفل می‌کند |

### اصلاحِ T11
در سندباکسِ بدونِ فلگ، درزِ کیل‌سوییچ را «باز» دیدم؛ در تولید `OCTOPUS_WIRE_KILL_SEAM=1` است (flags.cmd:689) — **بسته**. گزارش نهایی هم اصلاح شد.

### گزارش کامل gitleaks (C2) — سطح A
- ۷۸۱ یافته / ۱۵۱۰ کامیت / ۸۳۴MB · گزارش redact‌شده: `_ops/tests/_baselines/gitleaks-full-20260815.json`
- توزیع: `_ops` ۳۴۸ · `03 - Projects` ۳۲۲ · `Obsidian Vault` قدیمی ۱۰۳ · قواعد: generic-api-key ۴۸۶ · sourcegraph-access-token ۲۵۷ · gcp ۳۲ · anthropic ۲ · github-PAT ۲ · openai ۱ · telegram ۱
- ۴۵۳ یافته در فایل‌های هنوز-موجود (عمدتاً توکن‌های شخص-ثالثِ داخل دامپ‌های داده) · جدیدترین: 2026-08-12
- **چکِ حیاتی (توسط این نشست): هیچ‌کدام از ۹ کلیدِ زندهٔ فعلیِ `.env` (deepseek/fugu/glm/zai/sakana/دو توکن تلگرام/gmail/pocketsmith) در هیچ فایل tracked نیست — صفر**
- ۳۷ از ۳۸ موردِ پرخطر فقط در تاریخ‌اند (فایل‌های حذف‌شده)؛ **تنها موردِ زندهٔ پرخطر: GitHub PAT در `03 - Projects/Mining/02 - Code/Robo-data/scout_all_in_one.py:38`** (کامیت 2026-07-14) → چرخشِ PAT در GitHub + پاک‌سازیِ فایل = دستِ مالک
- `.env` در گیت track نشده ✓ (فقط .env.example)
