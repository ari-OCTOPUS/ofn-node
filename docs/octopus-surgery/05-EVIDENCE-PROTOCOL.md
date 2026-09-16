# Evidence protocol — draft

Policy envelope: `node_id=octopus-continuity-180`,
`asserted_ip=192.168.0.180`, `vantage=cursor-this-host-only`,
`scope=this_host_only`, `claim_type=policy`, evidence: repository invariants and this audit.

## Canonical cycle

```text
observe → hypothesize → predict → low-risk test → result → receipt → verify → update
```

Canonical report wording:

```text
Hypothesis H with confidence C predicted P.
Test T returned R.
R is consistent / inconsistent / indeterminate with H.
receipt=<schema/id/path/hash>.
```

The system must not substitute “I understood” for a measured update.

## Required claim envelope

```yaml
node_id:
asserted_ip:
vantage:
scope: this_host_only | explicitly_bounded_scope
claim_type: observation | inference | hypothesis | prediction | test_result | policy
evidence:
command:
commit_sha:
observed_at_utc:
limitations: []
alternative_explanations: []
```

System-wide promotion requires independent evidence from at least two node IDs. A missing LAN
listener is not evidence that a loopback API is absent. A body not found on this host is
`body_not_on_this_host`, not `body_missing`.

## Status vocabulary

- `VERIFIED`: directly reproduced at the recorded commit and scope.
- `PARTIAL`: only part of the claim is reproduced.
- `CONTRADICTED`: reproduced evidence conflicts with the claim.
- `NOT_FOUND`: not found in the searched commit/path; not an existence claim.
- `BLOCKED`: access, safety or owner decision prevents the probe.
- `STALE`: evidence describes another time, commit or repository.

## Receipt requirements

A test receipt records command, working directory, branch, commit, Python version, UTC interval,
exit code, collected/passed/failed/skipped counts, output SHA-256 and safety environment.

An action receipt additionally records:

- exact request and policy classification;
- approval reference and binding hash;
- pre/post state hashes;
- external effects and cost;
- rollback command and rollback verification;
- independent verifier result.

`EXECUTED` without a durable receipt must be downgraded to `FAILED` or `UNKNOWN_EFFECT`.

## Independent verification

A verifier is independent only if it uses at least one of:

- an oracle/specification not imported from the implementation;
- a frozen fixture captured before the implementation result;
- an independent calculation/dependency;
- a property/invariant;
- a mutation or adversarial test that demonstrably detects a planted fault.

Copying expected values, formulas or prediction objects from the implementation is
self-verification and cannot yield `VERIFIED`.

## Safety

- Raw private material is never read, copied or hashed by the agent.
- Logs redact hostnames and omit unnecessary IPs.
- Tests use temporary state and no external network.
- Full-suite claims are blocked when the official runner intentionally performs a live request
  or writes a capability/runtime marker.
