---
type: base-data-report
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
created: 2026-07-12
updated: 2026-07-12
created_by: fugu-ultra
scope: "Project-F / اونلی فنز — base data for OS build"
tags: [project-f, base-data, obsidian, audit, os-foundation]
aliases: ["Project-F Base Data", "گزارش دیتای پایه Project-F", "اونلی فنز Base Report"]
---

# BASE DATA REPORT — Project-F / اونلی فنز

> **هدف:** گزارش پایهٔ Obsidian-ready برای ساخت OS/سیستم عامل پروژه روی دیتای موجود.  
> **مسیر مبنا:** `F:\backup\03 - Projects\اونلی فنز`  
> **محدودیت دسترسی:** Desktop مستقیم در این ابزار در دسترس نبود؛ تنها مسیر مجاز `F:\backup` بود. هیچ مسیر Desktop یا پوشه‌ای با نام «پازل اختاپوش» در محدودهٔ مجاز پیدا نشد. بنابراین نسخهٔ موجود در vault مبنا گرفته شد.  
> **اصل حاکم:** Read/report فقط. هیچ فایل جابه‌جا نشد، هیچ کد اجرا نشد، هیچ رسانه‌ای باز نشد، هیچ اکشن خارجی انجام نشد.

---

## 0. Executive Summary

Project-F یک پروژهٔ **creator-business faceless / feet-only** با وضعیت `validation` است. پروژه از نظر research، playbook، control manifest، brain/studio/langar specs و کدهای اولیه بسیار غنی است، اما طبق اسناد خودش هنوز **outward execution = صفر** دارد: نه اکانت واقعی، نه پست، نه DM، نه پرداخت، نه launch. مهم‌ترین بلاکر فعال **GATE 0** است: کشور محل اقامت creator/partner باید ثبت شود تا Branch A/B مشخص شود. تا بسته‌شدن GATE 0 و verdictهای انسانی، پروژه فقط باید در حالت **read / analyse / draft / propose** بماند.

سه نتیجهٔ کلیدی برای ساخت OS:

1. **Source of Truth فعلی چندلایه و تا حدی متعارض است.** `PROJECT.md`, `CLAUDE.md`, `PROJECT-F-CONTROL-MANIFEST.json`, `ACQUISITION-ENGINE`, `DecisionLog`, `OpenQuestions`, `THREAD-CLOSURE-D` همگی نقش canonical دارند و باید در OS به یک registry استاندارد تبدیل شوند.
2. **کنترل‌پلین داخلی تقریباً طراحی شده است.** `brain/`, `langar/`, `studio/`, `AGENT-CONTROL-INTERFACE.md` و `PROJECT-F-CONTROL-MANIFEST.json` هستهٔ runtime/control surface را تعریف می‌کنند؛ اما فعال‌سازی Telegram و هر outward action hard-gated است.
3. **برای Obsidian باید ساختار canonical از وضعیت فعلی استخراج شود، نه اینکه فایل‌ها فوراً جابه‌جا شوند.** duplication بین root/docs/research وجود دارد؛ media/PII باید محافظت شود؛ draftهای تستی در `studio/drafts.json` باید quarantine یا reset با approval شود.

---

## 1. Scope & Working Notes

### 1.1 مسیرهای بررسی‌شده

```text
F:\backup\03 - Projects\اونلی فنز
├── root markdown/json/python
├── brain/
├── langar/
├── studio/
├── docs/
├── research/
├── research-results/
├── external-research-2026-07-05/
├── drafts-awaiting-gate/
├── _memory/
└── _inbox-other-projects/
```

### 1.2 فایل‌ها/پوشه‌هایی که عمداً با احتیاط برخورد شدند

- فایل‌های رسانه‌ای/تصویری: فقط inventory، بدون بازکردن یا توصیف محتوا.
- فایل پرسشنامهٔ partner: وجود و نقش آن ثبت شد، اما محتوای حساس بازنشر نمی‌شود.
- secrets/env/key/wallet/seed/pem: طبق سیاست vault خوانده یا echo نشد.
- کد Python: فقط خوانده شد؛ اجرا نشد.

### 1.3 وضعیت خواندن

خوانده شد:

