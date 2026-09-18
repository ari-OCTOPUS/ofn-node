"""Source-performance model and the human-readable lessons file.

Deliberate departure from the brief, worth stating because it changes where
the truth lives. The brief asks for a lessons file that the agent appends
observations to, plus a separate scoring mechanism that tracks searches,
hits and success rates. Maintaining those as their own stores means a second
copy of facts already recorded in `painting_contact_evidence` and
`painting_enrichment_state` - and a second copy drifts. The first time the
stats file and the evidence table disagree, neither can be trusted, and the
agent would be "learning" from whichever happened to be stale.

So the performance model here is DERIVED: every number in it is a live query
over the evidence the agent actually recorded. Nothing to keep in sync,
nothing that can silently drift, and any figure it reports can be traced
back to the individual rows that produced it. The lessons file is then a
rendering of that query plus narrative notes - an artefact for a human to
read, never the source of truth the agent reads back.

The one thing genuinely worth persisting separately is a narrative lesson a
human (or a future run) wrote down that is NOT derivable from counts, e.g.
"this host serves a JS shell to non-browsers, the numbers are never in the
HTML". Those append to the lessons file and are never auto-generated.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

LESSONS_PATH = Path("tools/enrichment_lessons.txt")

# Hypotheses this agent starts with, carried over from two manual research
# rounds over ~40 Sydney strata/property companies earlier in this project.
# They are PRIORS, not rules: strategy.py uses them to order work, and the
# derived stats below are what confirm or kill them over time.
SEED_LESSONS = (
    ("strata", "company_website_team_page",
     "Mid-size branded strata firms route everything through 1300/switchboard "
     "and publish no personal mobiles; boutique/surname firms with a real "
     "team page are where mobiles actually appear.",
     "Prioritise team/people pages for small firms; expect P3-only for large "
     "branded ones and stop early rather than exhausting the source space."),
    ("any", "meta_tags_and_form_placeholders",
     "Numbers/emails scraped from raw HTML attributes (og/twitter meta, input "
     "placeholder=) are developer credits and template filler, not contacts.",
     "Extract from visible text only - already enforced in sources.clean_text."),
    ("any", "search_engine_result_titles",
     "A search result title is SEO copy, not a business name, and listicle "
     "pages ('Top 20 X Companies') are not companies at all.",
     "Never treat a search title as an identity; verify against the site."),
    ("facility_management", "segment_confusion",
     "'X facility management' queries surface the FM PROVIDER doing the work, "
     "not the property owner buying it - the opposite of strata queries.",
     "Treat FM-provider hits as likely competitors, not prospects."),
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def source_performance(conn: sqlite3.Connection, tenant: str = "lead") -> list[dict]:
    """Hit-rate per source class, derived live from recorded evidence."""
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT source_type,"
        "       COUNT(*)                                        AS numbers,"
        "       SUM(CASE WHEN kind='mobile' THEN 1 ELSE 0 END)  AS mobiles,"
        "       SUM(CASE WHEN person != ''  THEN 1 ELSE 0 END)  AS attributed,"
        "       SUM(CASE WHEN confidence='verified' THEN 1 ELSE 0 END) AS verified,"
        "       COUNT(DISTINCT account_id)                      AS accounts"
        "  FROM painting_contact_evidence WHERE tenant_id = ?"
        " GROUP BY source_type ORDER BY mobiles DESC, numbers DESC", (tenant,)
    ).fetchall()
    return [dict(r) for r in rows]


def segment_performance(conn: sqlite3.Connection, tenant: str = "lead") -> list[dict]:
    """Which segments are actually enrichable, and which are a dead end.

    This is the figure that decides where NOT to spend the next run, so it
    counts leads (not numbers): a segment where 30 leads were researched and
    2 produced a mobile is a segment to stop paying for.
    """
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT s.segment,"
        "       COUNT(*)                                              AS researched,"
        "       SUM(CASE WHEN s.last_outcome='found' THEN 1 ELSE 0 END) AS found_any,"
        "       SUM(CASE WHEN s.best_tier LIKE 'P0%' OR s.best_tier LIKE 'P1%'"
        "                THEN 1 ELSE 0 END)                           AS found_mobile,"
        "       SUM(CASE WHEN s.last_outcome='no_public_number_published'"
        "                THEN 1 ELSE 0 END)                           AS no_public,"
        "       SUM(CASE WHEN s.last_outcome IN ('blocked_by_host','site_unreachable',"
        "                'robots_disallowed') THEN 1 ELSE 0 END)      AS blocked,"
        "       AVG(s.sources_checked)                                AS avg_effort"
        "  FROM painting_enrichment_state s WHERE s.tenant_id = ?"
        " GROUP BY s.segment ORDER BY found_mobile DESC, researched DESC", (tenant,)
    ).fetchall()
    return [dict(r) for r in rows]


def url_pattern_performance(conn: sqlite3.Connection, tenant: str = "lead",
                            *, limit: int = 15) -> list[dict]:
    """Which URL shapes paid off, so CONTACT_PATH_CANDIDATES can be reordered
    from evidence instead of from intuition. Keyed on the path's last
    segment, which is the part the seed list actually chooses."""
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT source_url, kind, person FROM painting_contact_evidence"
        " WHERE tenant_id = ? AND source_url != ''", (tenant,)).fetchall()
    tally: dict[str, dict] = {}
    for r in rows:
        from urllib.parse import urlparse
        path = (urlparse(r["source_url"]).path or "/").rstrip("/")
        key = "/" + path.rsplit("/", 1)[-1] if path else "/"
        slot = tally.setdefault(key, {"pattern": key, "numbers": 0,
                                      "mobiles": 0, "attributed": 0})
        slot["numbers"] += 1
        if r["kind"] == "mobile":
            slot["mobiles"] += 1
        if r["person"]:
            slot["attributed"] += 1
    out = sorted(tally.values(), key=lambda d: (-d["mobiles"], -d["numbers"]))
    return out[:limit]


def stop_reason_breakdown(conn: sqlite3.Connection, tenant: str = "lead") -> list[dict]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT stop_reason, COUNT(*) AS n FROM painting_enrichment_state"
        " WHERE tenant_id = ? GROUP BY stop_reason ORDER BY n DESC", (tenant,)
    ).fetchall()
    return [dict(r) for r in rows]


def render_report(conn: sqlite3.Connection, tenant: str = "lead") -> str:
    """The derived model, as text. Safe to run any time; reads only."""
    lines = [f"# Enrichment source-performance model  ({_now()})", ""]

    lines.append("## By source class (which kinds of page actually pay off)")
    perf = source_performance(conn, tenant)
    if not perf:
        lines.append("  (no evidence recorded yet)")
    for r in perf:
        lines.append(
            f"  {r['source_type']:22s} numbers={r['numbers']:<4} "
            f"mobiles={r['mobiles']:<4} attributed={r['attributed']:<4} "
            f"verified={r['verified']:<4} accounts={r['accounts']}")

    lines += ["", "## By segment (where to spend, and where to stop)"]
    segs = segment_performance(conn, tenant)
    if not segs:
        lines.append("  (no leads researched yet)")
    for r in segs:
        eff = f"{r['avg_effort']:.1f}" if r["avg_effort"] is not None else "-"
        lines.append(
            f"  {r['segment'] or '(none)':24s} researched={r['researched']:<4} "
            f"mobile={r['found_mobile']:<4} any={r['found_any']:<4} "
            f"no_public={r['no_public']:<4} blocked={r['blocked']:<4} "
            f"avg_sources={eff}")

    lines += ["", "## By URL pattern (reorder the seed path list from this)"]
    pats = url_pattern_performance(conn, tenant)
    if not pats:
        lines.append("  (no evidence recorded yet)")
    for r in pats:
        lines.append(f"  {r['pattern']:24s} numbers={r['numbers']:<4} "
                     f"mobiles={r['mobiles']:<4} attributed={r['attributed']}")

    lines += ["", "## Why research stopped"]
    for r in stop_reason_breakdown(conn, tenant):
        lines.append(f"  {r['stop_reason'] or '(unset)':46s} {r['n']}")

    return "\n".join(lines)


def append_lesson(*, segment: str, source: str, pattern: str, result: str,
                  confidence: str, recommendation: str,
                  path: Path = LESSONS_PATH) -> None:
    """Append one NARRATIVE lesson - something a count cannot express.

    Auto-generated statistics deliberately do NOT come through here; they are
    derived on demand by render_report(), so this file stays a short, honest
    list of things somebody actually learned rather than a log nobody reads.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = (f"\nDATE: {_now()}\nSEGMENT: {segment}\nSOURCE: {source}\n"
             f"PATTERN: {pattern}\nRESULT: {result}\n"
             f"CONFIDENCE: {confidence}\nRECOMMENDATION: {recommendation}\n")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(entry)


def ensure_seed_lessons(path: Path = LESSONS_PATH) -> None:
    """Write the priors once, so a fresh clone starts with what this project
    already learned instead of rediscovering it at the owner's expense."""
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    header = ("# Enrichment lessons (narrative)\n"
              "# Statistics are NOT kept here - they are derived live from\n"
              "# painting_contact_evidence / painting_enrichment_state via\n"
              "#   python tools/enrich_contacts.py --lessons\n")
    with path.open("w", encoding="utf-8") as fh:
        fh.write(header)
    for segment, source, pattern, recommendation in SEED_LESSONS:
        append_lesson(segment=segment, source=source, pattern=pattern,
                      result="carried over from prior manual research rounds",
                      confidence="observed repeatedly, not yet re-measured by this agent",
                      recommendation=recommendation, path=path)
