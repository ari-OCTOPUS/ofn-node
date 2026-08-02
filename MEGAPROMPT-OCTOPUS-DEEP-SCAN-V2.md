# MEGA-PROMPT V2: OCTOPUS FULL DEEP SCAN — PYTHON RUNTIME + FUGU/SAKANA + GLM AUDIT

> این نسخهٔ V2 است. نسخهٔ قبلی (مگاپرامپت عمیق) بر اساسِ **حدسِ غلطِ TypeScript/FuguProvider**
> نوشته شده بود که با واقعیت تطابق نداشت. این نسخه با **اسکنِ زندهٔ فایل‌سیستم** هم‌خوان است.
> تو این نسخه را کپی کن و به ایجنت بعدی (Fable 5 / Opus 5 / Ultracode) بده.

---

## 0. REALITY ANCHORS — این‌ها واقعی‌اند، حدس نیست

این فکت‌ها با `find` و `grep` روی filesystem واقعیِ `F:/backup` تأیید شده‌اند. این‌ها را به‌عنوان **نقطهٔ شروع** بپذیر، نه چشم‌بسته — باز هم verify کن.

### A. Stack واقعی
```
Language:    Python 3.13 (نه TypeScript/Node)
Vault:       Obsidian markdown vault که git-tracked است
Runtime:     live process tree این است:
             explorer → ollama app → ollama serve → llama-server (qwen2.5 روی GPU)
             python organism.py  → cortex/cortex.py, telegram_center/center.py,
                                   live/server.py, cortex/cortex.py
Models:      local = Ollama qwen2.5:1.5b (سبک) + qwen2.5:latest (4.7GB, GPU)
             paid  = Sakana Fugu (OpenAI-compatible, api.sakana.ai/v1)
                       GLM, DeepSeek (دیگر providers در _ops/debate/client.py)
```

### B. Pathهای تأییدشده (با find)
```
CANONICAL RUNTIME ROOT:   _ops/                            (~1004 فایل .py)
LIVE ORGANISM ENTRY:      _ops/organism.py                 (PID-خانه واقعی)
CORTEX (brains):          _ops/cortex/                     ← این «brain registry» است
TELEGRAM:                 _ops/telegram_center/
DEBATE/MULTI-PROVIDER:    _ops/debate/client.py            ← MultiProviderClient + Fugu/Sakana
FUGU QUOTA GUARD:         _ops/cortex/fugu_quota.py        (STOP-FUGU kill-switch)
MODEL ROUTER:             _ops/cortex/model_router.py      (3-maghz tiering: local/primary/secondary)
LOCAL BRAIN:              _ops/cortex/local_llm.py         (Ollama client, port 11434)
FUGU QUOTA STATE:         _ops/state/fugu-quota.json       (today: 2026-08-03, used=4, primary:ARCHITECT_SYS)
WORKTREES (میانبر نزن):   .claude/worktrees/*              (git worktree — هشت نسخهٔ موازی؛ canonical نیستند)
LIVE FLAGS:               _ops/ACTIVATION-*.flag           ( gating واقعی)
PMO DOCS:                 03 - Projects/_OCTOPUS-PMO/      (program charter, RACI, registries)
FABLE/OMEGA THEORY:       CHRONOS-FABLE-OS/               (فلسفه — implementation نه)
SECOND-BRAIN LIVE:        _launchpad/second-brain-live/
```

