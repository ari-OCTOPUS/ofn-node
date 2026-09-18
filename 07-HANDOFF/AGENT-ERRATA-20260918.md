# AGENT ERRATA — 2026-09-18 (owner: «به ایجنتم اشتباهاتشو بگو»)

Written by the agent (L) about its own work, for the agent's next session. Each line is a real
mistake that was caught, what the truth was, and the rule it changes. Nothing here is cosmetic.

## Claims that were wrong (measured later)
1. **«۱۰۰ و ۱۶۰ پشت دیوار اعتبارنامه‌اند»** — recorded in an earlier memory and repeated to the owner.
   **Truth (measured 2026-09-18):** both are live NATS leaves; the laptop reached both as `root` with the
   piggybank key. *Rule: a memory line about access is stale until re-probed; the description field said
   "7/7 online" while the body still said "BLOCKED" — read the whole file, then probe.*
2. **«JetStream مصرف‌کننده ندارد»** — said to the owner in the same report.
   **Truth:** the *telemetry* stream has a durable consumer `vault-pulse` (`fleet-vault-consumer.py`);
   the "0 consumers" note belonged to the **fleet-job bus** (`SHADOW_LOCAL_JSONL`). *Rule: name the
   stream/subject when reporting a consumer count; jsz fields I fail to parse are not zero.*
3. **`systemd-logind` masking labelled a defect.** **Truth:** the same `/dev/null` symlink exists on
   138, 182, 114 and 193 with the same provisioning date — deliberate fleet hardening.
   *Rule: before calling something broken, check two more nodes; fleet-wide + same date = design.*

## Process mistakes (all caught by my own tests/probes)
4. **A2 inventory fix kept only an aggregate pre-image** (29 zero variants of 48 active products); no
   per-item list → rollback is therefore aggregate. *Rule: capture the item list before a bulk write.*
5. **Dropped 22 dedupe keys at once** (`MONEY-BATCH@*` in `owner-ask-sent.json`) instead of only the
   current card's key. Harmless but over-broad. *Rule: mutate the narrowest possible scope.*
6. **Tested a service-shaped loop by hand** → `NO_EMAIL_ADDRESS_OR_CREDS`, a false failure: a manual
   `python3` run lacks the unit's `EnvironmentFile` (GMAIL_*). Re-run through `systemctl start` proved
   the real path. *Rule: test a service through its service.*
7. **A transient `URLError` silently ate one real decision card.** *Rule (now implemented): every
   owner-facing send retries; a failed send is recorded, never swallowed.*
8. **`pgrep -fa apply_signed_inbound` matched its own command line** → the W1 collector would have
   declared a false FAIL on a clean node. Fixed with the `[a]pply_signed_inbound` bracket trick +
   wrapper filtering; caught only because the collector was dry-run on real data first.
   *Rule: dry-run any verdict-producing tool on live data before arming it.*
9. **Two of my own new tests were wrong, not the code**: a retry regex that demanded `for ... in (1, 2)`
   (the code uses `range(attempts)`), and a by-path module loader that broke `@dataclass` because the
   module was not registered in `sys.modules`. *Rule: when a test fails, first ask whether the test
   encodes the contract or just my mental image of the implementation.*
10. **Wrong host in a probe**: ran `systemctl status octopus-gap001-*` while SSH'd to **138** and
    reported empty output as if the units were missing. *Rule: every remote claim names its host.*
11. **Wrong port list in a listener check** (`ss … | grep -E "8788|8080|8000|8774"` while hunting for
    8791) → "nothing is listening" was my grep's fault, not the system's. *Rule: grep the exact value.*
12. **Earlier session (kept for the record):** a commit message said tests were green when the suite
    was red (`pytest | tail` hid the exit code). Fixed then with an honest follow-up commit; the
    standing rule is now: always read `PYTEST_EXIT`, never pipe a test run through `tail` alone.

## What is verified about today's work (so the next session does not have to re-derive it)
- PR **#266** (`lane/runtime-export-20260918`, head `50f8727708b8`): 11 commits, one per file, all nine
  files byte-identical to the running files on 138 (source sha256 == git index blob sha256), tests
  `tests/test_runtime_export_20260918.py` **14 passed / exit 0**, `require-fresh-base` **pass**,
  `hygiene` **pass**; only `require-independent-approval` is red (it needs a human independent review,
  which is exactly what it is for).
- The five runtime changes were live on 138 hours before they reached git — that gap is the thing this
  export closes; from now on, a runtime change without a paired branch is an incomplete change.
