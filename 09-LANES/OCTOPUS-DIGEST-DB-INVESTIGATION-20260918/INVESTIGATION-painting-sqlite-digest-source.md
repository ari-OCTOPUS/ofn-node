# INVESTIGATION REPORT — painting.sqlite path & digest data source (P0)

**Date:** 2026-09-18 · **Asked by:** Elaheh (via Ari) · **Type:** read-only investigation
**Constraints honoured:** nothing was written, moved, deleted, migrated or restarted; no DB copied; no secrets/PII — paths and row counts only.

## Answer in one line
**The digest runs on no schedule anywhere in the fleet.** The 114-row DB lives only on Elaheh's laptop (`elahe-X550CC`), which is not part of the Octopus fleet — so the owner's call list has been coming from a **manual** run on that machine. Scenario **(C)**, refined: not "a third DB path", but "no automated host at all".

## Evidence

### 1. Is the digest wired to a timer, and where?
| Host | digest unit files | digest timers active |
|---|---|---|
| board138 | **4** (`octopus-owner-digest-morning/evening.{service,timer}`) | **0 — both timers `disabled/inactive`** |
| 100 / 114 / 160 / 180 / 182 / 193 | 0 | 0 |
| this laptop (Armin) | 0 scheduled tasks matching `digest`, 0 digest artifacts in the last 7 days | — |

The two 138 units are **not** the call-list digest: they run
`ofn/agents/owner_digest_emit.py --card-type digest_morning|digest_evening`
(`WorkingDirectory=/home/ari/ofn`), and that script **does not reference painting.sqlite or LeadStore at all** — it builds a Telegram digest from other state. They are also disabled.

### 2. How does `tools/owner_digest.py` resolve its DB?
```
tools/owner_digest.py:67   ap.add_argument("--db", type=str, default="painting.sqlite", ...)
tools/owner_digest.py:73   store = LeadStore(args.db)
ofn/adapters/lead_store.py  def __init__(self, path): self._pool = Pool(path)
```
- The default is a **bare relative filename** → it is resolved by sqlite3 **against the process CWD**.
- The canonical path in code is `ofn/config.py: painting_path() = <state_dir>/painting.sqlite`, with `state_dir = $OFN_STATE_DIR or <default>` — but **the digest does not use it**; only an explicit `--db` overrides.
- ⚠️ **Defect:** sqlite3 *creates* a missing file, then `apply_schema` seeds the schema — so running the digest from a directory without the DB yields a **silently empty call list with no error**. This is a plausible mechanism for an empty-list failure that nobody would notice.

### 3. Every `painting*.sqlite` found (path → row count)
| Host | Path | `painting_b2b_accounts` |
|---|---|---|
| 138 | `backups/lead-outbox-20260807-004347/painting.sqlite` | **0 rows** (the 2026-08-07 backup) |
| 160 | `/tmp/pytest-of-root/pytest-*/…/painting.sqlite` | ERR (test fixtures, different schema) |
| 193 | `/tmp/pytest-of-root/pytest-*/…/painting.sqlite` | ERR (test fixtures) |
| 100 / 114 / 180 / 182 | none found (depth ≤6) | — |
| Armin laptop (F:, C:\Users) | none found (depth ≤6) | — |
| **elahe-X550CC** | `~/Desktop/OFN_Elahe_repo/ofn-node/painting.sqlite` | **114 rows** (reported by Elaheh; **not reachable from this fleet — unverified here**) |

`painting.sqlite` is gitignored, so no copy has ever travelled through git — consistent with each host holding its own copy or none.

### 4. Is the call-log migration applied on the digest's DB?
- On every **fleet** copy: not applicable — no populated DB exists (0-row backup, plus pytest fixtures of a different schema).
- On the canonical 114-row DB (elahe-X550CC): **unverified from here** → this must be checked on that machine:
  `sqlite3 <db> ".tables" | grep -c painting_call_log ; sqlite3 <db> "select count(*) from v_account_last_call"`
- ⚠️ Related finding: the **runtime copy on 138 does not carry the digest work at all** — `tools/owner_digest.py` there has **no `_MOBILE_RE`** (the mobile classifier is absent). So even if someone ran the digest on 138, the regex fix and the call-log work would not be in it. This is the known 138↔main lineage divergence (covered by `MEGAPROMPT-CONVERGENCE-138`).

### 5. Does the regex fix reach the owner? (step 4.5 of the brief)
Cannot be proven, and the reason is now explicit: the only DB where it could be proven (114 rows) sits on a host outside the fleet, while the host inside the fleet has an empty DB and no classifier. The unit-level proof stands (the fix's own tests pass), but "the owner's next call list shows the 6 extra mobiles" is **unverified** until the DB and the code are on the same host.

## Proposed convergence plan — PROPOSAL ONLY, not executed
1. **Decide the digest host first** (owner decision, not engineering): the digest must run where the populated DB lives, or the DB must move to where the digest runs. Nothing else is trustworthy until this is fixed.
2. Designate **the 114-row DB with the 10 real call outcomes as source of truth** (it is the only copy holding real outcomes).
3. **Copy it to the chosen host only with explicit owner approval** — per the brief, divergent copies with real call history are reconciled deliberately, never overwritten. Before any copy: hash both sides and diff `painting_call_log` row-by-row (date + outcome + account), so no call history can be lost.
4. Make the digest **fail-closed**:
   - require an absolute DB path (`--db` or `$OFN_STATE_DIR`, defaulting to `config.painting_path`), never the bare relative name;
   - **refuse to emit** a digest when `painting_b2b_accounts` returns 0 rows (kills the silent empty-list bug);
   - print the resolved absolute path + row counts in the digest header so the source is always visible.
5. Install the timer **only on the chosen host**, with the absolute path in `Environment=`/`ExecStart`.
6. Add the missing classifier + call-log work to that host's code (or land the convergence mission so 138 and main agree).

## Open owner-decision (flagged, not resolved)
If, during step 3's hash-and-diff, the two DBs turn out to both hold call outcomes that differ → **stop and ask the owner which history wins**; losing real call records silently is not acceptable.
