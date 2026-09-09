---
status: open
requires: owner_decision
topic: painting-public-lead-form-o9-exception
---

# Public painting enquiry is store-only (Prompt B2)

Implemented because the owner prompt named painting A/A2 as a blocker:
anonymous POST `/api/v1/public/painting/leads` on the **lead host only**
writes `painting_leads` and returns `outbound=0`, `baseline_action=0`.

Not decided here (still owner):

- Whether the live tunnel should advertise `/enquire` on the public lead
  hostname.
- Studio consent → map / ofn-marketing (left closed).
- Any later outbound from these rows (still the existing outbox + owner
  gate ladder).

O9 catalog / store / checkout remain flag-gated and default-off.

Push of `cursor/painting-public-lead-form-01b4` was denied by the
HOLD_EXTERNAL egress hook in this session (retried). Local tip
`db68a2a`. Owner or a later authorized publish path must push and
open the PR. ManagePullRequest cannot create until the remote has
the commits.
