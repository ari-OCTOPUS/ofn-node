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

## 2. Review PR 6 at its exact head SHA after focused CI

Status: READY after the reconciliation push and green observation-contract checks
Decision: inspect CI on the current head; do not merge, deploy, open D7, or rotate secrets.
The exact SHA is written in the PR body after push. Do not approve an older SHA.

```text
OWNER-CONFIRM: reviewed PR 6 at <full SHA from PR body>; merge remains unauthorized
```

---

## 3. OWNER-09 hermetic full suite — recorded

Status: DONE
Result: `HERMETIC_BOUNDARY_VIOLATION` — 770/827 passed; 57 failed; 1 live skipped; 1459s.
Scoring campaign regression repaired at `d6eeadd`; 14/14 via `run_all --only`. Full 827 not rerun after repair.

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
