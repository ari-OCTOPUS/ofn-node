"""Per-lead research loop: fetch, read, attribute, verify, record.

Reuses the polite-HTTP stack already proven in `ofn.agents.b2b_discovery`
(RobotsGate for robots.txt, HostThrottle for per-host spacing, fetch_url for
403-is-final / 429-backs-off retry semantics) rather than growing a second
one. The only thing added here is a binary fetch, because fetch_url decodes
its body to text and a PDF is not text - and even that goes through the same
robots gate and the same throttle, so PDF reading is exactly as polite as
every other request this project makes.

Collection-only: GETs, plus writes to the local painting store. Nothing is
sent anywhere.
"""
from __future__ import annotations

import sqlite3
import time
import urllib.request
from urllib.parse import urlparse

from ..agents import b2b_discovery as bd
from . import evidence as ev
from . import phones as ph
from . import sources as src
from . import strategy as st

# Per-lead ceiling on HTTP requests. An operational control, not a research
# rule: the stopping policy in strategy.py is what normally ends a lead, and
# this only catches the pathological case (a site that links to hundreds of
# contact-ish pages). Raise it freely for a deeper run.
DEFAULT_REQUEST_BUDGET = 14
PDF_MAX_BYTES = 6 * 1024 * 1024

# A real company's contact/team page carries a handful of numbers: a
# switchboard, maybe a fax, an after-hours line, and the direct numbers of
# the few people shown. A page carrying MANY numbers is a directory listing
# other businesses, and every number on it belongs to somebody else.
#
# This is not hypothetical: the first live run pulled 61 "direct office"
# numbers out of four leads, because one lead's recorded website was a
# strata-directory domain. Attributing those to the lead would have filled
# the owner's call list with unrelated companies - the exact
# company-identity failure that makes a contact table untrustworthy. When a
# page trips this, its numbers are dropped wholesale rather than guessed
# between, and the page is counted as checked so the lead does not silently
# look unresearched.
MAX_NUMBERS_PER_SOURCE = 6


def fetch_bytes(url: str, *, robots: bd.RobotsGate, throttle: bd.HostThrottle,
                timeout: int = 25, max_bytes: int = PDF_MAX_BYTES) -> dict:
    """Binary sibling of b2b_discovery.fetch_url, for PDFs.

    Same politeness contract: robots.txt is checked first and a Disallow is
    honoured, the per-host throttle is respected, and a 403 is accepted as a
    final answer rather than retried. Capped read so a huge file cannot
    exhaust memory on a 4GB board.
    """
    if not robots.allowed(url):
        return {"ok": False, "kind": "robots_disallowed", "body": b"", "url": url}
    throttle.throttle(urlparse(url).netloc, now=time.time, sleep=time.sleep)
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": bd.USER_AGENT, "Accept": "application/pdf"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"ok": True, "kind": "ok", "body": r.read(max_bytes), "url": url}
    except Exception as exc:                                  # noqa: BLE001
        code = getattr(exc, "code", None)
        kind = "blocked_403" if code == 403 else "error"
        return {"ok": False, "kind": kind, "body": b"", "url": url}


