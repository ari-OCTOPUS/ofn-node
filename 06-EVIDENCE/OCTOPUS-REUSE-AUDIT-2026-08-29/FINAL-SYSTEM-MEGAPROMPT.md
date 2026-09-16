---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, megaprompt, qualified-draft, propose-only]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/00-THREE-NODE-VERDICT]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-MEGAPROMPT-LANES]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/NODE-138-EVIDENCE/00-VERDICT]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/NODE-182-EVIDENCE/00-VERDICT]]"
---

# FINAL SYSTEM MEGAPROMPT — qualified draft (not a GO)

```text
PACK=06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29
FINAL_SYSTEM_MEGAPROMPT_READY=NO
FINAL_SYSTEM_MEGAPROMPT_EXECUTABLE=NO
MUTATIONS_AUTHORIZED=NO
MARK_AS_FIXED=NO
P2_IMPLEMENTATION_AUTHORIZED=NO
EDGE6_PATCH_AUTHORIZED=NO
NEW_SUBSYSTEM=FORBIDDEN
THREE_BOARD_BOUNDARY=KEEP
observed_at=2026-08-29T06:10:00Z
```

Paste **one lane** to one agent. Do not give one agent two lanes. Do not start a lane whose `OWNER_GO` is still `NO`. This document is a map, not authorization.

Shared bans:

```text
NO_NEW_ENDPOINT=1
NO_NEW_DB=1
NO_NEW_QUEUE=1
NO_NEW_WITNESS_SERVICE=1
NO_STORE_MERGE=1
NO_LOCAL_UUID_PROVENANCE=1
NO_SECRET_READ=1
NO_MOSQUITTO_PGREP=1
NO_OFN_KEEP_GATES_OPEN=1
NO_T1_T5_EXECUTION=1
NO_TELEGRAM_ENABLE=1
NO_CUSTOMER_SEND=1
NO_0.0.0.0_BIND=1
```

Every claim needs an arbiter envelope (`node_id`, `asserted_ip`, `vantage`, `scope`, `claim_type`, `evidence`). Default `scope=this_host_only`. Do not promote `system_wide` without two `node_id`s. Missing LAN ports ≠ absent loopback APIs (`claim_type=inference` + alternatives). Disk absence on 180 = `body_not_on_this_host`, not `body_missing`.

---

## Identity (do not collapse)

| Claimed | Live | Rule |
|---|---|---|
| Cursor session “board 180 quality brain” | vault host `DESKTOP-KA9RFN5` / `192.168.0.191` | CONTRADICTED; speak as 191 observer |
| 180 | local/proposal layer; OFN body false | PROPOSE_ONLY |
| 138 | DietPi `192.168.0.138` `/home/ari/ofn` | OFN body; commander claim is UNSIGNED |
| 182 | witness/observe DISPUTED | `may_authorize=false`; runtime this pack NOT_OBSERVED |

Do not write revenue / sent / booking except from board 138 ledger after a live proof. Do not treat 138 outbox counts as sent.

---

## Locked facts

### 138 (LIVE_VERIFIED from 191 SSH, 2026-08-29)

- HEAD `a27eb0536793c7fc040917bb645e9057707298f4` parent `6881337`.
- P1 four files on disk; `data.owner_items` in read model.
- PID `1351408` started 2026-08-27 11:33:39 AEST → **P1 not loaded**.
- `queue.js` reads `data.items` only.
- Bind `127.0.0.1:8791-8794`. SSH `0.0.0.0:22`.
- timesyncd enabled, **inactive**; NTP=no.
- Telegram: five `OFN_BOT_TOKEN_*` **names**; zero pollers. Do not add a sixth bot.
- Organs = YAML packs + adapters inside ofn-node. `/home/ari/ziman-node` ABSENT.
- Vault `c803dee` is not an object on 138. Do not port vault `event_store`/`command_bus`.

### 182 (disk + prior artifacts only)

- Role DISPUTED: A2-001 silent vs C-034 observe vs unsigned V2/systemd lab-witness vs L191 EDGE-8.
- Machine A: 138 `witness_mint` = STRUCTURAL_PASS only. Not canonical 182.
- Machine B: isolated worker copy; ACK ≠ effect.
- `630c5060` is not this-run receipt. `wr_950f8d0e` predates proposal.
- Last same-run proof = `registry_projection`. First missing = `proposal_enqueue`.
- P2 fields owned by 182 = NONE.
- draft-11 body NOT_FOUND; still-required UNKNOWN.

