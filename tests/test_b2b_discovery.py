"""B2B discovery/harvest agent — multi-source, collection-only.

Mirrors the project's existing harvester test style (test_seek_harvest.py,
test_tender_dedup.py): pure functions are tested directly with no network;
store-touching behaviour runs against a real (temp-file) LeadStore via
tempfile.TemporaryDirectory(), exactly like test_tender_dedup.py — a
self-cleaning context object, never an unmanaged bare temp-dir path
(tests/test_tmpdir.py forbids that repo-wide).

Scope: this agent discovers and normalizes B2B *company* candidates
(strata/facility/property managers etc.) and upserts them into the existing
painting_b2b_accounts table via LeadStore.create_account. It does not send
anything — every assertion here is about collection, normalization, identity
resolution and persistence, never outreach.
"""
from __future__ import annotations

import os
import tempfile
import unittest

from ofn.adapters.lead_store import LeadStore
from ofn.agents import b2b_discovery as bd

NOW = "2026-09-06T00:00:00Z"
TENANT = "lead"


def store():
    d = tempfile.TemporaryDirectory()
    st = LeadStore(os.path.join(d.name, "painting.sqlite"))
    return d, st


def candidate(**kw) -> dict:
    base = {
        "business_name": "Riverside Strata Management",
        "website": "https://riversidestrata.com.au",
        "phone": "",
        "email": "",
        "address": "",
        "suburb": "Parramatta",
        "state": "NSW",
        "industry": "strata management",
        "source": "test_source",
        "source_url": "https://directory.example.com/riverside-strata",
        "source_type": "directory",
        "notes": "",
    }
    base.update(kw)
    return base


def make_collector(source_id, raw_candidates, *, source_type="directory",
                    domains=(), robots_disallowed=0, blocked=0, errors=()):
    """A trivial fixed-output SourceCollector — no network, fully offline."""
    def _collect():
        return bd.CollectorResult(
            candidates=tuple(raw_candidates),
            domains_checked=tuple(domains),
            robots_disallowed=robots_disallowed,
            blocked=blocked,
            errors=tuple(errors),
        )
    return bd.SourceCollector(source_id=source_id, source_type=source_type, collect=_collect)


class TestDiscoversNewCompany(unittest.TestCase):
    def test_discovers_new_company(self):
        d, st = store()
        try:
            collectors = [make_collector("dir_a", [candidate()])]
            report = bd.run_discovery(st, collectors, now_iso=NOW)
            self.assertEqual(report["new_accounts_created"], 1)
            accounts = st.accounts(TENANT, limit=100)
            names = [a["business_name"] for a in accounts]
            self.assertIn("Riverside Strata Management", names)
            row = next(a for a in accounts if a["business_name"] == "Riverside Strata Management")
            self.assertEqual(row["website"], "https://riversidestrata.com.au")
        finally:
            st.close(); d.cleanup()


class TestExistingCompanyIsUpserted(unittest.TestCase):
    def test_existing_company_is_upserted(self):
        d, st = store()
        try:
            collectors = [make_collector("dir_a", [candidate()])]
            bd.run_discovery(st, collectors, now_iso=NOW)
            bd.run_discovery(st, collectors, now_iso=NOW)  # same candidate again
            accounts = st.accounts(TENANT, limit=100)
            matching = [a for a in accounts if a["business_name"] == "Riverside Strata Management"]
            self.assertEqual(len(matching), 1, "replay must not create a duplicate row")
        finally:
            st.close(); d.cleanup()


class TestSameCompanyFromMultipleSourcesIsDeduplicated(unittest.TestCase):
    def test_same_company_from_multiple_sources_is_deduplicated(self):
        d, st = store()
        try:
            # Same business, same official domain, found by two independent
            # sources with slightly different presentation (whitespace/case) —
            # the exact "McCormacks Strata / McCormacks Strata Management"
            # shape the spec calls out, but via the domain signal this time.
            from_google = candidate(
                business_name="Riverside Strata Management",
                website="https://riversidestrata.com.au",
                source="google_search", source_type="search",
                source_url="https://www.google.com/search?q=riverside+strata",
            )
            from_seek = candidate(
                business_name="RIVERSIDE STRATA MANAGEMENT",
                website="http://www.riversidestrata.com.au/contact",
                phone="+61 2 9876 5432",
                source="yellow_pages", source_type="directory",
                source_url="https://www.yellowpages.com.au/riverside-strata",
            )
            collectors = [
                make_collector("google_search", [from_google], source_type="search"),
                make_collector("yellow_pages", [from_seek], source_type="directory"),
            ]
            report = bd.run_discovery(st, collectors, now_iso=NOW)
            accounts = st.accounts(TENANT, limit=100)
            matching = [a for a in accounts if "riverside" in a["business_name"].lower()]
            self.assertEqual(len(matching), 1,
                             f"expected one merged account, got {len(matching)}: {matching}")
            self.assertEqual(report["new_accounts_created"], 1)
            self.assertEqual(report["duplicates_prevented"], 1)
            # the second source's phone must have been folded into the same row
            self.assertIn("9876 5432", matching[0]["contact_channel"] + matching[0]["notes"])
        finally:
            st.close(); d.cleanup()

    def test_mccormacks_style_name_variant_is_matched_via_domain(self):
        """The exact scenario named in the spec: 'McCormacks Strata' vs the
        real existing row 'McCormacks Strata Management' must not become a
        second account when the discovered domain matches the existing one."""
        d, st = store()
        try:
            st.create_account(TENANT, {
                "business_name": "McCormacks Strata Management",
                "website": "https://mccormacks.com.au",
                "segment": "strata",
                "suburb": "Sydney",
            }, now_iso=NOW)
            before = len(st.accounts(TENANT, limit=100))

            collectors = [make_collector("dir_b", [candidate(
                business_name="McCormacks Strata",
                website="https://mccormacks.com.au/about",
                source="dir_b", source_type="directory",
            )])]
            report = bd.run_discovery(st, collectors, now_iso=NOW)

            after = st.accounts(TENANT, limit=100)
            self.assertEqual(len(after), before, "must upsert the existing row, not add one")
            self.assertEqual(report["new_accounts_created"], 0)
            self.assertEqual(report["duplicates_prevented"], 1)
            mcc = [a for a in after if "mccormacks" in a["business_name"].lower()]
            self.assertEqual(len(mcc), 1)
            # the good existing name must survive — a weaker source's shorter
            # name must not clobber it (see TestPreservesExistingData below)
            self.assertEqual(mcc[0]["business_name"], "McCormacks Strata Management")
        finally:
            st.close(); d.cleanup()

    def test_ambiguous_similar_name_without_domain_match_is_not_merged(self):
        """Weak name-only similarity, no corroborating domain: the spec says
        preserve both rather than risk merging two different businesses."""
        d, st = store()
        try:
            st.create_account(TENANT, {
                "business_name": "Apex Strata",
                "website": "https://apexstrata.com.au",
                "segment": "strata",
            }, now_iso=NOW)
            collectors = [make_collector("dir_c", [candidate(
                business_name="Apex Strata Management",
                website="",  # different/unknown site - no corroborating signal
                source="dir_c",
            )])]
            report = bd.run_discovery(st, collectors, now_iso=NOW)
            names = sorted(a["business_name"] for a in st.accounts(TENANT, limit=100))
            self.assertIn("Apex Strata", names)
            self.assertIn("Apex Strata Management", names)
            self.assertEqual(report["new_accounts_created"], 1)
            self.assertEqual(report["possible_duplicates_flagged"], 1)
        finally:
            st.close(); d.cleanup()