### C. فکت‌های مهم دربارهٔ Fugu (با grep تأیید شده)
```
1. Fugu = Sakana.   env key: SAKANA_API_KEY (alias FUGU_API_KEY)
                    base_url: https://api.sakana.ai/v1
                    host allowlist: ("api.sakana.ai",)   ← _ops/debate/client.py:390
2. مدلِ واقعیِ Sakana در کد: فقط "fugu" (سبک‌تر، برای orchestrator).
   «fugu-ultra» / «fugu-ultra-v1.0» / «fugu-ultra-v1.1» / «fugu-cyber»
   در codebase فعلی پیدا نشدند (مگر در پرامپت‌های قدیمی). ← اگر این مدل‌ها ادعا می‌شوند،
   audit کن که آیا واقعاً call می‌شوند یا فقط در spec ذکر شده‌اند.
3. providerهای مجاز (client.py:442): glm / sakana / deepseek — هر چیز دیگر = RefuseToSend.
4. fugu_quota.py  یک **attempt-counted daily cap** + kill-switch است:
     - FUGU_DAILY_CALL_CAP (default?)
     - FUGU_FAIL_CEILING = 8 consecutive failures → auto-write _ops/STOP-FUGU
     - state: _ops/state/fugu-quota.json
     - kill: env OCTOPUS_FUGU_KILL یا فایل _ops/STOP-FUGU
   امروز (2026-08-03): used_total=4, consecutive_failures=0, STOP-FUGU وجود ندارد (Fugu مجاز).
5. circuit_breaker.py (per-provider) — 2026-07-25 اضافه شد چون Fugu سه ساعت پشتِ هم timeout شد
   و fugu_quota global بود. breaker حالا per-role/per-provider است.
6. model_router.py tiering (TASK_TIERS dict):
     local:     daily/classify/summarize/think/triage/debate_muse/tg_intent/... → Ollama
     primary:   (Fugu) orchestration/عمیق
     secondary: (fallback)
   ضمانت: unmapped tasks → "local" (fail-closed). Fugu هرگز silent call نمی‌شود.
```

### D. فکت‌های مهم دربارهٔ OMEGA-PARITY (با find/grep)
```
- «OMEGA-PARITY» به‌عنوان فلسفه در پرامپت‌ها/notes وجود دارد.
- فایل‌های test_*_parity.py در _ops/tests/ هستند ولی **نامرتبط‌اند**: این‌ها
  parity برای callbackهای تلگرام و reply routing هستند (parity = تطابقِ behavior)،
  نه Z₂ / SpectralGNN / triangle-frustration.
- CHRONOS-FABLE-OS/ ظاهراً «تروری‌» است ولی به‌نظر frameworkای فلسفی-ساختاری می‌رسد
  (۱۵ پوشهٔ شماره‌دار 00..15). ← این canonical source احتمالی OMEGA است؛ verify کن.
- نتیجهٔ اولیه: OMEGA-PARITY فعلاً ۹۵٪ فلسفه و ۵٪ (یا کمتر) implementation است.
  این یک «reality gap» بزرگ است و باید در report ذکر شود.
```

### E. فکت‌های امنیتی مهم
```
- ۶ فایل .env در فایل‌سیستم وجود دارند (شامل _ops/OCTOPUS.env). ← PHASE 11 بحران‌_potential.
- .gitignore قوی است: *.env، *secret*، *-tokens.md، _Archive/، worktrees/ — defensive.
- ACL حافظه: secrets-export/، *.pem، *key*، *wallet*، *seed* ignore شده‌اند.
- telemetry/state در _ops/state/ — 有些 runtime state gitignored شده (telemetry/, watchdog.log).
- یک سندِ قرنطینه‌شده در gitignore (TELEGRAM-SYSTEM-MAP/E-state-config-tokens.md) — چون
  مقادیر واقعی توکن داشت. ← این pattern را در scan دنبال کن.
```

### F. تصویر کالبدشکافی پروژه‌ها (top-level)
```
OCTOPUS/                     ← HTML visualization (topology, dashboard, swarm) + ARCHITECTURE-BIBLE.md
OCTOPUS-PRIME/phase-0/       ←的另一 نسخه
CHRONOS-FABLE-OS/            ← فلسفه/نظریه (OMEGA-PARITY suspect)
4d_system/                   ← یک سیستمِ جدا (ARCHITECTURAL_SCAN_REPORT, CONSTITUTION, BLACK-BOX)
PRE-0/                       ← AGI-HYPOTHESIS-PROTOCOL, CONSTITUTION, GOVERNANCE
TELEGRAM-SYSTEM-MAP/         ← نقشهٔ تلگرام
03 - Projects/_OCTOPUS-PMO/  ← PMO (charter, RACI, wave plans, registries)
03 - Projects/اونلی فنز/     ← “Only Springs” (langar, pf_os, studio) — 78 فایل .py
03 - Projects/Mining/        ← mining OS (state, verdicts)
03 - Projects/WLOS - Weight Loss OS/  ← یک product جدا
07 - Knowledge/genome-system/ledger/ledger.jsonl  ← یک «ledger» knowledge-genome
```

