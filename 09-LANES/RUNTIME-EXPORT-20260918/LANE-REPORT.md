# LANE REPORT — RUNTIME-EXPORT-20260918

GOV_VERSION=V8 · LADDER=L2 · read-only on the board except where stated; no live edit deployed

## Why this lane exists

The owner audited the day's claims against canonical git and found drift. This
lane measured that claim rather than accepting or denying it, captured what is
actually running on board 138, and fixed the one defect the measurement turned up.

## 1. Runtime snapshot — DONE, 16/16 byte-verified

`tools/runtime_snapshot.py` captures each file's sha256 **on the node** and
re-computes it locally after a base64 fetch. `sha256_verified=true` means the
local copy is byte-identical to the running file. Files were fetched base64 on
purpose: a text fetch rewrites line endings and the hash then describes something
that is not running.

- `evidence/RUNTIME-SNAPSHOT-MANIFEST.json` — 13 repo files + 3 system files
- `evidence/runtime-snapshot-138/` — the byte-exact copies
- `evidence/board138-dirty-probe.txt` — what is dirty and what changed since 09-17
- Secrets: contents are never printed; a pattern scan records match **kind and
  count only**. All 16 files scanned clean of the credential patterns tested.

Board identity: `fe0c55e0a952e0048ff6bd3ddb8ab9419cd1dc0d` — "merge(canonical):
align board138 with origin/main@ae187e03". The board is *on* the canonical lineage
and has local modifications on top of it.

## 2. Drift vs canonical — measured with blob hashes

`tools/drift_vs_canonical.py` compares `git hash-object` of each live file against
the blob sha canonical git reports for the same path (`evidence/DRIFT-VS-CANONICAL.json`).

Canonical `ari-OCTOPUS/ofn-node@main` = **`ae187e03ecb4`** (3454 blobs) — exactly
the HEAD the owner quoted.

| Verdict | Files |
|---|---|
| IDENTICAL | none of the sampled 13 |
| **DRIFT** (in canonical, content differs) | `ofn/ziman_cycle/gates.py`, `ofn/agents/owner_notify.py`, `ofn/agents/glass_runner.py` |
| **ABSENT_FROM_CANONICAL** | `tools/w1_verdict_collector.py`, `state/revenue-drive/{owner_ask,owner_reply,action_executor,proposal_intake,uwork_acceptance_test,patch_uwork_wire,funnel_reconcile}.py`, `ofn/agents/{owner_digest_emit,owner_queue_notify_hook}.py` |

**The owner's drift table is confirmed.** Nothing live was in canonical when the
claims were made.

### What each drifted patch actually does (diffed, not taken on trust)

| File | Change | Effect |
|---|---|---|
| `ofn/ziman_cycle/gates.py` | +1/−1: `hold_external: bool = True` → `False` | the A1 Ziman hold release |
| `ofn/agents/owner_notify.py` | +17/−1: new `_urlopen_retry(req, timeout=15, attempts=2)` wired into `send()` | the R1 notify fix — self-contained and testable |
| `ofn/agents/glass_runner.py` | +81/−2: `callback_query` rows spooled to the MONEY lane with owner-chat identity + `answerCallbackQuery` ack; message identity switched to the sender; `edited_message` accepted | the Telegram button loop |

Preimages exist for all three (`.pre-a1-*`, `.pre-r1retry-*`, `.pre-ownerlink2/4/5-*`,
`.bak-callback-*`), listed in the manifest — rollback material is intact.

## 3. The attribution finding — the claim was overstated, a different defect is real

The earlier lane reported that `owner_reply.py` consumes customer email replies as
owner votes. Measured, that is **not** what happens:

- the spool `state/revenue-drive/tg-inbox.jsonl` holds 26 rows: **14 match the
  owner allowlist** (12 `callback` taps + 1 `message` + 1 null-kind) and **12 do
  not** — and those 12 are exactly `kind=REPLY_DETECTED`, the customer email
  replies, carrying **no `chat` field at all**
- `tg_get()` filters on `str(d.get("chat","")) in chat_allow.split(",")`, so
  chat-less rows are excluded **today**