class TestOfficialWebsiteIsRecorded(unittest.TestCase):
    def test_official_website_is_recorded(self):
        d, st = store()
        try:
            collectors = [make_collector("dir_a", [candidate(
                business_name="Harbour Facilities Management",
                website="https://harbourfm.com.au",
            )])]
            bd.run_discovery(st, collectors, now_iso=NOW)
            row = next(a for a in st.accounts(TENANT, limit=100)
                      if a["business_name"] == "Harbour Facilities Management")
            self.assertEqual(row["website"], "https://harbourfm.com.au")
        finally:
            st.close(); d.cleanup()


class TestNoFabricatedWebsite(unittest.TestCase):
    def test_no_fabricated_website(self):
        """No website evidence at all -> stays empty, never guessed from the name."""
        d, st = store()
        try:
            collectors = [make_collector("dir_a", [candidate(
                business_name="Unknown Site Painting Prospects Pty Ltd",
                website="",
            )])]
            bd.run_discovery(st, collectors, now_iso=NOW)
            row = next(a for a in st.accounts(TENANT, limit=100)
                      if "Unknown Site" in a["business_name"])
            self.assertEqual(row["website"], "")
        finally:
            st.close(); d.cleanup()

    def test_ambiguous_multiple_candidate_urls_not_guessed(self):
        """normalize_candidate must refuse an ambiguous multi-URL hint rather
        than picking one — this is exercised at the raw-candidate boundary,
        the same place a directory listing with several similar-looking
        links would surface the ambiguity."""
        raw = candidate(website="https://a-example.com.au, https://b-example.com.au")
        c = bd.normalize_candidate(raw)
        self.assertEqual(c.website, "", "a multi-URL/ambiguous hint must not be guessed")


class TestPhoneRegexExtractsAuFormats(unittest.TestCase):
    def test_phone_regex_extracts_au_formats(self):
        text = (
            "Sydney +61 2 8123 4567, Melbourne 03 9123 4567, "
            "Mobile 0412 345 678, Freecall 1300 654 321, "
            "Support 1800 111 222, Brisbane 07 3123 9876"
        )
        found = bd.extract_phones(text)
        self.assertEqual(len(found), 6, found)
        digits = ["".join(ch for ch in f if ch.isdigit()) for f in found]
        # +61 2 8123 4567 normalizes to the same national number as 02 8123 4567
        self.assertTrue(any(dg.endswith("28123456" "7") or dg == "61281234567" for dg in digits))
        self.assertTrue(any(d.startswith("1300") for d in digits))
        self.assertTrue(any(d.startswith("1800") for d in digits))
        self.assertTrue(any(d.startswith("0412") for d in digits))

    def test_phone_dedupes_intl_and_domestic_form_of_same_number(self):
        text = "Call +61 2 9876 5432 or 02 9876 5432 (same line)."
        found = bd.extract_phones(text)
        self.assertEqual(len(found), 1, found)

    def test_phone_regex_ignores_non_phone_numbers(self):
        text = "ABN 12 345 678 901. Invoice #4471123. No phone here."
        self.assertEqual(bd.extract_phones(text), [])


class TestNoFabricatedContactInformation(unittest.TestCase):
    def test_no_fabricated_contact_information(self):
        d, st = store()
        try:
            collectors = [make_collector("dir_a", [candidate(
                business_name="Quiet Property Group",
                phone="", email="",
            )])]
            bd.run_discovery(st, collectors, now_iso=NOW)
            row = next(a for a in st.accounts(TENANT, limit=100)
                      if a["business_name"] == "Quiet Property Group")
            self.assertNotIn("@", row["contact_channel"])
            for fake in ("info@", "contact@", "sales@"):
                self.assertNotIn(fake, row["notes"].lower())
            self.assertEqual(row["contact_channel"], "")
        finally:
            st.close(); d.cleanup()

    def test_extract_emails_never_invents(self):
        self.assertEqual(bd.extract_emails(""), [])
        self.assertEqual(bd.extract_emails("no email in this sentence at all"), [])

    def test_extract_emails_finds_real_ones(self):
        # example.org is IANA-reserved for documentation - not a realistic
        # stand-in for "a real found email" now that placeholder-domain
        # filtering exists (see TestExtractEmailsRejectsPlaceholders).
        found = bd.extract_emails("Contact info@company.com.au or sales@mccormacks.com.au today")
        self.assertEqual(set(e.lower() for e in found),
                         {"info@company.com.au", "sales@mccormacks.com.au"})


class TestPreservesExistingData(unittest.TestCase):
    def test_weaker_source_does_not_blank_existing_website(self):
        d, st = store()
        try:
            st.create_account(TENANT, {
                "business_name": "Solid Facilities Co",
                "website": "https://solidfacilities.com.au",
                "suburb": "Chatswood",
                "segment": "commercial",
            }, now_iso=NOW)
            # A second, weaker source finds the same company (by name match
            # after stripping the legal suffix) but has no website at all.
            collectors = [make_collector("dir_weak", [candidate(
                business_name="Solid Facilities Co Pty Ltd",
                website="",
                suburb="",
            )])]
            bd.run_discovery(st, collectors, now_iso=NOW)
            row = next(a for a in st.accounts(TENANT, limit=100)
                      if "Solid Facilities" in a["business_name"])
            self.assertEqual(row["website"], "https://solidfacilities.com.au",
                             "a blank from a weaker source must not erase a known website")
            self.assertEqual(row["suburb"], "Chatswood")
        finally:
            st.close(); d.cleanup()