- core files: `PROJECT.md`, `README.md`, `HOME.md`, `INDEX.md`, `CLAUDE.md`, `project-master-reference.md`, `PROJECT-F-CONTROL-MANIFEST.json`, `AGENT-CONTROL-INTERFACE.md`, `DecisionLog.md`, `OpenQuestions.md`
- strategy/playbooks: `MASTER-BUILD`, `Feet-Content-Business-Master-Playbook`, `MONETIZATION-EXPANSION`, `Fable5-Build-Spec`, `PROJECT-F-BRAIN-SPEC`, `PROJECT-F-FULL-REPORT`
- research corpus: `research-results/P1-P10`, `00-executive-summary`, `11`, `12`, `13`, `RESEARCH-INTEGRATION round1/round2`, `ACQUISITION-ENGINE`
- automation/control: `brain/*.py`, `langar/*.py`, `studio/*.py`, JSON config/state files
- drafts: `drafts-awaiting-gate/*`
- memory: `_memory/onlyfans-project-memory-2026-07-05.md`

Inventoried only:

- `test/` empty in tree snapshot.
- `_inbox-other-projects/Ziman_DM_Bot_Package.docx` binary docx, not read as text.

---

## 2. Current State Map

### 2.1 Project identity

```yaml
project_code: Project-F
local_name: اونلی فنز
public_cross_domain_name: Project-F
status: active / validation
risk_level: high
autonomy_level: read-only / propose-only until gates close
owner: آری
team_model: two-person 50/50, A=Operator, C=Creator
current_execution_state: zero outward execution according to project docs
```

### 2.2 Business model summary

```yaml
business_type: creator-economy / faceless feet-only content brand
primary_revenue_hypothesis:
  - free page / subscriber funnel
  - PPV ladder
  - customs
  - tips
  - later VIP / bundles
platform_strategy:
  - OnlyFans: primary monetization
  - Fansly: mirror + discovery
  - Reddit: growth engine
  - X: brand hub / link route
  - TikTok/IG/Shorts: SFW-only later bridge
  - Email/Telegram: owned audience / reports / cockpit, not direct payment
```

### 2.3 Core blocker

```yaml
GATE_0:
  description: "partner/creator country of residence must be recorded and Branch A/B selected"
  status: OPEN according to PROJECT.md and HOME.md
  effect: "no outward action"
  required_record_line: "محل اقامت پارتنر: ___ · تاریخ: ___ · پیامد: Branch A/B"
```

### 2.4 Hard rules

From `PROJECT-F-CONTROL-MANIFEST.json`, `CLAUDE.md`, `DecisionLog.md`:

```yaml
hard_rules_locked:
  - feet-only
  - no face
  - no body
  - no explicit content
  - geo-block Iran across layers
  - no targeting users inside Iran
  - in-platform payment only
  - no platform ToS violation
  - bidirectional privacy
  - no city-level geo facts in public copy
  - Project-F code outside this folder
  - 18+ and recorded consent
  - creator boundary supersedes all plans
```

### 2.5 Current maturity

| Domain | Status | Evidence |
|---|---|---|
| Strategy | Rich / over-complete | MASTER-BUILD, Playbook, Acquisition Engine |
| Research | Very rich | P1–P13, Round1, Round2, external research |
| Governance | Strong draft | CLAUDE.md, Manifest, Control Interface, DecisionLog |
| Runtime brain | Built as code/spec, not live | brain/, BRAIN-BENCHMARK |
| Telegram cockpit | Built/spec, gated | langar/, SABA studio |
| Actual market execution | Not started | repeated zero-execution statements |
| Obsidian hygiene | Good but duplicated | INDEX/HOME strong, duplicate root/docs/research copies |
| Sensitive data control | Strong principles, but some state files need cleanup | drafts.json test data, partner questionnaire exists |

---

## 3. Folder / Vault Architecture

### 3.1 Current folder map

```text
اونلی فنز/
├── PROJECT.md
├── README.md
├── HOME.md
├── INDEX.md
├── CLAUDE.md
├── DecisionLog.md
├── OpenQuestions.md
├── PROJECT-F-CONTROL-MANIFEST.json
├── AGENT-CONTROL-INTERFACE.md
├── project-master-reference.md
├── strategy/playbook docs at root
├── brain/                     # code + benchmark + state
├── langar/                    # operator cockpit code/spec/runbook/config
├── studio/                    # creator studio code/spec/runbook/config/state
├── docs/                      # duplicate/reference copies
├── research/                  # duplicate/research copies
├── research-results/          # P1-P13 corpus
├── external-research-2026-07-05/
├── drafts-awaiting-gate/
├── _memory/
├── _inbox-other-projects/
└── test/
```

