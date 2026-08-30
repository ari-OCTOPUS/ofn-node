# ARCHIVE PACKET — C4 (propose-only; owner approval required for any physical move/delete)

> Rule (owner): حذف فیزیکی داده/فایل بدون مالک ممنوع. This packet **proposes**; it does not delete.
> Evidence base: read-only cartographer sweep (file:line) + live on-disk artifact reality.
> Rollback for every item: it stays exactly where it is until you approve; a "move" is `git mv`
> (reversible), never `rm`. Nothing here is money/secret/identity.

## Method
An item qualifies as **archive-candidate** only if: (a) 0 live (non-test) importers/callers, AND
(b) its on-disk artifact is absent or frozen, AND (c) it is not a declared SoT in the
SOURCE-OF-TRUTH-CHARTER. Anything failing a test stays KEEP.

## A. Dead code paths (0 live importers — evidence)

| item | evidence | on-disk | proposed action | rollback |
|---|---|---|---|---|
| `chord/` (whole pkg) | only importer `doctor/doctor.py:767-768`, lazy, behind `OCTOPUS_WIRE_CHORD_SHADOW` (unset) | `chord/state/chord-ledger.jsonl` **never created** → never executed live | **quarantine**: keep code, leave flag off; revisit if doctor-shadow is ever armed. If still dark in 30d → `git mv chord/ _archive/chord/` | restore flag / `git mv` back |
| `vault_updater.py` | 0 importers (only tests + a string label in `code_autonomy.py:38` allowlist, not an import) | propose engine, unwired | **ARCHIVE-candidate** → `git mv _ops/vault_updater.py _archive/` after owner ok | `git mv` back |
| `vault_updater_apply.py` | 0 importers; writes `VAULT_AUTO_WRITE` note but no caller | unwired applier | **ARCHIVE-candidate** (with vault_updater.py) | `git mv` back |
| `vault_updater_gate.py` | imported only by `vault_updater_apply.py` (itself dead) | — | **ARCHIVE-candidate** iff the other two go; else KEEP | `git mv` back |

## B. Frozen projection artifacts (write path unwired)

| item | evidence | proposed action |
|---|---|---|
| `state/reviews/*.json` (4 files) | `review_bus.submit_review` has **0 non-test callers**; files frozen 2026-07-10; readers exist (`phase_gate.py:321`) | **KEEP the files** (readers live) but mark `review_bus.py` writer **archive-candidate**; do NOT delete reviews (a live reader consumes them) |
| `state/chrono.db.pre-v4` | my Phase-0 migration rollback anchor | **KEEP until owner confirms C-series stable**, then delete (owner) |

## C. Root cruft (safe cleanup candidates — owner confirms)

| item | evidence | proposed action |
|---|---|---|
| `_ops/2026-07-21` | 0-byte empty file (bad-command artifact) | `git rm` after owner ok (empty; zero risk) |
| stray dir literally named `F:backup` | path-bug artifact (backslash mishandled) | inspect contents → `git mv`/remove after owner ok |
| `_ops/state/_wtest.py` (4 B), `_ops/state/_probe_write_test.txt` | test scratch left in state/ | remove after owner ok |

## D. Honesty fixes already applied (no owner needed — additive)
- `durable_journal.py`: removed the stale "ORPHAN 2026-07-16: zero live callers" implication (added a note: it now has 2 live callers via C2-D). It is **NOT** an archive-candidate.

## NOT archived (verified live — for the record)
`baseline.py` (2 importers), `germline.py` (`wiring.py:138`), `idea_graph.py` (`wiring.py:1553`),
`checkpoint.py` (reachable via unified_bus), `cardiac.py` (heart, behind WIRE_BIO),
`durable_journal.py` (now wired), `unified_bus.py` (substrate, dormant not dead),
`events.py` + `review_bus` readers (live dashboard/phase-gate), all SoT stores.

## One owner decision
Approve moving group **A** (dead vault_updater* + chord quarantine→archive) and group **C**
(root cruft) to `_archive/` via `git mv` / `git rm`? Group **B** reviews stay (live reader).
Until you say yes, everything remains in place.