class TestRobotsTxtRespected(unittest.TestCase):
    def test_robots_txt_respected(self):
        """A Disallow: /private rule must block that path without touching
        the network (the injected opener must never be called for it)."""
        calls = []

        def fake_robots_fetch(url):
            return "User-agent: *\nDisallow: /private\n"

        def fake_opener(req, timeout):
            calls.append(req.full_url if hasattr(req, "full_url") else req)
            raise AssertionError("must not fetch a disallowed URL")

        gate = bd.RobotsGate(fetch=fake_robots_fetch)
        self.assertFalse(gate.allowed("https://example.com/private/page"))
        self.assertTrue(gate.allowed("https://example.com/contact"))

        throttle = bd.HostThrottle(min_interval_s=0, jitter_s=0)
        result = bd.fetch_url(
            "https://example.com/private/page",
            opener=fake_opener, robots=gate, throttle=throttle,
            now=lambda: 0.0, sleep=lambda s: None,
        )
        self.assertEqual(result["kind"], "robots_disallowed")
        self.assertFalse(result["ok"])
        self.assertEqual(calls, [], "a disallowed URL must never reach the opener")

    def test_robots_fetch_failure_fails_open(self):
        """No robots.txt reachable (404/network error) -> treated as allowed,
        matching the common convention that absence of robots.txt means no
        restriction is declared."""
        gate = bd.RobotsGate(fetch=lambda url: None)
        self.assertTrue(gate.allowed("https://example.com/anything"))


class TestRateLimitPerHost(unittest.TestCase):
    def test_rate_limit_per_host(self):
        throttle = bd.HostThrottle(min_interval_s=5.0, jitter_s=0.0)
        self.assertEqual(throttle.wait_seconds("example.com", now=100.0), 0.0,
                         "first request to a host waits nothing")
        throttle.record("example.com", now=100.0)
        self.assertAlmostEqual(throttle.wait_seconds("example.com", now=101.0), 4.0)
        self.assertEqual(throttle.wait_seconds("example.com", now=106.0), 0.0,
                         "after the interval has elapsed, no more waiting is required")
        # a different host is independent — concurrency=1 is per-host, not global
        self.assertEqual(throttle.wait_seconds("other.example.com", now=101.0), 0.0)

    def test_fetch_url_serializes_same_host_requests(self):
        """Two consecutive fetch_url calls to the same host must sleep for
        the configured minimum interval between them (never issued back to
        back), proving per-host concurrency=1 with a real delay."""
        slept = []
        clock = {"t": 0.0}

        def fake_opener(req, timeout):
            class Resp:
                status = 200
                def read(self_):
                    return b"<html>ok</html>"
                def __enter__(self_):
                    return self_
                def __exit__(self_, *a):
                    return False
                def getcode(self_):
                    return 200
            return Resp()

        def fake_sleep(seconds):
            slept.append(seconds)
            clock["t"] += seconds

        gate = bd.RobotsGate(fetch=lambda url: None)
        throttle = bd.HostThrottle(min_interval_s=3.0, jitter_s=0.0)
        for _ in range(2):
            bd.fetch_url("https://same-host.example.com/page",
                        opener=fake_opener, robots=gate, throttle=throttle,
                        now=lambda: clock["t"], sleep=fake_sleep)
        self.assertTrue(any(s >= 3.0 for s in slept),
                        f"second request to the same host must wait, slept={slept}")


class TestMultipleSourcesAreSupported(unittest.TestCase):
    def test_multiple_sources_are_supported(self):
        collectors = [
            make_collector("search_engine", [candidate(
                business_name="Alpha Property Services", website="https://alphaprop.com.au",
                source_type="search")], source_type="search",
                domains=("alphaprop.com.au",)),
            make_collector("industry_directory", [candidate(
                business_name="Beta Facility Group", website="https://betafacility.com.au",
                source_type="directory")], source_type="directory",
                domains=("betafacility.com.au",)),
            make_collector("tender_portal", [candidate(
                business_name="Gamma Construction", website="",
                source_type="tender")], source_type="tender"),
            make_collector("company_website", [candidate(
                business_name="Delta Strata", website="https://deltastrata.com.au",
                source_type="website")], source_type="website",
                domains=("deltastrata.com.au",)),
        ]
        d, st = store()
        try:
            report = bd.run_discovery(st, collectors, now_iso=NOW)
            self.assertEqual(report["sources_checked"], 4)
            self.assertEqual(report["new_accounts_created"], 4)
            self.assertGreaterEqual(report["domains_checked"], 3)
            names = {a["business_name"] for a in st.accounts(TENANT, limit=100)}
            for expected in ("Alpha Property Services", "Beta Facility Group",
                            "Gamma Construction", "Delta Strata"):
                self.assertIn(expected, names)
            # top_sources must attribute candidates back to their own source
            top_ids = {row["source_id"] for row in report["top_sources"]}
            self.assertTrue({"search_engine", "industry_directory",
                            "tender_portal", "company_website"} <= top_ids)
        finally:
            st.close(); d.cleanup()

    def test_one_failing_source_does_not_stop_the_others(self):
        def boom():
            raise RuntimeError("blocked: login required")

        collectors = [
            bd.SourceCollector(source_id="broken", source_type="directory", collect=boom),
            make_collector("good_source", [candidate(business_name="Still Found Pty Ltd")]),
        ]
        d, st = store()
        try:
            report = bd.run_discovery(st, collectors, now_iso=NOW)
            self.assertEqual(report["new_accounts_created"], 1)
            self.assertGreaterEqual(len(report["errors"]), 1)
            self.assertEqual(report["sources_checked"], 2)
        finally:
            st.close(); d.cleanup()


class TestMaxCandidatesIsOperationalNotArchitectural(unittest.TestCase):
    def test_max_candidates_caps_a_run_without_being_hardcoded(self):
        # Distinct websites too - otherwise every synthetic company shares
        # the fixture default domain and Tier A correctly merges them,
        # which would test identity resolution instead of the candidate cap.
        many = [candidate(business_name=f"Company {i} Pty Ltd",
                          website=f"https://company{i}.example.com.au")
               for i in range(10)]
        d, st = store()
        try:
            collectors = [make_collector("big_source", many)]
            report = bd.run_discovery(st, collectors, now_iso=NOW, max_candidates=3)
            self.assertEqual(report["candidates_discovered"], 3)
            self.assertEqual(len(st.accounts(TENANT, limit=100)), 3)
        finally:
            st.close(); d.cleanup()

    def test_no_max_candidates_means_unlimited(self):
        many = [candidate(business_name=f"Company {i} Pty Ltd",
                          website=f"https://company{i}.example.com.au")
               for i in range(10)]
        d, st = store()
        try:
            collectors = [make_collector("big_source", many)]
            report = bd.run_discovery(st, collectors, now_iso=NOW, max_candidates=None)
            self.assertEqual(report["candidates_discovered"], 10)
        finally:
            st.close(); d.cleanup()


