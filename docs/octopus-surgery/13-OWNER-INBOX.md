# Owner inbox

D-27 (2026-09-02) supersedes D-26 authorization fields. D-26 remains
the historical record. Partner voices are still not independently
observed. Real flags in `ofn/config.py` were not defaulted on.

---

## 1. D-26 STAGE-01 package — recorded

Status: DONE — authorization superseded by D-27
Decision: owner accepted the senior package and later attested that
Maliheh, Abbas and Saba all signed. This vantage did not hear those
three voices.

```text
OWNER-CONFIRM: D-26 recorded 2026-09-01; authorization_superseded_by=D-27
```

---

## 2. Keep the local vault/surgery branch unpublished

Status: STANDING — reinforced by D-26
Decision: `LOCAL_VAULT_BRANCH_PUBLICATION_FORBIDDEN`.

```text
OWNER-CONFIRM: vault_to_public_ofn_node = forbidden
```

---

## 3. Keep secret rotation closed until secrets actually rotate

Status: STANDING — D-27 authorizes wire/money but does not flip
`OFN_KEEP_GATES_OPEN` or `OFN_WIRE_OUTBOUND`. Kill switch remains
`OFN_EXTRA_CLOSED_GATES`.

```text
OWNER-CONFIRM: secret_rotation stays shut until real rotate;
OFN_KEEP_GATES_OPEN not set; OFN_WIRE_OUTBOUND stays env-gated
```

---

## 4. Wave 1 not started

Status: STANDING
Decision: envelope + run store + financial H1 stay on the vault body.
Do not start them from this GitHub lineage. Do not add a second envelope
family on ofn-node.

```text
OWNER-CONFIRM: wave_1_started=false; wave_1_body=vault
```

---

## 5. Accept current distance: 45% ± 7%, not 90%

Status: STANDING
Decision: credit the five surgeries; do not promote historical Brier or test-count claims.
Official announced weighted figure is **45.70** (Recovery=34). See
`ACCOUNTING-CORRECTION-20260831.yaml`. D-26 does not close C-001..C-004.

```text
OWNER-CONFIRM: campaign overall 45% ± 7%; official announced 45.70; 90% gates remain closed
```

---

## 6. D-27 unlock — authorized, capped, reversible

Status: DONE as a record on this lineage; merge to `main` waits on
GitHub review (branch protection). Week proof is still one real
`PAINT-L5-001` payment receipt.

```text
OWNER-CONFIRM: D-27 implementation=yes merge=yes wire=yes money=yes
caps 25/50/0; C-009 closed; partner_voices independently observed=false
```

---

## 7. D-28 — three fields still unforged

Status: DONE as a record. Voices, Saba `record_release`, and actual
secret rotation did not happen on this host. Painting was not blocked.

```text
OWNER-CONFIRM: D-28 risk_accepted_unrotated; GATE_OPEN_UNTIL_UTC=2026-09-16
partner_voices independently observed=false; saba release unsigned
```