### 3.2 Obsidian strengths

- `HOME.md` is a functional dashboard with Dataview blocks and static fallbacks.
- `INDEX.md` is a curated MOC with clear sections.
- Core files use frontmatter and aliases.
- Project is link-rich and already partially optimized for Obsidian.
- The control manifest is machine-readable and PII-minimized.

### 3.3 Obsidian issues

| Issue | Severity | Notes |
|---|---:|---|
| Duplicate root/docs/research files | Medium | Many files exist in root and `docs/`/`research/` with same or near-same names. Need canonical selection before moving. |
| `studio/drafts.json` polluted with many test drafts | High for runtime | Contains many pending test-like entries (`title`, `t`, `draft-003`, etc.). Should be treated as test junk, not production queue. |
| Mixed code + notes in project root | Medium | Obsidian can handle it, but OS build needs separated interface contracts. |
| Binary docx in `_inbox-other-projects` | Low/Medium | Belongs to another project; should not pollute Project-F base OS. |
| PII-sensitive partner questionnaire | High privacy | Must remain inside project, never cross-domain summarized with identity. |
| `research/` duplicates root/research-results | Medium | Need dedup/source-of-truth decision. |

---

## 4. Proposed Obsidian-Optimized OS Structure

> **مهم:** این فقط migration proposal است. هیچ move خودکار بدون approval و link validation انجام نشود.

```text
اونلی فنز/
│
├── 00-Control/
│   ├── PROJECT.md
│   ├── MANIFEST.json              # current PROJECT-F-CONTROL-MANIFEST.json
│   ├── AGENT-CONTROL-INTERFACE.md
│   ├── CLAUDE.md
│   ├── DecisionLog.md
│   ├── OpenQuestions.md
│   ├── VerdictQueue.md            # from THREAD-CLOSURE §۹
│   ├── RiskRegister.md
│   └── Status.md
│
├── 01-Identity/
│   ├── Brand-Decision.md
│   ├── Persona-Lore.md
│   ├── Claims-Register.md
│   └── Privacy-Charter.md
│
├── 02-Strategy/
│   ├── project-master-reference.md
│   ├── MASTER-BUILD-2026-07-04.md
│   ├── Feet-Content-Business-Master-Playbook.md
│   ├── MONETIZATION-EXPANSION-2026-07-04.md
│   └── Canonical-Strategy-Reconciliation.md
│
├── 03-Acquisition/
│   ├── ACQUISITION-ENGINE-2026-07-05.md
│   ├── Channel-Map.md
│   ├── Reddit-Engine.md
│   ├── X-Engine.md
│   ├── Funnel-Geoblock.md
│   └── Owned-Audience.md
│
├── 04-Content-Production/
│   ├── 30-Faceless-Clips-ReadyToFilm.md
│   ├── Content-Topics-Trends-2027.md
│   ├── Content-Taxonomy.md
│   ├── Shot-SOP.md
│   └── Asset-Registry.md
│
├── 05-Experiments-KPI/
│   ├── Fable5-Build-Spec.md
│   ├── KPI-Dashboard-Spec.md
│   ├── Experiment-Log.md
│   └── Gate-Metrics.md
│
├── 06-Compliance-OpSec/
│   ├── OpSec-Checklist.md
│   ├── Legal-Tax-Questions-AU.md
│   ├── GeoBlock-Checklist.md
│   ├── Consent-Boundary-Register.md
│   └── Incident-Runbook.md
│
├── 07-Research/
│   ├── research-results/
│   ├── external-research-2026-07-05/
│   ├── RESEARCH-INTEGRATION-round1.md
│   └── RESEARCH-INTEGRATION-round2-2026-07-10.md
│
├── 08-Brain-Runtime/
│   ├── brain/
│   ├── PROJECT-F-BRAIN-SPEC.md
│   ├── BRAIN-BENCHMARK-2026-07-10.md
│   └── Runtime-State-Notes.md
│
├── 09-Telegram-Interfaces/
│   ├── langar/
│   ├── studio/
│   ├── LANGAR-SPEC.md
│   ├── SABA-STUDIO-SPEC.md
│   └── Telegram-Activation-Gates.md
│
├── 10-Drafts-Awaiting-Gate/
│   └── drafts-awaiting-gate/
│
├── 11-Reports/
│   ├── STATE-REPORT-2026-07-05.md
│   ├── PROJECT-F-FULL-REPORT-2026-07-09.md
│   └── BASE-DATA-REPORT-2026-07-12.md
│
├── 12-Memory/
│   ├── onlyfans-project-memory-2026-07-05.md
│   └── Memory-Policy.md
│
├── 90-Inbox/
│   └── _inbox-other-projects/
│
└── 99-Archive/
```

