# ADR-F2 — Counter canonical sources

status: ACCEPTED (owner GO 2026-09-08 via PC_worker) — canon files
carve_out: HOLD (single owner pick still required)
class: A (documentation only)
class_z: this file must not mutate EXTERNAL_ACTIONS / NEW_LAN_LISTENERS / MAY_AUTHORIZE values

Owner GO accepts the *canon file paths*. It does not apply live numbers.
This ADR does not write `_ops/` or `F:\backup`, and does not invent
ofn-node copies of vault files created on the laptop.

## Owner vote (executed 2026-09-08 via PC_worker)

```
F2-VOTE: EA=EXTERNAL_ACTIONS.json | NL=NEW_LAN_LISTENERS.json (create) | MA=MAY_AUTHORIZE.json (create) | carve_out_conversation_task=HOLD
```

## Accepted canon (vault files live outside this git tree)

| Token | Accepted live source | ofn-node rule |
|---|---|---|
| `EXTERNAL_ACTIONS` | `_ops/state/EXTERNAL_ACTIONS.json` key `EXTERNAL_ACTIONS` | no live `EXTERNAL_ACTIONS=` assignment under `ofn/` |
| `NEW_LAN_LISTENERS` | `_ops/state/NEW_LAN_LISTENERS.json` | no live assignment under `ofn/` |
| `MAY_AUTHORIZE` | `_ops/state/MAY_AUTHORIZE.json` | no live `MAY_AUTHORIZE=` assignment under `ofn/` |
| `may_authorize` (code field) | `ofn/agents/brain_schema.py` default `False` + reject `True` | already in this repo |

NL/MA **create-on-GO** is approved. Vault files were created on the laptop
outside this repo. This checkout does not add copies under `ofn/` or `_ops/`.

Inside ofn-node, `ofn/agents/brain_schema.py` remains the `may_authorize`
code canon (`may_authorize: bool = False` at line 77; `SchemaViolation` on
`True` at lines 89–91). Uppercase `MAY_AUTHORIZE` is a separate token.

## Carve-out HOLD

Owner selected **both** yes and no for `conversation.py`
`may_authorize=True` versus hard-false. This ADR does **not** encode both.
Wording stays undecided until a single owner pick.
`ofn/agents/brain_schema.py` stays the ofn-node `may_authorize` code canon.

status: open
requires: owner_decision (single pick; not both)

## Map hash (laptop receipts — not re-hashed here)

Recorded sha256 (PAIR J prompt 2 / laptop receipts):

`2918BD48073E6876F10A98AAA01F6D736061D7DEE3D33826E07E742D57B28D39`

The map file is not in this ofn-node checkout. This session did not
recompute the digest. status: recorded, not re-hashed on this host.

## Contradiction — EXTERNAL_ACTIONS (Class Z; not resolved by this vote)

Laptop vault currently CONFLICTS `0` / `1` / `2` for `EXTERNAL_ACTIONS`
(PAIR J prompt 2 / laptop receipts; vault is outside this git tree).
This vote does **not** resolve that conflict. There is **no apply-values GO**
yet. This ADR does not pick one and does not “fix” those numbers.

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
  (no apply-values GO)
- Encoding the conversation.py carve-out as both yes and no
- Inventing ofn-node copies of laptop vault JSON
- Enabling `OCTOPUS_WIRE_*` / `OFN_WIRE_*` or opening a closed gate
