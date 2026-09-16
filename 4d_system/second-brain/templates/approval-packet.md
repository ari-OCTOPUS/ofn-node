---
id: approval_...
type: approval
brain_owner: SUPERBRAIN
status: waiting
risk_level: high        # low | medium | high | critical
sensitivity: internal
source: { kind: model, ref: "" }
confidence: 0.0
created_at: 2026-07-11
updated_at: 2026-07-11
policy:
  requires_approval: true
  approval_id: approval_...
---

# Approval Packet — <one-line action summary>

> The reviewer decides in seconds from this packet (2026 HITL "evidence pack").
> Maps to B6: an `ActionProposal` with `EvidencePack` + `approval_ttl_epochs`.

- **Proposing brain:** B?  ·  **Action class:** external_communication | financial | content_publish | architecture_mutation | code_execution | vault_mass_update | memory_promote | private_data_export
- **Plain-language action:** …
- **Reasoning:** …
- **Estimated impact:** … (`expected_value_cents` if financial)
- **Reversibility:** reversible | irreversible | unknown
- **Rollback:** how to undo it
- **Alternatives weighed:** …
- **Evidence:** link(s) to `evidence-card` / trace
- **Approval TTL:** valid for N epochs from the verdict; stale after that (fresh verdict required)
- **Required role:** owner | domain_expert

## Verdict (human only)
- [ ] approve   - [ ] approve-with-edits   - [ ] deny
- **by:** …  **at (epoch):** …  **note:** …
