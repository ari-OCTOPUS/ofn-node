# Prompt for Next Agent — Cartographer + Memory Graph Enrichment

تو ایجنت بعدی در workspace زیر هستی:

```text
C:\Users\Armin\Desktop\پازل هشت پا
```

## مأموریت

سیستم چندایجنتی را حافظه‌دار کن و گراف سرچ را از seed فعلی به اسکن واقعی کل workspace ارتقا بده.

## اول این فایل‌ها را بخوان

```text
ARCHITECT-ORGANISM-CONTEXT.md
MULTI-AGENT-MEMORY-GRAPH-DESIGN.md
REGISTRY-ALIGNMENT.md
RISK-LADDER.md
VERDICT_QUEUE.md
_memory/graph/index.md
_memory/graph/nodes.jsonl
_memory/graph/edges.jsonl
_memory/agents/orchestrator.md
_memory/agents/cartographer.md
```

## کار مرحله‌ای

### Step 1 — Full inventory

- `03 - Projects` را لیست کن.
- `app`, `4d_system`, `نقشه اختاپوس` را هم به‌عنوان brain/tool scan کن.
- برای هر entity این فایل‌ها را پیدا کن:

```text
README.md
PROJECT.md
MANIFEST.yaml / MANIFEST.json
contracts/adapter.yaml
RUNBOOK.md
REGISTRY.md
VERDICT_QUEUE.md
DecisionLog.md
OpenQuestions.md
```

### Step 2 — Graph enrichment

به‌صورت append-only در این‌ها اضافه کن:

```text
_memory/graph/nodes.jsonl
_memory/graph/edges.jsonl
```

Node types:

```text
Project, Brain, Tool, Document, Decision, Question, Risk, Gate, Runbook, Manifest, Adapter, DataFolder
```

Edge types:

```text
OWNS, READS, WRITES, DEPENDS_ON, BLOCKED_BY, GATED_BY, SUPPORTS, FEEDS, REPORTS_TO, REQUIRES_VERDICT
```

### Step 3 — Report

`_memory/graph/graph-report.md` را آپدیت کن با:

- تعداد پروژه‌ها
- missing files per project
- high-risk edges
- next build order
- drift notes

### Step 4 — Accounting continuation

بعد از گراف، برگرد به Accounting و این‌ها را sync کن:

```text
03 - Projects/Accounting/OpenQuestions.md
03 - Projects/Accounting/DecisionLog.md
03 - Projects/Accounting/REGISTRY.md
03 - Projects/Accounting/RUNBOOK.md
```

اما فقط بعد از اینکه از مالک جواب verdictهای Accounting را گرفتی.

## Hard rules

- هیچ secret/API key/seed نخوان، ننویس، نخواه.
- PII را خلاصه/ماسک کن.
- Project-F را فقط با alias `ProjectF` یا `Project-F` بیرون از پوشه‌اش ذکر کن.
- هیچ اکشن بیرونی انجام نده.
- هیچ publish/send/spend/trade/lodge/pay/create-account نکن.
- فقط فایل‌های memory/report/registry/runbook/docs را ویرایش کن.

## Expected final answer to owner

در پایان بگو:

1. چند node/edge اضافه شد.
2. چه فایل‌هایی missing هستند.
3. قدم بعدی دقیق چیست.
4. از مالک چه verdictهایی لازم است.