- the live allowlist has exactly 1 entry (owner `…1610`) and **no empty entry**

So the two channels are currently disjoint and no email was read as a vote.
What is real is worse in kind, not in degree, because it is quiet:

**Defect A — the allowlist is used raw, and an empty entry admits every email.**
`chat_allow.split(",")` on `"<owner>,"` yields `["<owner>", ""]`, and a chat-less
row stringifies to `""`, so it matches. Reproduced against the **unpatched live
file**: with `allow="<owner>,"` and a spool of one email row + one owner row, the
reader returned **2 messages** (both). A trailing comma or a space in
`secrets.env` is enough to turn all 12 customer emails into owner decisions.

**Defect B — the documented cursor fix was never in effect.** The code comments
claim the cursor is now "the set of consumed row HASHES, not a line index", but
the writer emits `str(kept)` — an integer. Verified live: the cursor file contains
`2`, not JSON. Every run therefore falls back to the legacy index path, which is
the exact mechanism that had already "silently swallowed a real owner vote on
2026-09-18". The comment described a fix the code did not perform.

## 4. Fix implemented (in the lane, not deployed)

`pr/state/revenue-drive/owner_reply.py`, plus
`tests/test_owner_inbox_attribution.py` — **10/10 green**:

- allowlist entries are stripped and empties dropped, so an empty entry can never
  admit a chat-less row
- a row with no `chat` is never an owner decision (explicit, not incidental)
- the cursor is persisted as `{"hashes": [...], "v": 4}`, with in-place upgrade
  from a legacy integer cursor and a bounded set size
- malformed lines, duplicate delivery and a rewritten spool are covered

Negative control (why these tests are worth having): against the **unpatched**
file the same inputs produce 2 messages instead of 1 and an integer cursor. The
tests fail on the old code and pass on the new one.

**Not deployed to 138.** The owner's direction is to stop silent live edits and
land this through a PR, so the live file is untouched and the fix ships with its
test.

## 5. Honest limits

- Two of my own measurement bugs were caught and fixed in this lane: the batched
  metadata probe lost one file's hash lines (per-file fallback added, 16/16), and
  I first read `OFN_OWNER_USER_IDS` from a plain ssh shell that does not carry the
  service's `EnvironmentFile` — which produced a meaningless "0 rows match". The
  numbers in §3 come from reading the real env file, counting only.
- The email and Telegram channels still share one spool file. The fix makes the
  filter explicit and safe; separating the channels is a design change for the PR.
- Three live patches and ten files remain unexported. The PR is the next unit.
- I did not evaluate whether `glass_runner.py`'s +81 lines are correct beyond
  characterising them; that needs its own review with the button parser tested.

## Evidence paths

- `evidence/board138-dirty-probe.txt` · `evidence/RUNTIME-SNAPSHOT-MANIFEST.json`
- `evidence/runtime-snapshot-138/` (16 byte-verified files)
- `evidence/DRIFT-VS-CANONICAL.json` · `evidence/DRIFT-DIFF-SUMMARY.json`
- `pr/state/revenue-drive/owner_reply.py` · `tests/test_owner_inbox_attribution.py`

## Rollback

Nothing was deployed: no rollback is required for this lane. The snapshot itself
is additive under `09-LANES/RUNTIME-EXPORT-20260918/`. If the patched
`owner_reply.py` is later deployed, the pre-deploy file is recoverable from
`evidence/runtime-snapshot-138/state__revenue-drive__owner_reply.py`
(sha256 in the manifest).

## Next actions

1. **PR `LANE-20260918-RUNTIME-EXPORT`** — three drifted files as real diffs
   against `ae187e03`, plus the absent files, with paired tests per patch
   (notify retry and gate flip are straightforward; the button parser needs its
   own test) and the preimage receipts above.
2. Include the `owner_reply` fix in that same PR.
3. 138 keeps running unmodified until the PR lands.
4. `A2` still needs the owner's Shopify scope change; `consent reconcil` and the
   W1 verdict (timer 09:20Z, finalizer 09:25Z) are watched, not touched.
