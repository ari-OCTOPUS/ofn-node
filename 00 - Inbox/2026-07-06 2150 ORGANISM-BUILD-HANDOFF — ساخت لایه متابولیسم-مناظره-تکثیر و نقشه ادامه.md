---
type: handoff
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [metabolic-governor, debate, replication, budget]
created: 2026-07-06
updated: 2026-07-06
created_by: agent
sources:
  - "[[00 - Inbox/2026-07-06 1930 PROMPT-PACK — سه پرامپت مرحله‌ای (متابولیسم-مناظره-تکثیر)]]"
  - "[[04 - Architect System/2026-07-06 METABOLIC-GOVERNOR-proposal]]"
---

# ORGANISM-BUILD-HANDOFF — جلسه ۲۱ (Claude Code) · وضعیت + نقشهٔ کامل ادامه

> مأموریت آری: «تا کد نوشتن کامل برو تو این ایده‌ها و منسجم‌شان کن — یک کل واحد؛ منبع F:\backup؛
> بعداً UI؛ هدف اول: روشن‌شدن، کارکردن، یادش‌ماندن، هوشمند/خودیادگیرنده؛ یک ماه لپ‌تاپ روشن، دیتا جمع کنیم.»
> جلسه وسط کار (پیش از بازبینی خصمانه و دفترداری کامل) به دستور آری متوقف و این handoff ثبت شد.
> **هر ایجنت بعدی: اول این نوت، بعد §۴ (کارهای باقی‌مانده به ترتیب) را اجرا کن.**

## ۱) چه ساخته شد (همه additive، همه shadow، صفر call پولی، صفر اتوماسیون روشن)

هر سه Stage پک + وحدت‌بخش، **کد کامل و تست‌شده** (۳۲ چک در ۶ فایل تست، همه سبز، آفلاین $0):

| فایل | نقش | وضعیت |
|---|---|---|
| `_ops/budget/opslib.py` | کتابخانه مشترک: مسیرها، micro-USD، نرخ پین، LockedJson، پل ledger ژنوم (NOTE+subtype)، STOP/FREEZE، heartbeat/alert/CONFLICT | ✅ تست‌شده |
| `_ops/budget/telemetry.py` | T1: تلمتری واحد دو استک (ledger.jsonl ژنوم + core.db/usage مغز) + تله «or 0» → suspects + تطبیق I3 (FREEZE + شرط مرگ STOP-METABOLIC) | ✅ تست‌شده |
| `_ops/budget/organ_gate.py` | T2: گیت per-organ روی budget_gate (دست‌نخورده)؛ همه اعداد از budgets.yaml؛ fail-closed کامل | ✅ تست‌شده |
| `_ops/budget/governor_epoch.py` | T3: گاورنر سایه؛ **epoch آلوستاتیک** (تابع فشار: velocity/deadline/anomaly، نه clock)؛ dry قطعی $0 + مود LLM دوقفله؛ H1/H2/H5 چک‌شده؛ لاگ به ledger | ✅ تست‌شده |
| `_ops/debate/client.py` | کلاینت stdlib؛ model/base_url فقط از budgets.yaml؛ فقط `DEEPSEEK_API_KEY`؛ گارد leak (فقط api.deepseek.com)؛ قیمت قفل‌نشده= PriceNotLocked؛ usage غایب= TelemetryError؛ est بدترین‌حالت با سربار reasoning | ✅ تست‌شده |
| `_ops/debate/topics.py` | موضوع فقط از whitelist (seed + plan.yaml ژنوم + ارگان‌های budgets)؛ truncate ۲۰۰۰؛ پوشش ‹‹‹ ››› + GUARD_SENTENCE | ✅ تست‌شده |
| `_ops/debate/debate_loop.py` | limit cycle خلاق×معمار؛ ≤۳ دور؛ هر call گیت‌خورده؛ EXPERIENCE هر دور + PROPOSAL هفت‌فیلدی humility برای دکتر ژنوم؛ بازمانده→ `SURVIVORS-QUEUE.md` (صف انسان)؛ live دوقفله (تاریخ ≥۰۷/۲۱ + `ACTIVATION-DEBATE.flag`) | ✅ تست‌شده |
| `_ops/budget/fitness.py` | پذیرش **فقط** از `logs/outbox.jsonl` (پس از کلیک انسان) با تطبیق core.db؛ mismatch>10٪ = حذف cell + alert (ضدreward-hacking)؛ `authoritative:false` تا ۲۸ روز دادهٔ EXPERIENCE (قفل جلسه ۱۶) | ✅ تست‌شده |
| `_ops/budget/replication.py` | σ_effective از ledger؛ σ>1= ALERT cancer-axis + توقف؛ MAX_CELLS=6، عمق ۱، آستانه ۴۰٪ (پیش‌فرض پک [SPEC])؛ PROJECT_F مستثنا؛ فقط PROPOSAL human-gated، هرگز spawn | ✅ تست‌شده |
| `_ops/organism.py` | **کل واحد**: حلقه همیشه-روشن؛ تیک ۵دقیقه‌ای؛ epoch آلوستاتیک؛ fitness/σ روزانه؛ heartbeat ساعتی به `_memory/HEARTBEAT.md`؛ state ماشین‌خوان + HTTP فقط‌خواندنی `127.0.0.1:8771` (`/api/organism|telemetry|fitness|replication` — **هوک UI نسخه بعد**)؛ bind انحصاری = قفل تک‌نمونه (بدون تله SO_REUSEADDR) | ✅ کامپایل سبز؛ اجرای بلندمدت هنوز نه |
| `_ops/RUN-ORGANISM.bat` | لانچر ۳۰روزه: chcp 65001 + PYTHONUTF8 + حلقه restart؛ ASCII خالص، CRLF verify شده؛ kill تمیز= فایل `_ops/STOP-ORGANISM` | ✅ آماده؛ هنوز اجرا نشده |
| `_ops/tests/` (harness + ۶ فایل + run_all) | محیط ایزوله (vault موقت در TEMP؛ هیچ state واقعی لمس نمی‌شود)؛ `python -X utf8 _ops/tests/run_all.py` | ✅ همه سبز |
| `04 - Architect System/prompts/` | `metabolic-governor-v0.1.txt` (عین §۱ سند METABOLIC) + `debate-muse-role.txt` + `debate-architect-role.txt` | ✅ |

