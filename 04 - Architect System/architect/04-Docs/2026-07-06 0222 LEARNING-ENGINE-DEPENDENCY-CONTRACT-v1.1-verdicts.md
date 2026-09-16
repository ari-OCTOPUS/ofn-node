---
type: architecture
status: ready
tags: [learning-engine, cross-cutting, dependency-contract, spine, governance]
created: 2026-07-06
updated: 2026-07-06
supersedes: "[[04 - Architect System/architect/04-Docs/2026-07-06 0215 LEARNING-ENGINE-DEPENDENCY-CONTRACT-v1-draft]]"
---

> [!note] ثبت ایجنت (Inbox-first)
> نسخه به‌روز آری (2026-07-06) با **verdictهای ۱–۸ embedded** — جایگزین draft قبلی. نرمال‌سازی: frontmatter با schema سازگار (کلیدهای اصلی: `type: architecture-spec` · `owner: آری`)؛ wikilink نوت‌های غایب → متن ساده؛ تایپوی مدل مبدأ اصلاح. **verdict تکمیلی آری همین جلسه: «سیستم روی maximum risk»** — تفسیر ثبت‌شده در [[_memory/EXPERIENCE-LEDGER|ledger]]: بیشترین autonomy مجاز در چارچوب منشور؛ لیست سیاه و §Security Gate ساختاراً human-only می‌مانند.

# LEARNING-ENGINE-DEPENDENCY-CONTRACT — ستون فقرات مستقل

> **مفهوم اصلی:** Learning Engine یک ماژول مستقل است — lifecycle، state، manifest و تستِ جدا دارد و می‌توان آن را جدا از کل ساختار ساخت/اجرا کرد. اما «مستقل» یعنی **encapsulated**، نه «جدای». این موتور **قراردادهای وابستگی صریح (typed contracts)** با کل ساختار دارد: از هر لایه می‌خورد و به هر لایه برمی‌گرداند. این یعنی یک **ستون فقرات عرضی (cross-cutting spine)** که عمود بر لایه‌های L1–L9 می‌ایستد و به همه وصل است.
> منبع: خودِ ساختار. هر ادعای فراتر از فایل‌های آپلودی با «استنباط».

---

## ۱. چرا «مستقل + وابسته» هم‌زمان؟

| اصل | معنی |
|---|---|
| **استقلال (independence)** | Engine حافظهٔ state خودش را دارد (`LEARNING-STATE.json`)، ورودی/خروجی contract آن فایل-محور است، می‌توان آن را در sandbox جدا ساخت و تست کرد بدون نیاز به کل vault زنده، و خرابیِ یک لایه نباید Engine را kill کند (fail-degraded نه fail-dead). |
| **وابستگی به کل ساختار (whole-structure dependency)** | Engine به‌صورت قراردادی به هر یک از ۹ لایه وصل است: از هر کدام یک ورودی مشخص می‌خورد و یک خروجی مشخص برمی‌گرداند. هیچ لایه‌ای حق ندارد بداند Engine چطور فکر می‌کند — فقط contract را رعایت می‌کند. |

> این الگو (spine + contracts) مزیت بزرگی دارد: **می‌توان Engine را یک‌تنها جایگزین کرد** (نسخهٔ v2، یا موتور غیر-Fugu) بدون بازنویسی لایه‌ها؛ و **می‌توان یک لایه را تعویض کرد** بدون دست‌زدن به Engine — تا وقتی contract حفظ شود. این همان **separation of concerns در سطح سیستم‌عامل**.

---

## ۲. نقشهٔ وابستگی به کل ساختار

```
                        ┌─────────────────────────┐
                        │   LEARNING ENGINE        │
                        │   (مستقل · state خود)    │
                        │   LEARNING-STATE.json    │
                        └────────────┬─────────────┘
                                     │ contractها (خوردن/دادن)
   ╔═════════════════════════════════╪═══════════════════════════════╗
   ║                                 │                               ║
   ▼                                 ▼                               ▼
 L1 GOVERNANCE          L2 CONTROL              L2b EXT. INTELLIGENCE
 (قانون اساسی)          (دو مغز)                 (Fugu)
   ▲                       ▲                       ▲
   │                       │                       │
   ▼                       ▼                       ▼
 L3 INGEST/SECURITY    L4 MEMORY/KNOWLEDGE     L5 PROJECT/OPS
 (گیت‌ها)               (حافظه)                  (پروژه‌ها/G0–G4)
   ▲                       ▲                       ▲
   │                       │                       │
   ▼                       ▼                       ▼
 L6 PEOPLE    L7 LOG/TELEMETRY    L8 HANDOFF    L9 AGENT REGISTRY
```