class TestDryRunWritesNothing(unittest.TestCase):
    def test_dry_run_does_not_write_to_the_store(self):
        d, st = store()
        try:
            before = len(st.accounts(TENANT, limit=100))
            collectors = [make_collector("dir_a", [candidate()])]
            report = bd.run_discovery(st, collectors, now_iso=NOW, dry_run=True)
            after = len(st.accounts(TENANT, limit=100))
            self.assertEqual(before, after, "dry-run must not persist any account")
            self.assertEqual(report["new_accounts_created"], 1,
                             "dry-run still reports what WOULD have happened")
        finally:
            st.close(); d.cleanup()


# A REAL captured excerpt of https://html.duckduckgo.com/html/ for the query
# "strata management companies Parramatta NSW" (POST, honest USER_AGENT,
# robots.txt for this exact host verified Allow: / beforehand) - three
# results: two real companies and one directory/comparison site
# (comparestrata.com), which is exactly why KNOWN_AGGREGATOR_HOSTS exists.
# This is embedded verbatim (not reconstructed from memory) so the parser
# is tested against the real thing, per the project's own "run it against
# the code, not the description of the code" standard.
REAL_DDG_RESULT_HTML = """
<div class="result results_links results_links_deep web-result ">
                  <div class="links_main links_deep result__body"> <!-- This is the visible part -->

                      <h2 class="result__title">
                        <a rel="nofollow" class="result__a" href="https://www.strataandco.com.au/service-areas/western-sydney/parramatta/">Strata Management - Parramatta | Strata &amp; Co.</a>
                      </h2>

                      <div class="result__extras">
                        <div class="result__extras__url">
                          <a class="result__url" href="https://www.strataandco.com.au/service-areas/western-sydney/parramatta/">
                            www.strataandco.com.au/service-areas/western-sydney/parramatta/
                          </a>
                        </div>
                      </div>
                        <a class="result__snippet" href="https://www.strataandco.com.au/service-areas/western-sydney/parramatta/"><b>Strata</b> &amp; Co. are your fully licensed, local <b>strata</b> managers that provide the best priced <b>strata</b> <b>management</b> services in <b>Parramatta</b> and surrounding suburbs.</a>
                    <div class="clear"></div>
                  </div>
                </div>
                <div class="result results_links results_links_deep web-result ">
                  <div class="links_main links_deep result__body">
                      <h2 class="result__title">
                        <a rel="nofollow" class="result__a" href="https://comparestrata.com/nsw/areas/lga/parramatta/">Parramatta Strata Managers | CompareStrata</a>
                      </h2>
                      <div class="result__extras">
                        <div class="result__extras__url">
                          <a class="result__url" href="https://comparestrata.com/nsw/areas/lga/parramatta/">
                            comparestrata.com/nsw/areas/lga/parramatta/
                          </a>
                        </div>
                      </div>
                        <a class="result__snippet" href="https://comparestrata.com/nsw/areas/lga/parramatta/">The <b>Parramatta</b> council area in Greater Sydney has a substantial <b>strata</b> market with 2,781 registered schemes covering 79,588 lots.</a>
                    <div class="clear"></div>
                  </div>
                </div>
                <div class="result results_links results_links_deep web-result ">
                  <div class="links_main links_deep result__body">
                      <h2 class="result__title">
                        <a rel="nofollow" class="result__a" href="https://www.strataunited.com.au/parramatta">Strata Management Parramatta | Local Strata Managers</a>
                      </h2>
                      <div class="result__extras">
                        <div class="result__extras__url">
                          <a class="result__url" href="https://www.strataunited.com.au/parramatta">
                            www.strataunited.com.au/parramatta
                          </a>
                        </div>
                      </div>
                        <a class="result__snippet" href="https://www.strataunited.com.au/parramatta"><b>Parramatta&#x27;s</b> trusted <b>strata</b> <b>management</b> specialists. <b>Strata</b> United provides local expertise, transparent fees and no lock-in contracts.</a>
                    <div class="clear"></div>
                  </div>
                </div>
"""


