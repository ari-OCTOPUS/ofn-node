# MEGAPROMPT — next agent (after W1-SPINE conditional accept)
Date: 2026-09-02. Language: FA or EN. You are ONE lane only.

## Binding
Read `AGENTS.md` then `07-HANDOFF/wave1-pack/megaprompts/00-SHARED-PREAMBLE.md`.
Truth: runtime > repo file > fresh HANDOFF > chat (chat is not evidence).
HOLD_EXTERNAL. No `OCTOPUS_WIRE_*` `OFN_WIRE_*` `auto_email`. Do not rewrite three hearts + pulse_arbiter. No Cycle-8, no fifth route, no Telegram customer send, painting out of scope. Do not decide owner gates (NBB-V4, O-3 ESP32, D1, D7, VLAN).

## World state (do not rediscover)
- Concept-without-code share = **49.5% derived-from-chart** (open+unbuilt), not 45%, not verified. Blocked 10.6% is owner decision, not a concept gap.
- Order is not negotiable: Envelope + Run Store + H1 fix → edge contract → boards.
- W1-SPINE **conditional accept** by PC_worker. Evidence `09-LANES/W1-SPINE/EVIDENCE.md` sha256 `c6b813cebe059ba3a8337c7c1d6df7c4ad783074bb33c37a948d2642addde857`. 8/8 unittest E3-negatives. Uncommitted worktree `C:\Users\Armin\.cursor\projects\f-backup\w1-spine` branch `feat/w1-spine-20260902` base `3a7ca66`. Envelope **not** on 138/180/182.
- COMM-LOOP live mesh type is `witness_request` (not `.v1`; nack `90d6e726`). Last on-contract hop ack `1ab64100`, payload correlation `4f75b619`, SKIP `604298a8`. 182 skip table `7ba4ef33`.
- MERGE-MAP sha `aa91b838`: 180 think, 138 carry, 182 judge. Dual outbox: do not merge senders.
- Wave 2 is **LOCKED** until W1-MONEY, W1-SCALE, W1-FREE each deliver `09-LANES/<LANE>/EVIDENCE.md` with five sections and a non-empty failures section.

## Your job — pick exactly one remaining W1 lane
Open a **new** Cursor worktree. Never two lanes.

```
cursor -w w1-money
cursor -w w1-scale
cursor -w w1-free
```

Pack: `F:\backup\07-HANDOFF\wave1-pack\` (git `3a7ca66`).

| If you are | Read | Own | Forbidden |
|---|---|---|---|
| W1-MONEY | megaprompts/W1-MONEY.md | `src/nbb_cp/api/` `tests/nbb_cp/api/` | `_ops/` `metrics/` |
| W1-SCALE | megaprompts/W1-SCALE.md | `metrics/` `tests/metrics/` | `eval/` `_ops/` `src/` |
| W1-FREE | megaprompts/W1-FREE.md | `09-LANES/W1-FREE/` `tests/snapshot/` | any source mutate |

Touching a file outside own paths = STOP and report, not a warning.

## W1-SCALE clash (do not hide)
Lane text asks blinded **synthetic** green/red. `AGENTS.md` forbids generating synthetic data. Record both rules `status: open`. Prefer **recorded** fixtures already in repo. If none exist, do not invent numbers; write `unverified` and stop that sub-item. Do not delete metric v1 (`metrics/recorded_replay_brier.v1.md`).

## Evidence or reject
`09-LANES/<LANE>/EVIDENCE.md`:
1. raw command + full pytest/unittest tail + timestamp
2. claims table with path or `unverified`
3. what failed (empty = reject)
4. `git diff --stat` of owned paths only
5. rollback commands

Hash ACCEPTANCE/pass-criterion **before** coding. Return PATH + SHA256 to PC_worker. Do not commit unless owner says. Do not push.

## Do not
- Start W2-EDGE / W2-JUDGE / W2-TRUTH / W2-CTX
- Wire boards to Envelope this turn
- Enable flags, send Telegram, remint 1522
- Use Grok chat as transport
- Re-judge 180 pack `edcdf04e` or 138 inventory `c0f97dd7`

## Done looks like
One lane, one worktree, one EVIDENCE.md, owned-path diff only, failures non-empty, HOLD_EXTERNAL still true.
