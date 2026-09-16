---
type: architecture
status: active
tags: [architecture, organism, agentic, gap-analysis, roadmap]
created: 2026-07-31
updated: 2026-07-31
created_by: agent
sources:
  - "`ARCHITECTURE-SOT.md` + `PRE-0/*`"
  - "`06 - Architecture Maps/MASTER-ARCHITECTURE-2026-07-29.md` (روی master؛ در این worktree هنوز نیست)"
  - "`OCTOPUS-25-IMPROVEMENTS-2026-07-29.md` · `OCTOPUS-BLINDSPOTS-DELTA-5.md`"
  - "`_ops/SGC-14-PROTOCOL.md` · `_ops/action_bridge/HANDOFF.md` · `_ops/unified_control/*` · `_ops/owner_console/*` · `_ops/world_discovery/*` · `_ops/telegram_contract/*` · snapshotهای `_ops/state/`"
  - "[Anthropic — multi-agent research system](https://www.anthropic.com/engineering/built-multi-agent-research-system)"
  - "[OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) · [Temporal](https://docs.temporal.io/workflow-execution) · [MCP spec](https://modelcontextprotocol.io/specification/2025-06-18) · [OpenTelemetry Traces](https://opentelemetry.io/docs/concepts/signals/traces/)"
---

# اختاپوس در برابر معماری‌های عامل‌محور پیشرو — 2026-07-31

> بررسی فقط‌خواندنی (صفر تغییر در کد/state/فلگ/Git/پروسه). مبنا: منابع کانونی و تازهٔ بالا، نه کل اسناد قدیمی. هدف: فقط شکاف‌هایی که از شواهد خود پروژه پشتیبانی می‌شوند — نه «ماژول جذاب بعدی».

## حکم اصلی

اختاپوس از نظر **ایده، گارد و تعداد قابلیت‌ها** از بسیاری معماری‌های agentic جلوتر است؛ اما از نظر **یکپارچگی اجرایی و تحویل end-to-end** عقب‌تر.

```text
اندام‌های زیاد
+ قراردادهای متعدد
+ چند مسیر مأموریت
+ چند مدل حافظه
+ stateهای پراکنده
- یک workflow اجرایی واحد
- trace سراسری
- حافظهٔ واقعاً مصرف‌شونده
- اثبات end-to-end
```

> اختاپوس مغز، قلب، حافظه، دکتر، قطب‌نما، پا و سیستم ایمنی دارد؛ اما هنوز همهٔ این‌ها با یک دستگاه عصبی و یک پروندهٔ مأموریت واحد کار نمی‌کنند.

## مقایسه با معماری‌های پیشرو

هیچ معماری واحدی «بهترین جهان» نیست؛ معیار مرجع ترکیبی است از: orchestrator-worker با context ایزوله (Anthropic Research)، primitives کم + ابزار schemaدار + handoff + tracing (OpenAI Agents SDK)، اجرای durable با event history و replay (Temporal)، قرارداد استاندارد ابزار/منبع و capability negotiation (MCP)، trace سراسری (OpenTelemetry)، حافظهٔ episodic/semantic/procedural با consolidation و retrieval routing، و الگوهای production: least privilege، sandbox، receipt، canary، rollback.

