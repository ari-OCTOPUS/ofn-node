"""What to research next, and when to stop - with a reason that survives
being questioned.

Two decisions live here.

TARGET SELECTION decides which leads are worth a run at all. It reads the
account's current contact field and its recorded research history, so a lead
that already has a good mobile is skipped, and a lead that has been
researched three times and come back empty is backed off rather than
re-ground forever. That back-off is the single biggest efficiency lever on
this dataset: prior manual rounds established that most mid-size strata
firms simply do not publish personal numbers, so the default outcome for
them is a permanent, correct "no".

STOPPING decides when one lead has had enough. The brief explicitly rejects
"N steps and stop", and rightly - the right amount of effort depends on what
has been found so far and what is left unexplored. The policy below is
written as explicit named rules so every stop emits a reason a human can
argue with, rather than a silent budget cut.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field

from . import phones as ph

# ── explainable stop reasons ────────────────────────────────────────────────
STOP_P0_FOUND = "personal_mobile_with_attribution_found"
STOP_MOBILE_NO_BETTER = "mobile_found_and_no_higher_value_source_remaining"
STOP_EXHAUSTED = "source_space_exhausted_without_verified_phone"
STOP_BUDGET = "per_lead_request_budget_exhausted"
STOP_BLOCKED = "all_known_paths_blocked_by_host"
STOP_NO_WEBSITE = "no_website_on_record_and_no_search_result"
STOP_ROBOTS = "robots_disallowed_on_official_site"
STOP_DEAD_PATHS = "site_does_not_use_the_remaining_path_conventions"

# After this many consecutive fetches that returned nothing usable, the
# remaining speculative paths are not worth buying. Live runs showed every
# lead consuming its entire request budget on /team, /our-people, /staff...
# guesses that all 404 on sites which simply do not use those URLs - while
# the pages those sites DO publish had already been found and followed. Six
# is deliberately forgiving: a couple of misses is normal, six in a row is
# the site telling us its conventions are different.
MAX_CONSECUTIVE_MISSES = 6

# Leads whose research history says "do not pay for this again". A lead that
# came back no_public_number_published this many times is treated as settled
# until a human resets it, because the evidence space for a small company
# does not grow much between runs.
MAX_ATTEMPTS_BEFORE_BACKOFF = 3


@dataclass
class LeadTarget:
    account_id: str
    business_name: str
    website: str
    segment: str
    contact_channel: str
    group: str                     # "A" no phone / "B" no mobile
    attempts: int = 0
    last_outcome: str = ""


@dataclass
class ResearchState:
    """Mutable per-lead research progress, consulted by should_stop."""
    requests_used: int = 0
    sources_checked: int = 0
    candidates: list = field(default_factory=list)
    people: list = field(default_factory=list)
    urls_seen: list = field(default_factory=list)
    unexplored: list = field(default_factory=list)
    blocked_hosts: int = 0
    had_any_success: bool = False
    # Pages rejected wholesale as directory listings (see
    # researcher.MAX_NUMBERS_PER_SOURCE). Tracked so a lead whose only
    # "source" was a directory is reported honestly rather than as a clean
    # "nothing published".
    directory_pages: int = 0
    consecutive_misses: int = 0

    @property
    def best_tier(self) -> str:
        return ph.best_tier(self.candidates)


def select_targets(conn: sqlite3.Connection, *, tenant: str = "lead",
                   limit: int | None = None, only_no_phone: bool = False,
                   only_no_mobile: bool = False,
                   include_backed_off: bool = False) -> list[LeadTarget]:
    """Leads worth researching, best-value first.

    Reads with raw SQL rather than LeadStore.accounts() on purpose: that
    method clamps its limit to MAX_PAGE (100) regardless of what the caller
    asks for, so on a table that has already passed 100 rows it silently
    hides the tail - which would mean the newest leads, exactly the ones
    most likely to still need a phone number, never got researched.
    """
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT a.account_id, a.business_name, a.website, a.segment,"
        "       a.contact_channel,"
        "       COALESCE(s.attempts, 0)   AS attempts,"
        "       COALESCE(s.last_outcome,'') AS last_outcome"
        "  FROM painting_b2b_accounts a"
        "  LEFT JOIN painting_enrichment_state s ON s.account_id = a.account_id"
        " WHERE a.tenant_id = ?", (tenant,)).fetchall()

    targets: list[LeadTarget] = []
    for r in rows:
        cc = (r["contact_channel"] or "").strip()
        found = ph.extract_candidates(cc, allow_fax=True)
        has_mobile = any(c.kind == ph.KIND_MOBILE for c in found)
        has_any = bool(found)

        if has_mobile:
            continue                      # group C - already good, never re-grind
        group = "A" if not has_any else "B"
        if only_no_phone and group != "A":
            continue
        if only_no_mobile and group != "B":
            continue
        if (not include_backed_off
                and r["attempts"] >= MAX_ATTEMPTS_BEFORE_BACKOFF
                and r["last_outcome"] != "blocked_by_host"):
            # Blocked leads are exempt from back-off: a block is a property of
            # the host on the day, not evidence about whether a number exists.
            continue
        targets.append(LeadTarget(
            account_id=r["account_id"], business_name=r["business_name"],
            website=(r["website"] or "").strip(), segment=r["segment"] or "",
            contact_channel=cc, group=group, attempts=r["attempts"],
            last_outcome=r["last_outcome"]))

    # Never-tried before retried; group A (no phone at all) before group B
    # (has a switchboard); leads with a website before those without, since
    # a website is the only high-confidence source class available.
    targets.sort(key=lambda t: (t.attempts, t.group != "A", not t.website,
                                t.business_name.lower()))
    return targets[:limit] if limit else targets


def plan_paths(segment: str) -> tuple[str, ...]:
    """Segment-aware ordering of the seeded paths.

    The ordering differs by segment because the segments genuinely differ:
    a strata firm's value is in its named managers, so people pages come
    first; a construction/fit-out head contractor's useful contact is
    usually a project or estimating desk reached from the contact page.
    """
    from .sources import CONTACT_PATH_CANDIDATES
    people_first = ("/our-team", "/team", "/our-people", "/people", "/staff",
                    "/meet-the-team", "/our-staff", "/management",
                    "/our-management-team", "/leadership", "/directors")
    contact_first = ("/contact", "/contact-us", "/contact-us/", "/contactus")

    if segment in ("strata", "property_management", "real_estate",
                   "body_corporate"):
        lead = people_first + contact_first
    elif segment in ("commercial_construction", "fitout", "refurbishment",
                     "labour_hire"):
        lead = contact_first + people_first
    else:
        lead = contact_first + people_first
    rest = tuple(p for p in CONTACT_PATH_CANDIDATES if p not in lead)
    return lead + rest


def should_stop(st: ResearchState, *, request_budget: int) -> tuple[bool, str]:
    """Explainable stopping policy. Returns (stop, reason).

    Ordered by how conclusive each condition is, so the reason reported is
    always the strongest true one rather than whichever fired first by
    accident.
    """
    if st.best_tier == ph.TIER_P0:
        return True, STOP_P0_FOUND

    if st.requests_used >= request_budget:
        return True, STOP_BUDGET

    # A bare mobile is the goal; keep going only while a source class that
    # could ATTRIBUTE it (a people page) is still unexplored.
    if st.best_tier == ph.TIER_P1:
        people_pages_left = any(
            any(k in u.lower() for k in ("team", "people", "staff",
                                         "management", "leadership"))
            for u in st.unexplored)
        if not people_pages_left:
            return True, STOP_MOBILE_NO_BETTER

    if not st.unexplored:
        if st.blocked_hosts and not st.had_any_success:
            return True, STOP_BLOCKED
        return True, STOP_EXHAUSTED

    # The site has answered, repeatedly, that it does not use the URL shapes
    # still queued. Buying more of them is paying to be told the same thing.
    if st.consecutive_misses >= MAX_CONSECUTIVE_MISSES:
        return True, STOP_DEAD_PATHS

    return False, ""


def outcome_for(st: ResearchState, *, had_website: bool,
                robots_blocked: bool) -> str:
    """Turn research progress into one of the differentiated outcomes.

    The distinction the brief insists on: "found nothing" and "could not
    look" are different facts with different retry policies, and collapsing
    them is what makes an agent waste a year re-checking a host that blocks
    it, while never re-checking a company that simply had no team page up
    that week.
    """
    from .evidence import (OUT_BLOCKED, OUT_FOUND, OUT_NO_PUBLIC_NUMBER,
                           OUT_NO_WEBSITE, OUT_ROBOTS, OUT_SITE_UNREACHABLE)
    if st.candidates:
        return OUT_FOUND
    if robots_blocked:
        return OUT_ROBOTS
    if not had_website:
        return OUT_NO_WEBSITE
    if st.blocked_hosts and not st.had_any_success:
        return OUT_BLOCKED
    if not st.had_any_success:
        return OUT_SITE_UNREACHABLE
    return OUT_NO_PUBLIC_NUMBER
