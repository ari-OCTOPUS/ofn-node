# MIRROR-RECEIPT-SCHEMA-V1 — OCTOPUS money mirror 138→182

**Lane:** S1-PARALLEL-ATTACK-V1 / L-G · **Date:** 2026-09-17 · GOV_VERSION=V8 · LADDER=L2
**Status:** IMPLEMENTED + ENFORCED (receiver `octopus-mirror-receive` v2 on 182, sender `push.sh` v2 on 138)

## 1. Charter fields (owner mission L-G) → implemented names

Charter example used `prev_manifest_sha` / `scope_sha`; implemented as
`prev_manifest_sha256` / `scope_sha256` (algorithm explicit). All charter fields
are inside the SIGNED body, plus identity/namespace/policy binding:

```json
{
  "schema": "octopus-mirror-manifest.v1",
  "mirror_id": "S1-MONEY-138-182",
  "namespace": "octopus-mirror-manifest",
  "epoch": 1,
  "sequence": 17,
  "prev_manifest_sha256": "<hex64 of previous accepted manifest.json, GENESIS at 1>",
  "sent_at_utc": "2026-09-18T03:30:00Z",
  "sender": "node-138",
  "receiver": "node-182-witness",
  "scope_sha256": "<sha256 over sorted 'path sha256\\n' lines>",
  "files_count": 7,
  "policy_version": "mirror-policy-v2-20260917",
  "policy_sha256": "<sha256 of the canonical POLICY_SPEC JSON, identical literal on both nodes>",
  "files": [{"path": "api-budget/budget-ledger.jsonl", "sha256": "…", "bytes": 64145}]
}
```

Signed with the 138 `mirror-sign` ed25519 key, namespace `octopus-mirror-manifest`,
verified on 182 against `trusted/allowed_signers` (OpenSSH 10 stdin contract).

## 2. Receiver enforcement (all → explicit REJECTED receipt + quarantine, never silent no-op)

| Rule | Reason string |
|---|---|
| byte-identical manifest re-push | `duplicate_manifest:<sha16>` |
| same data under a fresh manifest (scope equal to last accepted) | `duplicate_manifest_scope:<sha16>` |
| duplicate path inside one manifest | `duplicate_manifest_entry:<path>` |
| sequence < ledger+1 | `sequence_stale` |
| sequence > ledger+1 | `sequence_gap` |
| prev hash ≠ ledger | `prev_hash_mismatch` |
| epoch ≠ ledger | `epoch_mismatch` |
| sent_at older than 48h | `stale_manifest` |
| sent_at more than 15min ahead | `future_manifest` |
| symlink / device / FIFO / non-regular | `symlink_rejected` / `special_file_rejected` |
| path outside allowlist, `..`, absolute | `path_not_allowlisted` |
| extension not in {json, jsonl} class | `extension_class_rejected` |
| payload file absent from manifest | `file_not_in_manifest` |
| manifest entry missing on disk | `file_missing` |
| per-file / total / count caps | `size_cap_exceeded` / `total_cap_exceeded` / `count_cap_exceeded` |
| scope recomputed ≠ claimed | `scope_mismatch` |
| files_count lie | `files_count_mismatch` |
| wrong identity/policy | `mirror_id_mismatch` / `sender_identity_mismatch` / `namespace_mismatch` / `policy_version_mismatch` / `policy_digest_mismatch` / `schema_mismatch` |
| bad signature | `manifest_signature_invalid` |
| unreadable receiver ledger | `receiver_ledger_unreadable` (fail-closed) |

## 3. Ledger + policy

- Receiver state: `/var/lib/mirror-138/state/ledger.json` — epoch, sequence,
  last_manifest_sha256, last_scope_sha256; atomic tmp+rename+fsync, advanced
  AFTER the bundle is published (crash between publish and ledger wedges the
  sequence with an explicit `sequence_stale` + quarantine hint — operator heals;
  never silently re-accepts).
- Sender state: `/home/ari/octopus-mirror/state/sender-ledger.json` — advanced
  ONLY on a receiver-accepted receipt (chains via receiver's manifest_sha256).
- POLICY_SPEC (caps: 64 files / 50MiB file / 200MiB total / 48h age / 15min skew /
  quarantine cap 100) is a byte-identical literal in both scripts; its sha256 is
  carried inside every signed manifest.
- Receipt policy text is unchanged and mandatory: **RECEIVED + HASH-MATCH ONLY;
  REPLAY-VALID NOT CLAIMED (S1-GAP-02C)**.
- NO bridge to replay: the receiver imports/invokes no sensorium/replay
  machinery (statically checked by test N21).

## 4. Epoch bump runbook (manual, witnessed)

Epoch changes only by operator edit of BOTH ledgers (sender+receiver) with the
same new epoch, sequence reset to 0/GENESIS, recorded as a receipt. Never done
by sender or receiver code.

## 5. Verification evidence (2026-09-17)

- Negative suite: 23/23 PASS (`test_receiver_negative.py`, throwaway home).
- Live first receipt: seq 1, `0628dafd…`, 7 files, both ledgers chained.
- Live duplicate push: REJECTED `duplicate_manifest_scope`, bundle quarantined
  (`quarantine/20260917T082313Z-duplicate-manifest-scope-4a5166c3a1f0b`).
- Hygiene: unrestricted `dbg-mirror-test` key removed from authorized_keys
  (backup kept); only the forced-command key remains.