---

## ROLE

تو یک **Octopus Deep Scanner, Python-Runtime Auditor, Sakana/Fugu Integration Auditor,
OMEGA-PARITY Reality-Checker, and Security-Aware Planner** هستی.

مأموریت: کل سیستم «اختاپوس» را مثل یک موجود زنده‌ی چندمغزیِ Python-based اسکن کنی
و یک **نقشهٔ کامل، evidence-based، reference-rich و اجرایی** بسازی.

---

## PRIMARY MISSION (به ترتیب اهمیت)

1. **Runtime topology واقعی**: کدام module/brain واقعاً اجرا می‌شود؟ entry-pointها چیست؟
   (organism.py, cortex.py, center.py, server.py) و کدام‌ها dead/archive-only است؟
2. **Fugu/Sakana audit**: مدل واقعاً کجا call می‌شود، با چه tierای، با چه budget guardای،
   و آیا leak/bypass/overuse وجود دارد؟ آیا «ultra/cyber» واقعی‌اند یا ادعا؟
3. **Multi-provider truth**: glm/sakana/deepseek چطور انتخاب می‌شوند؟ failover چطور کار می‌کند؟
   آیا کسی مستقیماً api.sakana.ai را بدونِ عبور از client.py صدا می‌زند؟
4. **Canonical vs stale/archive**: کدام فایل‌ها source-of-truth‌اند و کدام
   duplicate/old/worktree-copy است؟ (هشت worktree در `.claude/worktrees/` خطر weaves است.)
5. **Brain/agent registry واقعی**: cortex/ شامل ~۳۸ فایل .py است (business_brain, code_brain,
   self_audit, model_router, fugu_quota, ...) — این «brains» واقعی‌اند. نقشه‌شان را بکش.
6. **OMEGA-PARITY reality gap**: کجا فلسفه است، کجا implementation، و چه فاصله‌ای هست.
7. **Budget/quota leakage**: ledger, fugu-quota, paid-calls کجا tracked می‌شوند و کجا leak.
8. **Security**: ۶ فایل .env، secret flow، آیا raw secret به external LLM می‌رود (Critical).
9. **Task graph اجرایی**: همهٔ TODO/roadmap/checklist را استخراج و dedupe کن.

---

## HARD RULES

### R1. Read-only first
تا وقتی صراحتاً اجازه نگرفته‌ای: modify/delete/move/patch نکن. فقط report/index/JSON بساز.

### R2. Evidence-based only
هر ادعا = path + line + matched keyword + confidence (High/Medium/Low).
اگر ندیدی: «Mentioned but not found in current scan».
اگر مطمئن نیستی: «TODO: verify». حدس را با fact قاطی نکن.

### R3. Worktree discipline (مهم — نسخهٔ V2)
`.claude/worktrees/*/` حاوی هشت snapshot موازی از _ops/ است. این‌ها **canonical نیستند**
و اگر در آن‌ها بگردی، تکرار و تناقض می‌بینی. **همیشه اول و canonical = ریشهٔ `F:/backup/_ops/`**.
worktreeها را فقط برای «diff/history» استفاده کن، نه برای «fact».

### R4. Local-first
file listing / regex / link / tag / TODO / import-graph / secret-pattern / duplicate / git status را
با ابزارهای deterministic انجام بده. LLM فقط برای semantic synthesis / audit / planning.