| محور | الگوی پیشرو | وضعیت واقعی اختاپوس | حکم |
|---|---|---|---|
| حاکمیت | policy-as-code و approval اثرمحور | PRE-0، fail-closed، owner gate، kill-switch | **قوی** |
| ابزارها | ابزارهای schemaدار و capability negotiation | چند manifest و registry، اما schemaها یکدست نیستند | **نیمه‌کامل** |
| workflow | یک اجرای durable با replay | چند FSM و چند مسیر مأموریت جدا | **شکاف اصلی** |
| اقدام | plan → tool → receipt → result | Action Bridge ساخته شده، caller زنده ندارد | **آماده ولی قطع** |
| حافظه | write + retrieve + consolidate + revise | نوشتن و consolidation هست؛ decision read ضعیف/غایب | **write-heavy** |
| خودمدل | snapshot تازه و قابل اعتماد | self-model بسیار کهنه؛ doc coverage با awareness اشتباه می‌شود | **شکسته از نظر freshness** |
| observability | trace سراسری و context propagation | event/log زیاد، اما trace واحد همهٔ مراحل را نمی‌پوشاند | **پراکنده** |
| چندایجنتی | context مستقل + وظیفهٔ دقیق + budget | ایجنت‌های موازی زیاد، overlap و foreign hunk دیده شده | **توانمند ولی پرریسک** |
| ارزیابی | native-runtime، long-horizon، side-effect audit | تست فراوان و mutation خوب؛ E2E زنده محدود | **آفلاین قوی، زنده ناقص** |
| self-improvement | candidate → sandbox → eval → promotion | C6 و Doctor هستند؛ verdict همیشه رفتار آینده را عوض نمی‌کند | **حلقهٔ نیمه‌بسته** |
| رابط انسان | یک درِ ساده برای مأموریت و تصمیم | تلگرام پیشرفته، ولی acceptance کامل نشده | **نزدیک به مفیدشدن** |
| مدل دنیا | evidence graph + hypothesis + experiment | World Discovery ساخته شد؛ اجرای اول `NO_VALID_DISCOVERY` | **علمی اما هنوز کم‌اثر** |

## شواهد فعلی مهم (snapshotهای روی دیسک، 2026-07-30)

```text
innervation coverage = 80%  · dead spots: spine/pacemaker, self-model
self-model.json ts = 2026-07-29T15:26:56  → سن ≈ 1662 دقیقه نسبت به innervation
heart: mode=shadow, wire_open=false, shadow_only=true
Action Bridge:     66 checks green · 8 mutation proofs · IMPLEMENTED_NOT_INTEGRATED
Unified Control:   27 checks green · 8 mutation proofs · IMPLEMENTED_NOT_INTEGRATED · NOT_LIVE
World Discovery:   85 tests · NO_VALID_DISCOVERY · IMPLEMENTED_NOT_INTEGRATED
```

SGC-14 امروز این را دارد: «جهت → هدف → پیش‌ثبت → مشاهده → حکم → روش بعدی» — اما هنوز نه: «جهت → هدف → برنامه → **اقدام → رسید → نتیجه → یادگیری**». یعنی مشکل واقعاً **کمبود اتصال** است، نه کمبود قابلیت.

## معماری هدف

```text
مالک/Telegram → Intent & Mission Compiler → Durable Mission Kernel → Planner/Cortex
→ Capability & Tool Registry → Action Bridge → پاها/ابزارها/World Discovery
→ Execution Receipt → Independent Evaluator → Verified Memory → Planner چرخهٔ بعد
```

لایه‌های عرضی: PRE-0/Policy · Budget · Kill-switch · Trace · Freshness · Privacy · Rollback.

نقش‌ها: Heart = تنظیم ریتم/فشار نه فرمانده · Compass = اتصال جهت مالک به هدف · Cortex = برنامه‌ریزی · Action Bridge = کنترل اختیار و اجرا · Legs = کارگران محدود · Evaluator = قاضی مستقل · Memory = تجربهٔ تأییدشده نه مجوز · Telegram = رابطه با مالک.

## پیشنهادهای اولویت‌دار

### P0-1 · Durable Mission Kernel واحد

مسیرهای جدا (`test_cycle`، `telegram_center/mission.py`، `mission_runner.py`، `work_pump`، `action_bridge`، `unified_control`، `world_discovery`، مسیر Doctor/C6) همه به یک state machine واحد conform شوند:

```text
CREATED → VALIDATED → PREREGISTERED → PLANNED → AUTHORIZED → EXECUTING
→ OBSERVED → EVALUATED → COMPLETED|PARTIAL|FAILED|BLOCKED → CONSOLIDATED
```

