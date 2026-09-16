---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, megaprompt, lanes, propose-only]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY/00-VERDICT]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY/02-ROLE-AUTHORITY]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY/03-OWNER-DECIDE-12-FIELDS]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY/06-IDEMPOTENCY-AND-RECEIPTS]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY/08-EDGE6-CAUSAL-TRACE]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY/09-FOUR-INDEPENDENT-FIXES]]"
---

# P2 Mega-prompt — five independent lanes

```text
PACK=06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY
EVIDENCE_SHA256=44805a261e9de062c88e15fdca720d92393bb6e4a7b6104484a4b251d4e0b82f
P2_IMPLEMENTATION_AUTHORIZED=NO
EDGE6_PATCH_AUTHORIZED=NO
MARK_AS_FIXED=NO
NEW_SUBSYSTEM=FORBIDDEN
THREE_BOARD_BOUNDARY=KEEP
```

Paste **one lane** to one agent. Do not give one agent two lanes. Do not start a lane whose `OWNER_GO` is still `NO`.

Shared bans for every lane:

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
```

---

## LANE 1 — P1 runtime activation (138 only)

```text
LANE=P1_RUNTIME
BOARD=138
OWNER_GO=NO
MAY_RESTART=NO_UNTIL_OWNER_GO
END_TO_END=NO
```

**Read first:** `P2-DISCOVERY/01-P1-COMMIT-AUDIT.md`, `10-RUNTIME-ACTIVATION-PLAN.md`, `P1-RESULT.md`.

**Fact:** source commit `a27eb0536793c7fc040917bb645e9057707298f4` adds `data.owner_items`. Live PID last proven `1351408` started 2026-08-27 on `6881337`. Fourth file is test-only and justified.

**Do:**

1. Re-read live PID, ExecStart, `git rev-parse HEAD` on `/home/ari/ofn`. Do not assume 1351408 still holds.
2. If HEAD ≠ `a27eb05`, STOP and report. Do not merge from vault `c803dee`.
3. Wait for owner GO, then one `systemctl restart ofn.service`.
4. Prove `LOADED_COMMIT=a27eb05`, `OWNER_ITEMS_PRESENT=true`, `MESH_ITEMS_PARITY=true`, callback miss → `degraded` not fake empty-success.
5. Leave `queue.js` untouched. Restart is not end-to-end.

**Do not:** G3 scan-budget in the same restart unless owner names both. Do not treat 138 outbox counts as sent.

**Done when:** post-restart hash proof exists. `MARK_AS_FIXED` still `NO` for P1 e2e.

---

## LANE 2 — owner_items UI (138, after Lane 1)

```text
LANE=OWNER_ITEMS_UI
BOARD=138
OWNER_GO=NO
DEPENDS=LANE_1_LOADED
```

**Read first:** `09-FOUR-INDEPENDENT-FIXES.md` §4, `P1-RESULT.md`.

**Fact:** `web/cockpit-v2/src/pages/queue.js` is source, not generated. Reads `data.items` only. Vault `panel.html` also `data.items`. Missing callback must stay `owner_items=null` + degraded.

**Do:**

1. Confirm Lane 1 loaded before editing UI.
2. Render a **separate** labelled business group from `owner_items` (six metadata fields, no payload).
3. Do not change mesh `items` order, count, or pagination.
4. Show source / freshness / type. Empty-success on callback miss is forbidden.
5. Add a frontend test. Minimal files: `queue.js` + that test.

**Do not:** mix with OwnerDecision / P2. Do not invent IDs.

---

## LANE 3 — P2 binding (blocked)

```text
LANE=P2_BINDING
BOARD=138_plus_182_request
OWNER_GO=NO
P2_BINDING=BLOCKED
LOCAL_MINTING=FORBIDDEN
```

**Read first:** `02-ROLE-AUTHORITY.md`, `03-OWNER-DECIDE-12-FIELDS.md`.

**Fact:** live `owner_decide` is `{id, approve, confirmed_twice}` → `approve_manual`. Twelve fields exist only on the spine snapshot. Canonical count = 0. Missing = 9. `action` and `idempotency_key` are `AVAILABLE_UNVERIFIED`. Three payload hashes are contradicted.

**Stop until owner ranks:**

1. Signed mesh registry vs A2-001 (180 execute, A2-scoped) vs unsigned V2/180 `nodes.json` (180 quality-only) vs C-034 (182 observe).
2. Whether 182 still requires `draft-11` (string absent from vault).
3. Producers for `run_id`, `artifact_sha`, `verdict_sha`, `recipient_masked`, `expires_at`, `rollback`.

**If later authorized, smallest seam:** bind on the **producer before enqueue**; `owner_decide` only validates an existing binding; no local UUID/timestamp fill; no `witness_mint` inside `Node.owner_decide`; 182 remains the only witness request target if that role is confirmed.

**RED required (when authorized):** missing binding → fail-closed, outbox stays pending; hash mismatch fail-closed; reject path must not depend on OwnerDecision.

---

## LANE 4 — EDGE-6 (180 isolated worktree)

```text
LANE=EDGE6
BOARD=180
OWNER_GO=NO
EDGE6_PATCH_AUTHORIZED=NO
```

**Read first:** `04-TRANSMIT-PATH-A.md`, `05-TRANSMIT-PATH-B.md`, `06-IDEMPOTENCY-AND-RECEIPTS.md`, `08-EDGE6-CAUSAL-TRACE.md`.

**Fact:** EDGE-6 = 180 proposal outbox send/drain to 138. Last same-run proof = `live_spine_run` registry. First missing = proposal enqueue. PATH_A (`handle_task` persist/transmit) is canonical. PATH_B (inline persist/transmit, synthetic `run_id`) is a second transmit. Morning “add 3 persist lines” **is PATH_B** — do not add it again.

**Do, in an isolated worktree, before any live patch:**

1. Re-hash live worker vs `c43afff0`. Header `72e3b3a3` / “NOT live” is stale (`CON-WORKER-HASH`).
2. Hermetic fake-transport test: both paths fire with different `reply:{mid}:{sha}` keys.
3. Only after that proof + owner GO: **delete PATH_B**, keep PATH_A.
4. Do not replay `run-spine-138-snap-20260828T005835Z` without a separate GO.

**Do not:** treat registry as receipt. Treat ACK as effect. Treat `630c5060` as this-run receipt. Spawn mosquitto. Bind `0.0.0.0` for new services.

---

## LANE 5 — four independent defects (191 + 138)

```text
LANE=FOUR_DEFECTS
BOARDS=191_and_138
OWNER_GO=NO
INDEPENDENT_OF_EDGE6=YES
```

Run as **four tickets**, not one commit.

| Ticket | Status | Files | Note |
|---|---|---|---|
| 5a BEARER | **CLOSED** vault `7d65f2d` | `_ops/flag_drift.py`, `test_flag_drift.py` | `_SECRET_TOKENS` includes `BEARER`. Do not reopen. Do not read secret values. |
| 5b rfc_id | CLOSED on this vault + 191 WebView | none | Do not reopen. Persistent Menu Button is a separate Telegram object. |
| 5c scan budget | OPEN on 138 | `cockpit_v2_read_model.py` + test | Partition budget; do not raise 2048 unbounded. Needs `ofn.service` load. Conflicts with Lane 1 if same file — serialize. |
| 5d owner_items UI | OPEN | see Lane 2 | Do not duplicate Lane 2. |

---

## Owner GO checklist (this session cannot tick)

- [ ] Signed mesh role registry, or explicit rank of A2-001 / V2 / C-034
- [ ] draft-11 still binding? yes / no / retire
- [ ] Lane 1 restart on 138
- [ ] Lane 4 PATH_B delete on 180
- [ ] Twelve-field producers named
- [ ] Which of 5a / 5c may land without the others

Until those exist, agents stay in propose / isolated-test / report. No deploy.