class TestDuckDuckGoRealSearchBackend(unittest.TestCase):
    def test_parse_duckduckgo_html_extracts_real_companies(self):
        results = bd.parse_duckduckgo_html(REAL_DDG_RESULT_HTML)
        names = [r["business_name"] for r in results]
        sites = [r["website"] for r in results]
        self.assertIn("https://www.strataandco.com.au/service-areas/western-sydney/parramatta/", sites)
        self.assertIn("https://www.strataunited.com.au/parramatta", sites)
        self.assertTrue(any("Strata" in n for n in names))

    def test_parse_duckduckgo_html_filters_known_aggregators(self):
        """The comparestrata.com result (a comparison/directory site, not a
        prospect company) must be excluded - a quality filter, not
        fabrication: nothing is invented, one noisy row is skipped."""
        results = bd.parse_duckduckgo_html(REAL_DDG_RESULT_HTML)
        sites = [r["website"] for r in results]
        self.assertFalse(any("comparestrata.com" in s for s in sites))
        self.assertEqual(len(results), 2)

    def test_aggregator_list_covers_hosts_seen_in_a_real_run(self):
        """Regression lock for hosts a real live run against
        html.duckduckgo.com actually surfaced as noise (company databases,
        review platforms, market-research firms) — not guesses."""
        for host in ("ensun.io", "companydata.com", "clutch.co",
                    "mordorintelligence.com", "aeroleads.com", "productreview.com.au",
                    "au.seek.com", "au.jora.com", "australiayp.com"):
            self.assertIn(host, bd.KNOWN_AGGREGATOR_HOSTS)

    def test_parse_duckduckgo_html_excludes_non_australian_tlds(self):
        """Defense in depth alongside the region-disambiguation fix: this is
        an Australia-only discovery agent, so a .uk/.co.uk (or other
        obviously non-AU) result is out of scope regardless of how it was
        found - a real run surfaced 10 UK 'Newcastle upon Tyne' facilities
        firms from one under-specified query before this existed."""
        uk_html = REAL_DDG_RESULT_HTML.replace(
            "www.strataunited.com.au/parramatta", "www.somefirm.co.uk/newcastle")
        results = bd.parse_duckduckgo_html(uk_html)
        self.assertFalse(any(".co.uk" in r["website"] for r in results))

    def test_parse_duckduckgo_html_empty_or_no_results_page(self):
        self.assertEqual(bd.parse_duckduckgo_html(""), [])
        self.assertEqual(bd.parse_duckduckgo_html("<html><body>no results</body></html>"), [])

    def test_duckduckgo_search_raises_harvest_error_on_blocked_fetch(self):
        def fake_fetch(url, **kw):
            return {"ok": False, "kind": "blocked_403", "status": 403, "body": None, "url": url}

        search = bd.duckduckgo_search(
            robots=bd.RobotsGate(fetch=lambda u: None),
            throttle=bd.HostThrottle(min_interval_s=0, jitter_s=0),
            fetch=fake_fetch,
        )
        with self.assertRaises(bd.HarvestError):
            search("strata management NSW")

    def test_duckduckgo_search_returns_parsed_results_on_success(self):
        def fake_fetch(url, **kw):
            self.assertIn("data", kw, "search must POST a body, not a query-string GET")
            self.assertIsNotNone(kw["data"])
            return {"ok": True, "kind": "ok", "status": 200,
                   "body": REAL_DDG_RESULT_HTML, "url": url}

        search = bd.duckduckgo_search(
            robots=bd.RobotsGate(fetch=lambda u: None),
            throttle=bd.HostThrottle(min_interval_s=0, jitter_s=0),
            fetch=fake_fetch,
        )
        results = search("strata management Parramatta NSW")
        self.assertEqual(len(results), 2)

    def test_duckduckgo_search_wires_into_query_collector(self):
        """End-to-end (still offline): the real backend function plugs
        straight into make_query_search_collector with no adapter needed."""
        def fake_fetch(url, **kw):
            return {"ok": True, "kind": "ok", "status": 200,
                   "body": REAL_DDG_RESULT_HTML, "url": url}

        search = bd.duckduckgo_search(
            robots=bd.RobotsGate(fetch=lambda u: None),
            throttle=bd.HostThrottle(min_interval_s=0, jitter_s=0),
            fetch=fake_fetch,
        )
        collector = bd.make_query_search_collector(
            "duckduckgo", search=search, regions=("Parramatta",), industries=("strata management",))
        result = collector.collect()
        self.assertEqual(len(result.candidates), 2)
        self.assertEqual(result.errors, ())


class TestSearchCollectorCircuitBreaks(unittest.TestCase):
    def test_repeatedly_failing_backend_stops_early_with_one_summary_error(self):
        """A structurally broken/unavailable search backend must not be
        retried across the entire query matrix (hundreds of queries) - that
        is hammering a source already proven dead. A few consecutive
        failures should stop that collector and report ONE clear reason,
        not one near-identical error string per query."""
        calls = []

        def always_fails(query):
            calls.append(query)
            raise bd.HarvestError("no search backend configured for this run")

        collector = bd.make_query_search_collector(
            "flaky_search", search=always_fails,
            regions=("NSW", "VIC", "QLD"), industries=("strata", "facilities", "property"))
        result = collector.collect()
        self.assertLess(len(calls), 9, "must not try every query once the backend is clearly broken")
        self.assertEqual(len(result.errors), 1, result.errors)
        self.assertIn("no search backend configured", result.errors[0])
        self.assertEqual(result.candidates, ())

    def test_search_backend_recovers_after_transient_failures_keeps_going(self):
        """A backend that fails a couple of times then starts returning
        results must NOT be tripped by the same breaker - only a run of
        consecutive failures circuit-breaks, not occasional ones."""
        state = {"n": 0}

        def flaky_then_ok(query):
            state["n"] += 1
            if state["n"] <= 2:
                raise bd.HarvestError("transient")
            return [{"business_name": f"Result for {query}", "website": ""}]

        collector = bd.make_query_search_collector(
            "recovering_search", search=flaky_then_ok,
            regions=("NSW",), industries=("strata", "facilities", "property", "construction"))
        result = collector.collect()
        self.assertGreaterEqual(len(result.candidates), 1)


class TestBroadQueryStrategy(unittest.TestCase):
    def test_build_search_queries_covers_many_states_and_industries(self):
        queries = bd.build_search_queries()
        self.assertGreater(len(queries), 20,
                           "query strategy must not be a tiny fixed handful")
        joined = " ".join(queries).lower()
        for state in ("nsw", "vic", "qld", "wa"):
            self.assertIn(state, joined)
        for term in ("strata", "facilities management", "property management"):
            self.assertIn(term, joined)
        self.assertEqual(len(queries), len(set(queries)), "no duplicate queries")

    def test_region_names_are_disambiguated_from_same_named_overseas_cities(self):
        """A live run against a real search backend proved this isn't
        theoretical: bare 'Newcastle' pulled in Newcastle-upon-Tyne, UK
        results (10 of 33 new accounts in one real run were UK companies -
        .co.uk domains, 'Tyne and Wear' addresses) because the query never
        said which Newcastle. Same risk exists for 'Perth' (Scotland) and
        is cheap to close for every city by just always naming the state."""
        ambiguous_cities = ("Newcastle", "Perth", "Sydney", "Melbourne", "Brisbane")
        for city in ambiguous_cities:
            self.assertNotIn(city, bd.AU_REGIONS,
                             f"{city!r} must carry its state (e.g. '{city} NSW'), "
                             f"not appear bare — it is not uniquely Australian")

    def test_industry_terms_target_customers_not_competitors(self):
        """painting_b2b_accounts is a CUSTOMER prospect list (the real 74
        existing rows are strata/facility/property/government companies -
        zero painting companies among them). A term that searches for other
        painting businesses surfaces competitors, not prospects, and a live
        run caught exactly this: it must never be in the list."""
        joined = " ".join(bd.INDUSTRY_TERMS).lower()
        self.assertNotIn("painting compan", joined)

    def test_query_prefix_samples_broadly_across_industries(self):
        """A capped run (--max-queries-per-source) takes a PREFIX of this
        list. If industry were the outer loop, a small prefix would just be
        one industry across many regions - exactly the live-run bug where
        the first 12 queries were all 'commercial painting companies' in 12
        different cities and never reached strata/facility/property at all.
        The first dozen queries must already touch several industries."""
        prefix = bd.build_search_queries()[:12]
        distinct_industries = {q.rsplit(" ", 1)[0] if " " in q else q for q in prefix}
        # a looser, robust check: how many of the known INDUSTRY_TERMS values
        # appear as a literal prefix of at least one of the first 12 queries
        touched = {ind for ind in bd.INDUSTRY_TERMS
                  if any(q.startswith(ind) for q in prefix)}
        self.assertGreaterEqual(len(touched), 4,
                                f"first 12 queries only touched {touched!r}")

    def test_build_search_queries_is_extensible(self):
        base = bd.build_search_queries()
        extended = bd.build_search_queries(
            industries=tuple(bd.INDUSTRY_TERMS) + ("solar farm operators",))
        self.assertGreater(len(extended), len(base))


