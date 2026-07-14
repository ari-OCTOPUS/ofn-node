# 🧠🕸️ Multi-Agent Memory + Graph Search Design

> Workspace: `پازل هشت پا`  
> Created: 2026-07-11  
> Objective: حافظه‌دار کردن همهٔ ایجنت‌ها و طراحی سیستم جستجوی گرافی برای بهترین اجرای مرحله‌به‌مرحله.

---

## 0. خلاصهٔ تصمیم

این workspace باید یک سیستم چندایجنتی با سه لایه حافظه داشته باشد:

1. **Project Memory** — حافظهٔ محلی هر پروژه.
2. **Graph Memory** — گراف مشترک ارتباطات بین پروژه‌ها، تصمیم‌ها، فایل‌ها، ریسک‌ها و اکشن‌ها.
3. **Execution Memory** — لاگ اجرای مرحله‌ای، verdictها، خطاها و handoff برای ایجنت بعدی.

اصل طراحی:

```text
هر ایجنت قبل از پاسخ/ویرایش باید graph search بزند، context مرتبط را لود کند، بعد عمل کند، بعد memory را append کند.
```

---

## 1. نقش‌ها / Agent Roles

| Agent | نقش | ورودی | خروجی | حافظه اصلی |
|---|---|---|---|---|
| Orchestrator | تقسیم کار و ترتیب اجرا | root registry + verdict queue | task packet | Execution Memory |
| Cartographer | اسکن فایل‌ها و ساخت گراف | workspace files | graph index | Graph Memory |
| Project Steward | تکمیل هر پروژه | project folder | README/MANIFEST/RUNBOOK/REGISTRY | Project Memory |
| Risk Governor | ریسک و hard-gate | risk ladder + manifests | allow/deny/propose verdict | Risk Memory |
| Accountant Steward | قلب مالی | Accounting docs | tax-safe runbook + questions | Accounting Memory |
| Revenue Steward | Lead/Ziman | portfolio + funnel docs | experiment plan | Revenue Memory |
| Privacy Steward | Project-F | contained docs | safe status only | Containment Memory |
| Crypto/Mining Sentinel | sensing only | registries | alert-only reports | Sensing Memory |
| Brain Integrator | NBB/4D/Architect sync | app/4d/context | adapter plan | Brain Memory |
| Handoff Writer | پایان هر مرحله | deltas + decisions | prompt for next agent | Execution Memory |

---

## 2. Memory Architecture

### 2.1 Folder layout پیشنهادی

```text
_memory/
  graph/
    nodes.jsonl
    edges.jsonl
    index.md
    graph-report.md
  agents/
    orchestrator.md
    cartographer.md
    accounting-steward.md
    revenue-steward.md
    risk-governor.md
    handoff-writer.md
  execution/
    runs.jsonl
    errors.jsonl
    decisions.jsonl
    open-loops.md
```

در این distilled workspace اگر `_memory/` وجود ندارد، ساخته می‌شود.

### 2.2 Memory event schema

هر memory append باید چنین شکلی داشته باشد:

```json
{
  "ts": "2026-07-11T00:00:00+10:00",
  "agent": "accounting-steward",
  "event_type": "observation|decision|action|question|error|handoff",
  "entity": "Accounting",
  "summary": "short safe summary",
  "evidence_paths": ["03 - Projects/Accounting/RUNBOOK.md"],
  "risk": "low|medium|high|critical",
  "requires_verdict": false,
  "next": ["..."],
  "pii_safe": true,
  "secret_safe": true
}
```

---

## 3. Graph Model

### 3.1 Node types

```yaml
Project
Brain
Tool
Document
Decision
Question
Risk
Gate
Runbook
Manifest
Adapter
DataFolder
ExternalAction
```

### 3.2 Edge types

```yaml
OWNS
READS
WRITES
DEPENDS_ON
BLOCKED_BY
GATED_BY
SUPPORTS
FEEDS
REPORTS_TO
SUPERCEDES
MENTIONS
REQUIRES_VERDICT
CONTAINS_PII
CONTAINS_SECRET_POINTER
```

### 3.3 Example graph edges