### 4.1 Migration rule

```text
Do not move now.
First create: Migration Map → Link Validation → Canvas/Dataview Risk Check → Owner Approval → Batch Move → Validate.
```

---

## 5. Agent Role Map

### 5.1 Existing implied agents

| Agent / Module | Location | Role | Status |
|---|---|---|---|
| Master/Architect control | `AGENT-CONTROL-INTERFACE.md`, Manifest | Observe, queue verdicts, kill-switch only | Specified |
| Project-F Brain | `brain/project_f_brain.py`, `PROJECT-F-BRAIN-SPEC.md` | Control-plane + 7 subagents | Code/spec exists |
| Learning layer | `brain/learning.py`, benchmark | Thompson/UCB bandit, exploration-aware learning | Code exists, not executed here |
| AcquisitionBrain | `brain/acquisition.py` | Learn from aggregated post performance | Code exists |
| ABTestTracker | `brain/ab_tracker.py` | Experiment tracking | Code exists |
| KPI Renderer | `brain/kpi_dashboard.py` | HTML dashboard | Code exists |
| Orchestrator | `orchestrator.py` | Full loop, imports vault-level `_ops/neural` | Dependency risk |
| Langar | `langar/` | Ari operator Telegram cockpit | Built/spec, activation gated |
| Saba Studio | `studio/` | Creator-facing Telegram UI | Built/spec, activation gated |

### 5.2 Recommended OS agent society

```text
Project-F Executive Controller
├── Governance / Compliance Guard
├── OpSec & Privacy Guard
├── Research Curator
├── Acquisition Strategist
├── Content Production Planner
├── Pricing / Unit Economics Analyst
├── Experiment & KPI Analyst
├── Memory Curator
├── Telegram Cockpit Adapter (Langar)
├── Creator Studio Adapter (Saba Studio)
└── Evaluator / Regression Tester
```

### 5.3 Authority model

```yaml
default_authority:
  allowed:
    - read
    - map
    - summarize
    - draft
    - propose
    - create candidate reports
    - create memory candidates
  forbidden:
    - create real accounts
    - publish
    - send DMs
    - spend or pay
    - login to platforms
    - alter locked rules
    - reveal identity/content outside folder
    - process raw media
    - write canonical memory without curator gate
```

---

## 6. Telegram Interaction Model

### 6.1 Existing design

- `langar/` = Ari/operator cockpit.
- `studio/` = creator studio UI.
- `PROJECT-F-CONTROL-MANIFEST.json` describes commands, file handoffs and kill switches.
- Telegram activation is explicitly hard-gated; BotFather token creation is human-only.

### 6.2 Existing commands from manifest

Operator cockpit:

```text
/status
/gates
/verdicts
/saba
/drafts
/brief
/think <topic>
/kpi
/report
/upgrade
/rules
/kill
/revive
```

Creator studio:

```text
/start
/menu
/halt
/resume
```

### 6.3 Telegram-safe output template

```text
🎛 Project-F | <TOPIC>
🆔 <DECISION_OR_TASK_ID>
📌 وضعیت:
📊 دادهٔ پایه:
⚠️ ریسک:
✅ تصمیم لازم:
📚 فایل مرجع:
```

### 6.4 Telegram activation gates

```yaml
telegram_activation_requirements:
  - GATE_0 closed with Branch A
  - Security Gate / OpSec checklist complete
  - Tokens stored outside repo/env only
  - Langar tests pass
  - Saba Studio tests pass
  - one-week shadow mode
  - no media/PII in bot flows
  - owner chat-id allowlist
```

---

## 7. Prompt Rewrite Pack / Operating Charter Pack

### 7.1 Existing prompt/charter artifacts