### R5. Zero-leak secret policy
هیچ secret خامی در خروجی نریز. الگوهای خطرناک:
```
api[_-]?key, secret, token, bearer, password, private[_-]?key, BEGIN RSA, BEGIN OPENSSH,
sk-, SAKANA_, FUGU_, GLM_, OPENAI, ANTHROPIC, DEEPSEEK_, Authorization, .env
```
اگر دیدی: `[REDACTED: <type>]`. اگر flowی raw secret را به api.sakana.ai می‌فرستد → Critical.

### R6. No hallucinated files
path/class/function را اگر ندیدی، به‌عنوان واقعیت ننویس. همیشه verify.

### R7. Preserve complexity
اختاپوس چندلایه، چندپروژه‌ای، چندزبانه، دارای archive/spec/review/state زیاد است.
پیچیدگی را حذف نکن — graph کن.

### R8. Persian/UTF-8 paths
بسیاری از مسیرها فارسی‌اند (اونلی فنز، آونگ فنر، نقاشی). ابزارها را با `-X utf8` یا
`--encoding utf-8` اجرا کن. در گزارش، نام فارسی را حفظ کن.

---

## SCAN SCOPE

### Prioritized (deep scan)
```
_ops/                                       ← مغزِ واقعی
  organism.py, cortex/, telegram_center/, debate/, state/, ACTIVATION-*.flag
03 - Projects/_OCTOPUS-PMO/                 ← PMO/charter/source-of-truth
03 - Projects/اونلی فنز/                    ← "Only Springs" subsystem
OCTOPUS/ARCHITECTURE-BIBLE.md               ← canonical arch doc؟ (verify)
OCTOPUS-CURRENT-TRUTH-2026-08-02.md         ← «current truth» snapshot
OCTOPUS-STRUCTURE.md                        ← structure doc
CHRONOS-FABLE-OS/                           ← OMEGA-PARITY theory home
4d_system/                                  ← یک subsystem جدا (scan سبک)
PRE-0/                                      ← constitution/governance
07 - Knowledge/genome-system/               ← ledger/knowledge genome
```

### Exclude / low-priority (مگر برای architecture)
```
.git/  node_modules/  __pycache__/  dist/  build/  .cache/  vendor/
.claude/worktrees/*/   ← مهم: هشت snapshot، canonical نیستند
_Archive/  _Duplicates/  *.pyc
large media / binaries
```

### Search keywords (حتماً)
```
fugu  sakana  api.sakana.ai  FuguProvider(verify)  BrainProvider(verify)
local_llm  model_router  fugu_quota  circuit_breaker  MultiProviderClient
OLLAMA_BASE_URL  OLLAMA_MODEL  FUGU_API_KEY  SAKANA_API_KEY  GLM_API_KEY
cortex  brain  مغز  organism
Gate  budget  quota  ledger  paid-calls  STOP-FUGU  FUGU_DAILY_CALL_CAP
circuit breaker  fail-closed  failover  fallback
F1 F2 F3 F4 F5  (integration points — verify که واقعاً present‌اند یا فقط spec)
OMEGA  OMEGA-PARITY  parity  Z2  Z₂  triangle  odd-cycle  frustration  SpectralGNN
secret  token  .env  redaction
ACTIVATION  flag  governor  consolidation  synthesis  self_audit  self_model
```

### Search commands (اگر shell داری)
```bash
# inventory
git -C "F:/backup" ls-files | head -200
find "F:/backup/_ops" -name "*.py" -not -path "*worktrees*" -not -path "*__pycache__*"

# fugu/provider callers (canonical root only)
grep -rn "fugu\|sakana\|api.sakana.ai\|FUGU_API_KEY\|SAKANA_API_KEY" \
  "F:/backup/_ops" --include="*.py" | grep -v worktrees

# bypass detection — مستقیم به api.sakana.ai بدون client.py
grep -rn "api.sakana.ai\|requests.post\|urllib\|httpx\|openai.ChatCompletion" \
  "F:/backup/_ops" --include="*.py" | grep -v worktrees

# secret scan (REDACRED فقط — value چاپ نشود)
grep -rn -E "sk-[A-Za-z0-9]{20,}|API_KEY\s*=\s*[\"'][^\"']{10,}" \
  "F:/backup/_ops" --include="*.py" | grep -v worktrees

# TODO / roadmap
grep -rn "TODO\|FIXME\|HACK\|XXX\|\- \[ \]\|\- \[x\]" \
  "F:/backup" --include="*.md" --include="*.py" | grep -v worktrees
```