هر مأموریت این شناسه‌ها را حفظ کند: `trace_id / goal_id / prereg_id / mission_id / action_id / receipt_id / verdict_id / memory_id`.
اصل Temporal: پس از crash، مأموریت از آخرین event معتبر ادامه پیدا می‌کند، نه از حدس.
**Done:** خاموش/روشن وسط مأموریت · resume دقیق از event history · عدم تکرار side effect · transition غیرمجاز fail-closed · یک timeline قابل نمایش در تلگرام.

### P0-2 · رفع freshness خودمدل و state

- حل temp→replace در `ORGANISM-STATE.json` و `self-model.json`؛ writer lease و single-writer؛ retry محدود + backoff + alert؛ حفظ state قبلی هنگام شکست.
- freshness بخشی از authorization شود: `self-model stale → read-only allowed → planning with warning → autonomous mutation blocked`.
- **Done:** `self-model age < SLA · ORGANISM-STATE age < SLA · innervation=100% · dead_spots=[]` یا استثنای صریح ماشین‌خوان.

### P0-3 · اتصال واقعی Goal به Action Bridge (نسازید، وصل کنید)

```text
Exact Prereg Row → Unified Control → Canonical Mission → Action Request → Action Bridge → Receipt
```

قانون‌ها: متن method مجوز نیست · unknown action = block · A0/A1 در sandbox · A2 فقط پس از governance مشخص · A3 کارت مالک · A4/A5 رأی اثرمحور · A6 رد کامل.
**Done:** یک مأموریت read-only واقعی end-to-end: Direction → Goal → Prereg → Mission → A0 Action → Receipt → Metric → Verdict → Memory.

### P1-4 · حافظهٔ چهارلایه با مصرف تصمیمی

Working / Episodic / Semantic / Procedural؛ چرخهٔ Ingest → Extract → Verify → Consolidate → Retrieve → **Use in decision** → Revise/Forget.
قبل از plan: query بر اساس goal/blocker/tool/outcome/owner-feedback similarity. بعد از plan سیستم بگوید: کدام خاطره استفاده شد، چرا، چه تغییری در تصمیم داد.
امنیت (ضد memory poisoning): هر memory با `origin / trust class / scope / evidence refs / created_at / expires_at / revision history / authority=never`. اصل «حافظه مجوز نیست» حفظ شود.
**Done:** تست A/B ثابت کند retrieval کیفیت تصمیم را بهتر کرده، نه فقط متن بیشتری به prompt افزوده.

### P1-5 · Retrieval Router واحد

انتخاب بین exact lookup / temporal / semantic / entity graph / procedural / **no retrieval**. اگر retrieval کمکی نمی‌کند، context اضافه نشود.

### P1-6 · Trace سراسری OpenTelemetry-style

هر span: `trace_id / span_id / parent_span_id / mission_id / component / operation / start-end / status / input_hash / output_hash / cost / model-tool / effect_class / evidence refs / error type`.
**Done:** در پاسخ «چرا این مأموریت شکست خورد؟» بات اولین span خراب را نشان دهد، نه حدس از چند JSONL.

### P1-7 · سلامت بر اساس پیشرفت

برای هر component سه وضعیت جدا: `PROCESS_ALIVE / LOOP_PROGRESSING / USEFUL_OUTPUT_FRESH`. Watchdog باید cycle counter، event progress، queue drain، output freshness و stuck transition را بسنجد — نه فقط process/port.

### P1-8 · Capability Contract استاندارد (شبیه MCP)

هر قابلیت: `capability_id / input_schema / output_schema / action_contract / risk_class / owner_gate / surface / runtime_probe / cost_model / privacy_scope / tests / version`.
سه اصل: registration مجوز نیست · tool description دادهٔ غیرقابل اعتماد است · negotiation و version compatibility لازم است.
**Done:** `ALL_IMPLEMENTED_CAPABILITIES ⊆ VALID_MANIFESTS ∪ EXPLICIT_DORMANT ∪ EXPLICIT_BLOCKED` — قابلیت بی‌manifest بی‌صدا ناپدید نشود (`world_discovery` الان manifest مستقل ندارد).