```text
Lead-نقاشی --FEEDS--> Accounting
Ziman --FEEDS--> Accounting
Mining --INFORMS--> Accounting
Crypto-eToro --ALERTS--> Accounting
Project-F --FEEDS_SAFE_ALIAS--> Accounting
Accounting --REPORTS_TO--> Architect/_ops
NBB-CP --MAY_GOVERN--> tenants
Architect/_ops --BOSS_OF--> workspace
```

---

## 4. Graph Search Protocol

هر ایجنت قبل از کار باید این سه query را اجرا کند:

### Query A — local context

```text
entity = target project
return: PROJECT/README/MANIFEST/adapter/RUNBOOK/REGISTRY/DecisionLog/OpenQuestions
```

### Query B — dependency context

```text
target project → incoming/outgoing edges depth=2
return: dependencies, blockers, feeds, risks
```

### Query C — gate context

```text
target project → gates + hard-gated actions
return: allowed actions, denied actions, verdicts required
```

---

## 5. Retrieval ranking

برای هر task، context با این وزن انتخاب شود:

| سیگنال | وزن |
|---|---:|
| مسیر مستقیم به entity | 5 |
| manifest/runbook/registry | 4 |
| تصمیم جدیدتر | 4 |
| risk/gate file | 5 |
| dependency depth=1 | 3 |
| dependency depth=2 | 1 |
| historical docs older/conflicting | -1 |
| contains PII/secret | exclude unless local-only |

---

## 6. Step-by-step build plan

### Phase 1 — Memory substrate

- [ ] Create `_memory/graph/`.
- [ ] Create `_memory/agents/`.
- [ ] Create `_memory/execution/`.
- [ ] Seed node list from `REGISTRY-ALIGNMENT.md`.
- [ ] Seed edges from root README + Accounting flow.

### Phase 2 — Cartographer pass

- [ ] Scan top-level folders.
- [ ] For each project, detect README/MANIFEST/adapter/RUNBOOK/REGISTRY.
- [ ] Write `nodes.jsonl` and `edges.jsonl`.
- [ ] Write human report `graph-report.md`.

### Phase 3 — Agent memory pass

- [ ] Create per-agent memory files.
- [ ] Each agent logs role, allowed actions, forbidden actions.
- [ ] Add memory append protocol to each next-agent prompt.

### Phase 4 — Project hardening pass

Order:

1. Accounting
2. Lead-نقاشی
3. Ziman
4. Project-F
5. Mining
6. Crypto-eToro
7. app/NBB-CP
8. 4d_system
9. نقشه اختاپوس

### Phase 5 — Handoff automation

- [ ] Every phase ends with `NEXT_AGENT_PROMPT.md`.
- [ ] Prompt includes current graph status, open verdicts, exact next actions.

---

## 7. Safety choices

### چرا JSONL؟

- append-only
- git-friendly
- easy diff
- safe partial recovery

### چرا graph در کنار Markdown؟

- Markdown برای انسان.
- JSONL برای ایجنت.
- اگر یکی خراب شد، دیگری context را نگه می‌دارد.

### چرا depth=2 search؟

- depth=1 برای dependencies مستقیم.
- depth=2 برای اثرات cross-project مثل Lead → Accounting → Architect.
- depth>2 در این workspace noise زیاد می‌کند.

### چرا Project-F containment؟

- edgeها فقط با alias `Project-F` ساخته می‌شوند.
- هیچ identity/content/platform بیرون از local folder echo نمی‌شود.

---

## 8. Candidate implementation pseudocode

```python
for task in task_queue:
    target = task.entity
    local = graph.search(target, depth=0, types=["Manifest", "Runbook", "Decision", "Question"])
    deps = graph.neighborhood(target, depth=2)
    gates = graph.filter_edges(target, edge_type="GATED_BY")
    context = rank(local + deps + gates)

    if task.action in hard_gated_actions(target):
        write_verdict_request(task)
        append_memory(event_type="question")
        continue

    result = agent.execute(task, context)
    append_memory(event_type="action", evidence_paths=result.paths)
    update_graph(result.new_nodes, result.new_edges)
```

---

## 9. Current recommended next action

ایجنت بعدی باید اول حافظه و گراف را بسازد، نه اینکه مستقیم برود سراغ کدنویسی پروژه‌ها.

اولویت فوری:

```text
Create _memory graph substrate → seed registry graph → scan Accounting → update handoff prompt
```