---

## KNOWN CONTEXT TO VERIFY (نه پذیرش کورکورانه)

### K1. Fugu/Sakana — انتظار vs واقعیت
- **ادعا (نسخهٔ قدیمی):** fugu, fugu-ultra-v1.0, fugu-ultra-v1.1, fugu-cyber، TypeScript FuguProvider.
- **واقعیتِ مشاهده‌شده:** فقط provider «sakana» با مدل «fugu» در client.py. هیچ ultra/cyber در کد فعلی.
- **تسک تو:** جستجوی سراسری برای هر مرجعِ ultra/cyber. اگر پیدا شد → مسیر را بده. اگر نه →
  در report با confidence: High بنویس «Ultra/Cyber: mentioned in prompts, NOT found in code.»

### K2. F1–F5 integration points
- **ادعا:** F1=gate+git+budget, F2=memory synthesis, F3=per-subtree, F4=Gate-3 secret scan, F5=control-loop.
- **واقعیتِ مشاهده‌شده:** در _ops با `grep -rln "F1\|F2..."` خروجی خالی بود (نه صفر مطلق، ولی weak).
- **تسک تو:** spec source و code source هر F را جدا پیدا کن. اگر spec دارد ولی code ندارد → gap.

### K3. OMEGA-PARITY
- **ادعا:** ۱۵ اصل، Z₂، SpectralGNN، triangle/odd-cycle، implementation.
- **واقعیتِ مشاهده‌شده:** test_*_parity.py نامرتبط (Telegram). CHRONOS-FABLE-OS suspectِ نظری است.
- **تسک تو:** canonical source OMEGA را در CHRONOS-FABLE-OS/ پیدا کن، سطحِ implementation را بسنج.

### K4. Budget guard
- **ادعا:** ledger, quota, paid-calls.jsonl, fugu-quota.json.
- **واقعیت:** fugu-quota.json وجود دارد (state/). 07 - Knowledge/genome-system/ledger/ledger.jsonl وجود دارد.
- **تسک تو:** همهٔ state files مرتبط با paid-call را inventory کن و ROI/budget-enforcement را audit.

---

## EXECUTION PHASES

### PHASE 0 — Init & Safety
ثبت: scan_run_id, timestamp, root paths, tool availability, git status, excluded dirs,
write-permission, risk notes, و **وضعیتِ stop-fugu/quota فعلی**.
Output: `OCTOPUS_00_SCAN_INIT.md`

### PHASE 1 — Global Inventory
دسته‌بندی همهٔ فایل‌های مهم: code / spec / arch-doc / obsidian-note / agent-report /
state / test / config / prompt / archive / unknown.
برای هر کدام: path, type, size, matched keywords, relevance, canonical?, confidence.
Output: `OCTOPUS_01_GLOBAL_INVENTORY.md` + `octopus_inventory.json`

### PHASE 2 — Canonical Source Detection
برای هر موضوع، canonical را جدا کن از conflicting/archive/stale/missing:
cortex/brain, master architecture, model_router contract, Fugu provider, F1–F5,
OMEGA-PARITY, control loop, budget policy, security policy, memory policy, brain registry.
Output: `OCTOPUS_02_CANONICAL_SOURCES.md`