class TestNormalizeAndDomainHelpers(unittest.TestCase):
    def test_registrable_domain_collapses_variants(self):
        variants = [
            "https://mccormacks.com.au/contact",
            "http://www.mccormacks.com.au/",
            "mccormacks.com.au",
            "WWW.MCCORMACKS.COM.AU",
        ]
        domains = {bd.registrable_domain(v) for v in variants}
        self.assertEqual(domains, {"mccormacks.com.au"})

    def test_normalize_name_strips_legal_suffix_only(self):
        self.assertEqual(bd.normalize_name("ABC Painting Pty Ltd"), bd.normalize_name("ABC Painting"))
        # business-descriptor words are NOT stripped - they can be load-bearing
        self.assertNotEqual(bd.normalize_name("McCormacks Strata"),
                            bd.normalize_name("McCormacks Strata Management"))


class TestCleanTitleName(unittest.TestCase):
    """Real business_name values a live run put straight into the DB before
    this fix (confirmed by querying painting.sqlite directly), used as the
    test fixtures rather than invented strings."""

    def test_bare_generic_word_is_unreliable(self):
        self.assertEqual(bd.clean_title_name("Home"), "")

    def test_first_segment_generic_falls_through_to_later_segment(self):
        # Real row: fma.com.au's own <title> was literally "Home"; a
        # DIFFERENT real row shows the same shape with an actual name behind
        # the generic lead-in.
        self.assertEqual(
            bd.clean_title_name("Home - Marion Facilities Management"),
            "Marion Facilities Management")

    def test_brand_in_last_of_three_pipe_segments(self):
        self.assertEqual(
            bd.clean_title_name(
                "Facilities Management Company | Sydney, Melbourne & Brisbane | NFM"),
            "NFM")

    def test_tight_pipe_spacing_still_splits(self):
        # Real title had no space before the second segment's own leading
        # word ("Sydney |Facilities...").
        self.assertEqual(
            bd.clean_title_name(
                "Facilities Management Sydney |Facilities Management Companies Sydney"),
            "")  # every segment is generic-only here - correctly unreliable

    def test_em_dash_separator(self):
        self.assertEqual(
            bd.clean_title_name("City Facilities Management Australia — Innovative Solutions"),
            "City Facilities Management Australia")

    def test_mid_word_hyphen_is_not_a_split_point(self):
        self.assertEqual(bd.clean_title_name("Sydney-Wide Facility Group"),
                         "Sydney-Wide Facility Group")

    def test_plain_reliable_title_passes_through_unchanged(self):
        self.assertEqual(bd.clean_title_name("SPM Facilities Management"),
                         "SPM Facilities Management")

    def test_empty_input(self):
        self.assertEqual(bd.clean_title_name(""), "")

    def test_search_engine_truncation_ellipsis_is_stripped(self):
        # Real stored value found in painting.sqlite during this fix:
        # length 10, literal "Aurora ..." - the search backend's own
        # snippet truncation, not a display artifact - from the full title
        # "Facilities Management Sydney | 24/7 Commercial Maintenance |
        # Aurora ...".
        self.assertEqual(
            bd.clean_title_name(
                "Facilities Management Sydney | 24/7 Commercial Maintenance | Aurora ..."),
            "Aurora")


class TestLooksLikeArticle(unittest.TestCase):
    """Real (url, title) pairs from the same live run."""

    def test_top_n_url_slug(self):
        self.assertTrue(bd.looks_like_article(
            url="https://qmt.com.au/top-20-facility-management-companies-in-australia/",
            title="Top 20 Facility Management Companies in Australia 2026 Guide"))

    def test_comparison_title_with_no_article_url_pattern(self):
        # This one's URL has no "/top-"/"/blog/"/etc - only the title marks
        # it as a listicle, and it is hosted on a real company's own domain.
        self.assertTrue(bd.looks_like_article(
            url="https://www.cameronfacilities.com.au/what-are-the-leading-integrated-facilities-management-providers-in-australia/",
            title="Top Facilities Management Companies in Australia Compared"))

    def test_ordinary_company_page_is_not_an_article(self):
        self.assertFalse(bd.looks_like_article(
            url="https://nationalfm.com.au/", title="National Facilities Management"))
        self.assertFalse(bd.looks_like_article(
            url="https://www.spmfm.com.au/", title="SPM Facilities Management"))

    def test_blog_path_pattern(self):
        self.assertTrue(bd.looks_like_article(
            url="https://example.com.au/blog/best-strata-managers", title="Anything"))


class TestExtractOgSiteName(unittest.TestCase):
    def test_extracts_real_captured_markup(self):
        # Attribute order exactly as served by nationalfm.com.au (verified
        # live during this fix).
        html = '<meta property="og:site_name" content="National Facilities Management" />'
        self.assertEqual(bd.extract_og_site_name(html), "National Facilities Management")

    def test_reversed_attribute_order(self):
        html = '<meta content="Cameron Facilities" property="og:site_name" />'
        self.assertEqual(bd.extract_og_site_name(html), "Cameron Facilities")

    def test_absent_tag_returns_empty(self):
        self.assertEqual(bd.extract_og_site_name("<title>Home</title>"), "")


class TestExtractSchemaOrgName(unittest.TestCase):
    def test_extracts_organization_name(self):
        html = """
        <script type="application/ld+json">
        {"@context": "https://schema.org", "@type": "Organization",
         "name": "National Facilities Management", "url": "https://nationalfm.com.au"}
        </script>"""
        self.assertEqual(bd.extract_schema_org_name(html), "National Facilities Management")

    def test_list_of_ld_objects(self):
        html = """
        <script type="application/ld+json">
        [{"@type": "WebPage", "name": "Home"},
         {"@type": "LocalBusiness", "name": "Marion Facilities Management"}]
        </script>"""
        self.assertEqual(bd.extract_schema_org_name(html), "Marion Facilities Management")

    def test_malformed_json_does_not_raise(self):
        html = '<script type="application/ld+json">{not valid json</script>'
        self.assertEqual(bd.extract_schema_org_name(html), "")

    def test_no_ld_block_returns_empty(self):
        self.assertEqual(bd.extract_schema_org_name("<title>Home</title>"), "")