| Artifact | Role |
|---|---|
| `CLAUDE.md` | operating charter / hard rules / workflow |
| `PROMPTS-2026-07-05.md` | ingestion, automation, verification prompts |
| `PROJECT-F-BRAIN-SPEC.md` | GLM/build prompt and brain spec |
| `LANGAR-SPEC.md` | cockpit spec |
| `SABA-STUDIO-SPEC.md` | creator UI spec |
| `marketing-automation-100-topics-2026.md` | broad automation KB / system prompt |

### 7.2 Candidate prompt pack for OS build

Create as proposals only:

```text
09-Agents/Prompt-Versions/
├── PROJECT-F-EXECUTIVE-CONTROLLER-v0.1.md
├── PROJECT-F-RESEARCH-CURATOR-v0.1.md
├── PROJECT-F-COMPLIANCE-GUARD-v0.1.md
├── PROJECT-F-OPSEC-GUARD-v0.1.md
├── PROJECT-F-ACQUISITION-STRATEGIST-v0.1.md
├── PROJECT-F-CONTENT-PLANNER-v0.1.md
├── PROJECT-F-KPI-ANALYST-v0.1.md
├── PROJECT-F-MEMORY-CURATOR-v0.1.md
└── PROJECT-F-EVALUATOR-v0.1.md
```

### 7.3 Prompt invariants

```text
Project-F only.
Never expand identities outside folder.
No external execution.
No platform login.
No publishing.
No DM sending.
No payment.
No raw media processing.
No city-level geo facts.
No Persian textual targeting.
AI drafts; human sends.
Memory candidate ≠ truth.
```

---

## 8. Marketing / Acquisition Experimentation Matrix

> All experiments are **draft/proposal only** until GATE 0 + human verdict.

| ID | Hypothesis | Channel | Variant | Primary metric | Guardrail | Gate |
|---|---|---|---|---|---|---|
| PF-EXP-001 | Reddit niche posts with verified profile produce higher qualified clicks than generic promo subs | Reddit | Tier-1 feet subs vs promo subs | hub→OF clicks / post | no spam, rules checked | G0 + account setup |
| PF-EXP-002 | X pinned funnel converts better than bio-only | X | `x-pin` vs `x-bio` tracking | OF click-through | no forbidden geo/identity terms | G0 + X profile verdict |
| PF-EXP-003 | Starter PPV $5–8 improves first purchase without harming revenue | OF | $5 vs $8 | unlock-rate + first-purchase | price change human-approved | launch + dashboard |
| PF-EXP-004 | Visual cultural cues improve engagement without text risk | X/OF | neutral visual vs cue visual | engagement, no risky inbound | no Persian text, no Iran targeting | OpSec review |
| PF-EXP-005 | Bluesky is a low-risk discovery channel | Bluesky | 15 min/week test | clicks/week | no PII, no overinvestment | post-G1 |

---

## 9. Governance / Safety / Approval Boundaries

### 9.1 Risk ladder

| Risk | Examples | Default action |
|---|---|---|
| Green | read, summarize, map, draft internal report | allow/propose |
| Yellow | prompt candidates, schema candidates, dashboard draft | propose + log |
| Orange | changing docs that affect governance, Telegram activation prep, pricing proposals | require human verdict |
| Red | platform accounts, public posts, DMs, payments, policy change, identity/content exposure | deny until explicit human action |

### 9.2 Hard gates

```yaml
hard_gated:
  - GATE_0 Branch A/B decision
  - signing partnership agreement
  - creating accounts
  - publishing
  - sending DM
  - setting public price
  - changing PPV ladder
  - activating Telegram bots
  - connecting external APIs
  - using real platform dashboards
  - handling media or identity data
  - changing locked rules
```

### 9.3 Kill switches

```yaml
kill_switches:
  langar: "langar/KILL or /kill"
  studio: "studio/HALT or /halt"
  budget: "AUD cap breach → fail closed"
  platform_warning: "stop related automation + log incident"
```

---

## 10. Integration with Larger Octopus System

### 10.1 Limb contract

```yaml
limb_id: Project-F
limb_type: high-risk revenue experiment
path: "03 - Projects/اونلی فنز"
control_manifest: "PROJECT-F-CONTROL-MANIFEST.json"
public_cross_domain_name: "Project-F"
autonomy: "read-only/propose-only until gates"
interface_mode: "observe + verdict queue + kill switch; no execution"
source_of_truth:
  - PROJECT.md
  - CLAUDE.md
  - PROJECT-F-CONTROL-MANIFEST.json
  - AGENT-CONTROL-INTERFACE.md
  - DecisionLog.md
  - OpenQuestions.md
  - THREAD-CLOSURE-D-2026-07-10.md
  - _memory/onlyfans-project-memory-2026-07-05.md
```