### P1-9 · Least-Privilege Tool Selection

کم‌اختیارترین ابزار کافی، نه مؤثرترین: مشاهدهٔ فایل → read-only tool نه shell · ساخت draft → sandbox artifact نه Telegram send · سنجش وضعیت → state reader نه restart. هر escalation با دلیل و receipt.

### P1-10 · از test count به Mission Reliability

معیار اصلی: «چند مأموریت end-to-end بدون تخلف کامل شد؟» — نه «چند تست سبز شد؟».
سبد پیشنهادی: ۲۰ read-only · ۱۰ artifact · ۱۰ owner-gated · ۵ cross-session · ۵ crash/restart · ۵ دادهٔ خصمانه · ۵ tool failure · ۵ memory poisoning · ۵ چندایجنتی.
سنجه‌ها: mission success · false completion · unauthorized effect · resume correctness · duplicate effect · evidence integrity · owner correction rate · memory usefulness · cost per successful mission · time to useful result.
نکته: پژوهش long-horizon نشان می‌دهد مدل‌های frontier روی کار طولانی بسیار ضعیف‌تر از بنچمارک کوتاه‌اند — موفقیت یکی‌دو چرخه کافی نیست.

### P2-11 · Orchestrator-worker فقط برای کار واقعاً موازی

Simple → یک agent · Comparison → ۲–۴ · Broad research → چند agent مستقل · Shared-file code change → **یک writer + چند reviewer read-only** (جلوی foreign hunk و overwrite جلسات موازی). هر subagent با objective/scope/owned files/forbidden files/output schema/budget/deadline/evidence requirement/parent trace. (هزینهٔ چندایجنتی ~۱۵× chat — گزارش Anthropic.)

### P2-12 · Agent Lease و Ownership Registry

قبل از ویرایش: `agent_id / mission_id / paths / mode / lease expiry / base commit`. فایل با writer lease فعال را agent دیگر فقط می‌خواند. Git ابزار coordination اصلی نباشد؛ lease قبل از Git تعارض را بگیرد.

### P2-13 · مسیر Promotion واحد برای self-improvement

Observation → Hypothesis → Reproduction → Candidate → Sandbox → Held-out Eval → Adversarial Review → Canary → Owner Promotion → Limited Live → Monitor → Rollback/Promote. هیچ candidate ای evaluator یا معیار پذیرش خودش را تغییر ندهد. (DELTA-5: C6 verdict همیشه رفتار را عوض نمی‌کند.)
**Done:** candidate واقعی · prediction قبل از آزمایش · baseline منجمد · held-out مستقل · canary محدود · rollback drill اجراشده · owner-signed promotion.

### P2-14 · Protective Signals خارج از اختیار Orchestrator

non-suppressible: global halt · budget exhaustion · scope violation · secret exposure · evidence tampering · memory-origin violation · rollback unavailable. سیگنال‌هایی مثل stress یا heart shadow فعلاً advisory بمانند.

### P2-15 · Heart = regulator، نه commander

طراحی فعلی درست است (`shadow_only=true`, `wire_open=false`). قبل از بازشدن wire: hash کنترل هماهنگ با simulation · `delta_self` معتبر · freshness کامل · canary طولانی. قلب goal را تغییر نمی‌دهد؛ فقط شدت و زمان‌بندی.

### P2-16 · World Discovery = sensor، نه decision maker

مسیر درست: observation/evidence/hypothesis → Mission Planner → falsifiable experiment → Action Bridge. برای دور دوم: relation-level discovery (چه ترکیب قابلیتی بین رقبا غایب است؟ niche قابل‌آزمایش اختاپوس؟ چه شاهدی فرضیه را رد می‌کند؟) به‌جای claim تک‌منبعی.