class ContactResearcher:
    """Researches one lead at a time against its official website.

    Search-engine expansion is deliberately NOT wired in by default. On this
    dataset the official site is the only source class that yields `verified`
    confidence, and two prior manual rounds showed third-party results for
    these companies are dominated by data-broker and listing pages that the
    brief forbids or that carry near-zero trust. `search` is accepted as an
    injectable hook so that expansion is a configuration change rather than
    a rewrite, and so tests can drive it offline.
    """

    def __init__(self, conn: sqlite3.Connection, *, run_id: str,
                 robots: bd.RobotsGate | None = None,
                 throttle: bd.HostThrottle | None = None,
                 fetch=None, fetch_bin=None, search=None,
                 request_budget: int = DEFAULT_REQUEST_BUDGET,
                 read_pdfs: bool = True, verbose: bool = False) -> None:
        self.conn = conn
        self.run_id = run_id
        self.robots = robots or bd.RobotsGate()
        self.throttle = throttle or bd.HostThrottle()
        self._fetch = fetch or (lambda u: bd.fetch_url(
            u, robots=self.robots, throttle=self.throttle))
        self._fetch_bin = fetch_bin or (lambda u: fetch_bytes(
            u, robots=self.robots, throttle=self.throttle))
        self._search = search
        self.request_budget = request_budget
        self.read_pdfs = read_pdfs and src.pdf_parser_available()
        self.pdf_parser_missing = read_pdfs and not src.pdf_parser_available()
        self.verbose = verbose

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(f"    {msg}", flush=True)

    def research(self, target: st.LeadTarget) -> dict:
        """Research one lead. Returns a per-lead report; never raises."""
        state = st.ResearchState()
        robots_blocked = False
        website = target.website.strip()

        if not website:
            outcome = ev.OUT_NO_WEBSITE
            self._persist(target, state, outcome, st.STOP_NO_WEBSITE)
            return self._report(target, state, outcome, st.STOP_NO_WEBSITE)

        domain = bd.registrable_domain(website)
        base = website if website.startswith("http") else "https://" + website

        # Seed the queue: homepage first, then segment-ordered known paths.
        queue: list[str] = [base]
        for path in st.plan_paths(target.segment):
            u = src.seeded_urls(base)
            queue.extend(x for x in u if x.endswith(path.rstrip("/")) or
                         x.rstrip("/").endswith(path.rstrip("/")))
        # de-dup, preserve order
        seen_q: set[str] = set()
        queue = [u for u in queue if not (u in seen_q or seen_q.add(u))]
        state.unexplored = list(queue)

        pdf_queue: list[str] = []
        stop_reason = ""

        while state.unexplored:
            stop, stop_reason = st.should_stop(state, request_budget=self.request_budget)
            if stop:
                break
            url = state.unexplored.pop(0)
            if url in state.urls_seen:
                continue
            state.urls_seen.append(url)
            state.requests_used += 1

            res = self._fetch(url)
            kind = res.get("kind")
            if kind == "robots_disallowed":
                robots_blocked = True
                self._log(f"robots disallow  {url}")
                continue
            if kind in ("blocked_403", "blocked_429"):
                state.blocked_hosts += 1
                self._log(f"blocked {kind}   {url}")
                continue
            if not res.get("ok") or not res.get("body"):
                state.consecutive_misses += 1
                self._log(f"unreachable      {url}")
                continue

            state.consecutive_misses = 0
            state.had_any_success = True
            state.sources_checked += 1
            html = res["body"]
            self._harvest(html, url, domain, target, state)

            # Layer 2: follow contact-ish links the seed list never knew about.
            #
            # These go to the FRONT of the queue, ahead of any seeded path
            # not yet tried. The first live run made the reason concrete: on
            # three real sites the whole per-lead budget was spent on
            # speculative /team, /our-people, /staff... guesses that all
            # 404'd, so the links the homepage actually advertised were
            # never fetched at all. A link the site really publishes is
            # strictly better evidence than a path we hoped existed.
            discovered = [u for u in src.discover_links(html, url, domain, limit=8)
                          if u not in state.urls_seen and u not in state.unexplored]
            state.unexplored[:0] = discovered
            if self.read_pdfs:
                for p in src.discover_pdfs(html, url, domain, limit=3):
                    if p not in pdf_queue:
                        pdf_queue.append(p)

        # PDFs last: they are the most expensive fetch and the least often
        # decisive, so they only run if the cheaper HTML space did not settle
        # the lead already.
        if self.read_pdfs and pdf_queue:
            stop, _r = st.should_stop(state, request_budget=self.request_budget)
            if not stop:
                for purl in pdf_queue[:3]:
                    state.requests_used += 1
                    res = self._fetch_bin(purl)
                    if not res.get("ok") or not res.get("body"):
                        if res.get("kind") in ("blocked_403", "blocked_429"):
                            state.blocked_hosts += 1
                        continue
                    text = src.read_pdf_text(res["body"])
                    if not text:
                        continue
                    state.sources_checked += 1
                    state.urls_seen.append(purl)
                    # require_label: PDF text extraction can spill internal
                    # font-metric/object arrays full of phone-shaped digit
                    # runs, so a PDF number is trusted only when a contact
                    # cue sits right before it. HTML visible text does not
                    # need this - its false positives are already handled by
                    # the ABN/fax/etc. context rejects.
                    self._harvest_text(text, purl, domain, target, state,
                                       require_label=True)

        if not stop_reason:
            _stop, stop_reason = st.should_stop(state, request_budget=self.request_budget)
            stop_reason = stop_reason or st.STOP_EXHAUSTED
        if robots_blocked and not state.candidates and not state.had_any_success:
            stop_reason = st.STOP_ROBOTS

        outcome = st.outcome_for(state, had_website=True, robots_blocked=robots_blocked)
        self._persist(target, state, outcome, stop_reason)
        return self._report(target, state, outcome, stop_reason)

    # ── extraction ──────────────────────────────────────────────────────────

    def _harvest(self, html: str, url: str, domain: str,
                 target: st.LeadTarget, state: st.ResearchState) -> None:
        self._harvest_text(src.clean_text(html), url, domain, target, state)

    def _harvest_text(self, text: str, url: str, domain: str,
                      target: st.LeadTarget, state: st.ResearchState,
                      *, require_label: bool = False) -> None:
        """Read numbers and people out of ONE source's visible text and record
        each number as evidence tied to that exact URL.

        `require_label` (used for PDF sources) keeps only numbers with a
        contact cue right before them - see phones.has_contact_label.
        """
        people = src.extract_people(text)
        for name, role in people:
            if (name, role) not in state.people:
                state.people.append((name, role))

        source_type = src.classify_source_type(url, domain)
        candidates = ph.extract_candidates(text)
        if require_label:
            candidates = [c for c in candidates
                          if ph.has_contact_label(text, c.raw)]
        if len(candidates) > MAX_NUMBERS_PER_SOURCE:
            self._log(f"DIRECTORY-LIKE ({len(candidates)} numbers) - discarding "
                      f"all, cannot attribute to this company: {url}")
            state.directory_pages += 1
            return

        for cand in candidates:
            person, role = src.nearest_person(text, cand.raw, people)
            cand = cand.with_attribution(person=person, role=role)

            # The stored snippet is the proof: it is the actual text the
            # number was read from, so a human can re-open the page and
            # confirm it rather than taking this agent's word for it.
            idx = text.find(cand.raw)
            snippet = text[max(0, idx - 90):idx + len(cand.raw) + 60] if idx >= 0 else ""

            conflict = ev.detect_conflict(self.conn, "lead", target.account_id,
                                          person, cand.e164) if person else ""
            branch = src.branch_mismatch_note(
                source_url=url, context=snippet,
                expected_state=src.detect_state(target.business_name))
            conflict = " | ".join(x for x in (conflict, branch) if x)
            record = ev.Evidence(
                account_id=target.account_id, business_name=target.business_name,
                raw_number=cand.raw, e164=cand.e164, kind=cand.kind,
                tier=cand.tier, person=cand.person, role=cand.role,
                source_url=url, source_domain=urlparse(url).hostname or "",
                source_type=source_type, context_snippet=snippet,
                corroborations=self._corroboration_count(cand.e164, url),
                conflict_note=conflict, run_id=self.run_id)
            if ev.record_evidence(self.conn, record):
                state.candidates.append(cand)
                self._log(f"FOUND {cand.tier:24s} {cand.raw:18s} "
                          f"{cand.person or '(unattributed)'}  <- {url}")
        self.conn.commit()

    def _corroboration_count(self, e164: str, this_url: str) -> int:
        """How many DISTINCT domains have published this number.

        Distinct domains, not rows: the same number in a site's header and
        its footer is one source saying one thing twice, which is not
        corroboration and must not be allowed to inflate confidence.
        """
        rows = ev.evidence_for_number(self.conn, "lead", e164)
        domains = {r["source_domain"] for r in rows if r["source_domain"]}
        domains.add(urlparse(this_url).hostname or "")
        return max(1, len({d for d in domains if d}))

    # ── persistence ─────────────────────────────────────────────────────────

    def _persist(self, target: st.LeadTarget, state: st.ResearchState,
                 outcome: str, stop_reason: str) -> None:
        ev.save_state(
            self.conn, account_id=target.account_id, tenant="lead",
            business_name=target.business_name, segment=target.segment,
            outcome=outcome, stop_reason=stop_reason,
            best_tier=state.best_tier, sources_checked=state.sources_checked,
            urls_seen=state.urls_seen,
            people_found=[f"{n} ({r})" for n, r in state.people],
            numbers_found=len(state.candidates), run_id=self.run_id)
        self.conn.commit()

    def _report(self, target: st.LeadTarget, state: st.ResearchState,
                outcome: str, stop_reason: str) -> dict:
        return {
            "account_id": target.account_id,
            "business_name": target.business_name,
            "segment": target.segment,
            "group": target.group,
            "outcome": outcome,
            "stop_reason": stop_reason,
            "best_tier": state.best_tier,
            "requests_used": state.requests_used,
            "sources_checked": state.sources_checked,
            "people_found": [f"{n} ({r})" for n, r in state.people],
            "candidates": [
                {"raw": c.raw, "e164": c.e164, "kind": c.kind, "tier": c.tier,
                 "person": c.person, "role": c.role} for c in state.candidates],
        }