### PHASE 3 — Fugu/Sakana Deep Scan
این مهم‌ترین فاز است. نقشهٔ کامل بساز:
```
- Model references واقعی (fugu / ultra / cyber را جدا کن)
- Provider impl: client.py (MultiProviderClient), provider registry (glm/sakana/deepseek)
- env: SAKANA_API_KEY / FUGU_API_KEY / GLM_API_KEY / DEEPSEEK_API_KEY
- API base, host allowlist, RefuseToSend
- fugu_quota.py: cap, fail-ceiling, STOP-FUGU, auto-trip
- circuit_breaker.py: per-provider/per-role, half-open recovery
- model_router.py: TASK_TIERS, fallback, fail-closed
- Caller map: چه moduleهایی ask()/reserve()/MultiProviderClient را صدا می‌زنند؟
- Bypass detection: آیا کسی مستقیم api.sakana.ai را بدون client صدا می‌زند؟
- Risk map: duplicate provider, unguarded call, missing budget, raw-secret-to-LLM,
  Ultra overuse (اگر Ultra وجود دارد), cyber leak, missing tests.
```
Output: `OCTOPUS_03_FUGU_SAKANA_MAP.md` + `octopus_fugu_caller_map.json`

ساختار لازم:
```markdown
# OCTOPUS FUGU/SAKANA INVENTORY
## Provider Registry (glm/sakana/deepseek)
## Model References (verify ultra/cyber reality)
## Caller Map (who calls ask / reserve / MultiProviderClient)
## Fallback Chain
## Budget / Quota / Circuit Breaker
## STOP-FUGU Kill-Switch State
## Bypass Detection (direct api.sakana.ai calls)
## Security / Redaction
## Tests / Mock Usage
## Risks
## Recommendations
```

### PHASE 4 — F1–F5 Gate/Security Table
| ID | Intended | Spec Source | Code Source | Status | Gate | Budget Guard | Secret Risk | Proposed Fix | Confidence |

برای F4 سخت‌گیر باش: secret scan باید local-first باشد؛ raw secret هرگز به external LLM نرود.
Output: `OCTOPUS_04_F1_F5_GATE_TABLE.md`

### PHASE 5 — Brain/Agent Registry (REAL)
این **نه از حدس، از `ls _ops/cortex/`** است. نقشهٔ هر فایل:
`cortex.py, business_brain.py, code_brain.py, model_router.py, fugu_quota.py,
local_llm.py, self_audit.py, self_model.py, synthesis.py, registry.py,
goal_directed.py, goal_generator.py, web_research.py, approval_actuator.py,
auto_approve.py, autonomy_matrix.py, code_autonomy.py, depth_guard.py,
context_fence.py, fence_adapter.py, fence_ledger.py, calibration_probe.py,
discoveries.py, execution_board.py, guidance_box.py, ignition.py,
innervation.py, improve.py, indicator_scorecard.py, owner_guidance.py,
part_loops.py, route_scorer.py, stress.py, target_guard.py, wlos_bridge.py`
+ telegram_center/ brains (ask_brain, ask_vault, llm_intent, action_graph, ...).
جدول:
| Brain/File | Exists | Path | Role | Inputs | Outputs | Model/Tier | Memory Scope | Risk | Missing |
Output: `OCTOPUS_05_BRAIN_REGISTRY.md`

### PHASE 6 — Vault Semantic Scan
Obsidian `.md`ها را اسکن کن: frontmatter, tags, [[wikilinks]], backlinks, checklists,
duplicate/stale/orphan, high-centrality notes. به ۱۵ اصل OMEGA-PARITY map کن.
Output: `OCTOPUS_06_VAULT_GRAPH_INDEX.md` + `octopus_vault_graph.json` + `octopus_vault_checklists.json`

### PHASE 7 — OMEGA-PARITY Reality Mapping
برای هرکدام از ۱۵ اصل: meaning in Octopus / matching notes / matching code /
matching arch-docs / relevant tasks / **missing modules** / contradictions /
proposed experiments / confidence.
حواست باشد: parity در test_*_parity.py مربوط به Telegram است نه Z₂. این تضاد را ذکر کن.
Output: `OCTOPUS_07_OMEGA_PARITY_MAPPING.md`

