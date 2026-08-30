#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Standalone test for the claims ledger.  Run:  python tools/test_claims_ledger.py

Asserts (per the ledger's contract):
  1. every adr/ADR-*.md yields EXACTLY one row in CLAIMS_LEDGER.csv;
  2. no row has an empty claim or an empty verdict;
  3. every machine-verdict row (INTEGRATE / OPTIMIZE / REJECTED) carries a
     NUMERIC primary_value (extracted, never invented);
  4. the CSV round-trips: parse -> re-serialize == the exact bytes on disk,
     AND a fresh deterministic rebuild from the sources reproduces the file.

Stdlib-only, no pytest. Exit code 0 = green, 1 = failure.
"""

from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
ROOT = TOOLS_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))

import build_claims_ledger as bcl  # noqa: E402

CSV_PATH = ROOT / "CLAIMS_LEDGER.csv"
MACHINE_VERDICTS = {"INTEGRATE", "OPTIMIZE", "REJECTED"}
ALLOWED_VERDICTS = MACHINE_VERDICTS | {"DISCARD", "accepted", "FAIL-by-design"}

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    status = "ok " if cond else "FAIL"
    print(f"  [{status}] {msg}")
    if not cond:
        _failures.append(msg)


def main() -> int:
    print("test_claims_ledger")

    check(CSV_PATH.exists(), "CLAIMS_LEDGER.csv exists (run tools/build_claims_ledger.py first)")
    if not CSV_PATH.exists():
        return 1

    # normalize line endings so a git autocrlf checkout cannot fail the
    # byte-level round-trip (the builder always emits LF)
    raw = CSV_PATH.read_bytes().decode("utf-8").replace("\r\n", "\n")
    parsed = list(csv.reader(io.StringIO(raw)))
    check(len(parsed) >= 2, "CSV has a header and at least one data row")
    header, data = parsed[0], parsed[1:]

    # -- schema ------------------------------------------------------------ #
    check(header == bcl.COLUMNS, f"header == {bcl.COLUMNS}")
    check(all(len(r) == len(bcl.COLUMNS) for r in data),
          "every row has exactly one cell per column")
    rows = [dict(zip(header, r)) for r in data]
    check(len(rows) >= 16, f"at least 16 rows (found {len(rows)})")

    # -- 1. exactly one row per ADR file ------------------------------------ #
    adr_files = sorted(p.name for p in (ROOT / "adr").glob("ADR-*.md"))
    check(len(adr_files) > 0, "adr/ADR-*.md files exist on disk")
    expected_ids = sorted("ADR-" + n.split("-")[1] for n in adr_files)
    actual_ids = sorted(r["claim_id"] for r in rows if r["claim_id"].startswith("ADR-"))
    check(actual_ids == expected_ids,
          f"every ADR file yields exactly one row ({len(expected_ids)} ADRs)")
    src_by_id = {("ADR-" + n.split("-")[1]): f"adr/{n}" for n in adr_files}
    check(all(r["source"] == src_by_id[r["claim_id"]]
              for r in rows if r["claim_id"].startswith("ADR-")),
          "each ADR row's source column points at its own ADR file")

    # -- 2. no empty claim / verdict ---------------------------------------- #
    check(all(r["claim"].strip() and r["claim"] != bcl.UNKNOWN for r in rows),
          "no row has an empty/unknown claim")
    check(all(r["verdict"].strip() for r in rows), "no row has an empty verdict")
    check(all(r["verdict"] in ALLOWED_VERDICTS for r in rows),
          f"every verdict is one of {sorted(ALLOWED_VERDICTS)}")

    # -- 3. machine verdicts carry a numeric primary_value ------------------ #
    def is_num(s: str) -> bool:
        try:
            float(s)
            return True
        except ValueError:
            return False

    machine_rows = [r for r in rows if r["verdict"] in MACHINE_VERDICTS]
    check(len(machine_rows) > 0, "there is at least one machine-verdict row")
    for r in machine_rows:
        check(is_num(r["primary_value"]),
              f"{r['claim_id']} ({r['verdict']}) has numeric primary_value "
              f"({r['primary_value']!r})")

    # -- 4a. round-trip: parse -> re-serialize == bytes on disk ------------- #
    reserialized = bcl.serialize_rows(rows)
    check(reserialized == raw, "CSV round-trips (parse -> serialize == file bytes)")

    # -- 4b. deterministic rebuild reproduces the committed artifact -------- #
    rebuilt = bcl.serialize_rows(bcl.build_rows())
    check(rebuilt == raw, "fresh rebuild from adr/ + specs/ reproduces the CSV")

    # -- bonus lattice sanity ------------------------------------------------ #
    fail_rows = [r for r in rows if r["verdict"] == "FAIL-by-design"]
    check(len(fail_rows) >= 1, "at least one intentionally-failing spec row")
    check(all(r["evidence_tag"] in ("FACT", "EST", bcl.UNKNOWN) for r in rows),
          "evidence_tag is FACT, EST, or unknown (never invented)")

    if _failures:
        print(f"RESULT: FAIL ({len(_failures)} failing check(s))")
        return 1
    print(f"RESULT: PASS ({len(rows)} rows, {len(machine_rows)} machine verdicts)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
