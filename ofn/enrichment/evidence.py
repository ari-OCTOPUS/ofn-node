"""Structured provenance for every discovered contact, plus per-lead research
state.

Two tables, both created lazily with CREATE TABLE IF NOT EXISTS inside the
existing painting.sqlite — not a second database, and deliberately NOT added
to `ofn/adapters/lead_store.py`'s SCHEMA/MIGRATIONS tuples. That file is
shared production surface other work on this repo is actively editing; a new
append-only table that nothing else reads is safer owned here, and it keeps
this agent removable without a migration to undo.

`painting_contact_evidence` is append-only and is the answer to the question
the spec insists must always be answerable: where exactly did this number
come from? It stores the source URL, the source class, and the actual text
snippet the number was read out of — so a human can re-open the page and see
it, and so a later run can tell corroboration from repetition.

`painting_enrichment_state` is the memory that stops the agent burning the
same effort forever on leads whose numbers are simply not published. It
records what was tried, what happened, and why research stopped.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone

# Source classes, ranked. The ranking is the backbone of the confidence
# model: it encodes "a number on the company's own site is worth more than
# the same number on a scraped listing", which is the whole difference
# between provenance and hearsay.
SRC_OFFICIAL_SITE = "official_site"
SRC_OFFICIAL_PDF = "official_pdf"
SRC_GOV = "government"
SRC_ASSOCIATION = "association_or_event"
SRC_NEWS = "news_or_publication"
SRC_LISTING = "business_listing"
SRC_SEARCH_SNIPPET = "search_snippet"

_SOURCE_RANK = {
    SRC_OFFICIAL_SITE: 100, SRC_OFFICIAL_PDF: 95, SRC_GOV: 85,
    SRC_ASSOCIATION: 70, SRC_NEWS: 55, SRC_LISTING: 35,
    SRC_SEARCH_SNIPPET: 20,
}

CONF_VERIFIED = "verified"
CONF_PROBABLE = "probable"
CONF_WEAK = "weak"

# Outcomes. The spec is explicit that "not found" must not swallow every
# distinct failure, because the right retry policy differs for each: a WAF
# block is worth retrying from a different path, while "this company
# genuinely publishes no mobile" is worth never retrying.
OUT_FOUND = "found"
OUT_NO_PUBLIC_NUMBER = "no_public_number_published"
OUT_SITE_UNREACHABLE = "site_unreachable"
OUT_BLOCKED = "blocked_by_host"
OUT_ROBOTS = "robots_disallowed"
OUT_NO_WEBSITE = "no_website_on_record"
OUT_AMBIGUOUS = "ambiguous_company_identity"
OUT_ERROR = "error"

_EVIDENCE_TABLE = """
CREATE TABLE IF NOT EXISTS painting_contact_evidence (
    evidence_id       TEXT PRIMARY KEY,
    tenant_id         TEXT NOT NULL DEFAULT 'lead',
    account_id        TEXT NOT NULL,
    business_name     TEXT NOT NULL DEFAULT '',
    raw_number        TEXT NOT NULL,
    e164              TEXT NOT NULL,
    kind              TEXT NOT NULL DEFAULT '',
    tier              TEXT NOT NULL DEFAULT '',
    person            TEXT NOT NULL DEFAULT '',
    role              TEXT NOT NULL DEFAULT '',
    source_url        TEXT NOT NULL DEFAULT '',
    source_domain     TEXT NOT NULL DEFAULT '',
    source_type       TEXT NOT NULL DEFAULT '',
    context_snippet   TEXT NOT NULL DEFAULT '',
    confidence        TEXT NOT NULL DEFAULT 'weak',
    corroborations    INTEGER NOT NULL DEFAULT 1,
    conflict_note     TEXT NOT NULL DEFAULT '',
    applied_to_account INTEGER NOT NULL DEFAULT 0,
    run_id            TEXT NOT NULL DEFAULT '',
    discovered_at     TEXT NOT NULL,
    verified_at       TEXT NOT NULL DEFAULT ''
)
"""

_STATE_TABLE = """
CREATE TABLE IF NOT EXISTS painting_enrichment_state (
    account_id        TEXT PRIMARY KEY,
    tenant_id         TEXT NOT NULL DEFAULT 'lead',
    business_name     TEXT NOT NULL DEFAULT '',
    segment           TEXT NOT NULL DEFAULT '',
    last_outcome      TEXT NOT NULL DEFAULT '',
    stop_reason       TEXT NOT NULL DEFAULT '',
    best_tier         TEXT NOT NULL DEFAULT '',
    attempts          INTEGER NOT NULL DEFAULT 0,
    sources_checked   INTEGER NOT NULL DEFAULT 0,
    urls_seen_json    TEXT NOT NULL DEFAULT '[]',
    people_found_json TEXT NOT NULL DEFAULT '[]',
    numbers_found     INTEGER NOT NULL DEFAULT 0,
    last_run_id       TEXT NOT NULL DEFAULT '',
    first_attempt_at  TEXT NOT NULL DEFAULT '',
    last_attempt_at   TEXT NOT NULL DEFAULT ''
)
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Idempotent. Safe on every run and on a database that predates this
    agent entirely."""
    conn.execute(_EVIDENCE_TABLE)
    conn.execute(_STATE_TABLE)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_contact_evidence_account "
                 "ON painting_contact_evidence (tenant_id, account_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_contact_evidence_e164 "
                 "ON painting_contact_evidence (tenant_id, e164)")
    conn.commit()


@dataclass
class Evidence:
    """One number, from one source, with the proof attached."""
    account_id: str
    business_name: str
    raw_number: str
    e164: str
    kind: str
    tier: str
    source_url: str
    source_domain: str
    source_type: str
    context_snippet: str = ""
    person: str = ""
    role: str = ""
    corroborations: int = 1
    conflict_note: str = ""
    tenant_id: str = "lead"
    run_id: str = ""
    discovered_at: str = field(default_factory=_now)

    @property
    def evidence_id(self) -> str:
        """Deterministic: the same number from the same page is the same
        evidence row, so re-running never inflates the corroboration count
        or the audit trail with duplicates."""
        key = f"{self.tenant_id}|{self.account_id}|{self.e164}|{self.source_url}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]

    @property
    def confidence(self) -> str:
        """Concrete and derivable, never a feel.

        verified  the company's own domain (page or PDF) published it, or a
                  government record did - the source *is* the authority on
                  its own contact details.
        probable  a trustworthy third party published it (association, event,
                  news), or two independent weaker sources agree.
        weak      one low-trust source and nothing corroborating it.
        """
        rank = _SOURCE_RANK.get(self.source_type, 0)
        if rank >= 85:
            return CONF_VERIFIED
        if rank >= 55 or self.corroborations >= 2:
            return CONF_PROBABLE
        return CONF_WEAK

    @property
    def verified_at(self) -> str:
        """Only set when the number was actually read out of a fetched source
        by this process. Blank means nobody should treat it as verified."""
        return self.discovered_at if self.context_snippet else ""


def record_evidence(conn: sqlite3.Connection, ev: Evidence) -> bool:
    """Append one evidence row. Returns True when it was new.

    ON CONFLICT DO NOTHING rather than an upsert: evidence is a historical
    record of an observation, and an observation does not get rewritten.
    """
    cur = conn.execute(
        "INSERT INTO painting_contact_evidence ("
        " evidence_id, tenant_id, account_id, business_name, raw_number, e164,"
        " kind, tier, person, role, source_url, source_domain, source_type,"
        " context_snippet, confidence, corroborations, conflict_note,"
        " applied_to_account, run_id, discovered_at, verified_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,?,?,?)"
        " ON CONFLICT(evidence_id) DO NOTHING",
        (ev.evidence_id, ev.tenant_id, ev.account_id, ev.business_name,
         ev.raw_number, ev.e164, ev.kind, ev.tier, ev.person, ev.role,
         ev.source_url, ev.source_domain, ev.source_type,
         ev.context_snippet[:500], ev.confidence, ev.corroborations,
         ev.conflict_note, ev.run_id, ev.discovered_at, ev.verified_at),
    )
    return cur.rowcount > 0


def mark_applied(conn: sqlite3.Connection, evidence_id: str) -> None:
    conn.execute("UPDATE painting_contact_evidence SET applied_to_account = 1 "
                 "WHERE evidence_id = ?", (evidence_id,))


def evidence_for_number(conn: sqlite3.Connection, tenant: str,
                        e164: str) -> list[sqlite3.Row]:
    """Every independent source that published this number, for the target
    account or any other. Two rows from two different domains is real
    corroboration; two rows from one domain is one source repeating itself."""
    conn.row_factory = sqlite3.Row
    return list(conn.execute(
        "SELECT * FROM painting_contact_evidence WHERE tenant_id = ? AND e164 = ?"
        " ORDER BY discovered_at", (tenant, e164)))


def detect_conflict(conn: sqlite3.Connection, tenant: str, account_id: str,
                    person: str, e164: str) -> str:
    """A named person already on record against a DIFFERENT number for this
    account is not automatically an error - people have a desk line and a
    mobile. It is only worth flagging when the two numbers are the same KIND,
    which is the shape of a stale-vs-current contradiction. Returns a note,
    or "" when there is nothing to flag; never silently picks a winner.
    """
    if not person:
        return ""
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT e164, kind, source_url FROM painting_contact_evidence"
        " WHERE tenant_id = ? AND account_id = ? AND lower(person) = lower(?)"
        " AND e164 != ?", (tenant, account_id, person, e164)).fetchall()
    from .phones import classify_kind
    mine = classify_kind(e164)
    clashes = [r for r in rows if r["kind"] == mine]
    if not clashes:
        return ""
    others = ", ".join(f"{r['e164']} ({r['source_url']})" for r in clashes[:3])
    return (f"CONFLICT: {person} also published as {others} - same number kind, "
            f"not reconciled; both retained for human review")


# ── per-lead research state ─────────────────────────────────────────────────

def load_state(conn: sqlite3.Connection, account_id: str) -> dict | None:
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM painting_enrichment_state WHERE account_id = ?",
                       (account_id,)).fetchone()
    return dict(row) if row else None


def save_state(conn: sqlite3.Connection, *, account_id: str, tenant: str,
               business_name: str, segment: str, outcome: str, stop_reason: str,
               best_tier: str, sources_checked: int, urls_seen: list,
               people_found: list, numbers_found: int, run_id: str) -> None:
    """Upsert the research record for one lead. `attempts` accumulates so the
    strategy layer can back off leads that have already been looked at
    several times without success."""
    now = _now()
    conn.execute(
        "INSERT INTO painting_enrichment_state ("
        " account_id, tenant_id, business_name, segment, last_outcome,"
        " stop_reason, best_tier, attempts, sources_checked, urls_seen_json,"
        " people_found_json, numbers_found, last_run_id, first_attempt_at,"
        " last_attempt_at)"
        " VALUES (?,?,?,?,?,?,?,1,?,?,?,?,?,?,?)"
        " ON CONFLICT(account_id) DO UPDATE SET"
        "  last_outcome=excluded.last_outcome, stop_reason=excluded.stop_reason,"
        "  best_tier=excluded.best_tier, attempts=painting_enrichment_state.attempts+1,"
        "  sources_checked=excluded.sources_checked, urls_seen_json=excluded.urls_seen_json,"
        "  people_found_json=excluded.people_found_json,"
        "  numbers_found=excluded.numbers_found, last_run_id=excluded.last_run_id,"
        "  last_attempt_at=excluded.last_attempt_at",
        (account_id, tenant, business_name, segment, outcome, stop_reason,
         best_tier, sources_checked, json.dumps(urls_seen[:60]),
         json.dumps(people_found[:30]), numbers_found, run_id, now, now),
    )
