# Contact-enrichment agent

Finds publicly-published business contact numbers for `painting_b2b_accounts`
leads that have none (or only a switchboard), records where every number came
from, and learns which research paths actually pay off.

Collection-only: HTTP GETs plus writes to the local painting store. It sends
nothing and contacts nobody.

## Running it

```bash
# research only - records evidence/state, does NOT touch the accounts table
python tools/enrich_contacts.py --max 10 --verbose

# research AND append found contacts to painting_b2b_accounts
python tools/enrich_contacts.py --max 10 --apply

# preview with no writes of any kind
python tools/enrich_contacts.py --max 5 --dry-run

# target groups
python tools/enrich_contacts.py --only-no-phone  --max 20 --apply   # group A
python tools/enrich_contacts.py --only-no-mobile --max 20 --apply   # group B

# what has been learned / what is on record
python tools/enrich_contacts.py --lessons
python tools/enrich_contacts.py --report
```

`--max` counts LEADS, not requests. Per-lead effort is governed by the
stopping policy and capped by `--request-budget` (default 14).

Safety defaults worth knowing:

* nothing reaches `painting_b2b_accounts` without `--apply`;
* `--apply` takes a timestamped backup (`painting.sqlite.bak-enrich-*`) first;
* writes are read-then-append — an existing number is never overwritten, and
  a number already present (compared in normalised form) is never duplicated.

## Scheduling

Deliberately NOT shipped as a unit file in `deploy/systemd/`. That directory
is covered by `tests/test_units.py`, which asserts every unit present there is
also installed by `install.sh`; adding units without editing the installer
would turn a passing assertion red, and the installer is shared deploy
surface. Run it from cron, or add the unit below by hand when the installer
is next touched.

Cron (daily 06:00):

```cron
0 6 * * * cd /home/ari/ofn && /usr/bin/python3 tools/enrich_contacts.py \
    --only-no-phone --max 10 --apply >> /var/log/ofn-enrich.log 2>&1
```

Equivalent systemd pair, if preferred:

```ini
# ofn-enrich.service
[Unit]
Description=OFN B2B contact enrichment
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=/home/ari/ofn
ExecStart=/usr/bin/python3 tools/enrich_contacts.py --only-no-phone --max 10 --apply
MemoryMax=512M
Nice=10
```

```ini
# ofn-enrich.timer
[Unit]
Description=Daily OFN contact enrichment
[Timer]
OnCalendar=*-*-* 06:00:00
Persistent=true
[Install]
WantedBy=timers.target
```

The process loads state, selects targets, researches, verifies, persists and
exits. It needs no terminal and holds no lock between runs.

## Resuming

Resumability is structural rather than a separate checkpoint file. After every
lead, `painting_enrichment_state` records the outcome, the stop reason, the
URLs seen and the people found. Target selection then excludes leads already
settled, so re-running after a crash continues from where it stopped. A lead
that has come back empty `MAX_ATTEMPTS_BEFORE_BACKOFF` times is retired from
selection (use `--include-backed-off` to force a retry); a lead that was
*blocked* is exempt from that back-off, because a block is a fact about the
host that day, not evidence about whether a number exists.

## Where the data lives

* `painting_contact_evidence` — append-only provenance. One row per
  (number, source URL), carrying the source class, the confidence, the person
  and role if known, any conflict/branch caution, and the actual text snippet
  the number was read from. This is what answers "where exactly did this come
  from".
* `painting_enrichment_state` — per-lead research memory: outcome, stop
  reason, effort, attempts.
* `painting_b2b_accounts.contact_channel` — the human-facing summary the
  owner's digest reads. Capped at 220 characters by `lead_store`, so when
  contacts do not fit whole, the highest-tier ones take the room and the rest
  stay in the evidence table rather than being truncated into corruption.

## Confidence

Derived, not asserted:

| confidence | meaning |
|---|---|
| `verified` | the company's own domain (page or PDF), or a government record |
| `probable` | a trusted third party (association/event/news), or two independent sources agreeing |
| `weak` | a single low-trust source with nothing corroborating it |

`verified_at` is only set when the number was actually read out of a fetched
source by the process; a blank means nobody should treat it as verified.

## Known limitations

* **PDF reading is optional.** The repository ships no dependency manifest and
  is stdlib-only (4GB board). If `pypdf` is importable it is used; if not,
  PDFs are recorded as unexplored rather than as "nothing found". On the
  target board it is currently NOT installed.
* **Search-engine expansion is off by default.** `ContactResearcher` accepts a
  `search` hook, but nothing is wired to it. On this dataset the official site
  is the only source class yielding `verified` confidence, and prior manual
  rounds found third-party results dominated by data-broker and listing pages
  that are either forbidden or near-worthless.
* **Branch ambiguity is flagged, not resolved.** A contact found on a
  company's interstate page is recorded with a `BRANCH CAUTION` note; the
  agent does not try to decide whether it is still useful.
* **`LeadStore.accounts()` clamps to 100 rows** regardless of the `limit`
  argument (`MAX_PAGE`). This agent therefore reads targets with raw SQL.
  Other callers — including `tools/owner_digest.py` — are still subject to
  that cap and silently miss leads beyond the hundredth.