Engine در **مرکز** نیست (مرکز = governance). Engine یک **شریان عرضی** است که از بالا تا پایین عبور می‌کند و در هر لایه یک tap دارد.

---

## ۳. قرارداد وابستگی (Dependency Contract) — به ازای هر لایه

هر قرارداد دو بخش دارد: **خوردن (consumes)** از لایه + **دادن (emits)** به لایه. هیچ وابستگی پنهان نیست — همه در `LEARNING-CONTRACT.yaml` ثبت می‌شود.

### 3.1 — L1 Governance (PROJECT_INSTRUCTIONS)

| جهت | قرارداد |
|---|---|
| خوردن | Engine قانون اساسی، مرز invariant↔mutable، لیست سیاه human-only، Property Schema را می‌خواند (read-only) |
| دادن | Engine **هرگز** governance را نمی‌نویسد؛ پیشنهاد تغییر قانون = فقط از طریق `AGENT_QUESTIONS` (propose-only) |
| استقلال | اگر governance نباشد، Engine با snapshot کپی‌شده در Engine state کار می‌کند (fail-degraded) |

### 3.2 — L2 Control (TWO-BRAIN)

| جهت | قرارداد |
|---|---|
| خوردن | نردبان L0–L3، §Security Gate status، kill-switch flag، حالت حلقهٔ فعلی |
| دادن | Engine به control loop گزارش می‌دهد: «در کدام L هستم»، «کدام جهش در ارزیابی»، «هزینهٔ انباشته» — برای داشبورد `fleet-live-dashboard` |
| استقلال | Engine خودش verdict نمی‌دهد؛ verdict = کنترل انسانی. Engine فقط proposes. |

### 3.3 — L2b External Intelligence (Fugu)

