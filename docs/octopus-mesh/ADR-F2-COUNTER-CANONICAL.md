# ADR-F2 — Counter canonical sources

status: PROPOSED — PENDING_OWNER_VOTE
requires: owner_decision
class: A (documentation + owner ballot only)
class_z: this file must not mutate EXTERNAL_ACTIONS / NEW_LAN_LISTENERS / MAY_AUTHORIZE values

This is a proposal. It does not create vault files, does not write `_ops/`
or `F:\backup`, and does not pick a live number for any counter.

## Owner vote (fill in; do not execute create until GO)

```
F2-VOTE: EA=EXTERNAL_ACTIONS.json | NL=NEW_LAN_LISTENERS.json (create|defer) | MA=MAY_AUTHORIZE.json (create|defer) | carve_out_conversation_task=yes|no
```

## Proposed canon (outside this git tree unless noted)

| Token | Proposed live source | ofn-node rule until owner GO |
|---|---|---|
| `EXTERNAL_ACTIONS` | `_ops/state/EXTERNAL_ACTIONS.json` key `EXTERNAL_ACTIONS` | no live `EXTERNAL_ACTIONS=` assignment under `ofn/` |
| `NEW_LAN_LISTENERS` | `_ops/state/NEW_LAN_LISTENERS.json` — create only after owner GO | no live assignment under `ofn/` |
| `MAY_AUTHORIZE` | `_ops/state/MAY_AUTHORIZE.json` — create only after owner GO | no live `MAY_AUTHORIZE=` assignment under `ofn/` |
| `may_authorize` (code field) | `ofn/agents/brain_schema.py` default `False` + reject `True` | already in this repo |

Inside ofn-node, `ofn/agents/brain_schema.py` remains the `may_authorize`
code canon (`may_authorize: bool = False` at line 77; `SchemaViolation` on
`True` at lines 89–91). Uppercase `MAY_AUTHORIZE` is a separate token.

## Map hash (laptop receipts — not re-hashed here)

Recorded sha256 (PAIR J prompt 2 / laptop receipts):

`2918BD48073E6876F10A98AAA01F6D736061D7DEE3D33826E07E742D57B28D39`

The map file is not in this ofn-node checkout. This session did not
recompute the digest. status: recorded, not re-hashed on this host.

## Contradiction — EXTERNAL_ACTIONS (do not resolve)

Laptop vault currently CONFLICTS `0` / `1` / `2` for `EXTERNAL_ACTIONS`
(PAIR J prompt 2 / laptop receipts; vault is outside this git tree).
This ADR does not pick one and does not “fix” those numbers.

| claim | value_a | source_a | value_b | source_b | resolution | status |
|---|---|---|---|---|---|---|
| EXTERNAL_ACTIONS | 0 | `docs/octopus-mesh/RUNTIME-V1-STATUS.md` line 55 | conflict {0, 1, 2} | PAIR J prompt 2 — laptop vault (not in this git tree) | null | open |

`NEW_LAN_LISTENERS=0` and `MAY_AUTHORIZE=false` also appear in
`docs/octopus-mesh/RUNTIME-V1-STATUS.md` lines 56–57. Those lines are
document text, not live `ofn/` assignments. This ADR leaves them unchanged.

## A2 CI lock (not duplicated on this branch)

`tests/test_counter_source_f2.py` is absent from `origin/main` @
`0522fb85f63a57a9955be113e9a3eab070a3bff2`. The same path exists on
`refs/pull/236/head` @ `5e3254f` (fetched this session). That test
already:

- keeps `brain_schema` as `may_authorize` canon (default `False`; `True` raises)
- fails if any `ofn/**` file with suffix `.py` / `.json` / `.cmd` / `.env`
  assigns `EXTERNAL_ACTIONS` / `NEW_LAN_LISTENERS` / `MAY_AUTHORIZE` via
  `NAME=value`
- fails if any `ofn/**/*.py` uses keyword `may_authorize=True`

This ADR does not copy that test. Merge of the A2 lock is a separate PR
(see #236). A second ofn-node file reporting a different live value for
those three uppercase counters is a CI failure once that test is on the
default branch.

## Out of scope

- Creating `_ops/state/*.json` before owner GO
- Changing production counter values (Class Z)
- Enabling `OCTOPUS_WIRE_*` / `OFN_WIRE_*` or opening a closed gate