### 10.2 Cross-project boundaries

| Other limb | Allowed connection | Forbidden |
|---|---|---|
| Accounting | aggregate revenue under code Project-F only | identity/content details |
| Architect / Control Plane | status, gates, verdict queue, kill switch | hard-gated execution |
| Ziman | none, except `_inbox-other-projects` quarantine | mixing domains |
| Telegram processing | status/approval surface | raw PII/media |
| Memory | candidate summaries and governance facts | secrets/identity/raw conversations |

---

## 11. Source-of-Truth Matrix

| Data / Decision | Current file | Status | Issue |
|---|---|---|---|
| Live project status | `PROJECT.md` | active | GATE 0 open; some sections long |
| Machine control contract | `PROJECT-F-CONTROL-MANIFEST.json` | strong | good candidate for registry ingestion |
| Operating charter | `CLAUDE.md` | active | must remain high-priority |
| Navigation | `HOME.md`, `INDEX.md` | strong | HOME Dataview depends on plugin |
| Decisions | `DecisionLog.md` | strong | large file; may need split by year/topic later |
| Open questions | `OpenQuestions.md` | strong | many items; should map to VerdictQueue |
| Acquisition canonical | `ACQUISITION-ENGINE-2026-07-05.md` | canonical-draft | duplicated in research folder |
| Pricing decision | `THREAD-CLOSURE`, `DECISION-MATRIX`, `ppv-ladder draft` | unresolved | needs verdict |
| Brand decision | 12-prelaunch + THREAD-CLOSURE | unresolved | Anar Soles proposed, not final |
| Runtime state | JSON in `brain/`, `studio/`, `langar/` | mixed | some test/junk state present |
| Partner consent/boundary | questionnaire file | sensitive | do not echo outside project |

---

## 12. Asset / File Inventory Map

### 12.1 Core root files

| File | Purpose | OS role |
|---|---|---|
| `PROJECT.md` | Project identity, active context, blockers, next actions | canonical status |
| `README.md` | Agent-friendly entry map | onboarding |
| `HOME.md` | Obsidian dashboard | human cockpit |
| `INDEX.md` | curated MOC | navigation |
| `CLAUDE.md` | project operating charter | agent policy |
| `PROJECT-F-CONTROL-MANIFEST.json` | machine-readable control manifest | registry/control contract |
| `AGENT-CONTROL-INTERFACE.md` | narrative control interface | orchestrator handoff |
| `DecisionLog.md` | decision ledger | governance history |
| `OpenQuestions.md` | unresolved questions | verdict queue source |
| `project-master-reference.md` | master business reference | strategy source, older than newer docs |
| `Knowledge_Base_Memory_Synthesis.md` | old memory skeleton | stale/reference only |
| `PROMPTS-2026-07-05.md` | mission prompts | prompt library |

### 12.2 Strategy / playbook docs

| File | Purpose | Note |
|---|---|---|
| `MASTER-BUILD-2026-07-04.md` | 20-section execution playbook | contains one pricing/name version |
| `Feet-Content-Business-Master-Playbook.md` | Fable5-ready playbook | second master; conflicts exist |
| `MONETIZATION-EXPANSION-2026-07-04.md` | revenue diversification M1-M11 | awaits human verdict |
| `Fable5-Build-Spec.md` | 10 DB operational build | not confirmed built |
| `PROJECT-F-BRAIN-SPEC.md` | brain architecture + GLM prompt | runtime blueprint |
| `PROJECT-F-FULL-REPORT-2026-07-09.md` | audit/full report | pre-control-interface snapshot |

### 12.3 Research corpus