class TestExtractBusinessNamePriorityChain(unittest.TestCase):
    def test_og_site_name_wins_over_messy_title(self):
        html = ('<title>Top Facilities Management Companies in Australia Compared</title>'
               '<meta property="og:site_name" content="Cameron Facilities" />')
        name = bd.extract_business_name(
            original_title="Top Facilities Management Companies in Australia Compared",
            fetched_html=html)
        self.assertEqual(name, "Cameron Facilities")

    def test_falls_back_to_cleaned_fetched_title_when_no_meta_tags(self):
        html = "<title>Facilities Management Company | Sydney, Melbourne &amp; Brisbane | NFM</title>"
        name = bd.extract_business_name(original_title="irrelevant", fetched_html=html)
        self.assertEqual(name, "NFM")

    def test_falls_back_to_original_search_title_when_fetch_unavailable(self):
        # fetched_html=None - the real pacificbmg.com.au scenario: a live
        # 403 on the enrichment fetch during this fix.
        name = bd.extract_business_name(
            original_title="SPM Facilities Management", fetched_html=None)
        self.assertEqual(name, "SPM Facilities Management")

    def test_fetched_page_says_only_home_and_no_meta_tags_drops_to_original(self):
        # The real fma.com.au case: <title>Home</title>, no og:site_name, no
        # JSON-LD. If the ORIGINAL search title was also just "Home", there
        # is genuinely nothing reliable anywhere.
        html = "<title>Home</title>"
        name = bd.extract_business_name(original_title="Home", fetched_html=html)
        self.assertEqual(name, "")


class TestExtractEmailsRejectsPlaceholders(unittest.TestCase):
    """A live fetch during this fix found extract_emails returning
    "youremail@mail.com" straight out of a Contact Form 7 <input
    placeholder="..."> attribute on a real site's homepage - real HTML,
    not a real contact."""

    def test_form_placeholder_attribute_is_rejected(self):
        html = ('<input name="your-email" placeholder="youremail@mail.com" '
               'class="wpcf7-form-control wpcf7-email" />')
        self.assertEqual(bd.extract_emails(html), [])

    def test_common_documentation_domains_are_rejected(self):
        for addr in ("info@example.com", "contact@example.org", "sales@test.com"):
            self.assertEqual(bd.extract_emails(f"Email us: {addr}"), [],
                             f"{addr} should have been rejected as a placeholder")

    def test_real_email_still_passes_through(self):
        self.assertEqual(bd.extract_emails("Contact mail@nationalfm.com.au today"),
                         ["mail@nationalfm.com.au"])


class TestContactExtractionIgnoresHiddenMarkup(unittest.TestCase):
    """probe_official_website must extract from VISIBLE page text, not raw
    HTML - a live fetch during this fix found a real page's own <meta
    name="twitter:data1" content="daniel@daodigital.com.au" /> (Twitter
    Card "Written by" author-credit metadata, almost certainly the
    site's web developer, not the business) landing in a candidate's
    contact info verbatim."""

    def test_meta_tag_content_is_not_treated_as_displayed_contact(self):
        html = (
            '<meta name="twitter:label1" content="Written by" />'
            '<meta name="twitter:data1" content="daniel@daodigital.com.au" />'
            '<p>Call 1300 820 330 or email mail@nationalfm.com.au for enquiries.</p>'
        )

        def fetch(url):
            return {"ok": True, "kind": "ok", "status": 200, "body": html, "url": url}

        probe = bd.probe_official_website("https://nationalfm.com.au/", fetch=fetch)
        self.assertEqual(probe["emails"], ["mail@nationalfm.com.au"])
        self.assertNotIn("daniel@daodigital.com.au", probe["emails"])

    def test_form_placeholder_attribute_is_not_treated_as_displayed_contact(self):
        html = '<input placeholder="youremail@mail.com" /><p>No real email on this page.</p>'

        def fetch(url):
            return {"ok": True, "kind": "ok", "status": 200, "body": html, "url": url}

        probe = bd.probe_official_website("https://example.com.au/", fetch=fetch)
        self.assertEqual(probe["emails"], [])


class TestExtractBusinessNameRejectsPollutedOgSiteName(unittest.TestCase):
    """og:site_name is the business's OWN declared name, but a live fetch
    during this fix found a real WordPress site whose og:site_name was
    LITERALLY "Australis Facilities Management | Just another WordPress
    site" - the CMS's uncustomized default tagline, never edited by the
    site owner. "Declared by the business" does not mean "the business
    actually edited it"."""

    def test_wordpress_default_tagline_is_stripped(self):
        html = ('<meta property="og:site_name" '
               'content="Australis Facilities Management | Just another WordPress site" />')
        name = bd.extract_business_name(original_title="irrelevant", fetched_html=html)
        self.assertEqual(name, "Australis Facilities Management")

    def test_clean_og_site_name_is_unaffected(self):
        html = '<meta property="og:site_name" content="National Facilities Management" />'
        name = bd.extract_business_name(original_title="irrelevant", fetched_html=html)
        self.assertEqual(name, "National Facilities Management")


class TestClassifyCandidate(unittest.TestCase):
    def test_strata_segment_is_likely_customer(self):
        self.assertEqual(
            bd.classify_candidate(segment="strata", text="strata management services"),
            "likely_customer")

    def test_pure_facility_management_is_uncertain(self):
        self.assertEqual(
            bd.classify_candidate(segment="facility_management",
                                  text="facilities management services Australia"),
            "uncertain")

    def test_explicit_painting_self_offer_is_likely_provider(self):
        self.assertEqual(
            bd.classify_candidate(segment="facility_management",
                                  text="our in-house painting team handles all repaints"),
            "likely_provider")

    def test_property_management_text_hint_overrides_unknown_segment(self):
        self.assertEqual(
            bd.classify_candidate(segment="commercial",
                                  text="full property management and body corporate services"),
            "likely_customer")