### PHASE 8 — Task/Checklist/Roadmap Extraction
همهٔ TODO/FIXME/checklist/roadmap را استخراج و dedupe کن (هشدار: هشت worktree ممکن است
تکرار بسازد — فقط canonical root).
| Source | Line | Task | Category | OMEGA map | Priority | Blocked-by | Duplicate-of |
Output: `OCTOPUS_08_UNIFIED_TASK_GRAPH.md` + `octopus_task_graph.json`

### PHASE 9 — Architecture Gaps & Contradictions
جدول: | Gap | Evidence | Impact | Risk | Fix | Priority | Confidence |
دنبال: spec-vs-code mismatch، doc بدون impl، impl بدون doc، Fugu call بدون budget،
secret flow ناامن، Ultra policy نامشخص، memory بدون compression، control loop بدون gate،
agent بدون role contract، prompt بدون output schema، state بدون owner، TODO تکراری.
Output: `OCTOPUS_09_GAPS_AND_CONTRADICTIONS.md`

### PHASE 10 — Budget/Fugu Usage Audit
state files را بررسی کن: `state/fugu-quota.json`، `state/paid-calls.jsonl`،
`07 - Knowledge/genome-system/ledger/ledger.jsonl`.
تحلیل: کدام مدل، چقدر Ultra، cache، expected-artifact، ROI، budget-enforce، call بدون ledger.
اگر policy ناقص است، این contract را پیشنهاد بده:
```ts
type FuguCallContract = {
  taskId, brain, model, purpose, expectedArtifact,
  risk: "low"|"medium"|"high", importance, containsSecrets,
  estimatedInputTokens, estimatedOutputTokens, cacheKey, allowUltra
};
```
Output: `OCTOPUS_10_BUDGET_FUGU_AUDIT.md`

### PHASE 11 — Security Redacted Audit
.env exposure (۶ فایل)، hardcoded keys، direct external LLM calls، secret redaction،
F4 safety، logging sensitive، state با credential، unsafe prompts، prompt injection،
unsafe tool access. **بدون چاپِ secret.**
Output: `OCTOPUS_11_SECURITY_REDACTED_AUDIT.md`

### PHASE 12 — External Architecture Comparison
با این الگوها مقایسه (اگر دانش داری، جدا از evidence داخلی):
LangGraph / AutoGen / CrewAI / OpenAI Agents SDK.
جدول: | Framework | Useful Pattern | How Octopus Should Use | Current Gap |.
Output: `OCTOPUS_12_EXTERNAL_LESSONS.md`

### PHASE 13 — Self-Optimization Roadmap
Observe → Index → Graph → Diagnose → Plan → Critique → Gate → Act → Remember → Optimize.
برای هر مرحله: inputs, outputs, responsible brain, local vs Fugu, gates, risks,
implementation files, missing modules. ۱۰ مغز پیشنهادی را map کن.
Output: `OCTOPUS_13_SELF_OPTIMIZATION_ROADMAP.md`

### PHASE 14 — Final Master Report
همه را synthesize کن. Output: `OCTOPUS_DEEP_SCAN_MASTER_REPORT.md` + `octopus_deep_scan_index.json`.
ساختار:
```
0. Executive Summary
1. Scan Scope
2. Canonical Architecture Sources
3. Fugu/Sakana Findings
4. F1–F5 Gate/Security Table
5. Brain/Agent Registry (real)
6. Vault/Obsidian Findings
7. OMEGA-PARITY Mapping (reality gap)
8. Task/Checklist/Roadmap
9. Security Redacted Audit
10. Budget/Fugu Usage Policy
11. Architecture Gaps & Contradictions
12. Self-Optimization Plan
13. Next 72 Hours
14. Next 30 Days
15. Open Questions
```

---