| جهت | قرارداد |
|---|---|
| خوردن | خروجی Fugu Responses API (تحلیل + فرضیه + دستور بعدی) |
| دادن | Engine به Fugu یک `prompt bundle` می‌دهد (SYSTEM-STATE + جهش‌نامه + سوال) — **با فیلتر secret/PII اعمال‌شده** (C17 + #13) |
| استقلال | اگر Fugu down/rate-limited/deprecated شد، Engine به fallback محلی (Qwen/Llama یا Claude) سوئیچ می‌کند — contract روی «OpenAI-compatible API» است نه روی Sakana (#82) |

### 3.4 — L3 Ingest/Security (PHASE-0A)

| جهت | قرارداد |
|---|---|
| خوردن | `ingest-manifest.json` (فایل‌های مجاز)، `quarantine-manifest.json`، نمرهٔ سلامت ستون ۱ |
| دادن | Engine هرگز eligibility را دوباره محاسبه نمی‌کند — فقط manifest می‌خواند (#PHASE-0A invariant) |
| استقلال | اگر manifest نباشد، Engine **halt** می‌کند (نمی‌تواند روی فایل ناشناخته یاد بگیرد) |

### 3.5 — L4 Memory/Knowledge

| جهت | قرارداد |
|---|---|
| خوردن | EXPERIENCE-LEDGER (append-only)، Mutation Ledger، نوت‌های `created_by: agent` |
| دادن | Engine جهش‌های تثبیت‌شده را به «ژنوم canonical» اضافه می‌کند (با verdict)؛ خروجی Fugu با `origin: fugu` + `<external_data>` برچسب می‌خورد |
| استقلال | حافظهٔ کوتاه‌مدت Engine در `LEARNING-STATE.json` خودش — با قطع session نمی‌میرد (#86) |

### 3.6 — L5 Project/Ops

| جهت | قرارداد |
|---|---|
| خوردن | `Active Context` و `Progress` هر PROJECT.md لمس‌شده، Gateهای G0–G4، متریک پروژه (برای تابع برازندگی) |
| دادن | Engine پیشنهاد next action به PROJECT.md می‌دهد (propose-only)، تحلیل برازندگی per-project |
| استقلال | Engine روی دادهٔ حساس Project-F فقط با Fugu استاندارد (opt-out) کار می‌کند — نه Ultra (C17) |

### 3.7 — L6 People

| جهت | قرارداد |
|---|---|
| خوردن | فقط metadata نقش/ارتباط (نه اطلاعات تماس) |
| دادن | هیچ — Engine هرگز به People نوت نمی‌نویسد (حریم خصوصی) |
| استقلال | قرنطینهٔ پیش‌فرض؛ دسترسی فقط با whitelist صریح |

### 3.8 — L7 Log/Telemetry

| جهت | قرارداد |
|---|---|
| خوردن | HEARTBEAT دوطرفه (watchdog)، خروجی زندهٔ زمان‌بند |
| دادن | هر چرخهٔ Engine یک ورودی در لاگ پروژه + `LEARNING-LEDGER` با `ledger_ref`، هزینه، نتیجه |
| استقلال | لاگ‌نویسی Engine مستقل از لاگ پروژه است (دو نوار موازی) |

### 3.9 — L8 Handoff

| جهت | قرارداد |
|---|---|
| خوردن | HANDOFF فعلی (وضعیت انتقال) |
| دادن | Engine یک wikilink به سطر `HEARTBEAT.md` در HANDOFF می‌گذارد (نه بخش خودکار — چون HANDOFF هر جلسه بازنویسی می‌شود و پایدار نمی‌ماند) |
| استقلال | state حیاتی هرگز فقط در HANDOFF نیست — در `LEARNING-STATE.json` (#122) |

> **VERDICT 2026-07-06:** به‌جای «بخش Learning state خودکار در HANDOFF» (که با الگوی overwrite نمی‌خواند)، یک سطر تاریخ‌دار در `_memory/HEARTBEAT.md` (هر تسک فقط سطر خودش) + wikilink در HANDOFF. منطبق با الگوی ratified موجود.

### 3.10 — L9 Agent Registry

| جهت | قرارداد |
|---|---|
| خوردن | AGENT_REGISTRY، وراثت §Gate، runbook ایجنت‌ها |
| دادن | Engine خودش در AGENT_REGISTRY ثبت می‌شود به‌عنوان یک ایجنت با `trigger: loop`، `autonomy_level: L1→L3` |
| استقلال | Engine یک ایجنت از نوع خاص است (learning)، نه زیرمجموعهٔ ایجنت‌های عادی |

> **VERDICT 2026-07-06 (تصمیم آری):** `trigger: loop` به Property Schema اضافه شود (گسترش schema با تأیید مالک). کلید `level` به‌جایش `autonomy_level` (موجود) استفاده می‌کند. این یعنی قبل از ثبت Engine در AGENT_REGISTRY، باید `Property Schema.md` + `.obsidian/types.json` در همان جلسه با تأیید مالک ویرایش شوند (قاعدهٔ §۶ PROJECT_INSTRUCTIONS: ایجنت هرگز کلید جدید اختراع نمی‌کند).

### 3.11 — L2c Capability Layer (Partner Skills / MCP servers)

> **منبع:** دایرکتوری Anthropic Partners (Fastly، DataRobot، CockroachDB، Tavily، monday.com، Wix، Pixeltable، Carta و غیره). هر partner یک MCP server / skill است با آیکون چرخ‌دنده (configure) یا + (install).

این یک **لایهٔ عرضی جدید** است — نه جایگزین Fugu، بلکه **مکمل** آن. Fugu موتور فکری است (ستون ۳)؛ این لایه ابزارهای اجرایی‌اند که Fugu یا Engine می‌توانند فراخوانی کنند. درست مثل اینکه به مغز، دست و چشم می‌دهیم.

| جهت | قرارداد |
|---|---|
| خوردن | Engine خروجی ابزار را (مثلاً نتایج Tavily search، schema CockroachDB، boards monday.com) به‌عنوان **داده** می‌گیرد — هرگز به‌عنوان دستور (#131 دفاع تزریق) |
| دادن | Engine به هر ابزار یک **typed call** می‌دهد (input schema مشخص)؛ ابزار خروجی structured برمی‌گرداند |
| استقلال | اگر یک ابزار down/uninstalled شد، Engine به ابزار جایگزین یا fallback محلی سوئیچ می‌کند (همان الگوی fail-degraded §۶) |

**قرارداد هر قابلیت (capability contract):**

```
capability:
  id: tavily-search        # یا cockroach-db، monday-ops، …
  source: partner-directory # Anthropic Partners
  type: mcp-server | skill
  input_schema: { ... }      # typed
  output_schema: { ... }     # typed — schema validation (#87)
  secrets_required: [TAVILY_API_KEY]   # → rotation checklist + .agentignore
  data_classification: public | sensitive | restricted
  allowed_for: [L1-propose, L2-bounded, L3-auto]   # سطح استقلال مجاز
  fallback: local-qwen-search | none
  cost_model: per-call | free | subscription
```

**نقشهٔ قابلیت‌های شناسایی‌شده (از تصویر):**

| Partner | قابلیت برای Engine | دادهٔ حساس؟ | سطح مجاز |
|---|---|---|---|
| **Tavily** | web search / extract / research — **جایگزین/مکمل web_search داخلی Fugu** (استراتژی fallback #82) | خیر (عمومی) | L1+ |
| **CockroachDB** | خواندن schema، نوشتن SQL، دیباگ کوئری — برای لایهٔ memory/داده | بله (داده) | L2+ |
| **monday.com** | ops / boards / items — مدیریت تسک‌های پروژه | بله (ops) | L1 propose-only |
| **DataRobot** | ML workflows — train/deploy/predict/monitor — برای تابع برازندگی خودکار | بله | L2+ |
| **Fastly** | edge/dev tools — deployment | خیر | L2+ |
| **Wix** | build/deploy سایت — برای پروژه‌های content | خیر | L1 propose-only |
| **Pixeltable** | داده/جدول | بله | L2+ |
| **Carta investors** | cap table / سرمایه‌گذاری | بله (مالی) | human-only verdict |

**قواعد حاکم (برگرفته از governance موجود):**

1. **هر کلید API partner = secret** → rotation checklist + `.agentignore` + `.claude/settings.json` (همان §۱۰ PROJECT_INSTRUCTIONS).
2. **دادهٔ حساس Project-F (Iran geo-block/KYC) هرگز به هیچ partner نرود** (C17) — مگر اینکه data_classification `sensitive` و `allowed_for` human-only باشد.
3. **خروجی هر ابزار = داده، نه دستور** (#131) — حتی نتایج Tavily که محتوای بیرونی دارد، قرنطینه و به‌عنوان داده رفتار می‌شود.
4. **schema validation الزامی** (#87) — خروجی بدفرم نباید حلقه را خراب کند.
5. **هزینهٔ هر ابزار در budget ceiling لحاظ شود** (#94) — نه فقط توکن Fugu.
6. **راستی‌آزمایی روزانهٔ قیمت/رفتار API** (#81) — promo‌ها تمام می‌شوند.
7. **تک‌منبع contract** (#108) — هم در `LEARNING-CONTRACT.yaml` و هم در کد drift نکنند.
8. **partner به‌عنوان ایجنت ثبت شود** در AGENT_REGISTRY با وراثت §Gate (L9) — همان قاعدهٔ خود سیستم.

**جایگاه در نقشهٔ وابستگی (§۲ به‌روز):**

```
   L2b External Intelligence (Fugu — موتور فکری)
          │
          ▼
   ┌───────────────────────────────────────┐
   │  L2c CAPABILITY LAYER (partner skills) │
   │  tavily · cockroach · monday · datarobot│
   │  fastly · wix · pixeltable · carta      │
   │  هر کدام typed contract + fallback      │
   └───────────────────────────────────────┘
          │
          ▼
   Engine می‌خورد (داده) / می‌دهد (typed call)
```

> **اصل:** Fugu تصمیم می‌گیرد «چه کار کنم»؛ Capability Layer «چطور انجامش دهم». این تفکیک، Fugu را سبک نگه می‌دارد (فقط فکر) و اجرا را به ابزار تخصصی می‌سپارد — همان فلسفهٔ multi-agent که Sakana هم دارد، اما با ابزارهای رسمی به‌جای ایجنت‌های ad-hoc.

---

## ۴. ترتیب وابستگی (Dependency Ordering)

این ترتیب نشان می‌دهد Engine برای **روشن‌شدن** به چه چیزی نیاز دارد و چه چیزی از Engine به‌عنوان پیش‌نیاز دارد:

```
L1 Governance ──► (پیش‌نیاز همه)
        │
        ▼
L3 Ingest/Security (گیت‌ها) ──► manifest
        │
        ▼
L4 Memory (LEDGER) ──► حافظهٔ ایمنی + جهش‌نامه
        │
        ▼
L7 Telemetry (HEARTBEAT) ──► آشتی حقیقت
        │
        ▼
┌───────────────────────────────────────────────┐
│  LEARNING ENGINE (مستقل)                       │
│  پیش‌نیاز داخلی: L2b (Fugu) + budget + Gate+git │
│  خروجی: mutation ledger + next-action proposals │
└───────────────────────────────────────────────┘
        │
        ▼
L2 Control (verdict انسان) ──► L5 Projects (تثبیت/اعمال)
        │
        ▼
L8 Handoff + L9 Registry (ثبت انتقال + شناسنامه)
```

> **نکتهٔ کلیدی استقلال:** Engine می‌تواند در حالت **shadow** (L0: فقط مشاهده + گزارش، بدون اعمال) حتی **قبل از بسته‌شدن Gate** کار کند — چون در این حالت فقط می‌خورد، نمی‌دهد. این یعنی می‌توان Engine را زود ساخت و هم‌زمان گیت‌ها را بست، بدون ریسک.

---

## ۵. state مستقل Engine

```
LEARNING-STATE.json
├─ engine_version: "v1"
├─ autonomy_level: "L1"          # فعلاً
├─ security_gate_status: "OPEN"  # halt تا بسته شود
├─ git_ready: false
├─ budget_ceiling_daily: null    # باز
├─ current_cycle:
│   ├─ observed_at: <timestamp Sydney>
│   ├─ hypothesis: "..."
│   ├─ fugu_call_pending: false
│   ├─ cost_accumulated_today: 0.00
│   └─ next_action_proposal: null
├─ mutation_ledger_ref: "EXPERIENCE-LEDGER::row-N"
├─ safety_memory:               # #66 حافظهٔ ایمنی
│   └─ reverted_mutations: [...]
├─ fallback_mode: false          # اگر Fugu down
├─ shadow_mode: true             # L0 امن
└─ last_sync_truth: null         # آشتی حقیقت
```

> این فایل **تنها منبع state Engine** است. اگر Engine restart شود، از همین فایل بالا می‌آید. state حیاتی هرگز در localStorage یا context (#86, #122).

---

## ۶. چه چیزی Engine را از بقیه جدا می‌کند (مرز استقلال)

| مرز | قاعده |
|---|---|
| **قرارداد فایل-محور** | Engine فقط از طریق manifest/ledger/contract با لایه‌ها حرف می‌زند — هیچ call مستقیم به کد لایه‌ها ندارد |
| **fail-degraded** | خرابیِ یک لایه = Engine به fallback یا shadow می‌رود، نه crash |
| **testable in isolation** | می‌توان با manifest/ledger ساختگی، Engine را در sandbox جدا تست کرد |
| **swappable** | نسخهٔ v2 Engine (یا موتور غیر-Fugu) قابل تعویض است بدون دست‌زدن به لایه‌ها |
| **state ownership** | `LEARNING-STATE.json` متعلق به Engine است؛ هیچ لایه‌ای مستقیماً در آن نمی‌نویسد |

## ۷. چه چیزی Engine را به کل ساختار وصل می‌کند (وابستگی)

| وابستگی | به کجا | چرا حیاتی |
|---|---|---|
| قانون اساسی + invariantها | L1 | بدون این، Engine نمی‌داند چه چیزهای هرگز جهش ندهد |
| manifest ingest | L3 | بدون این، Engine روی فایل ناشناخته یاد می‌گیرد (نشت) |
| LEDGER + جهش‌نامه | L4 | بدون این، حافظهٔ ایمنی نیست (جهش بد بی‌نهایت) |
| HEARTBEAT/زمان‌بند | L7 | بدون این، روی drift فکر می‌کند |
| verdict انسان | L2 | بدون این، خودمختاری بی‌کنترل |
| Fugu API | L2b | موتور فکری |
| متریک پروژه | L5 | تابع برازندگی |
| HANDOFF | L8 | انتقال state بین جلسات |
| AGENT_REGISTRY | L9 | Engine خودش یک ایجنت ثبت‌شده است |

---

## ۸. گیت‌های مخصوص Engine (اضافه بر گیت‌های ساختار)

| گیت | شرط | وضعیت |
|---|---|---|
| **shadow mode available** | فقط خواندن + گزارش، **صفر فراخوانی خارجی (نه Fugu، نه partner)** | ✅ می‌تواند همین حالا |
| **gate-closed mode** | Security Gate + git + budget | ❌ باز |
| **L2 bounded-auto** | + whitelist + استقلال کسب‌شده | ❌ باز |
| **L3 autonomous** | + Gate + git + budget + سقف | ❌ باز |
| **fallback path** | موتور جایگزین وقتی Fugu down | طراحی، اجرا نه (#82) |

> **VERDICT 2026-07-06 (تصمیم آری):** shadow mode همین حالا روشن شود، ولی تعریف سخت: **صفر فراخوانی خارجی** تا وقتی کلید API در ROTATION ثبت شده و `budget_ceiling_daily` عددی شود (الان `null` است). «با کال و کامل» = هدف، نه وضعیت الان؛ یعنی بعد از بسته‌شدن Gate + کلید + بودجه، Engine به مد کامل (با call) ارتقا می‌یابد. تا آن لحظه هر call خارجی (Fugu یا partner) = halt.

> **VERDICT 2026-07-06 (تصمیم آری) — F4:** هیچ فایلی قبل از سبز شدن در manifest (Gate 1–4 PHASE-0A) به Fugu یا partner فرستاده نمی‌شود. hardest rule، صفر استثناء. F4 فقط روی `ingest-manifest.json` سبز کار می‌کند — نه روی فایل خام.

---

## ۹. متریک سلامت Engine (مستقل از سلامت ساختار)

- **contract violations:** تعداد دفعاتی که یک لایه contract را نقض کرد (یا Engine نقض کرد) → باید صفر باشد
- **fallback rate:** درصد چرخه‌هایی که Fugu down بود و Engine به fallback رفت
- **shadow→active gap:** تفاوت رفتار Engine در shadow و active (نباید زیاد باشد)
- **state persistence:** پس از restart، state از فایل برمی‌گردد (باید ۱۰۰٪)
- **decay detection:** Engine باید drift خودش را نسبت به ساختار شناسایی کند (meta-learning)

---

## ۱۰. تصمیم‌های باز برای آری

| # | تصمیم | verdict 2026-07-06 |
|---|---|---|
| ۱ | shadow همین حالا؟ | ✅ بله، با شرط صفر-call خارجی تا کلید+budget |
| ۲ | `LEARNING-STATE.json` محل؟ | ✅ `04 - Architect System/learning-engine/` (state است نه recall) |
| ۳ | fallback موتور وقتی Fugu down؟ | ✅ Claude (موجود و تست‌شده) به‌عنوان fallback اول؛ مدل local فاز بعد |
| ۴ | `LEARNING-CONTRACT.yaml` تک‌منبع؟ | ✅ بله، در همان پوشهٔ Engine |
| ۵ | `trigger: loop` در AGENT_REGISTRY؟ | ✅ schema گسترش یابد (با تأیید مالک) |
| ۶ | F4 نشت secret به API خارجی؟ | ✅ فقط روی manifest سبز، صفر استثناء |
| ۷ | SELF-LEARNING-LOOP-SPEC مرجع؟ | ✅ سند در workspace موجود است؛ §۱۶ MASTER خودکفا شده + ارجاع نگه داشته شد. مالک باید نسخه را در vault ذخیره کند |
| ۸ | L8 HANDOFF «بخش Learning state»؟ | به‌جای overwrite HANDOFF: یک سطر در `_memory/HEARTBEAT.md` (هر تسک فقط سطر خودش) + wikilink در HANDOFF (منطبق با الگوی ratified) |

---

## ۱۱. منابع

- ساختار خود سیستم: `PROJECT_INSTRUCTIONS` (L1)، `TWO-BRAIN-CONTROL-BLUEPRINT` (L2)، `PHASE-0A-EXCLUSION-SPEC` (L3)، templates (L5–L9).
- `SELF-LEARNING-LOOP-SPEC` — منطبق با ریل‌های یادگیری (هنوز در vault ذخیره نشده — اقدام مالک، verdict #۷).
- `MASTER-ARCHITECTURE-SPEC` §16 — نمای کلی ([[04 - Architect System/architect/04-Docs/2026-07-06 0215 MASTER-ARCHITECTURE-SPEC-v1.3-draft|نسخه ثبت‌شده]]).
- Sakana Fugu API: RuntimeWire + تأیید چندمنبعی در [[04 - Architect System/architect/04-Docs/2026-07-06 0205 review-master-spec-v1.1|بازبینی v1.1]].

---

> **وضعیت:** ready (verdictهای ۱–۸ ثبت). Engine در shadow mode روشن — صفر call خارجی. فعال‌سازی کامل منوط به گیت‌های §۸.
