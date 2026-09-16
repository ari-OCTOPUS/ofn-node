# BRIDGE-CONTRACT — پل پاهای پول به مغز اختاپوس (P4)

> تاریخ: ۲۰۲۶-۰۸-۱۱ · وضعیت: سند (propose-only، بدون arm/live)

## اصل

پاهای پول (لید/CRM، Mining، Project-F، …) اختاپوس را به‌عنوان **مغز + دروازه** صدا می‌زنند.
پول داخل هسته قاطی نمی‌شود. هر پا = client جدا با capability allowlist خودش.

## API واقعی (از کد، نه خیالی)

### ۱. مغز: `model_router.ask()`

```python
from cortex.model_router import ask
result = ask(task="classify", prompt="...", system="...", max_tokens=128, tier="local")
# → {"ok": True, "text": "...", "tier": "local", "model": "qwen2.5:1.5b", "cost_usd": 0.0}
```

مسیر: `cortex/model_router.py:528`

### ۲. بستهٔ context: `ContextBundle.create()`

```python
from context_bundle import ContextBundle
bundle = ContextBundle.create(
    mission_id="m1", task_id="t1", trace_id="tr1",
    tenant_id="leg", project_id="lead", agent_role="leg_agent",
    phase="verify", objective="...", ttl_s=600)
errors = bundle.validate()
```

مسیر: `context_bundle.py:58` · schema: `octopus-context-bundle.v1`

### ۳. قرارداد کنترل: `authorization()`

```python
from control_contracts import ActionProposal, ApprovalDecision, authorization
result = authorization(proposal, decision)
# → {"allow": True/False, "reason": "...", "action_sha256": "..."}
```

مسیر: `control_contracts.py:163` · schema: `octopus-control.v2`

### ۴. دروازه‌های ایمنی (همه پاها باید عبور کنند)

| گیت | مسیر | تأثیر |
|---|---|---|
| kill_seam | `opslib.py:STOP_ORGANISM` | اگر file exists → deny همه |
| organ_gate | `organ_gate.py:reserve/settle` | سقف ماهانه per-organ |
| budget_gate | `budget_gate.py` | سقف روزانه + خط فاجعه |
| circuit_breaker | `circuit_breaker.py:check` | per-provider state machine |
| fugu_quota | `fugu_quota.py:reserve` | daily cap + fail ceiling |

هیچ پا حق دور زدن این گیت‌ها را ندارد.

## جدول effects برای هر پا

| پا | effects allowed | needs approval | forbidden |
|---|---|---|---|
| **Lead-نقاشی** | read state, propose lead, request info | send email, create invoice, outbound HTTPS | auto-send, money transfer |
| **Mining** | read metrics, snapshot | trade, wallet access, send | auto-trade |
| **Project-F** | read studio state, propose draft | publish, send DM, outbound | ToS violation, geo-block bypass |
| **Accounting** | read workbook names/mtimes | reconcile, write ledger | PII leak, auto-payment |

## Pilot پیشنهادی: Lead-نقاشی

**چرا:** ساده‌ترین پل است — فقط read + propose، کمترین ریسک.

**Dry-run plan:**
۱. Lead leg از `model_router.ask(task="classify")` برای دسته‌بندی لید استفاده می‌کند
۲. نتیجه از `ContextBundle` عبور می‌کند (typed handoff)
۳. هر action از `authorization()` می‌گذرد (propose-only)
۴. تأیید مالک از `approval_store` می‌آید
۵. اجرای واقعی از `outbound_https.execute_if_approved` (با approval port)

**هیچ اثر واقعی در dry-run:** همه mock/fixture، صفر network.

## قواعد سخت

۱. هر پا = capability-manifest.json جدا
۲. پول/ارسال/برداشت = همیشه از ApprovalPort / control_contracts
۳. پیش‌فرض: propose-only از پا → تأیید مالک → execute
۴. ContextBundle typed برای handoff؛ schema غلط = reject
۵. هیچ پا حق دور زدن organ_gate / breaker / kill را ندارد
۶. Project-F: Hard Rules منشور نقض نشود

## تست bridge

```text
تزریق از یادداشت لید → context_fence → alert (not execute)
tool payload مخرب → policy_oracle → forbidden-action-executed
approval replay → approval_store → single-use atomic → False
action hash mismatch → control_contracts → action-changed-after-approval
```

همه از test_ti_redteam_injection.py پوشش داده شده (RT01–RT25).
