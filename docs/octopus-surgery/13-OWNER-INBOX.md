# Owner inbox

Maximum five decisions. Only one action is immediately READY.
An agent must not treat silence as yes.

---

## 1. Review PR #6 on its exact current head after four focused checks pass

Status: READY — first and only immediate action
Decision: inspect focused CI on the current head reported in the PR body; do not merge, deploy, open D1/D7, generate OWNER_KEY, or rotate secrets.

```text
OWNER-CONFIRM: reviewed PR 6 at <NEW_FINAL_HEAD_SHA from PR body>;
focused CI passed 4/4 on this exact SHA;
merge remains unauthorized
```

---

## 2. Keep the local vault/surgery branch unpublished

Status: STANDING
Decision: `LOCAL_VAULT_BRANCH_PUBLICATION_FORBIDDEN`. Selective export is already `OPEN_AS_PR_6`.

```text
OWNER-CONFIRM: do not push surgery/cognition-authority-denylist-20260830-170620 to public ofn-node
```

---

## 3. OWNER-09 hermetic full suite — recorded

Status: DONE
Result: `HERMETIC_BOUNDARY_VIOLATION` — 770/827 passed; 57 failed; 1 live skipped.
Do not rerun OWNER-09 as a campaign gate.

---

## 4. Keep D1/D7/OWNER_KEY/secret rotation closed

Status: STANDING
Decision: this campaign did not open those gates.

```text
OWNER-CONFIRM: D1 D7 OWNER_KEY secret_rotation remain owner-only and closed
```

---

## 5. Accept current distance: 45% ± 7%, not 90%

Status: STANDING
Decision: credit the five surgeries; do not promote historical Brier or test-count claims.
Official announced weighted figure is **45.70** (Recovery=34). Exact 34-weighted
raw is 45.75; rounding delta −0.05. See `ACCOUNTING-CORRECTION-20260831.yaml`.

```text
OWNER-CONFIRM: campaign overall 45% ± 7%; official announced 45.70; 90% gates remain closed
```
