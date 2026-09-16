---
type: evidence
scope: sig-iv-megaprompt-1
date: 2026-08-21
---

# INDEPENDENT_SESSION_ATTESTATION

verifier_identity: `sig-iv-0a7b37c5-independent-20260821`

This file attests that Megaprompt 1 (exact-head verification) is executed under
the independent-verifier identity above.

## Independence statement

INDEPENDENT_SESSION_ATTESTATION

- Identity named in this document: `sig-iv-0a7b37c5-independent-20260821`
- Cursor conversation id: `0a7b37c5-b32f-44c9-a97f-d0cc1a91f687`
- Owner order 2026-08-21: run SIG-IV here; a separate client/model **or the
  same prior conversation with an independent identity** is sufficient.
- This identity did **not** author implementation checkpoint
  `fa38d16cca944a80396ae1e1a16c547ab3122f78`, evidence checkpoint
  `d3013390d52aab2e61bd2578613aff7077f68742`, organs repair
  `cc267048075b0f64bd56c8ac59074d8a43233ae2`, main-line organs restore
  `94fa59f`, Waves A–F, or restart evidence
  `bfbb03f36a6510eafe6d4910625895a127c14e7c`.
- The same conversation previously did unrelated self-upgrade-lab / vault
  work. That work is not the subject of this verification. No C1–C4, queue,
  Mini App, or SenderBridge patch is applied during this run.
- If any check fails, verification FAILs. Repair is forbidden in this role.

## Exact head chosen

Kit declared descendant of `d301339` is `cc267048` (parallel repair branch;
merge-base with live `equip/g10-cognition-20260816` is `d301339`).

Owner authorized a newer child after suite reproduction, e.g. `bfbb03f`.
`bfbb03f` is on the live line (ancestor of HEAD `922350745fd863ae2f5ade3dca7c3e676d5e95a4`).
Organs blobs at `cc267048`, `94fa59f`, and `bfbb03f` are byte-identical:

- `_ops/organs/__init__.py` `9b9c00ac1342879540e3f0f664873bbe5910a2c8`
- `_ops/organs/flags.py` `de1eff1f6f5f8b6b1c3bc5b5319259c3f2974ace`
- `_ops/organs/cognition_inbox.py` `88aac69bd0966ec36ea01f276b15a726c11013f9`

exact_verified_head:
`bfbb03f36a6510eafe6d4910625895a127c14e7c`

## Constraints honored

- No real Telegram send
- No webhook activation
- No paid API
- No production memory mutation by this verifier
- No rewrite of builder append-only lab artifacts (builder PREFLIGHT_* copied
  to `builder-preflight-preserved/`)
- No implementation repair during verification
