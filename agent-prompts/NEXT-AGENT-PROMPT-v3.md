# NEXT AGENT PROMPT v3 — اجرای مرحله بعد با حافظه + Graph Search

> Workspace:
>
> ```text
> C:\Users\Armin\Desktop\پازل هشت پا
> ```

## 0. نقش تو

تو ایجنت بعدی هستی. سیستم حالا حافظه‌دار و گراف‌دار شده. قبل از هر کار باید graph search بزنی، context را بخوانی، ریسک/گیت را چک کنی، بعد فقط کار مجاز را انجام بدهی.

---

## 1. اول این فایل‌ها را بخوان

```text
ARCHITECT-ORGANISM-CONTEXT.md
RISK-LADDER.md
VERDICT_QUEUE.md
REGISTRY-ALIGNMENT.md
MULTI-AGENT-MEMORY-GRAPH-DESIGN.md
_memory/graph/SCHEMA.md
_memory/protocols/GRAPH-SEARCH-PROTOCOL.md
_memory/graph/graph-report.md
_memory/graph/nodes.jsonl
_memory/graph/edges.jsonl
_memory/execution/runs.jsonl
_memory/execution/open-loops.md
```

بعد agent memory مربوط به کارت را بخوان:

```text
_memory/agents/orchestrator.md
_memory/agents/risk-governor.md
_memory/agents/accounting-steward.md
_memory/agents/revenue-steward.md
_memory/agents/privacy-steward.md
_memory/agents/sensing-sentinel.md
_memory/agents/brain-integrator.md
_memory/agents/handoff-writer.md
```

---

## 2. وضعیت فعلی

این pass انجام شده:

- `_memory/graph` ساخته و schema دارد.
- graph search protocol ساخته شده.
- برای همهٔ tenantها/brainها/toolها `RUNBOOK.md`, `REGISTRY.md`, `VERDICT_QUEUE.md` ساخته شده.
- agent memory برای ۹ نقش ساخته شده.
- گراف تا حدود ۷۴ node و ۸۹ edge غنی شده.

---

## 3. قانون قبل از هر action

برای target entity این‌ها را انجام بده:

```text
1. Load target node from nodes.jsonl.
2. Load all incoming/outgoing edges depth=2.
3. Load OWNS docs: Manifest/Runbook/Registry/Verdict/Questions.
4. Load GATED_BY and REQUIRES_VERDICT edges.
5. If action is hard-gated, do NOT execute. Write verdict request and stop that branch.
6. Append safe memory event to _memory/execution/runs.jsonl.
```

Hard-gated actions:

```text
publish / send / spend / trade / lodge / pay / create-account / deploy / run daemon / start mining / exchange API / wallet access / PII-to-LLM
```

---

## 4. کار مرحله بعد — Accounting first

هدف بعدی: Accounting را از حالت docs-ready به owner-input-ready ببری.

### 4.1 Graph search target

Target:

```text
Accounting
```

Required files:

```text
03 - Projects/Accounting/RUNBOOK.md
03 - Projects/Accounting/REGISTRY.md
03 - Projects/Accounting/VERDICT_QUEUE.md
03 - Projects/Accounting/MANIFEST.yaml
03 - Projects/Accounting/OpenQuestions.md
03 - Projects/Accounting/DecisionLog.md
```

### 4.2 اگر مالک جواب داده بود

اگر در پیام مالک جواب این‌ها بود:

```text
ACC-V1 Tax Agent
ACC-V2 business structure
ACC-V3 ABN
ACC-V4 GST
ACC-V5 separate bank
ACC-V6 software
ACC-V8 pilot 10 receipts
ACC-V9 ANZ CSV importer skeleton
```

آن‌ها را بدون PII به Accounting docs sync کن:

- `OpenQuestions.md` را update کن.
- `DecisionLog.md` را append کن.
- `REGISTRY.md` وضعیت fields را update کن.
- `RUNBOOK.md` next actions را update کن.

### 4.3 اگر مالک جواب نداده بود

منتظر نمان. فقط این خروجی را بده:

- دقیقاً بگو چه verdictهایی لازم است.
- بگو تا جواب نیاید چه کارهای بی‌خطر می‌شود کرد.
- برو سراغ Lead-Painting prep فقط docs-only.

---

## 5. کار unblocked اگر Accounting منتظر جواب بود

اگر Accounting بلاک بود، این کارها مجازند:

1. Lead-Painting: `OpenQuestions.md` را با verdict IDs جدید sync کن.
2. Ziman: `OpenQuestions.md` را با capacity/hero/channel sync کن.
3. Root `VERDICT_QUEUE.md` را با local verdict queueها cross-link کن.
4. `_memory/graph/graph-report.md` را با هر تغییر update کن.

بدون publish/send/spend.

---

## 6. Project-F containment

اگر به Project-F رسیدی:

- بیرون از پوشه فقط `Project-F`.
- هیچ نام شخص/پلتفرم/محتوا/مدیا در root graph یا پاسخ نیاور.
- فقط status/gate/branch/research-draft به‌شکل content-free.

---

## 7. پایان کارت

در پایان حتماً:

1. بگو چه فایل‌هایی عوض شد.
2. تعداد node/edge اگر تغییر کرد بگو.
3. Memory event append کن.
4. `agent-prompts/NEXT-AGENT-PROMPT-v4.md` بنویس.
5. از مالک فقط حداقل verdictهای لازم را بپرس.

---

## 8. جواب نهایی به مالک باید کوتاه و اجرایی باشد

ساختار جواب:

```text
انجام شد:
- ...

گراف/حافظه:
- ...

قدم بعد:
- ...

از تو لازم دارم:
- ...
```
