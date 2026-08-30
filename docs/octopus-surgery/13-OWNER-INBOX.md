---
documentation_lineage: rescue/octopus-live-tree-20260821
evidence_lineage: surgery/cognition-authority-denylist-20260830-170620
closeout_commit: b394b999b43ab12573ad574f33a5621a57c66686
evidence_commit: 470bb6031f1e51c9a8e6e1f1536c349e22a5200e
docs_branch: docs/octopus-campaign-sync-20260830
docs_base: 0f0e7f5345004284bd1355ff72b7b6ec68595dbd
deployed: false
merged_into_primary_vault: false
published_to_github: false
canonical_vault_status: NOT_SYNCED
---

# Owner inbox

Maximum five READY decisions. Confirmation text is ready to paste.
An agent must not treat silence as yes.

---

## 1. Accept that GitHub publish of this branch is blocked

Status: READY
Decision: keep the campaign local to germline/worktree; do not push the vault branch to public `ofn-node`.
Paste to confirm:

```text
OWNER-CONFIRM: do not push surgery/cognition-authority-denylist-20260830-170620 to public ofn-node
```

---

## 2. Optional designed export

Status: READY
Decision: if ofn-node should receive the surgery, export only the listed `_ops` and `docs/octopus-surgery` files onto a branch that already shares history with `github/main`.
Paste to confirm:

```text
OWNER-CONFIRM: prepare a designed export PR with surgery files only
```

---

## 3. OWNER-09 hermetic full suite — recorded

Status: DONE
Result: `HERMETIC_BOUNDARY_VIOLATION` — 770/827 passed; 57 failed; 1 live skipped.
Residue of 12 tracked state/evidence files was restored. No repairs. No push.
Next: decide canonical local lineage; do not publish.

---

## 4. Keep D1/D7/OWNER_KEY/secret rotation closed

Status: READY
Decision: this campaign did not open those gates and must not be asked to.
Paste to confirm:

```text
OWNER-CONFIRM: D1 D7 OWNER_KEY secret_rotation remain owner-only and closed
```

---

## 5. Accept current distance: 45% ± 7%, not 90%

Status: READY
Decision: credit the five surgeries; do not promote historical Brier or test-count claims.
Paste to confirm:

```text
OWNER-CONFIRM: campaign overall 45% ± 7%; 90% gates remain closed
```
