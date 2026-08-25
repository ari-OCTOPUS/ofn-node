# Wave 1 DLP policy

Policy status: `DEFINED_NOT_EXECUTED`

No provider request passed this policy because the zero-cost provider precondition failed first.

## Exact request allowlist

Only these three request kinds and topics would be eligible:

1. `CONCEPT_CHECK`: difference between observation, belief, and evidence in Active Inference.
2. `HYPOTHESIS_CRITIQUE`: critique one non-sensitive local hypothesis without raw telemetry.
3. `EXPERIMENT_DESIGN`: propose a low-risk falsifiable local experiment for the same hypothesis.

No fourth kind or topic is allowed.

## Required checks before any future send

- Request object must match a closed schema with exact kind/topic identifiers.
- Payload must be minimal concept text and below an explicit byte limit.
- It must contain no database rows, event payloads, episodes, private memory, LAN/IP data, owner information, filesystem paths, credentials, identity-ledger data, private prompts, or execution instructions.
- Secret patterns must be scanned and payload bytes compared against every loaded secret value without recording those values.
- IPv4/IPv6, private paths, token-like values, sensitive UUIDs, owner data, and forbidden topic terms must block the request.
- A receipt may retain only request kind, byte count, payload hash, redaction count, decision, and timestamp.
- Uncertainty must resolve to `REQUEST_BLOCKED_DLP=true`.

## Response checks

- Maximum response bytes must be explicit and enforced while reading.
- Redirects, unexpected hosts, tools/functions, streaming actions, shell/action requests, and executable content must be rejected.
- Stored output must be bounded, redacted, labeled `LEARNED_FROM_MODEL`, and carry provider ID, timestamp, response hash, and local-validation result.
- No model output may change preferences, safety rules, identity, owner policy, or executable state.

## Current result

- Requests evaluated by DLP: `0`
- Requests blocked by DLP: `0`
- Secrets exposed: `0`
- Private data exposed: `0`

The gate stopped at provider/cost preflight before payload construction.