**قراردادهای معماری که کد رعایت می‌کند:** budget_gate = تنها enforcer (I2، دست‌نخورده — سه باگش SHARD ثبت شد)؛ budgets.yaml فقط‌خواندنی (H7)؛ ledger ژنوم = حافظه ماشینی مشترک (EVENT_TYPES بسته → NOTE+subtype: `ALLOCATION_SHADOW`/`EXPERIENCE`/`SPAWN_PROPOSAL`/`ORGANISM_DAILY` — پیش‌فرض V2)؛ همه‌چیز append-only؛ fail-closed؛ گیت دوقفله برای هر مسیر زنده.

## ۲) فکت‌های verify‌شده این جلسه (از [RE-VERIFY] به [FACT])

- `budget_gate.py:13` هاردکد `CEIL_DAY_USD=2.0`؛ پارامتر agent ignore؛ `:90` باگ واحد ارزی DISASTER (AUD در برابر ثابت USD) — دست‌نخورده، SHARD برای V1.
- `genome-system/common/llm.py:30` هاردکد `api.anthropic.com` + `:57` فقط `ANTHROPIC_API_KEY`؛ **هیچ** پشتیبانی ANTHROPIC_BASE_URL → تله نشت کلید واقعی است (control-brain امن است چون `ANTHROPIC_BASE_URL=api.deepseek.com/anthropic` ست می‌کند — `app.py:65`، `setup_wizard.py:75`).
- متر «or 0»: ‏`llm.py:77-78` و `gateway.py:87-93` — تلمتری من این‌ها را suspect می‌شمارد.
- «approved» در outbox **وجود ندارد** — تأیید = `status='sent'` (سرچشمه: `approval.py:41-59`).
- تنها دو منبع حقیقت تلمتری موجود: `genome-system/ledger/ledger.jsonl` (METRIC/llm_cost_usd) و `control-brain/core.db` جدول usage. `budget-state.json` هنوز روی دیسک نیست (با اولین reserve ساخته می‌شود).
- git خزانه: repo سالم (۱۸۸۲ آبجکت) فقط `core.worktree` مرده؛ deny rule اجرایی دست‌زدن ایجنت را بست → دستور درست مالک در [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]] (ورودی آخر) ثبت شد: `git config --file "F:\backup\.git\config" --unset core.worktree`. git ژنوم: صفر آبجکت.
- کپی staging ژنوم در `07 - Knowledge/_backups/.staging-20260706-172057/` → هر grep بدون exclude دوبار می‌شمارد.
- گزارش کامل نقشه‌برداری (۴ ایجنت، ~۴۱۴k توکن): خلاصه‌اش در همین نوت؛ جزئیات path:line در خروجی workflow جلسه (بازتولید: چهار خواننده روی genome-system / control-brain / اسناد / call-siteها).

## ۳) چیزهایی که عمداً انجام **نشد**

- هیچ فایلی از genome-system و control-brain تغییر نکرد (فیکس llm.py = قدم بعدی §۴-۱).
- budget_gate.py دست‌نخورده (فیکس‌ها فقط با verdict V1).
- budgets.yaml دست‌نخورده (H7؛ diff پیشنهادی = §۴-۲).
- هیچ پرچم ACTIVATION ساخته نشد؛ organism هنوز روشن نشده؛ هیچ commit زده نشد (git خراب — قصهٔ بالا).

## ۴) کارهای باقی‌مانده به ترتیب (ایجنت بعدی دقیقاً از اینجا ادامه بده)

