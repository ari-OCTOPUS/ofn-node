# SECURITY-TEST-REVIEW.md

> agent F-E (read-only recon). Writer must verify before acting.

## summary
Both owner findings CONFIRMED against source. L-06: test_stop_contract.py::t_c_stop_probe_global_halt (line 52) references opslib.STOP via getattr(opslib,"STOP",None) — a nonexistent attribute; the real architect kill-switch is opslib.STOP_ARCHITECT (budget/opslib.py:52, checked by master_halted() at opslib.py:291). Consequences: the captured var `ost` is always None and never restored, the architect-STOP branch of global_halt() is never patched or exercised, and the "clean→proceed" assert (line 57) silently reads the LIVE F:\...\04 - Architect System\STOP path (passes only because that live file is absent) — a hermeticity leak and a coverage hole. The sibling test_master_halt.py:36 does it correctly by patching opslib.STOP_ARCHITECT, proving the intended attribute. L-08: memory/gate.py:_grade escalates trust to GRADED purely on the claimant-controlled boolean candidate["external_graded"] for both self_knowledge (gate.py:120-123, committer advisory_until_graded) and self_claim (gate.py:124-125, committer external_grade). No independent grader receipt, provenance, or signature is verified anywhere — a tree-wide grep shows external_graded is only ever READ from the candidate dict, never produced/validated by a grader. The docstring (gate.py:11-12) promises "escalation to GRADED only with external grade" but the code accepts the submitter's own assertion. test_memory_gate.py::t_b (lines 76-79) PINS this vulnerable behavior as correct — its own comment admits the claim can be false ("دروغین") yet asserts trust==GRADED, a green-lie that cements the escalation and would break if the code were fixed. The other in-scope security tests (human_append_guard, S1-04 cockpit stop guard, effector_gate_bridge, effector_idempotency, capability_gate, approval_queue_consistency, chrono_langar, master_halt) are solid: they assert real state (byte-identical files, HMAC verification, hash-chain verify, real gate status), not mock-was-called.

## findings
- **[high]** CONFIRM L-06: test_stop_contract.py::t_c_stop_probe_global_halt references opslib.STOP (nonexistent) instead of opslib.STOP_ARCHITECT; captures a dead var, never patches the real architect kill-switch, never exercises its global_halt branch, and leaks the 'clean→proceed' assert onto the live F:\...\04 - Architect System\STOP path.  
  evidence: `_ops/tests/test_stop_contract.py:52`  
  fix: Replace getattr(opslib,"STOP",None) with opslib.STOP_ARCHITECT; monkeypatch opslib.STOP_ARCHITECT = d/"STOP-ARCHITECT" in setup and restore it in finally (mirror test_master_halt.py:36); add an assertion that global_halt()[0] is True when STOP_ARCHITECT exists, so the architect-STOP → global_halt path is actually pinned. This preserves intent (prove supervisors honor architect STOP) while removing the hermeticity leak and dead code.
- **[medium]** opslib exposes STOP_ARCHITECT (architect/root kill-switch) and has NO attribute named STOP; master_halted() checks HALT_ALL then STOP_ARCHITECT — so the test's getattr default silently yields None and the STOP_ARCHITECT branch is never isolated.  
  evidence: `_ops/budget/opslib.py:52`  
  fix: Confirms L-06 root cause: the test names the wrong attribute. master_halted() at opslib.py:291 reads STOP_ARCHITECT.exists() — the very path the test fails to redirect to temp.
- **[critical]** CONFIRM L-08: memory/gate.py._grade escalates self_knowledge to GRADED whenever candidate['external_graded'] is True — a claimant-controlled boolean in the submitted dict, with no independent grader receipt, provenance check, or signature.  
  evidence: `_ops/memory/gate.py:121`  
  fix: Require a verifiable external-grade artifact (e.g. a signed grader receipt id + hash validated against an independent grader store) before returning GRADED; do not trust a raw boolean from the candidate. The docstring at gate.py:11-12 already states the intended contract ('escalation to GRADED only with external grade') — the code must enforce it.
- **[critical]** L-08 also affects self_claim namespace: committer 'external_grade' returns GRADED on the same unauthenticated candidate['external_graded'] flag; a tree-wide grep shows external_graded is only ever READ (gate.py:121,125), never produced or validated by any grader in production code.  
  evidence: `_ops/memory/gate.py:125`  
  fix: Same fix applies to the external_grade committer. self_claim has zero test coverage in test_memory_gate.py (t_b only exercises self_knowledge), so the escalation path is both unverified and untested.
- **[high]** Green-lie / stale characterization: test_memory_gate.py::t_b pins the L-08 vulnerable behavior as correct — it submits source='llm:think' with external_graded=True and asserts trust=='GRADED', and its own comment admits the claim is false/without-source ('دروغین بدونِ منبع'). This cements the escalation and would break if gate.py were fixed.  
  evidence: `_ops/tests/test_memory_gate.py:77`  
  fix: Rewrite t_b to assert the SECURE contract: a bare external_graded=True from a non-grader source must NOT reach GRADED (expect ADVISORY, or reject). Add a positive case that supplies a valid independent grader receipt and asserts GRADED only then. Add a self_claim analogue. Preserve the existing self_knowledge=ADVISORY and never-OWNER_CONFIRMED-from-llm assertions (lines 75,81) which are correct.
