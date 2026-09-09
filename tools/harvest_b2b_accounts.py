#!/usr/bin/env python3
"""Run the multi-source B2B account discovery agent against the painting store.

Usage:

    python tools/harvest_b2b_accounts.py --dry-run --max-candidates 50
    python tools/harvest_b2b_accounts.py                      # full, unlimited, writes

DB resolution order: --db argument, OFN_PAINTING_DB environment variable,
then the node's default state directory (ofn.config.load().painting_path) —
the same convention tools/ingest_buynsw_batch.py already uses.

--max-candidates and --dry-run are OPERATIONAL controls for a controlled
first run; they are not read anywhere inside ofn.agents.b2b_discovery's
identity-resolution or normalization logic, so a second run with a higher
(or no) --max-candidates and without --dry-run exercises the exact same
code path against a larger candidate set — the discovery capability itself
is never capped in code, only in this invocation.

This tool is COLLECTION-ONLY: it only ever performs HTTP GETs and
LeadStore.create_account upserts. It does not import outbox, does not send
email/SMS, and does not submit any form.

Exit codes: 0 = DONE, 1 = operational error (bad DB path, etc).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ofn.adapters.lead_store import LeadStore                        # noqa: E402
from ofn.agents import b2b_discovery as bd                           # noqa: E402


def default_db() -> str:
    env = os.environ.get("OFN_PAINTING_DB")
    if env:
        return env
    from ofn.config import load
    return load().painting_path


def build_default_collectors(*, enable_web_search: bool, max_queries: int | None) -> list:
    """The default source list for a real run. Deliberately built the same
    way tests build fixture collectors — via the SourceCollector factories —
    so nothing here is special-cased. Add more entries to extend coverage;
    nothing else in ofn.agents.b2b_discovery needs to change.

    The real backend is ofn.agents.b2b_discovery.duckduckgo_search: a
    genuine, robots-permitted (verified live against html.duckduckgo.com's
    own robots.txt, a different host from duckduckgo.com/www.duckduckgo.com
    with a different policy), transparently-identified search source. It
    goes through the same RobotsGate/HostThrottle/fetch_url every other
    fetch in this module uses — no special-casing for this one source.
    """
    collectors = []
    if enable_web_search:
        robots = bd.RobotsGate()
        throttle = bd.HostThrottle()
        search = bd.duckduckgo_search(robots=robots, throttle=throttle)
        # Same robots/throttle instances as the search backend above, so
        # enrichment fetches to a candidate's own site are governed by the
        # exact same per-host politeness as everything else — not a second,
        # looser fetch path.
        enrich = bd.make_website_enricher(fetch=bd.fetch_url, robots=robots, throttle=throttle)
        collectors.append(bd.make_query_search_collector(
            "web_search_b2b_prospects", search=search, max_queries=max_queries,
            enrich=enrich))
    return collectors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Discover B2B painting-prospect accounts from public "
                    "sources and upsert them into painting_b2b_accounts.")
    parser.add_argument("--db", default=None,
                        help="painting.sqlite path (default: OFN_PAINTING_DB "
                             "or the node state dir)")
    parser.add_argument("--max-candidates", type=int, default=None,
                        help="Operational cap on candidates considered this "
                             "run. Omit for no cap (default: unlimited).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run the full discovery/normalize/dedup "
                             "pipeline and report what WOULD change, "
                             "without writing to the store.")
    parser.add_argument("--no-web-search", action="store_true",
                        help="Skip the search-based collector entirely.")
    parser.add_argument("--max-queries-per-source", type=int, default=12,
                        help="Operational cap on how many of the "
                             "region x industry search queries this run "
                             "actually fires (default: 12). This is about "
                             "not hammering a live search backend with "
                             "hundreds of requests in one invocation, not "
                             "an architectural limit — build_search_queries() "
                             "still generates the full extensible set; pass "
                             "a higher number (or 0 for unlimited) once "
                             "you're ready for a larger run.")
    args = parser.parse_args(argv)

    max_queries = None if args.max_queries_per_source == 0 else args.max_queries_per_source
    collectors = build_default_collectors(
        enable_web_search=not args.no_web_search, max_queries=max_queries)

    store = LeadStore(args.db or default_db())
    try:
        report = bd.run_discovery(
            store, collectors,
            max_candidates=args.max_candidates,
            dry_run=args.dry_run,
        )
    finally:
        store.close()

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("", file=sys.stderr)
    print("=== Final run report ===", file=sys.stderr)
    print(f"Sources checked: {report['sources_checked']}", file=sys.stderr)
    print(f"Domains checked: {report['domains_checked']}", file=sys.stderr)
    print(f"Candidates discovered: {report['candidates_discovered']}", file=sys.stderr)
    print(f"New accounts created: {report['new_accounts_created']}", file=sys.stderr)
    print(f"Existing accounts enriched: {report['existing_accounts_enriched']}", file=sys.stderr)
    print(f"Duplicates prevented: {report['duplicates_prevented']}", file=sys.stderr)
    print(f"Possible duplicates flagged for review: {report['possible_duplicates_flagged']}", file=sys.stderr)
    print(f"Websites verified: {report['websites_verified']}", file=sys.stderr)
    print(f"Contacts found: {report['contacts_found']}", file=sys.stderr)
    print(f"Not found: {report['not_found']}", file=sys.stderr)
    print(f"Robots disallowed: {report['robots_disallowed']}", file=sys.stderr)
    print(f"403/429 parked: {report['blocked_403_429']}", file=sys.stderr)
    print(f"Errors: {len(report['errors'])}", file=sys.stderr)
    if report["top_sources"]:
        print("Top sources:", file=sys.stderr)
        for row in report["top_sources"]:
            print(f"  {row['source_id']}: {row['new_accounts']} new", file=sys.stderr)
    return 0 if report.get("status") == "DONE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
