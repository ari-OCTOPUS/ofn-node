# 🔎 GRAPH-SEARCH-PROTOCOL — پروتکل اجباری قبل از هر کار ایجنت

> هدف: هیچ ایجنتی بدون context، risk، و verdict کار نکند.

---

## 1. ورودی task

هر task باید این‌ها را داشته باشد:

```yaml
target_entity: Accounting | LeadPainting | Ziman | ProjectF | Mining | CryptoEtoro | NBB_CP | FourD | VaultScanner
action_type: read | report | draft | edit-doc | code | run | external
intent:
allowed_write_paths:
```

---

## 2. Graph search اجباری

برای target:

```text
A. Local node → path
B. Incoming/outgoing edges depth=2
C. GATED_BY edges
D. REQUIRES_VERDICT edges
E. OWNS edges → Manifest/Runbook/Registry/Adapter/Questions
```

---

## 3. Context ranking

| context | وزن |
|---|---:|
| RUNBOOK / REGISTRY / MANIFEST | 5 |
| GATED_BY / RISK | 5 |
| VERDICT_QUEUE | 5 |
| PROJECT / README | 4 |
| DecisionLog / OpenQuestions | 4 |
| depth-1 dependency | 3 |
| depth-2 dependency | 1 |
| old conflicting docs | -2 |
| PII/secret | exclude |

---

## 4. Action gate

```text
if action_type in [external, run, code, publish, send, spend, trade, lodge, pay, create-account]:
    require verdict
    write question
    stop
else:
    proceed if within allowed_write_paths
```

---

## 5. Memory append بعد از کار

بعد از هر کار، یک JSON line در:

```text
_memory/execution/runs.jsonl
```

با schema:

```json
{"ts":"ISO8601","agent":"name","event_type":"observation|action|question|handoff","entity":"id","summary":"safe summary","evidence_paths":["..."],"risk":"low|medium|high|critical","requires_verdict":false,"pii_safe":true,"secret_safe":true}
```

---

## 6. Recency / conflict rule

تصمیم جدیدتر بر قدیمی‌تر ارجح است، اما تاریخ حذف نمی‌شود.

اگر تناقض پیدا شد:

1. خط/فایل قدیمی حذف نشود.
2. event جدید با `event_type: decision` ثبت شود.
3. edge `SUPERSEDES` بین سند جدید و قدیمی اضافه شود.
4. در گزارش انسانی بنویس: `old doc retained for history`.

---

## 7. Containment rule

برای `ProjectF`:

- در root graph فقط alias.
- هیچ identity/platform/media/content بیرون از local folder.
- edge type ترجیحی: `FEEDS_SAFE_ALIAS`.