class TestUnreliableNameDropsCandidate(unittest.TestCase):
    def test_normalize_candidate_drops_when_name_extraction_yields_empty(self):
        """End-to-end wiring check: an enrichment step that could not find a
        reliable name must result in the candidate being dropped by the
        SAME existing rule normalize_candidate already has for a missing
        business_name - no new drop path needed, just make sure enrichment
        actually produces "" rather than a placeholder."""
        raw = {"business_name": "", "website": "https://fma.com.au/",
              "source": "web_search_b2b_prospects", "source_type": "search"}
        self.assertIsNone(bd.normalize_candidate(raw))


class TestWebsiteEnricherAddsContactAndClassification(unittest.TestCase):
    def _fake_fetch(self, pages: dict):
        def fetch(url, **kw):
            for path_marker, body in pages.items():
                if url.rstrip("/").endswith(path_marker):
                    return {"ok": True, "kind": "ok", "status": 200, "body": body, "url": url}
            return {"ok": False, "kind": "error", "status": None, "body": None, "url": url}
        return fetch

    def test_finds_name_contact_and_classification_from_real_shaped_page(self):
        homepage = (
            '<title>Home</title>'
            '<meta property="og:site_name" content="National Facilities Management" />')
        contact_page = (
            '<title>Contact</title>'
            '<p>Call us on 1300 820 330 or email mail@nationalfm.com.au. '
            'We manage strata and body corporate property portfolios.</p>')
        fetch = self._fake_fetch({
            "nationalfm.com.au": homepage,
            "nationalfm.com.au/contact": contact_page,
        })
        enrich = bd.make_website_enricher(
            fetch=fetch, robots=bd.RobotsGate(fetch=lambda u: None),
            throttle=bd.HostThrottle(min_interval_s=0, jitter_s=0))
        raw = {"business_name": "Facilities Management Company | Sydney | NFM",
              "website": "https://nationalfm.com.au/", "industry": "facility management NSW"}
        out = enrich(raw)
        self.assertEqual(out["business_name"], "National Facilities Management")
        self.assertEqual(out["phone"], "1300 820 330")
        self.assertEqual(out["email"], "mail@nationalfm.com.au")
        self.assertEqual(out["classification"], "likely_customer")  # strata/body corporate text hint
        self.assertEqual(out["enrichment_status"], "found")

    def test_no_contact_on_page_is_recorded_honestly_not_fabricated(self):
        fetch = self._fake_fetch({"example.com.au": "<title>Example Co</title>"})
        enrich = bd.make_website_enricher(
            fetch=fetch, robots=bd.RobotsGate(fetch=lambda u: None),
            throttle=bd.HostThrottle(min_interval_s=0, jitter_s=0))
        out = enrich({"business_name": "Example Co", "website": "https://example.com.au/"})
        self.assertEqual(out.get("phone", ""), "")
        self.assertEqual(out.get("email", ""), "")
        self.assertEqual(out["enrichment_status"], "no_contact_found")

    def test_every_path_blocked_is_unreachable_not_no_contact_found(self):
        def all_blocked(url, **kw):
            return {"ok": False, "kind": "blocked_403", "status": 403, "body": None, "url": url}
        enrich = bd.make_website_enricher(
            fetch=all_blocked, robots=bd.RobotsGate(fetch=lambda u: None),
            throttle=bd.HostThrottle(min_interval_s=0, jitter_s=0))
        out = enrich({"business_name": "Facilities Management Sydney |Facilities Management Companies Sydney",
                     "website": "https://www.pacificbmg.com.au/services/facilities-management/"})
        self.assertEqual(out["enrichment_status"], "unreachable")
        self.assertEqual(out["business_name"], "")  # no reliable segment either - correctly drops

    def test_no_website_is_marked_and_falls_back_to_title_cleaning(self):
        enrich = bd.make_website_enricher(
            fetch=lambda *a, **k: {"ok": False, "kind": "error", "status": None, "body": None, "url": ""},
            robots=bd.RobotsGate(fetch=lambda u: None),
            throttle=bd.HostThrottle(min_interval_s=0, jitter_s=0))
        out = enrich({"business_name": "SPM Facilities Management", "website": ""})
        self.assertEqual(out["enrichment_status"], "no_website")
        self.assertEqual(out["business_name"], "SPM Facilities Management")


class TestAutoDiscoveryTagOnlyOnNewAccounts(unittest.TestCase):
    """The critical safety property: this agent's own structured tags must
    never be written into an account it did not itself just create -
    stamping "UNVERIFIED" onto one of the 74 hand-researched accounts would
    be actively destructive, not merely unhelpful."""

    def _candidate(self):
        return bd.Candidate(
            business_name="Test Co", website="https://testco.com.au",
            source="web_search_b2b_prospects", source_type="search",
            classification="likely_customer", enrichment_status="found")

    def test_brand_new_account_gets_tagged(self):
        payload, changed = bd.merge_account(self._candidate(), None)
        self.assertIn(bd.AUTO_DISCOVERY_TAG, payload["notes"])
        self.assertIn("CLASSIFICATION: likely_customer", payload["notes"])
        self.assertIn("ENRICHMENT: found", payload["notes"])
        self.assertTrue(changed)

    def test_matched_existing_account_is_never_tagged(self):
        existing = {
            "account_id": "lead:acct:test-co", "business_name": "Test Co",
            "website": "https://testco.com.au", "notes": "Some hand-written research note.",
            "contact_channel": "", "suburb": "", "service_area": "", "evidence_url": "",
            "segment": "strata", "stage": "researched",
        }
        payload, changed = bd.merge_account(self._candidate(), existing)
        self.assertNotIn(bd.AUTO_DISCOVERY_TAG, payload["notes"])
        self.assertNotIn("CLASSIFICATION:", payload["notes"])
        self.assertNotIn("ENRICHMENT:", payload["notes"])
        self.assertIn("Some hand-written research note.", payload["notes"])


class TestSearchParsingExcludesArticles(unittest.TestCase):
    def test_article_result_is_dropped_from_search_parsing(self):
        html = (
            '<a rel="nofollow" class="result__a" '
            'href="https://qmt.com.au/top-20-facility-management-companies-in-australia/">'
            'Top 20 Facility Management Companies in Australia 2026 Guide</a>'
            '<a rel="nofollow" class="result__a" href="https://nationalfm.com.au/">'
            'Facilities Management Company | Sydney, Melbourne &amp; Brisbane | NFM</a>'
        )
        results = bd.parse_duckduckgo_html(html)
        sites = [r["website"] for r in results]
        self.assertNotIn("https://qmt.com.au/top-20-facility-management-companies-in-australia/", sites)
        self.assertIn("https://nationalfm.com.au/", sites)


if __name__ == "__main__":
    unittest.main()