| Folder/File | Purpose |
|---|---|
| `research-results/00-executive-summary.md` | roll-up of P1-P10 |
| `P1-channel-map.md` | channel matrix and competitor acquisition |
| `P2-x-growth-engine.md` | X/Twitter growth and policy |
| `P3-reddit-engine.md` | Reddit engine and anti-ban SOP |
| `P4-persona-hooks.md` | persona, lore, hooks |
| `P5-funnel-geoblock.md` | funnel + geo-block architecture |
| `P6-owned-audience.md` | email/Telegram ownership layer |
| `P7-dm-automation.md` | DM automation rules and HITL split |
| `P8-s4s-network.md` | S4S/collab economy |
| `P9-repurposing-pipeline.md` | content processing pipeline |
| `P10-analytics-experiment-loop.md` | measurement and experiment loop |
| `11-fresh-scan-2026-07-04.md` | policy/pricing fresh scan |
| `12-prelaunch-verification-2026-07-05.md` | prelaunch verification sprint |
| `13-external-ai-research-integration-2026-07-05.md` | external research integration |
| `RESEARCH-INTEGRATION-round1.md` | delta map round 1 |
| `RESEARCH-INTEGRATION-round2-2026-07-10.md` | deep round 2 WS-1..7 |

### 12.4 Runtime / code surface

| Path | Purpose | Risk/Note |
|---|---|---|
| `brain/project_f_brain.py` | control-plane + 7 agents | propose-only |
| `brain/learning.py` | Thompson/UCB learning | no execution here |
| `brain/acquisition.py` | acquisition memory/plan | aggregate-only |
| `brain/ab_tracker.py` | A/B tests | local JSON state |
| `brain/kpi_dashboard.py` | HTML renderer | read-only dashboard |
| `brain/lifecycle.py` | subscriber lifecycle aggregate | no PII intended |
| `brain/dual_brain*.py` | thinking/communication split | text guard terms |
| `orchestrator.py` | full loop using `_ops/neural` | external dependency risk |
| `langar/langar_bot.py` | operator Telegram cockpit | token required; not activated |
| `studio/saba_studio.py` | creator Telegram UI | token required; not activated |
| `studio/drafts.json` | draft queue | polluted with test data |

### 12.5 Drafts awaiting gate

| Draft | Purpose |
|---|---|
| `link-hub-copy.md` | GAML copy and 18+ gate draft |
| `x-profile.md` | X profile draft |
| `tracking-link-design.md` | tracking link map |
| `ppv-ladder.md` | reconciled pricing draft |
| `kpi-dashboard-spec.md` | KPI spec |

---

## 13. Key Contradictions & Uncertainties

### 13.1 Blocking / P0

| Conflict | Status | Required action |
|---|---|---|
| Partner/creator country of residence | Unknown | Close GATE 0 |
| Body expansion vs current consent boundary | Conflicted | Freeze or delete path by verdict |
| Final questionnaire question unclear | Open | Re-ask simply |

### 13.2 Strategy conflicts

| Topic | Conflict | Recommended resolution path |
|---|---|---|
| Partner hours | 30h vs ~3h/week; THREAD-CLOSURE says ~3h adopted from user input | Mark ~3h as current if owner confirms; archive old 30h as historical |
| Brand | Anar Soles vs Arch & Amber vs others | Choose after handle/trademark check |
| Pricing ladder | 3 versions; EXT-04 favored | Human verdict; then update all playbooks |
| Fansly | mirror vs equal-weight | Adopt “mirror with discovery-first” if approved |
| Canonical master doc | MASTER-BUILD vs Playbook | Create reconciliation note; do not silently overwrite |
| X labeling | sensitive ON vs per-post two-mode | Human verdict |
| AU block | block local buyers vs keep market | Human/creator decision before launch |

### 13.3 Runtime uncertainties

| Issue | Evidence | Action |
|---|---|---|
| `orchestrator.py` imports `_ops/neural` | code read; dependency outside project | test only with full vault after approval |
| `studio/drafts.json` contains many pending test drafts | read file; repeated junk-like entries | quarantine/reset candidate; do not treat as real queue |
| Tests reported green but not run now | docs claim 29 tests | run tests only after owner approval |
| Telegram bots not activated | runbooks show env needed | shadow-mode first |

---

## 14. Memory Candidates

> These are **candidates**, not canonical facts until memory curator accepts.

