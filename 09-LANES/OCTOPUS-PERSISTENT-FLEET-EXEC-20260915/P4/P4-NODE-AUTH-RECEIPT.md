# P4-NODE-AUTH-RECEIPT

**VERDICT:** PASS
**stamp_utc:** 2026-09-15T03:44:56Z
**method:** mesh_ssh ?? **fingerprint:** `SHA256:vuyFXOS/CAXrxWbXlQSgq9eDB+MklKq1KkGJW4435as`

## Per-node

| node | auth_status | bind_role | mesh_fp | batchmode+strict | neg_reject |
|---|---|---|---|---|---|
| 100 | OK | knowledge_retrieve | `SHA256:vuyFXOS/CAXrxWbXlQSgq9eDB+MklKq1KkGJW4435as` | True | True |
| 160 | OK | knowledge_prep | `SHA256:vuyFXOS/CAXrxWbXlQSgq9eDB+MklKq1KkGJW4435as` | True | True |
| 193 | OK | model_infer | `SHA256:vuyFXOS/CAXrxWbXlQSgq9eDB+MklKq1KkGJW4435as` | True | True |
| 114 | OK | eval_batch | `SHA256:vuyFXOS/CAXrxWbXlQSgq9eDB+MklKq1KkGJW4435as` | True | True |

## Lease tests

```json
{
  "lease_ok_100": {
    "pass": true,
    "state": "LEASED"
  },
  "lease_deny_unregistered": {
    "pass": true,
    "error": "REJECTED: LEASE DENY auth_status=UNREGISTERED for node_id=999 (need OK)"
  },
  "auth_status_100": "OK",
  "auth_status_180": "OK"
}
```

STOP before P5 ?? HOLD customer_send ?? may_authorize false ?? 138 sole commander
