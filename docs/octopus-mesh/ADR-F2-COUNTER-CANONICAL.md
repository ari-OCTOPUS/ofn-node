# ADR-F2 — Counter canonical sources

status: ACCEPTED (owner GO 2026-09-08 via PC_worker) — canon files
carve_out: no (hard-false; final owner vote supersedes HOLD)
class: A (documentation only)
class_z: this file must not mutate EXTERNAL_ACTIONS / NEW_LAN_LISTENERS / MAY_AUTHORIZE values

Owner GO accepts the *canon file paths*. It does not apply live numbers.
This ADR does not write `_ops/` or `F:\backup`, and does not invent
ofn-node copies of vault files created on the laptop.

## Owner vote (executed 2026-09-08 via PC_worker; carve-out finalized)

```
F2-VOTE: EA=EXTERNAL_ACTIONS.json | NL=NEW_LAN_LISTENERS.json (create) | MA=MAY_AUTHORIZE.json (create) | carve_out_conversation_task=no
```

Final carve-out: keep `may_authorize` hard-false. The prior HOLD (both
yes and no selected) is superseded and is not encoded.

## Accepted canon (vault files live outside this git tree)

| Token | Accepted live source | ofn-node rule |
|---|---|---|
| `EXTERNAL_ACTIONS` | `_ops/state/EXTERNAL_ACTIONS.json` key `EXTERNAL_ACTIONS` | no live `EXTERNAL_ACTIONS=` assignment under `ofn/` |
| `NEW_LAN_LISTENERS` | `_ops/state/NEW_LAN_LISTENERS.json` | no live assignment under `ofn/` |
| `MAY_AUTHORIZE` | `_ops/state/MAY_AUTHORIZE.json` | no live `MAY_AUTHORIZE=` assignment under `ofn/` |
| `may_authorize` (code field) | `ofn/agents/brain_schema.py` default `False` + reject `True` | already in this repo |

NL/MA **create-on-GO** is approved. Vault files were created on the laptop
outside this repo. This checkout does not add copies under `ofn/` or `_ops/`.

## may_authorize hard-false (no True path)

No code path may treat `may_authorize` as True — including
`_ops/owner_console/conversation.py` `kind=task`.
`ofn/agents/brain_schema.py` hard-false remains the ofn-node code canon
(`may_authorize: bool = False` at line 77; `SchemaViolation` on `True`
at lines 89–91). Uppercase `MAY_AUTHORIZE` is a separate token.

On 2026-09-08 a Class A fix was applied on the **laptop vault** (outside
this git tree). This ofn-node checkout does not contain those files and
does not invent copies. This host did not open `F:\backup`. Source: this
follow-up prompt + receipt path below (status: recorded, not re-hashed
on this host).

| claim | recorded value | source |
|---|---|---|
| `F:\backup\_ops\owner_console\conversation.py` | `may_authorize` now always False (was `kind=="task"` → True) | receipt below |
| `F:\backup\_ops\tests\test_board_cp.py` | assert False | receipt below |
| `t_panel_callbacks_same_queue` | PASS | receipt below |

Receipt (laptop; not in this git tree):
`F:\backup\00-SEASON\PROMPT-RUNS-20260908\import-counters\CLASS-A-CONVERSATION-HARD-FALSE.md`

ofn-node code canon is unchanged: `brain_schema.py` hard-false. This PR
does not add `conversation.py` or the vault test.

## Map hash (laptop receipts — not re-hashed here)

Recorded sha256 (PAIR J prompt 2 / laptop receipts):

`2918BD48073E6876F10A98AAA01F6D736061D7DEE3D33826E07E742D57B28D39`

The map file is not in this ofn-node checkout. This session did not
recompute the digest. status: recorded, not re-hashed on this host.

## Contradiction — EXTERNAL_ACTIONS (Class Z; not resolved by this vote)

Laptop vault currently CONFLICTS `0` / `1` / `2` for `EXTERNAL_ACTIONS`
(PAIR J prompt 2 / laptop receipts; vault is outside this git tree).
This vote does **not** resolve that conflict. There is **no apply-values GO**
and no vault 0/1/2 reconcile. This ADR does not pick one and does not
“fix” those numbers.

| claim | value_a | source_a | value_b | source_b | resolution | status |
|---|---|---|---|---|---|---|
| EXTERNAL_ACTIONS | 0 | `docs/octopus-mesh/RUNTIME-V1-STATUS.md` line 55 | conflict {0, 1, 2} | PAIR J prompt 2 — laptop vault (not in this git tree) | null | open |

`NEW_LAN_LISTENERS=0` and `MAY_AUTHORIZE=false` also appear in
`docs/octopus-mesh/RUNTIME-V1-STATUS.md` lines 56–57. Those lines are
document text, not live `ofn/` assignments. This ADR leaves them unchanged.

## A2 CI lock (not on this branch)

`tests/test_counter_source_f2.py` is absent from this branch. It lives on
PR #236. This ADR does not copy or edit that test.

## Out of scope

- Applying EXTERNAL_ACTIONS / NEW_LAN_LISTENERS / MAY_AUTHORIZE values
  (no apply-values GO; no vault 0/1/2 reconcile)
- Inventing ofn-node copies of laptop vault `conversation.py` / tests /
  receipts (Class A apply is on `F:\backup`, not this tree)
- Inventing ofn-node copies of laptop vault JSON
- Enabling `OCTOPUS_WIRE_*` / `OFN_WIRE_*` or opening a closed gate