```yaml
- candidate_id: PF-MEM-001
  type: governance
  claim: "Project-F is a high-risk OCTOPUS limb with default read-only/propose-only autonomy."
  evidence: PROJECT.md, CLAUDE.md, CONTROL-MANIFEST
  confidence: high

- candidate_id: PF-MEM-002
  type: governance
  claim: "GATE 0 is the current blocking gate; no outward execution should occur until Branch A/B is recorded."
  evidence: PROJECT.md, HOME.md, THREAD-CLOSURE-D
  confidence: high

- candidate_id: PF-MEM-003
  type: operating_model
  claim: "Acquisition canonical path is semi-automated: content factory → Reddit/X → GAML/OF/Fansly → human DM → KPI loop."
  evidence: ACQUISITION-ENGINE
  confidence: high

- candidate_id: PF-MEM-004
  type: runtime
  claim: "Langar and Saba Studio are designed as separate Telegram interfaces with file-based handoff and no media/PII."
  evidence: LANGAR-SPEC, SABA-STUDIO-SPEC, code
  confidence: medium-high

- candidate_id: PF-MEM-005
  type: data_quality_issue
  claim: "studio/drafts.json appears polluted with test drafts and must not be treated as production draft queue."
  evidence: studio/drafts.json
  confidence: high
```

---

## 15. Immediate Next Actions

### P0 — Base OS hygiene before build

1. **Confirm path/source:** Is this `F:\backup\03 - Projects\اونلی فنز` the same as Desktop `octopus puzzle/03 project/onlyfans`? If not, copy/sync source is needed.
2. **Create a canonical source-of-truth decision note:** do not move files yet.
3. **Quarantine runtime state issue:** treat `studio/drafts.json` as test polluted until owner approves reset or archival.
4. **Close GATE 0:** without this the OS must remain read-only/propose-only.

### P1 — Obsidian OS scaffold

1. Create candidate folder scaffold (`00-Control`, `01-Identity`, etc.) only after approval.
2. Create `VerdictQueue.md` from `THREAD-CLOSURE-D §۹`.
3. Create `RiskRegister.md` from Round2 §۷ + CLAUDE hard rules.
4. Create `SourceOfTruth-Matrix.md` from section 11 of this report.
5. Create `Runtime-State-Notes.md` documenting JSON state files and which are real vs test.

### P2 — Runtime validation

1. Run tests in read-only/sandbox mode only after approval:
   - `python3 -m unittest brain/test_learning.py -v`
   - `python3 -m unittest langar/test_langar.py -v`
   - `python3 -m unittest studio/test_saba_studio.py -v`
2. Validate no secrets in output.
3. Activate shadow-mode only after GATE 0/security gates.

---

## 16. Proposed Files to Add Next

```text
00-Control/BASE-DATA-REPORT-2026-07-12.md
00-Control/SOURCE-OF-TRUTH-MATRIX.md
00-Control/VERDICT-QUEUE.md
00-Control/RISK-REGISTER.md
00-Control/RUNTIME-STATE-NOTES.md
00-Control/MIGRATION-MAP-DRAFT.md
12-Memory/MEMORY-CANDIDATES-2026-07-12.md
```

Do not add these until owner approves scaffold/migration.

---

## 17. Obsidian Formatting Recommendations

### 17.1 Frontmatter standard

Every new canonical note should use:

```yaml
---
type: <report|control|risk-register|schema|runbook|moc>
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [project-f, ...]
aliases: []
---
```

### 17.2 Naming

- Keep `Project-F` for cross-domain outputs.
- Keep Persian local folder name; do not rename folder without full wikilink/canvas validation.
- Use dated reports for snapshots.
- Use non-dated canonical files for active source-of-truth notes.

### 17.3 Link discipline

- Use relative wiki links inside project for human docs: `[[OpenQuestions]]`.
- For cross-vault canonical root, use full path-style wiki link only when stable.
- Do not wikilink sensitive partner name/identity in cross-domain files.

---

## 18. Final Status

```yaml
report_status: created
path: "F:\backup\03 - Projects\اونلی فنز\BASE-DATA-REPORT-2026-07-12.md"
execution_performed: false
files_moved: false
code_run: false
media_opened: false
secrets_read: false
recommended_next_gate: "Owner confirms source path and approves whether to scaffold canonical 00-Control structure"
```

---

## 19. One Human Decision

آیا همین نسخهٔ vault در مسیر زیر، همان پروژه‌ای است که گفتی داخل Desktop / octopus puzzle / 03 project قرار دارد؟

```text
F:\backup\03 - Projects\اونلی فنز
```

- اگر **بله**: مرحلهٔ بعد، ساخت scaffold و فایل‌های canonical control است.
- اگر **نه**: باید مسیر Desktop را در allowed directories اضافه/وصل کنی یا فایل‌ها را به `F:\backup` sync کنی.