def apply_to_account(conn: sqlite3.Connection, *, account_id: str,
                     candidates: list, dry_run: bool = False) -> list[str]:
    """APPEND verified contacts to the account's contact_channel.

    Read-then-append, never overwrite: the existing value is read first and
    the new fragment is concatenated, so a switchboard number the owner
    already relies on is preserved alongside a newly found mobile. Numbers
    already present (compared on normalized form) are skipped, which is what
    makes re-running this safe rather than progressively corrupting the
    field.
    """
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT contact_channel FROM painting_b2b_accounts"
                       " WHERE account_id = ? AND tenant_id = 'lead'",
                       (account_id,)).fetchone()
    if row is None:
        return []
    existing = (row["contact_channel"] or "").strip()

    # lead_store._clean caps this column at 220 characters, so a blind
    # append can slice a phone number in half - the first apply run wrote
    # "Jay Pennay (Property Manag" and lost the number entirely. Contacts
    # are therefore added only while they FIT whole; anything that does not
    # is left out of the summary field rather than truncated into garbage.
    # Nothing is lost by doing so: painting_contact_evidence holds every
    # contact in full, with its source, and is the real record.
    FIELD_LIMIT = 220

    added: list[str] = []
    skipped_no_room = 0
    merged = existing
    for c in sorted(candidates, key=lambda x: ph.TIER_ORDER.index(x.tier)):
        if ph.already_present(c.e164, merged):
            continue
        label = f"{c.person} ({c.role}) {c.raw}" if c.person and c.role else (
            f"{c.person} {c.raw}" if c.person else c.raw)
        nxt = (merged + " | " + label) if merged else label
        if len(nxt) > FIELD_LIMIT:
            skipped_no_room += 1
            continue
        merged = nxt
        added.append(label)

    if skipped_no_room:
        # Reported to the caller (which logs it), never written into the
        # field itself - the field is for numbers the owner dials.
        print(f"      note: {skipped_no_room} further contact(s) did not fit "
              f"the {FIELD_LIMIT}-char field; full records are in "
              f"painting_contact_evidence")

    if added and not dry_run:
        conn.execute("UPDATE painting_b2b_accounts SET contact_channel = ?,"
                     " updated_at = ? WHERE account_id = ? AND tenant_id = 'lead'",
                     (merged, ev._now(), account_id))
        conn.commit()
    return added