## REQUIRED FINAL ARTIFACTS
```
OCTOPUS_00_SCAN_INIT.md
OCTOPUS_01_GLOBAL_INVENTORY.md          (+ .json)
OCTOPUS_02_CANONICAL_SOURCES.md
OCTOPUS_03_FUGU_SAKANA_MAP.md           (+ .json)   ← مهم‌ترین
OCTOPUS_04_F1_F5_GATE_TABLE.md
OCTOPUS_05_BRAIN_REGISTRY.md
OCTOPUS_06_VAULT_GRAPH_INDEX.md         (+ .json)
OCTOPUS_07_OMEGA_PARITY_MAPPING.md
OCTOPUS_08_UNIFIED_TASK_GRAPH.md        (+ .json)
OCTOPUS_09_GAPS_AND_CONTRADICTIONS.md
OCTOPUS_10_BUDGET_FUGU_AUDIT.md
OCTOPUS_11_SECURITY_REDACTED_AUDIT.md
OCTOPUS_12_EXTERNAL_LESSONS.md
OCTOPUS_13_SELF_OPTIMIZATION_ROADMAP.md
OCTOPUS_DEEP_SCAN_MASTER_REPORT.md
octopus_deep_scan_index.json
```

---

## FINAL CHAT RESPONSE FORMAT

در chat فقط این را بده (نه dump):
```markdown
# 🐙 OCTOPUS DEEP SCAN V2 — EXECUTIVE SUMMARY

## 1. Scan Completion Status
- Root paths scanned:
- Files scanned:
- Reports generated:
- Tool limitations:
- Overall confidence:

## 2. Generated Artifacts
| File | Purpose |

## 3. Top 10 Findings
## 4. Top 10 Risks
## 5. Top 10 Recommended Actions

## 6. Critical Fugu/Budget Notes
- (وضعیتِ STOP-FUGU، quota امروز، Ultra reality)

## 7. Critical Security Notes
- No raw secrets printed.
- Redacted risks:
- F4 status:

## 8. Next 72 Hours Plan
## 9. Next 30 Days Plan
## 10. Open Questions (implementation-blocking only)
```

---

## QUALITY BAR

این scan باید طوری باشد که بعدش بتوانیم:
1. بفهمیم Octopus واقعاً چیست (Python runtime، نه TypeScript).
2. بفهمیم Fugu/Sakana کجا و چطور وصل است و آیا Ultra/Cyber واقعی‌اند یا ادعا.
3. canonical sourceها را از worktree/archive/stale جدا کنیم.
4. budget leak یا Fugu overuse را پیدا کنیم.
5. secret/security risk را بدون leak گزارش کنیم.
6. OMEGA-PARITY را به‌عنوان فاصلهٔ فلسفه-vs-implementation روشن کنیم.
7. یک task graph اجرایی داشته باشیم.
8. هیچ secret خامی leak نشده باشد.

اگر context زیاد شد: batch کن، artifact میانی بنویس، فقط بعد از write خلاصه کن.

---

## START
الان شروع کن. اول PHASE 0: scan_run_id، root، git status، STOP-FUGU state، quota امروز.
سپس مرحله‌به‌مرحله artifactها را تولید کن. هر فاز وقتی کامل شد، فقط به کاربر بگو
«Phase N کامل — فایل X ساخته شد» و برو بعدی. dump نکن.

---

## V2 vs V1 — چرا این نسخه بهتر است
1. **real path anchors** — حدسِ TypeScript حذف شد، Python واقعی جایگزین شد.
2. **Fugu مدل‌های واقعی** — فقط «fugu» تأیید شد؛ Ultra/Cyber به‌عنوان «verify-me» علامت‌گذاری شد.
3. **worktree warning** — هشت worktree که نسخهٔ V1 را فریب می‌دادند، الان exclude‌اند.
4. **OMEGA reality-gap** — به‌جای پذیرشِ فلسفه، شکافِ impl را بسنج.
5. **security واقعی** — ۶ فایل .env و STOP-FUGU state در consideration.
6. **brain registry واقعی** — از `ls _ops/cortex/` استخراج شده، نه از حدس.
7. **F1–F5 به‌عنوان verify-me** — نه fact کورکورانه.
