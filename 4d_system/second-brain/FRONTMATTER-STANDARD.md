# Frontmatter standard (every note in the vault)

Spec §7. Every note any brain creates or normalizes carries this YAML frontmatter.
It is what makes routing, risk, provenance, and B6 policy decisions machine-checkable.

```yaml
---
id: note_...
type: inbox_item | project | knowledge | person | asset | architecture | run | approval | decision
brain_owner: B1 | B2 | B3 | B4 | B5 | B6 | B7 | B8 | SUPERBRAIN
status: raw | normalized | active | waiting | done | archived | canonical_candidate | canonical
risk_level: low | medium | high | critical
sensitivity: public | internal | confidential | restricted
source:
  kind: human | telegram | file | image | model | api | vault
  ref: ""
confidence: 0.0        # 0.0–1.0; unverified stays low
created_at: 2026-07-11
updated_at: 2026-07-11
links:
  projects: []
  people: []
  knowledge: []
  assets: []
  decisions: []
policy:
  requires_approval: false
  approval_id:
---
```

## Field notes (safety-relevant)

- **`sensitivity: restricted`** — `09 - People`, `Crypto - etoro`, `10 - Telegram`,
  Accounting. Reads are opt-in per folder; any action on these is owner-gated.
- **`status`** never jumps straight to `canonical`. It must climb the memory ladder
  `raw → episodic → semantic → canonical_candidate → (approval) → canonical` (spec §15);
  only an approved verdict promotes to `canonical`.
- **`confidence`** — knowledge notes without evidence stay low; B7 labels
  confirmed / likely / speculative / unverified.
- **`policy.requires_approval: true`** — the note describes a gated action; it becomes
  an `ActionProposal` through B6 and cannot execute without a human verdict.
