# T73 — cognition inbox (not telegram)

Path: `_ops/state/cognition_inbox/` (append-only `events.jsonl` + `receipts.json`).

```text
cognition_inbox/ (append-only)
  ← organ events (knowledge burst, …)
  ← owner decisions: not written here (A/B lane; we only read if present)
  → cortex advisory
  → business_brain advisory
  → metacontrol synthesis
```

Receipt shape:

```yaml
brain: cortex|business_brain|metacontrol
heard: true|false
input_ids: []
output_kind: advisory
evidence_ids: []
executable: false
```

Missing brain file → `BRAIN_DEGRADED`, not crash.

This session: cortex-state.json and business-brain-latest.json both present → `heard: true` ×3. Live processes were **not** restarted; receipts are from read of their latest files plus sidecar advisory.
