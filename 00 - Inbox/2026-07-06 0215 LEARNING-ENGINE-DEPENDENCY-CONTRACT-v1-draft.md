---
type: architecture
status: superseded
tags: [governance, architecture, learning-engine, fugu-integration]
created: 2026-07-06
updated: 2026-07-06
superseded_by: "[[00 - Inbox/2026-07-06 0222 LEARNING-ENGINE-DEPENDENCY-CONTRACT-v1.1-verdicts]]"
---

> [!note] ثبت ایجنت (Inbox-first)
> متن آری، آپلود 2026-07-06. نرمال‌سازی هنگام ثبت: frontmatter با [[06 - Architecture Maps/Property Schema|Property Schema]] سازگار شد (کلیدهای اصلی: type: architecture-spec · owner: آری)؛ wikilink به نوت‌های غایب (`SELF-LEARNING-LOOP-SPEC` — در vault نیست) به متن ساده تبدیل شد؛ ۴ خطای تایپی مدل مبدأ اصلاح شد. تا verdict آری: **proposal، نه canonical.**


# LEARNING-ENGINE-DEPENDENCY-CONTRACT — ستون فقرات مستقل

> **مفهوم اصلی:** Learning Engine یک ماژول مستقل است — lifecycle، state، manifest و تستِ جدا دارد و می‌توان آن را جدا از کل ساختار ساخت/اجرا کرد. اما «مستقل» یعنی **encapsulated**، نه «جدای». این موتور **قراردادهای وابستگی صریح (typed contracts)** با کل ساختار دارد: از هر لایه می‌خورد و به هر لایه برمی‌گرداند. این یعنی یک **ستون فقرات عرضی (cross-cutting spine)** که عمود بر لایه‌های L1–L9 می‌ایستد و به همه وصل است.
> منبع: خودِ ساختار. هر ادعای فراتر از فایل‌های آپلودی با «استنباط».

---

## ۱. چرا «مستقل + وابسته» هم‌زمان؟

| اصل | معنی |
|---|---|
| **استقلال (independence)** | Engine حافظهٔ state خودش را دارد (`LEARNING-STATE.json`)، ورودی/خروجی contract آن فایل-محور است، می‌توان آن را در sandbox جدا ساخت و تست کرد بدون نیاز به کل vault زنده، و خرابیِ یک لایه نباید Engine را kill کند (fail-degraded نه fail-dead). |
| **وابستگی به کل ساختار (whole-structure dependency)** | Engine به‌صورت قراردادی به هر یک از ۹ لایه وصل است: از هر کدام یک ورودی مشخص می‌خورد و یک خروجی مشخص برمی‌گرداند. هیچ لایه‌ای «حق ندارد» بداند Engine چطور فکر می‌کند — فقط contract را رعایت می‌کند. |

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
| دادن | Engine یک بخش «Learning state» به HANDOFF اضافه می‌کند (wikilink فقط، صفر secret) |
| استقلال | state حیاتی هرگز فقط در HANDOFF نیست — در `LEARNING-STATE.json` (#122) |

### 3.10 — L9 Agent Registry

| جهت | قرارداد |
|---|---|
| خوردن | AGENT_REGISTRY، وراثت §Gate، runbook ایجنت‌ها |
| دادن | Engine خودش در AGENT_REGISTRY ثبت می‌شود به‌عنوان یک ایجنت با `trigger: loop`، `level: L1→L3` |
| استقلال | Engine یک ایجنت از نوع خاص است (learning)، نه زیرمجموعهٔ ایجنت‌های عادی |

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
| **shadow mode available** | فقط خواندن + گزارش | ✅ می‌تواند همین حالا |
| **gate-closed mode** | Security Gate + git + budget | ❌ باز |
| **L2 bounded-auto** | + whitelist + استقلال کسب‌شده | ❌ باز |
| **L3 autonomous** | + Gate + git + budget + سقف | ❌ باز |
| **fallback path** | موتور جایگزین وقتی Fugu down | طراحی، اجرا نه (#82) |

---

## ۹. متریک سلامت Engine (مستقل از سلامت ساختار)

- **contract violations:** تعداد دفعاتی که یک لایه contract را نقض کرد (یا Engine نقض کرد) → باید صفر باشد
- **fallback rate:** درصد چرخه‌هایی که Fugu down بود و Engine به fallback رفت
- **shadow→active gap:** تفاوت رفتار Engine در shadow و active (نباید زیاد باشد)
- **state persistence:** پس از restart، state از فایل برمی‌گردد (باید ۱۰۰٪)
- **decay detection:** Engine باید drift خودش را نسبت به ساختار شناسایی کند (meta-learning)

---

## ۱۰. تصمیم‌های باز برای آری

1. آیا Engine در حالت **shadow** همین حالا (قبل از بسته‌شدن Gate) روشن شود؟ (پیشنهاد: بله — صفر ریسک، فقط گزارش)
2. آیا `LEARNING-STATE.json` در `_memory/` باشد یا در پوشهٔ Engine خودش؟ (پیشنهاد: پوشهٔ Engine، چون state حیاتی است نه دادهٔ recall)
3. آیا fallback موتور (وقتی Fugu down) مدل محلی (Qwen/Llama) یا Claude باشد؟ (#82)
4. آیا contractها در `LEARNING-CONTRACT.yaml` به‌عنوان منبع واحد truth باشد؟ (پیشنهاد: بله — تک‌منبع #108)

---

## ۱۱. منابع

- ساختار خود سیستم: `PROJECT_INSTRUCTIONS` (L1)، `TWO-BRAIN-CONTROL-BLUEPRINT` (L2)، `PHASE-0A-EXCLUSION-SPEC` (L3)، templates (L5–L9).
- `SELF-LEARNING-LOOP-SPEC` — منطبق درایل‌های یادگیری.
- `MASTER-ARCHITECTURE-SPEC` §16 — نمای کلی.
- Sakana Fugu API: RuntimeWire

---

> **وضعیت:** draft. Engine مستقل با قراردادهای وابستگی به کل ساختار. قابل اجرا در shadow همین حالا؛ فعال‌سازی کامل منوط به گیت‌های §۸. پس از ratify آری روی §۱۰، نسخهٔ v2 جایگزین می‌شود.
