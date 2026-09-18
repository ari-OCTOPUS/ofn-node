#!/usr/bin/env python3
"""Discover public business contact numbers for painting_b2b_accounts leads.

Safe by default: without --apply this runs the full research pipeline and
records the evidence/state it found, but does NOT touch the accounts table.
Reaching the owner's call list is an explicit decision.

    python tools/enrich_contacts.py --max 5 --verbose         # research only
    python tools/enrich_contacts.py --max 5 --apply           # + append contacts
    python tools/enrich_contacts.py --only-no-phone --max 20 --apply
    python tools/enrich_contacts.py --lessons                 # performance model
    python tools/enrich_contacts.py --report                  # what is on record

Resumable by construction: progress is checkpointed to
painting_enrichment_state after every lead, and target selection skips leads
already settled, so re-running after a crash continues rather than repeating.

Collection-only. Performs HTTP GETs and writes to the local painting store.
Sends nothing, contacts nobody.

Exit codes: 0 = completed, 1 = operational error.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import sys
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ofn.enrichment import evidence as ev            # noqa: E402
from ofn.enrichment import lessons as ls             # noqa: E402
from ofn.enrichment import phones as ph              # noqa: E402
from ofn.enrichment import researcher as rs          # noqa: E402
from ofn.enrichment import strategy as st            # noqa: E402


def default_db() -> str:
    env = os.environ.get("OFN_PAINTING_DB")
    if env:
        return env
    local = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "painting.sqlite")
    if os.path.exists(local):
        return local
    from ofn.config import load
    return load().painting_path


def backup(db_path: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    dest = f"{db_path}.bak-enrich-{stamp}"
    shutil.copy2(db_path, dest)
    os.chmod(dest, 0o600)
    return dest


def _print_report(rep: dict) -> None:
    print("\n" + "=" * 68)
    print(f"Run ID:    {rep['run_id']}")
    print(f"Started:   {rep['started']}")
    print(f"Finished:  {rep['finished']}")
    print(f"Mode:      {'APPLY (accounts updated)' if rep['apply'] else 'RESEARCH ONLY (no account writes)'}")
    print()
    print(f"Companies processed:        {rep['processed']}")
    print(f"Companies skipped (target): {rep['skipped']}")
    print()
    print("Contacts by tier:")
    print(f"  P0 personal mobile (named):  {rep['tier_counts'].get(ph.TIER_P0, 0)}")
    print(f"  P1 mobile (unattributed):    {rep['tier_counts'].get(ph.TIER_P1, 0)}")
    print(f"  P2 direct office:            {rep['tier_counts'].get(ph.TIER_P2, 0)}")
    print(f"  P3 general/switchboard:      {rep['tier_counts'].get(ph.TIER_P3, 0)}")
    print()
    print("Outcomes:")
    for k, v in sorted(rep["outcomes"].items(), key=lambda kv: -kv[1]):
        print(f"  {k:34s} {v}")
    print()
    print("Stop reasons:")
    for k, v in sorted(rep["stop_reasons"].items(), key=lambda kv: -kv[1]):
        print(f"  {k:46s} {v}")
    print()
    print(f"Average requests per lead:  {rep['avg_requests']:.1f}")
    print(f"Accounts updated:           {rep['accounts_updated']}")
    if rep["high_value"]:
        print("\nHigh-value contacts found:")
        for h in rep["high_value"]:
            print(f"  {h['business_name']}")
            print(f"    {h['person'] or '(unattributed)'} "
                  f"{('- ' + h['role']) if h['role'] else ''}")
            print(f"    {h['raw']}  [{h['tier']}]  conf={h['confidence']}")
            print(f"    source: {h['source_url']}")
    else:
        print("\nHigh-value contacts found: none this run")
    print("=" * 68)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Find public contact numbers for B2B painting leads.")
    p.add_argument("--db", default=None)
    p.add_argument("--max", type=int, default=10,
                   help="How many LEADS to process this run (default 10). "
                        "This is a lead count, not a per-lead search cap.")
    p.add_argument("--request-budget", type=int, default=rs.DEFAULT_REQUEST_BUDGET,
                   help=f"Max HTTP requests per lead (default "
                        f"{rs.DEFAULT_REQUEST_BUDGET}). Operational guard only; "
                        f"the stopping policy normally ends a lead first.")
    p.add_argument("--only-no-phone", action="store_true",
                   help="Group A only: leads with no phone at all.")
    p.add_argument("--only-no-mobile", action="store_true",
                   help="Group B only: leads with a phone but no mobile.")
    p.add_argument("--include-backed-off", action="store_true",
                   help="Also retry leads already settled as 'no public number'.")
    p.add_argument("--apply", action="store_true",
                   help="Append found contacts to painting_b2b_accounts. "
                        "Without this, nothing is written to the accounts table.")
    p.add_argument("--dry-run", action="store_true",
                   help="Research and print, writing NEITHER accounts nor "
                        "evidence/state. Use to preview a run.")
    p.add_argument("--no-pdf", action="store_true", help="Skip PDF sources.")
    p.add_argument("--lessons", action="store_true",
                   help="Print the derived source-performance model and exit.")
    p.add_argument("--report", action="store_true",
                   help="Print what is already on record and exit.")
    p.add_argument("--json", action="store_true", help="Emit the run report as JSON.")
    p.add_argument("--verbose", "-v", action="store_true")
    args = p.parse_args(argv)

    db_path = args.db or default_db()
    if not os.path.exists(db_path):
        print(f"ERROR: database not found: {db_path}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    ev.ensure_schema(conn)
    ls.ensure_seed_lessons()

    if args.lessons:
        print(ls.render_report(conn))
        return 0

    if args.report:
        rows = conn.execute(
            "SELECT business_name, person, role, raw_number, tier, confidence,"
            " source_url FROM painting_contact_evidence WHERE tenant_id='lead'"
            " ORDER BY tier, business_name").fetchall()
        print(f"{len(rows)} contact evidence rows on record\n")
        for r in rows:
            who = f"{r['person']} ({r['role']})" if r["person"] else "(unattributed)"
            print(f"  [{r['tier']:24s}] {r['business_name'][:34]:36s} {who:32s} "
                  f"{r['raw_number']:18s} {r['confidence']:9s} {r['source_url'][:60]}")
        return 0

    targets = st.select_targets(
        conn, limit=args.max, only_no_phone=args.only_no_phone,
        only_no_mobile=args.only_no_mobile,
        include_backed_off=args.include_backed_off)
    all_targets = st.select_targets(
        conn, only_no_phone=args.only_no_phone,
        only_no_mobile=args.only_no_mobile,
        include_backed_off=args.include_backed_off)

    if not targets:
        print("No leads need enrichment under the current filters.")
        return 0

    backup_path = ""
    if args.apply and not args.dry_run:
        backup_path = backup(db_path)
        print(f"Backed up {db_path} -> {backup_path}")

    run_id = uuid.uuid4().hex[:12]
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"Run {run_id}: {len(targets)} of {len(all_targets)} eligible leads "
          f"({'DRY-RUN' if args.dry_run else ('APPLY' if args.apply else 'research only')})")

    researcher = rs.ContactResearcher(
        conn, run_id=run_id, request_budget=args.request_budget,
        read_pdfs=not args.no_pdf, verbose=args.verbose)
    if researcher.pdf_parser_missing:
        print("  note: no PDF parser importable (pypdf); PDF sources skipped "
              "and recorded as unexplored, not as 'nothing found'.")

    tier_counts: dict[str, int] = {}
    outcomes: dict[str, int] = {}
    stop_reasons: dict[str, int] = {}
    high_value: list[dict] = []
    total_requests = 0
    accounts_updated = 0

    for i, t in enumerate(targets, 1):
        print(f"[{i}/{len(targets)}] {t.business_name[:52]:54s} "
              f"grp={t.group} seg={t.segment or '-'}")
        evidence_conn = conn
        shadow = None
        if args.dry_run:
            # Research against an in-memory shadow so nothing persists. The
            # provenance lookup below must then read from the SHADOW, not
            # from conn - the first live dry-run reported every contact as
            # "conf=unrecorded, source: (blank)" precisely because it looked
            # for evidence in a database the dry-run had deliberately not
            # written to.
            shadow = sqlite3.connect(":memory:")
            shadow.row_factory = sqlite3.Row
            ev.ensure_schema(shadow)
            evidence_conn = shadow
            r = rs.ContactResearcher(
                shadow, run_id=run_id, request_budget=args.request_budget,
                read_pdfs=not args.no_pdf, verbose=args.verbose,
                robots=researcher.robots, throttle=researcher.throttle)
            rep = r.research(t)
        else:
            rep = researcher.research(t)

        total_requests += rep["requests_used"]
        outcomes[rep["outcome"]] = outcomes.get(rep["outcome"], 0) + 1
        stop_reasons[rep["stop_reason"]] = stop_reasons.get(rep["stop_reason"], 0) + 1
        for c in rep["candidates"]:
            tier_counts[c["tier"]] = tier_counts.get(c["tier"], 0) + 1

        print(f"      -> {rep['outcome']:30s} best={rep['best_tier'] or '-':24s} "
              f"reqs={rep['requests_used']} stop={rep['stop_reason']}")

        if rep["candidates"] and args.apply and not args.dry_run:
            cands = [ph.PhoneCandidate(
                raw=c["raw"], e164=c["e164"], kind=c["kind"], tier=c["tier"],
                person=c["person"], role=c["role"]) for c in rep["candidates"]]
            added = rs.apply_to_account(conn, account_id=t.account_id,
                                        candidates=cands, dry_run=False)
            if added:
                accounts_updated += 1
                print(f"      += {' | '.join(added)}")

        seen_hv: set[tuple] = set()
        for c in rep["candidates"]:
            if c["tier"] in (ph.TIER_P0, ph.TIER_P1):
                if (t.account_id, c["e164"]) in seen_hv:
                    continue          # one contact, however many pages showed it
                seen_hv.add((t.account_id, c["e164"]))
                row = evidence_conn.execute(
                    "SELECT source_url, confidence FROM painting_contact_evidence"
                    " WHERE account_id=? AND e164=? ORDER BY discovered_at DESC LIMIT 1",
                    (t.account_id, c["e164"])).fetchone()
                high_value.append({
                    "business_name": t.business_name, "person": c["person"],
                    "role": c["role"], "raw": c["raw"], "tier": c["tier"],
                    "source_url": row["source_url"] if row else "",
                    "confidence": row["confidence"] if row else "unrecorded"})

        if shadow is not None:
            shadow.close()

    report = {
        "run_id": run_id, "started": started,
        "finished": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "apply": bool(args.apply and not args.dry_run),
        "processed": len(targets), "skipped": len(all_targets) - len(targets),
        "tier_counts": tier_counts, "outcomes": outcomes,
        "stop_reasons": stop_reasons,
        "avg_requests": (total_requests / len(targets)) if targets else 0.0,
        "accounts_updated": accounts_updated, "high_value": high_value,
        "backup": backup_path,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_report(report)
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
