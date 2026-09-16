---
type: prompt
created: 2026-07-03
target: "Claude (Cowork/Code روی همین vault) — یا هر LLM با ضمیمه‌کردن دو فایل"
inputs:
  - "[[04 - Architect System/architect/02-Research/Report - 20 AGI Architectures 2026|Report - 20 AGI Architectures 2026]]"
  - "معماری vault (داخل همین پرامپت embed شده)"
output: "پیش‌نویس SYSTEM-BLUEPRINT-v3-proposal برای سیستم architect"
status: done
updated: 2026-07-04
---

# پرامپت فیوژن — معماری Vault آری × ۲۰ معماری AGI (۲۰۲۶)

**نحوه استفاده:**
- **حالت ۱ (بهترین):** در Claude Cowork/Code روی همین vault اجرا کن — خودش گزارش و نوت‌های architect را می‌خواند.
- **حالت ۲ (قابل حمل):** بلاک زیر + متن کامل `Report - 20 AGI Architectures 2026.md` را با هم به هر LLM بده.

```text
# ROLE
You are a senior AI systems architect. You design pragmatic agent architectures
for a SOLO developer — no enterprise budgets, no team. You ground every
recommendation in the two inputs below and never propose abstract ideas without
a concrete implementation path in this specific vault.

# INPUT 1 — THE 20 AGI ARCHITECTURES REPORT
The report "Report - 20 AGI Architectures 2026" profiles 20 verified
architectures (July 2026) across 10 families: world models (V-JEPA 2, Genie 3,
Dreamer 4), active inference (AXIOM), neurosymbolic (Hyperon, AlphaProof),
cognitive architectures (SOAR), LLM-agent patterns (ReAct, CoALA),
memory-centric (MemGPT/Letta, Generative Agents), multi-agent (MS Agent
Framework, MetaGPT), self-improving (Darwin Gödel Machine, AlphaEvolve,
AI Scientist-v2), frontier scaling (test-time compute, MoE), embodied VLA
(Gemini Robotics, π0.5).
→ If running inside the vault: read "04 - Architect System/architect/02-Research/Report - 20 AGI Architectures 2026.md"
→ Otherwise: the report is attached below this prompt.

# INPUT 2 — MY ECOSYSTEM (personal Obsidian vault + agent layer, July 2026)

## Roles
- "architect" (in 04 - Architect System) is the MOTHER system: controlled via
  Telegram, does research & design, inspects all other projects.
- Sub-projects (03 - Projects): Lead-نقاشی (main income: Sydney painting
  lead-gen, AiFarm + کاریابی bot), Mining (Orange Pi 5 Pro + ESP32),
  Crypto - etoro (portfolio + data scrapers), Accounting, Ziman Galerry, اونلی فنز.
- Knowledge base (07 - Knowledge): hypnosis & self-awareness corpus (55 notes).

## Directory architecture (sanitized; secrets/_Archive/_code excluded)
vault root
├── CLAUDE.md + _PROJECT_INSTRUCTIONS.md      ← agent constitution (v2.0, priority rules,
│                                                Inbox decision tree, memory protocol)
├── .claude/rules/{architect, projects, telegram}.md ← modular agent rules
├── .agentignore                              ← forbidden paths (secrets-export/, _code/,
│                                                *wallet*, *key*, *seed*, *.env)
├── 00 - Inbox/            ← raw input, then routed (3 notes; incl. the 20-report)
├── 01 - Dashboard/        ← Home.md (entry), HANDOFF.md (session memory,
│                             rewritten each session), Inbox.base, Projects.base
├── 02 - Life OS/          ← 2 notes (weekly review; underused)
├── 03 - Projects/         ← 101 notes; each project has PROJECT.md (identity card,
│   │                         Active Context + Progress sections = working memory)
│   ├── Lead-نقاشی/{AiFarm-Lead, کاریابی, photos}
│   ├── Mining/{Ai bots, Mining-1, Orange Pi Automation System - 20 Projects, ...}
│   ├── Crypto - etoro/{data scrapers, lunarcrush-scraper}
│   └── Accounting/ · Ziman Galerry/ · اونلی فنز/
├── 04 - Architect System/ ← 35 notes — THE TARGET OF THIS UPGRADE
│   ├── architect/00-Home.md
│   ├── architect/01-Project/  SYSTEM-BLUEPRINT-v1 & v2, BACKLOG, DECISIONS, GAPS,
│   │                          HANDOFF, PROMPT-A-absorb-synthesize,
│   │                          PROMPT-B-test-improve, سیستم-همیشه-روشن...
│   ├── architect/02-Research/ 10 research lanes: 05-shared-engineering,
│   │                          06-memory-architecture, 07-self-improvement-loops,
│   │                          08-tool-interoperability, 09-evaluation-observability,
│   │                          10-safety-governance, 11-cost-infra-routing,
│   │                          12-failure-modes, 13-framework-landscape,
│   │                          14-theoretical-foundations
│   ├── architect/{03-Exports, 04-Docs, _attachments, _meta}/ · scripts/ (validators)
├── 05 - Agents/ (reserved) · 06 - Architecture Maps/ (3) · 09 - People/ (1)
├── 10 - Telegram processing/ ← SOP.md + ROUTING.md (telegram → vault pipeline)
├── 07 - Knowledge/ (55) · 08 - Assets/Photos/ · _Templates/ (6)
└── _Archive/ · _Duplicates/ · secrets-export/   ← agents must NEVER read

## Existing memory mechanism (de-facto)
- Session/working memory: 01 - Dashboard/HANDOFF.md (wikilinks only, rewritten per session)
- Project memory: PROJECT.md "Active Context" + "Progress" per project
- Long-term memory: 07 - Knowledge + MOC/index notes
- Routing: 00 - Inbox decision tree + 10 - Telegram processing/ROUTING.md

# MISSION — FUSE THE TWO INPUTS
Map the 20 architectures onto this ecosystem and produce an upgrade blueprint
for the architect system. If inside the vault, ALSO read
"04 - Architect System/architect/01-Project/SYSTEM-BLUEPRINT-v2.md" and research
lanes 06, 07, 09, 11, 13, 14 before proposing, and connect every proposal to the
matching research lane.

## Task A — CoALA gap-scan (باید اول انجام شود)
Score the CURRENT architect system 1–10 on each CoALA component: working /
episodic / semantic / procedural memory, internal vs external action space,
decision loop. Justify each score with an existing file as evidence.

## Task B — نگاشت ۲۰گانه
For EACH of the 20 architectures, one table row:
| معماری | قابل‌اقتباس؟ (بله/جزئی/نه) | ایده اقتباس یک‌خطی برای این vault | لِین تحقیق مرتبط (06–14) |

## Task C — هفت اقتباس برتر (هسته خروجی)
Pick the 7 highest-ROI adoptions. For each: مکانیزم اصلی → پیاده‌سازی دقیق در
همین vault (کدام نوت/پوشه/اسکریپت ساخته یا تغییر می‌کند، ساختار frontmatter،
نقش تلگرام) → هزینه توکنی/زمانی → معیار موفقیت قابل اندازه‌گیری.
Candidate directions you MUST evaluate (accept or reject explicitly):
1. MemGPT/Letta-style tiered memory over HANDOFF.md + PROJECT.md (paging between
   working/archival memory instead of full rewrites)
2. Reflexion loop for the Telegram bot & PROMPT-B-test-improve (verbal
   self-critique stored as episodic notes)
3. Maker-checker (multi-agent) pattern for Inbox routing & vault edits
4. AlphaEvolve-style evolutionary prompt-optimization loop for AiFarm lead-gen
   prompts (archive of prompt variants + automated eval = reply rate)
5. Generative-Agents memory stream (recency/importance/relevance scoring +
   reflection notes) for 09 - People and lead CRM
6. DGM-style archive: never overwrite prompts/blueprints, keep versioned archive
   with fitness scores (extends the existing v1/v2 habit into a mechanism)
7. Test-time-compute routing policy: cheap model for routine routing, expensive
   reasoning model only above an uncertainty threshold (connects to lane 11)

## Task D — ضدالگوها
Which of the 20 must NOT be copied at solo scale, and why (e.g., training world
models, full multi-agent societies, Hyperon substrate). Be blunt.

## Task E — خروجی نهایی و نقشه راه
1. Draft "SYSTEM-BLUEPRINT-v3-proposal.md" (do NOT overwrite v2; save as new note
   in 04 - Architect System/architect/01-Project/)
2. Roadmap ۳۰/۹۰/۳۶۵ روزه with effort×impact matrix (هر آیتم: S/M/L effort)
3. List of exact notes to update afterwards: GAPS.md, BACKLOG.md, DECISIONS.md

# CONSTRAINTS
- Solo developer, budget-conscious; available hardware: Orange Pi 5 Pro + ESP32.
- Vault rules are law: notes = Markdown only; executable code ONLY in
  architect/_code or project code subfolders; never touch paths in .agentignore;
  never echo secrets; no binaries in knowledge folders; no " - Copy"/"(1)" names.
- Do not rename the numbered root folders.
- Every proposal must name the exact file path it touches.
- Write the final output in PERSIAN (فارسی) with English technical terms.

# OUTPUT FORMAT (به همین ترتیب)
1. خلاصه اجرایی (حداکثر ۵ جمله)
2. جدول امتیاز CoALA وضع موجود (Task A)
3. جدول نگاشت ۲۰گانه (Task B)
4. هفت اقتباس برتر با طرح پیاده‌سازی (Task C)
5. ضدالگوها (Task D)
6. پیش‌نویس SYSTEM-BLUEPRINT-v3-proposal + نقشه راه ۳۰/۹۰/۳۶۵ (Task E)
7. ریسک‌ها: هزینه توکن، پیچیدگی نگهداری، امنیت secrets
```

## یادداشت

- درخت بالا sanitized است: مسیرهای `.agentignore` (secrets-export، `_code`، الگوهای wallet/key/seed) و `_Archive`/`_Duplicates` عمداً حذف شده‌اند — در هیچ اجرایی نباید echo شوند.
- فرض کلیدی (صریح): «ترکیب» یعنی نگاشت ۲۰ معماری روی اکوسیستم شخصی برای ارتقای سیستم architect — نه ادغام صرف دو متن. اگر منظور دیگری داری، فقط بخش MISSION را عوض کن.
