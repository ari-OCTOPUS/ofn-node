# 💰 Accounting REGISTRY

> Entity registry for Architect/_ops alignment. No PII/secret.

```yaml
entity_id: Accounting
name: Accounting
kind: tenant
owner: Ari
status: active
risk_level: high
risk_tier: R3
autonomy_floor: read-only / draft-only
role_in_ecosystem: FINANCIAL_HEART
control_contract: MANIFEST.yaml
adapter: contracts/adapter.yaml
runbook: RUNBOOK.md
public_alias: Accounting
pii_policy: financial PII stays local; tokenise before inference
boss_alignment: Architect/_ops compatible
security_gate: lifted-2026-07-06-but-financial-hard-gates-remain
```

---

## Interfaces

| interface | mode | implementation status |
|---|---|---|
| status | read | designed |
| report | read/draft | designed |
| compliance_scan | read/draft | designed |
| audit | read | designed |
| csv_import | draft-only | not built |
| receipt_ocr | draft-only | not built |

---

## Hard-gated actions

- lodge to ATO/ASIC
- move/pay money
- final ledger posting
- changing tax rule from `[Unverified]` to confirmed
- transmitting PII to LLM
- connecting bank/Xero APIs

---

## Required owner inputs

| field | status |
|---|---|
| registered tax agent | open |
| business structure | open |
| ABN status | open |
| GST status | open |
| accounting software | open |
| separate bank account | open |
| BAS cycle confirmation | open |
| worker/contractor status | open |

---

## Upstream touchpoints

| source | event | handling |
|---|---|---|
| Lead-Painting | invoice/payment | draft business income |
| Mining | coin received | draft income at AUD receipt value |
| Crypto-eToro | trade closed | draft CGT/personal note |
| Project-F | platform credit | draft A-share labelled `Project-F` |
| Ziman | sale | draft income + COGS |

---

## Current registry verdict

```text
Accounting is visible and contract-complete, but execution is intentionally zero until accountant + structure decisions are resolved.
```
