# Studio Architecture

Instagram and Google Business Profile are treated as active business assets but not active publishing connectors. The safe rollout is: read-only inventory -> brand profile draft -> asset vault consent/redaction -> content drafts -> owner approval -> dry-run publish receipt -> live publish only after explicit flags.

Publication gate: owner_release, active token, asset consent, policy pass, safe caption, idempotency key, rate limit, audit event. Block on visible address/plate/unknown person/unverified claim/unresolved complaint/token failure/kill switch.