- **[low]** Coverage/robustness note (not a green-lie): t_c in test_stop_contract.py exercises only HALT_ALL and STOP_ORGANISM via stop_probe; the architect-STOP contribution to master_halted/global_halt is asserted only in the sibling test_master_halt.py. Fixing L-06 closes this gap within the stop-contract suite itself.  
  evidence: `_ops/tests/test_stop_contract.py:57`  
  fix: After the L-06 fix, t_c should assert global_halt()[0] is True under an isolated STOP_ARCHITECT, giving the stop-contract suite self-contained coverage of the architect kill path.

## artifact
## F-E Security/Authority Test Review — Findings

### Owner-finding verdicts

| ID | Verdict | Exact code path | Nature |
|----|---------|-----------------|--------|
| **L-06** | **CONFIRMED** | `_ops/tests/test_stop_contract.py:52` uses `getattr(opslib, "STOP", None)`; real attr is `opslib.STOP_ARCHITECT` (`_ops/budget/opslib.py:52`, read by `master_halted()` at `opslib.py:291`) | Stale/wrong-path + hermeticity leak + dead var |
| **L-08** | **CONFIRMED** | `_ops/memory/gate.py:121` (self_knowledge, `advisory_until_graded`) and `_ops/memory/gate.py:124-125` (self_claim, `external_grade`) | Claimant-controlled trust escalation |

### L-06 detail
`t_c_stop_probe_global_halt` captures `ost = getattr(opslib, "STOP", None)` → always `None` (opslib has no `STOP`, only `STOP_ARCHITECT`). It patches only `HALT_ALL` and `STOP_ORGANISM` (lines 53-54) and restores only those (lines 68-69), so:
- `ost` is dead — captured, never used, never restored.
- `opslib.STOP_ARCHITECT` is never redirected to temp; the `assert stop_probe.global_halt()[0] is False` at line 57 reads the **live** `F:\...\04 - Architect System\STOP` and passes only because that file is absent (leaky, order-dependent).
- The architect-STOP → `global_halt()` branch is never exercised in this suite.
- The correct idiom is right next door: `test_master_halt.py:36` patches `opslib.STOP_ARCHITECT`.

### L-08 detail
`gate.py._grade` returns `("GRADED","commit")` whenever `candidate.get("external_graded") is True` — for both self_knowledge (line 121) and self_claim (line 125). The flag is a raw boolean in the submitted dict; a submitter with `source="llm:think"` sets it and reaches GRADED. Tree-wide grep confirms `external_graded` is **only ever read** (gate.py:121,125) and taxonomy.py:77 — never produced or validated by any independent grader. The docstring (gate.py:11-12) promises "escalation to GRADED only with external grade" but the code trusts the claimant's own assertion. No grader receipt, provenance, or signature is checked.

### Tests that MUST be fixed (preserve intent, remove green-lie)

1. **`test_memory_gate.py::t_b_self_knowledge_always_advisory` (lines 77-79)** — GREEN-LIE. Asserts `external_graded=True` from `llm:think` → `trust=="GRADED"` and its comment (line 76) admits the claim is false. Rewrite to assert a bare `external_graded` flag does NOT escalate (expect ADVISORY/reject); add a positive case requiring a valid grader receipt; add a self_claim analogue. Keep the correct self_knowledge=ADVISORY / never-OWNER_CONFIRMED-from-llm asserts (lines 75,81).

2. **`test_stop_contract.py::t_c_stop_probe_global_halt` (lines 49-69)** — wrong-path + leak. Use `opslib.STOP_ARCHITECT`, monkeypatch and restore it (mirror `test_master_halt.py:36`), and add `assert stop_probe.global_halt()[0] is True` under isolated STOP_ARCHITECT to actually pin the architect kill path.

### Tests reviewed and judged SOLID (assert real state, not mock-was-called)
- `test_human_append_guard.py` — real HMAC mint/verify, replay/tamper/expiry/fail-closed against real reason codes.
- `S1-04_test_cockpit_stop_guard.py` — byte-identical owner-STOP file survival, real `do_action` state, structural launcher invariants.
- `test_effector_gate_bridge.py` — real gate status, real events file, adversarial staleness/first-write-wins/fail-closed.
- `test_effector_idempotency.py` — real exactly-once on idempotency_key, real settle path.
- `test_capability_gate.py` — real three-condition gate + stale-fingerprint revoke.
- `test_approval_queue_consistency.py` — real EffectorGate; attacker manual-mutation defeated by reconcile.
- `test_master_halt.py` — correct STOP_ARCHITECT isolation; ordering + fail-loud.
- `test_chrono_langar.py` — real hash-chain verify, tamper/age-reversal/beat-jump = logical death.
