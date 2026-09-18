#!/usr/bin/env python3
"""One-off correction pass over painting_b2b_accounts rows this repo's own
b2b_discovery agent created BEFORE it learned to extract a real business
name, filter listicle/article pages, and tag its own output.

Scope: only rows whose `notes` contain the discovery agent's own literal
provenance string ("Discovered via search (<source_id>)") are ever touched.
Every one of the 74 hand-researched accounts that predate this agent has a
different notes shape (RELEVANCE:/APPROACH:/VERIFIED, no "Discovered via"
line) and is never matched by this script's selection query — this was
checked against the real DB, not assumed.

For each matched row:
  * an article/listicle page (looks_like_article) -> DELETE. It was never a
    company.
  * otherwise, re-run clean_title_name on the STORED business_name (the
    same logic ofn.agents.b2b_discovery.make_website_enricher now applies
    at discovery time):
      - "" (no reliable segment survives)         -> DELETE
      - a different, better name                  -> UPDATE business_name
      - already fine                                -> keep name as-is
  * every SURVIVING row gets AUTO_DISCOVERY_TAG + CLASSIFICATION stamped
    into notes if not already present (idempotent — safe to re-run), so
    tools/owner_digest.py's --include-unverified filter covers these older
    rows the same way it covers freshly-discovered ones.

Never touches account_id (the row is corrected in place, not recreated —
recreating under a new slug would orphan the old primary key instead of
fixing it) and never re-fetches the network: this is a static, offline
correction of what is already stored, using the SAME pure functions the
fixed discovery agent now applies live. A row whose real name genuinely
needs a fresh network lookup (the page was blocked in a prior run) is
DELETED here, not guessed at, and can be rediscovered by a normal
tools/harvest_b2b_accounts.py run once that source is reachable again.

Usage:
    python tools/cleanup_bad_discovery.py --dry-run     # preview only
    python tools/cleanup_bad_discovery.py               # backs up, then writes
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ofn.adapters.lead_store import LeadStore                          # noqa: E402
from ofn.agents import b2b_discovery as bd                             # noqa: E402

TENANT = "lead"
SELECTION_LIKE = "%Discovered via search (%"

# A stale artifact from a code path this session already removed from
# ofn.agents.b2b_discovery: an earlier version appended " [domain.tld]" to
# a generic title (e.g. "Home [fma.com.au]") instead of dropping the
# candidate outright. Confirmed live during this fix: fma.com.au's real
# <title> is "Home" with no og:site_name/JSON-LD, so the correct outcome IS
# dropping it — the bracket suffix must be stripped BEFORE the normal
# reliability check runs, or "fma" (not a generic word) makes the whole
# corrupted string look reliable.
_DOMAIN_BRACKET_RE = re.compile(r"\s*\[[a-z0-9.-]+\.[a-z]{2,}\]\s*$", re.IGNORECASE)


def _strip_domain_bracket_artifact(name: str) -> str:
    return _DOMAIN_BRACKET_RE.sub("", name).strip()


def default_db() -> str:
    env = os.environ.get("OFN_PAINTING_DB")
    if env:
        return env
    from ofn.config import load
    return load().painting_path


def _backup(db_path: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = f"{db_path}.backup-before-cleanup-{stamp}"
    shutil.copy2(db_path, dest)
    os.chmod(dest, 0o600)          # backups are owner-private, no exception
    return dest


def _classification_for(row: dict, name: str) -> str:
    """Best available evidence for CLASSIFICATION, using what is already
    stored — this is an offline correction pass, not a re-discovery run, so
    it never fetches the network for this."""
    text = " ".join([name, str(row.get("notes") or "")])
    return bd.classify_candidate(segment=str(row.get("segment") or ""), text=text)


def _tag_notes(notes: str, classification: str) -> str:
    """Append AUTO_DISCOVERY_TAG/CLASSIFICATION if not already present.
    Idempotent — running this twice on the same notes changes nothing the
    second time."""
    out = notes
    if bd.AUTO_DISCOVERY_TAG not in out:
        out = (out + " | " if out else "") + bd.AUTO_DISCOVERY_TAG
    if "CLASSIFICATION:" not in out:
        out = out + f" | CLASSIFICATION: {classification}"
    return out[:bd.MAX_TEXT]


def plan(rows: list[dict]) -> dict:
    """Pure: decide DELETE / UPDATE / KEEP for every candidate row. Returns
    the plan plus the actions needed, without touching the store — so this
    is exactly what --dry-run prints, and exactly what the real run
    executes, with no second code path between preview and action."""
    deletes: list[dict] = []
    updates: list[dict] = []
    kept: list[dict] = []
    for row in rows:
        name = _strip_domain_bracket_artifact(str(row.get("business_name") or ""))
        website = str(row.get("website") or "")
        if bd.looks_like_article(url=website, title=name):
            deletes.append({**row, "_reason": "article/listicle page, not a company"})
            continue
        cleaned = bd.clean_title_name(name)
        if not cleaned:
            deletes.append({**row, "_reason": "no reliable name segment in stored title"})
            continue
        classification = _classification_for(row, cleaned)
        new_notes = _tag_notes(str(row.get("notes") or ""), classification)
        if cleaned != name or new_notes != row.get("notes"):
            updates.append({**row, "_new_business_name": cleaned, "_new_notes": new_notes})
        else:
            kept.append(row)
    return {"deletes": deletes, "updates": updates, "kept": kept}


def apply(store: LeadStore, decided: dict, *, now_iso: str) -> None:
    conn = store._conn                                    # noqa: SLF001 — narrow, one-off maintenance script
    conn.execute("BEGIN IMMEDIATE")
    try:
        for row in decided["deletes"]:
            conn.execute(
                "DELETE FROM painting_b2b_accounts WHERE tenant_id = ? AND account_id = ?",
                (TENANT, row["account_id"]))
        for row in decided["updates"]:
            conn.execute(
                "UPDATE painting_b2b_accounts SET business_name = ?, notes = ?, updated_at = ? "
                "WHERE tenant_id = ? AND account_id = ?",
                (row["_new_business_name"], row["_new_notes"], now_iso, TENANT, row["account_id"]))
        for row in decided["kept"]:
            # Nothing changed for this row (name already fine, tags already
            # present from a prior cleanup run) — no write needed.
            pass
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Correct or remove painting_b2b_accounts rows created "
                    "by an earlier, name-extraction-buggy run of "
                    "ofn.agents.b2b_discovery.")
    parser.add_argument("--db", default=None)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the plan; write nothing, back up nothing.")
    args = parser.parse_args(argv)

    db_path = args.db or default_db()
    if not args.dry_run:
        backup_path = _backup(db_path)
        print(f"Backed up {db_path} -> {backup_path}", file=sys.stderr)

    store = LeadStore(db_path)
    try:
        rows = [r for r in store.accounts(TENANT, limit=bd.STORE_SCAN_LIMIT)
               if SELECTION_LIKE.strip("%") in (r.get("notes") or "")]
        decided = plan(rows)

        print(f"Auto-discovery rows found: {len(rows)}", file=sys.stderr)
        print(f"  to delete: {len(decided['deletes'])}", file=sys.stderr)
        for r in decided["deletes"]:
            print(f"    DELETE {r['account_id']}: {r['_reason']} "
                 f"(was {r['business_name']!r})", file=sys.stderr)
        print(f"  to correct: {len(decided['updates'])}", file=sys.stderr)
        for r in decided["updates"]:
            print(f"    UPDATE {r['account_id']}: {r['business_name']!r} "
                 f"-> {r['_new_business_name']!r}", file=sys.stderr)
        print(f"  kept as-is (already tagged/correct): {len(decided['kept'])}", file=sys.stderr)

        if args.dry_run:
            print("\n--dry-run: no changes written.", file=sys.stderr)
            return 0

        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        apply(store, decided, now_iso=now_iso)
        print(f"\nDone: {len(decided['deletes'])} deleted, "
             f"{len(decided['updates'])} corrected, "
             f"{len(decided['kept'])} kept unchanged.", file=sys.stderr)
        return 0
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())