1. **فیکس نشت کلید `07 - Knowledge/genome-system/common/llm.py`** (ریسک #۱ پک، مستقل از verdictها):
   `API_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/") + "/v1/messages"`
   + گارد leak در `_real_transport`: اگر URL شامل `api.anthropic.com` و کلید با `sk-ant-` شروع نمی‌شود → `RuntimeError` (کلید را echo نکن). + append به CHANGELOG ژنوم (v0.4.1) + تست additive `tests/leak_guard_test.py` + اجرای چهار تست خود ژنوم (`python tests/*_test.py` — آفلاین سبز بمانند).
2. **`_ops/budget/budgets-proposed-diff.md`** (پیشنهاد، نه اعمال — H7): ‏`global.aud_per_usd: 1.5`؛ بخش `loop.DEBATE_LOOP {cap_monthly: 5}` (V1)؛ ‏`routing.econ/reason.price_in/price_out` بعد از راستی‌آزمایی platform.deepseek.com؛ بخش `replication {max_cells: 6, spawn_depth: 1, accept_threshold: 0.40}`؛ ارگان‌های `PAINTING`/`ACCOUNTING` (الان در تلمتری UNMAPPED‌اند).
3. **`_ops/ORGANISM-SPEC.md`** — سند «کل واحد»: سه لایه (آناتومی MycoLedger / فیزیولوژی Heart / متابولیسم Governor)، نگاشت ماژول‌ها به همین فایل‌ها، ناوردی‌ها، نردبان فعال‌سازی، هوک‌های UI (چهار endpoint 8771). قالب فرانت‌متر مثل همین نوت.
4. **STAGE-REPORT-1/2/3** طبق schema بخش C پک (در `_ops/budget/STAGE1-REPORT.md`، `_ops/debate/STAGE2-REPORT.md`، `_ops/budget/STAGE3-REPORT.md`) — از دادهٔ همین نوت پر می‌شوند؛ `sigma_epoch_state: epoch_mode: allostatic، σ: n/a (pre-replication)`.
5. **بازبینی خصمانه چندایجنتی** روی کد نو (Workflow: منتقد درستی/امنیت/ناوردی + verify) و رفع یافته‌ها؛ بعد اجرای دوباره `run_all.py`.
6. **دفترداری پایان جلسه:** Active Context/Progress ‏[[04 - Architect System/architect/PROJECT|architect PROJECT]] + بازنویسی [[01 - Dashboard/HANDOFF|HANDOFF]] + اجرای هر دو validator (`python -X utf8 "04 - Architect System/scripts/validate_frontmatter.py"` و `find_broken_links.py`).
7. **smoke یک‌شبه organism:** ‏`RUN-ORGANISM.bat` را روشن کن؛ صبح چک: `_ops/state/ORGANISM-STATE.json` تازه، heartbeat ساعتی در `_memory/HEARTBEAT.md`، epochهای آلوستاتیک در `_ops/budget/epochs/`، صفر alert ناخواسته در `_ops/governor/governor-alerts.md`. بعد از سبزشدن → **شروع رسمی جمع دیتای ۳۰روزه** (خواستهٔ اصلی آری).
8. **فاز UI (خواستهٔ بعدی آری):** روی چهار endpoint موجود `127.0.0.1:8771` + `/api/genomes` داشبورد 8770 بساز؛ الگو: PANEL-SPEC (پنل ادمین). قبل از شروع، verdict فاز ۰ پنل لازم است.

## ۵) میز آری (فقط-مالک؛ بدون این‌ها مسیر زنده باز نمی‌شود)

1. **فیکس git (۲ دقیقه):** دستورهای دقیق در ورودی آخر [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]] → بعد یک commit ‏`agent-checkpoint` همهٔ ساخت این جلسه را برمی‌دارد.
2. **V1:** عدد لوپ مناظره (پیش‌فرض کد: AU$5/ماه) + تکلیف `CEIL_DAY_USD` + قفل قیمت DeepSeek از platform.deepseek.com.
3. **V2:** ماندن بر NOTE+subtype (پیش‌فرض اعمال‌شده) یا افزودن type نو به ledger.
4. **نردبان فعال‌سازی (به ترتیب INDEX):** بک‌اپ off-box → `genome_guard --init` → روشن‌کردن `RUN-ORGANISM.bat` (سایه، $0). پرچم‌های `ACTIVATION-DEBATE/REPLICATION/GOVERNOR-LLM.flag` را فقط خودت می‌سازی و کد قبل از **۰۷/۲۱** حتی با پرچم باز نمی‌شود.
5. **مقدم بر همه: فاز −۱ فروش (ددلاین ۰۷/۲۰)** — هیچ‌کدام از این‌ها جای ۳ مخاطب pitch را نمی‌گیرد.

## ۶) نحوهٔ اجرا (مرجع سریع)

- تست کل: `python -X utf8 "F:\backup\_ops\tests\run_all.py"`
- تلمتری دستی: `python -X utf8 "F:\backup\_ops\budget\telemetry.py"` · گیت: `organ_gate.py` · یک epoch: `governor_epoch.py`
- مناظرهٔ آفلاین: `python -X utf8 "F:\backup\_ops\debate\debate_loop.py" --topic-id seed-0`
- حلقهٔ کامل: دابل‌کلیک `F:\backup\_ops\RUN-ORGANISM.bat` → `http://127.0.0.1:8771`
- توقف تمیز: ساخت فایل `_ops/STOP-ORGANISM` (یا STOP-METABOLIC/STOP-DEBATE برای لایه‌ها)