### P3-17 · یک در، یک کارت مأموریت، یک timeline

Outer DM: هدف/کار فعلی/پیشرفت/مانع/قدم بعدی/نتیجه — نه صدها component. Inner DM: سلامت/هشدار/approval/receipt. Group: فقط پاها. قبل از UI جدید، ۱۲ سؤال acceptance موجود در Outer DM واقعاً پاسخ داده شوند.

## چیزهایی که نباید ساخته شوند

Event Bus جدید · Mission FSM جدید · حافظهٔ جدید · approval queue جدید · bot/poller جدید · dashboard دیگر · «مغز سوم» بی‌consumer · self-model دوم · اتصال مستقیم World Discovery به اجرا · وصل همهٔ شاخه‌های dormant · rewrite کامل `organism.py`/`wiring.py` · L4 یا auto-merge گسترده · قابلیت جدید قبل از manifest و runtime probe.

فایل‌های بزرگ و پرمسئولیت (`wiring.py` ~۳۳۶۴ خط · `approval_channel.py` ~۴۶۶۹ · `center.py` ~۲۳۷۰): راه‌حل rewrite نیست؛ الگوی **strangler** — خروج تدریجی مسئولیت‌ها پشت قراردادهای موجود.

## نقشهٔ اجرایی

- **موج ۱ — حقیقت و ستون فقرات:** state writer/freshness · mission state machine canonical · trace سراسری · exact prereg → mission → action · یک مأموریت read-only E2E.
- **موج ۲ — یادگیری:** memory retrieval در planner · outcome → procedural memory · memory-origin security · A/B retrieval usefulness · correction و forgetting.
- **موج ۳ — عملیات محدود:** پاها از Action Bridge · A0/A1 live · A3 owner-card · receipt/evaluator/memory closure · native-runtime mission benchmark.
- **موج ۴ — خودبهبودی کنترل‌شده:** C6 candidate واقعی · held-out + adversarial · canary · rollback drill · owner-signed promotion.

## پنج اهرم اصلی

1. **Durable Mission Kernel واحد**
2. **رفع freshness خودمدل و state**
3. **اتصال Action Bridge به exact prereg**
4. **Memory retrieval واقعی در نقطهٔ تصمیم**
5. **Mission-level native-runtime evaluation**

## جمع‌بندی

```text
قانون و ایمنی          قوی
تعداد اندام‌ها         بسیار زیاد
تست و mutation         قوی
خودهدف‌گذاری           زنده
اقدام کنترل‌شده        ساخته، ولی قطع
حافظه                  غنی، ولی کم‌مصرف در تصمیم
خودمدل                 کهنه
قلب                    shadow
observability          فراوان ولی پراکنده
چندایجنتی              قدرتمند ولی overlapدار
تلگرام                 نزدیک، اما acceptance کامل نشده
خودتکمیلی واقعی        هنوز کامل نیست
```

بهترین مسیر «بزرگ‌تر شدن» نیست؛ اختاپوس باید **کم‌primitiveتر، durableتر، قابل‌ردیابی‌تر و حلقه‌بسته‌تر** شود.

## منابع بیرونی

- [Anthropic — How we built our multi-agent research system](https://www.anthropic.com/engineering/built-multi-agent-research-system)
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)
- [Temporal Workflow Execution](https://docs.temporal.io/workflow-execution)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/specification/2025-06-18)
- [OpenTelemetry Traces](https://opentelemetry.io/docs/concepts/signals/traces/)
- arXiv: *Are We Ready for an Agent-Native Memory System?* · *Securing LLM-Agent Long-Term Memory Against Poisoning* · *WildClawBench: Real-World Long-Horizon Agent Evaluation* · *Invisible Orchestrators Suppress Protective Behavior* · *When Lower Privileges Suffice*