### 180 (owner-pasted pack; not re-hashed)

- Registry FOUND_LIVE_UNSIGNED.
- Worker provenance UNRESOLVED (header stale = hypothesis).
- Disk ~93%. Retention = proposal only. No delete.

### P2 card

- Live decide = `{id, approve, confirmed_twice}` → `approve_manual`.
- Twelve fields canonical=0, missing=9, available_unverified=2 (`action`, `idempotency_key`).
- Three payload hashes CONTRADICTED. Do not mint locally.

---

## LANE 1 — P1 runtime (138 only)

```text
LANE=P1_RUNTIME
BOARD=138
OWNER_GO=NO
MAY_RESTART=NO_UNTIL_OWNER_GO
```

Read: `P2-DISCOVERY/01-P1-COMMIT-AUDIT.md`, `10-RUNTIME-ACTIVATION-PLAN.md`, `NODE-138-EVIDENCE/06-P1-RUNTIME.md`.

1. Re-read live PID, ExecStart, `git rev-parse HEAD` on `/home/ari/ofn`.
2. If HEAD ≠ `a27eb05`, STOP. Do not merge from vault.
3. After owner GO: one `systemctl restart ofn.service`.
4. Prove `LOADED_COMMIT=a27eb05`, `OWNER_ITEMS_PRESENT=true`, mesh items parity, callback miss → degraded not fake empty-success.
5. Leave `queue.js` untouched. Restart ≠ end-to-end. Do not combine with 5c unless owner names both.

---

## LANE 2 — owner_items UI (after Lane 1)

```text
LANE=OWNER_ITEMS_UI
BOARD=138
OWNER_GO=NO
DEPENDS=LANE_1_LOADED
```

Separate labelled business group from `owner_items` (six metadata fields, no payload). Do not change mesh `items` order/count/pagination. Frontend test. Files: `queue.js` + that test. Not P2.

---

## LANE 3 — P2 binding (blocked)

```text
LANE=P2_BINDING
P2_BINDING=BLOCKED
LOCAL_MINTING=FORBIDDEN
OWNER_GO=NO
```

Stop until owner ranks signed registry vs A2-001 vs unsigned V2 vs C-034, answers draft-11, and names producers for the six open fields.

If later authorized: bind on the **producer before enqueue**; `owner_decide` only validates; no local UUID/timestamp; no `witness_mint` inside `Node.owner_decide`. Missing binding → fail-closed; outbox stays pending.

---

## LANE 4 — EDGE-6 (180 isolated worktree)

```text
LANE=EDGE6
BOARD=180
OWNER_GO=NO
EDGE6_PATCH_AUTHORIZED=NO
```

PATH_A (`handle_task` persist/transmit) is canonical. PATH_B (inline persist/transmit, synthetic `run_id`) is the second transmit. Morning “add 3 persist lines” **is PATH_B** — do not add it again.

1. Re-hash live worker vs `c43afff0`. Header `72e3b3a3` is stale.
2. Hermetic fake-transport: both paths fire with different `reply:{mid}:{sha}` keys.
3. After that proof + GO: **delete PATH_B**, keep PATH_A.
4. Do not replay `run-spine-138-snap-20260828T005835Z` without a separate GO.
5. Registry ≠ receipt. ACK ≠ effect.

---

## LANE 5 — independent defects

| Ticket | Status | Files | Note |
|---|---|---|---|
| 5a BEARER | **CLOSED** vault `7d65f2d` | `_ops/flag_drift.py` | Do not reopen. Values never copied. |
| 5b rfc_id | CLOSED | none | Persistent Menu Button is a separate Telegram object. |
| 5c scan budget | OPEN on 138 | `cockpit_v2_read_model.py` + test | Partition budget; do not raise 2048 unbounded. Serialize vs Lane 1. |
| 5d | = Lane 2 | — | Do not duplicate. |

---

## Owner GO checklist

- [ ] Signed mesh role registry, or explicit rank of A2-001 / V2 / C-034
- [ ] draft-11 still binding? yes / no / retire
- [ ] Lane 1 restart on 138
- [ ] Lane 4 PATH_B delete on 180
- [ ] Twelve-field producers named
- [ ] 5c may land without Lane 1? owner yes/no
- [ ] Optional: 182 live read-only SSH without `|mosquitto|`

Until those exist: propose / isolated-test / report only. No deploy.
