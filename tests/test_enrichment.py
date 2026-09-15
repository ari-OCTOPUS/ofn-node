"""Contact-enrichment agent tests — fully offline.

Every HTTP boundary is injected, so this suite never touches the network and
never depends on a live site still looking the way it did today. Temp
databases use tempfile.TemporaryDirectory() as a managed context (never a
bare mkdtemp — tests/test_tmpdir.py forbids that repo-wide, because
unmanaged temp dirs once filled this board's tmpfs and sent boot into SAFE
MODE).

Fixtures are modelled on markup and numbers actually observed while
researching Sydney strata/property companies for this project, including
the specific false positives that bit earlier runs.
"""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from ofn.enrichment import evidence as ev
from ofn.enrichment import lessons as ls
from ofn.enrichment import phones as ph
from ofn.enrichment import researcher as rs
from ofn.enrichment import sources as src
from ofn.enrichment import strategy as st

RUN = "testrun00001"


def _db(tmp: str) -> sqlite3.Connection:
    """A painting.sqlite-shaped database with just the columns this agent
    reads, plus the agent's own tables."""
    conn = sqlite3.connect(str(Path(tmp) / "painting.sqlite"))
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE painting_b2b_accounts (
        account_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL DEFAULT 'lead',
        segment TEXT NOT NULL DEFAULT '', business_name TEXT NOT NULL,
        website TEXT NOT NULL DEFAULT '', contact_channel TEXT NOT NULL DEFAULT '',
        notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT '',
        updated_at TEXT NOT NULL DEFAULT '')""")
    ev.ensure_schema(conn)
    return conn


def _account(conn, account_id, name, *, website="https://example.com.au",
             contact="", segment="strata"):
    conn.execute(
        "INSERT INTO painting_b2b_accounts (account_id, tenant_id, segment,"
        " business_name, website, contact_channel) VALUES (?,'lead',?,?,?,?)",
        (account_id, segment, name, website, contact))
    conn.commit()


# ── phone normalization and classification ──────────────────────────────────

class TestPhoneNormalization(unittest.TestCase):
    def test_all_required_au_formats_normalize(self):
        for raw, expect in [
            ("0499 038 901", "+61499038901"),      # mobile
            ("+61 499 038 901", "+61499038901"),
            ("0499038901", "+61499038901"),
            ("(02) 9326 4488", "+61293264488"),    # landline
            ("02 9326 4488", "+61293264488"),
            ("+61 2 9326 4488", "+61293264488"),
            ("03 9876 5432", "+61398765432"),
            ("07 3123 4567", "+61731234567"),
            ("08 6123 4567", "+61861234567"),
            ("1300 654 321", "+61300654321"),
            ("1800 123 456", "+61800123456"),
            ("13 20 92", "+61132092"),             # short service line
        ]:
            self.assertEqual(ph.normalize_au(raw), expect, f"for {raw!r}")

    def test_trunk_and_international_forms_are_the_same_contact(self):
        self.assertEqual(ph.normalize_au("0412 999 888"),
                         ph.normalize_au("+61 412 999 888"))
        self.assertEqual(ph.normalize_au("(02) 9326 4488"),
                         ph.normalize_au("+61293264488"))

    def test_kind_classification(self):
        self.assertEqual(ph.classify_kind("+61499038901"), ph.KIND_MOBILE)
        self.assertEqual(ph.classify_kind("+61293264488"), ph.KIND_LANDLINE)
        self.assertEqual(ph.classify_kind("+61300654321"), ph.KIND_SERVICE)
        self.assertEqual(ph.classify_kind("+61132092"), ph.KIND_SERVICE)

    def test_invalid_shapes_are_rejected_not_repaired(self):
        for bad in ("", "12345", "061 999", "+1 415 555 0100", "999999999999999"):
            self.assertEqual(ph.normalize_au(bad), "", f"{bad!r} should be invalid")


class TestFalsePositiveDefense(unittest.TestCase):
    """Every case here was a real misread risk on live pages."""

    def test_abn_is_not_a_phone(self):
        self.assertEqual(ph.extract_candidates("ABN 45 123 456 789"), [])
        self.assertEqual(ph.extract_candidates("A.B.N. 12 345 678 901"), [])

    def test_acn_is_not_a_phone(self):
        self.assertEqual(ph.extract_candidates("ACN 123 456 789"), [])

    def test_fax_is_excluded_by_default(self):
        self.assertEqual(ph.extract_candidates("Fax: 02 9326 4489"), [])
        self.assertEqual(ph.extract_candidates("Facsimile 02 9326 4489"), [])

    def test_fax_can_be_opted_in_for_dedup_comparison(self):
        got = ph.extract_candidates("Fax: 02 9326 4489", allow_fax=True)
        self.assertEqual(len(got), 1)

    def test_identifiers_are_not_phones(self):
        for text in ("Licence no 0412345678", "Invoice no 4012345678",
                     "Reference no 0298765432", "BSB 062 000",
                     "Registration no 0412 345 999"):
            self.assertEqual(ph.extract_candidates(text), [], f"for {text!r}")

    def test_placeholders_rejected(self):
        for bad in ("0400 000 000", "0000000000", "+61 412 345 678",
                    "0411 111 111"):
            self.assertEqual(ph.extract_candidates(bad), [], f"{bad!r}")

    def test_postcode_and_dates_are_not_phones(self):
        self.assertEqual(ph.extract_candidates("Sydney NSW 2000"), [])
        self.assertEqual(ph.extract_candidates("Updated 2026-09-11"), [])

    def test_repeated_group_from_pdf_font_metrics_is_rejected(self):
        """A live PDF run stored '507 507 507' (= 507x3) out of a CID
        font-width array. A three-times-repeated 3-digit group is a
        reference/tabular artifact, never a phone."""
        self.assertTrue(ph.is_placeholder("+61507507507"))
        self.assertEqual(ph.extract_candidates("1004[ 507 507 507] 1008"), [])


class TestPdfContactLabelRequirement(unittest.TestCase):
    """PDF text extraction can spill internal object/font-metric arrays full
    of phone-shaped digit runs. '715 433 453' is a valid-looking 07 landline
    that was really font-width data - not a repeated group, so only the
    contact-label requirement separates it from a real number."""

    def test_number_without_a_nearby_label_is_not_trusted(self):
        ctx = "endobj 114 0 obj [ 226 0 0 250 268] 923[ 894] 715 433 453 ]"
        self.assertFalse(ph.has_contact_label(ctx, "715 433 453"))

    def test_number_with_a_nearby_label_is_trusted(self):
        self.assertTrue(ph.has_contact_label(
            "Head office phone 02 9326 4488 for enquiries", "02 9326 4488"))
        self.assertTrue(ph.has_contact_label(
            "Direct: 0412 345 999", "0412 345 999"))

    def test_label_far_away_does_not_vouch(self):
        ctx = "call us " + ("x" * 80) + " 0412 345 999"
        self.assertFalse(ph.has_contact_label(ctx, "0412 345 999"))

    def test_real_numbers_still_survive_all_of_the_above(self):
        got = ph.extract_candidates(
            "Call Murray on 0499 038 901 or the office (02) 9326 4488")
        self.assertEqual({c.e164 for c in got},
                         {"+61499038901", "+61293264488"})

    def test_same_number_twice_is_one_contact(self):
        got = ph.extract_candidates(
            "Head office 02 9326 4488 ... footer: (02) 9326 4488")
        self.assertEqual(len(got), 1)

    def test_bracketed_country_code_keeps_a_clean_display_form(self):
        """Live run read '(+61) 416 551 123' as the mangled '61) 416 551 123'
        - correct digits, but a stray ')' the owner would see in their call
        list. The display form must be captured whole."""
        got = ph.extract_candidates("Sydney info@x.com.au (+61) 416 551 123")
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0].raw, "(+61) 416 551 123")
        self.assertEqual(got[0].e164, "+61416551123")
        self.assertNotIn(") ", got[0].raw.lstrip("(+61) "))  # no stray bracket


class TestTierAssignment(unittest.TestCase):
    def test_mobile_without_person_is_p1_and_with_person_is_p0(self):
        c = ph.extract_candidates("0499 038 901")[0]
        self.assertEqual(c.tier, ph.TIER_P1)
        self.assertEqual(c.with_attribution(person="Murray Cox",
                                            role="Strata Manager").tier,
                         ph.TIER_P0)

    def test_mobile_with_name_but_no_role_stays_p1(self):
        c = ph.extract_candidates("0499 038 901")[0]
        self.assertEqual(c.with_attribution(person="Murray Cox", role="").tier,
                         ph.TIER_P1)

    def test_landline_is_p2_and_service_is_p3(self):
        self.assertEqual(ph.extract_candidates("02 9326 4488")[0].tier, ph.TIER_P2)
        self.assertEqual(ph.extract_candidates("1300 654 321")[0].tier, ph.TIER_P3)

    def test_best_tier_picks_the_strongest(self):
        cands = ph.extract_candidates("1300 654 321 and 0499 038 901")
        self.assertEqual(ph.best_tier(cands), ph.TIER_P1)


class TestDuplicateDetection(unittest.TestCase):
    def test_already_present_matches_across_formats(self):
        self.assertTrue(ph.already_present(
            "+61499038901", "(02) 9326 4488 | Murray Cox 0499 038 901"))
        self.assertTrue(ph.already_present(
            "+61412999888", "contact +61 412 999 888"))

    def test_absent_number_reports_absent(self):
        self.assertFalse(ph.already_present("+61499038901", "(02) 9326 4488"))

    def test_placeholder_already_in_field_is_still_detected(self):
        """already_present answers 'is this string here', which is a
        different question from 'is this a good number' - routing it through
        the quality filters once made an existing placeholder invisible, so
        a re-run would have appended a duplicate of it."""
        self.assertTrue(ph.already_present("+61412345678", "office | 0412 345 678"))


# ── source discovery and attribution ────────────────────────────────────────

TEAM_HTML = """
<html><head><meta property="og:site_name" content="Alldis and Cox">
<meta name="twitter:data1" content="dev@webagency.com.au"></head><body>
<nav><a href="/our-people">Meet Our Strata Managers</a>
     <a href="/contact-us">Contact</a>
     <a href="https://facebook.com/x">Facebook</a>
     <a href="/docs/capability.pdf">Capability Statement</a></nav>
<div><h3>Murray Cox</h3><p>Strata Manager</p><p>M: 0499 038 901</p></div>
<div><h3>Sarah Nguyen, Business Development Manager</h3><p>0412 999 888</p></div>
<footer>Office (02) 9326 4488 | Fax 02 9326 4489 | ABN 45 123 456 789
<input placeholder="youremail@mail.com"></footer></body></html>
"""


class TestVisibleTextOnly(unittest.TestCase):
    def test_meta_tags_and_placeholders_never_reach_extraction(self):
        text = src.clean_text(TEAM_HTML)
        self.assertNotIn("dev@webagency", text)
        self.assertNotIn("youremail", text)

    def test_script_and_style_are_stripped(self):
        text = src.clean_text(
            "<script>var p='0499 038 901';</script><p>Call 02 9326 4488</p>")
        self.assertNotIn("0499", text)
        self.assertIn("9326", text)


class TestPeopleExtraction(unittest.TestCase):
    def test_names_and_roles_found(self):
        people = dict(src.extract_people(src.clean_text(TEAM_HTML)))
        self.assertEqual(people.get("Murray Cox"), "Strata Manager")
        self.assertEqual(people.get("Sarah Nguyen"), "Business Development Manager")

    def test_nav_furniture_is_stripped_from_the_front_of_a_name(self):
        """Flattening HTML runs a nav label into the first name; the leftmost
        regex match then returns 'Statement Murray Cox'. Observed on the
        first realistic fixture tested."""
        text = src.clean_text(
            "<a href='/x'>Capability Statement</a><h3>Murray Cox</h3><p>Director</p>")
        self.assertEqual(src.extract_people(text), [("Murray Cox", "Director")])

    def test_role_then_person_order_also_works(self):
        self.assertEqual(
            src.extract_people("Managing Director: Jane Smith"),
            [("Jane Smith", "Managing Director")])


class TestSeniorityPrefixBelongsToTheRole(unittest.TestCase):
    """Real defect from a live Civium page: greedy name matching parsed
    'Debbie Stanojevic Senior Property Manager' as a three-word NAME plus
    'Property Manager'. A wrong name is worse than no name - it tells the
    owner to ask for a person who does not exist."""

    def test_senior_prefix_stays_in_the_role(self):
        self.assertEqual(
            src.extract_people("Debbie Stanojevic Senior Property Manager"),
            [("Debbie Stanojevic", "Senior Property Manager")])

    def test_three_word_names_still_parse(self):
        self.assertEqual(
            src.extract_people("Mary Anne Watson Managing Director"),
            [("Mary Anne Watson", "Managing Director")])


class TestBranchMismatchDetection(unittest.TestCase):
    """A genuine contact at the wrong office is still the wrong contact for
    a Sydney painter - flagged, not discarded, because it is true."""

    def test_act_page_on_an_nsw_lead_is_flagged(self):
        note = src.branch_mismatch_note(
            source_url="https://civium.com.au/act/residential/property-management/",
            context="Jay Pennay Property Manager 0403 611 326 ACT",
            expected_state="nsw")
        self.assertIn("BRANCH CAUTION", note)
        self.assertIn("ACT", note)

    def test_matching_state_is_not_flagged(self):
        self.assertEqual(src.branch_mismatch_note(
            source_url="https://civium.com.au/nsw/property-management/",
            context="Sydney office", expected_state="nsw"), "")

    def test_unknown_expected_state_never_flags(self):
        self.assertEqual(src.branch_mismatch_note(
            source_url="https://x.com.au/act/", context="", expected_state=""), "")

    def test_state_detection_is_word_bounded(self):
        """Substring matching would fire 'act' on 'contact' and 'sa' on
        'same', flagging essentially every page."""
        self.assertEqual(src.detect_state("https://x.com.au/contact-us"), "")
        self.assertEqual(src.detect_state("the same office"), "")
        self.assertEqual(src.detect_state("/act/team"), "act")


class TestAttribution(unittest.TestCase):
    def test_person_number_attributed_to_the_nearest_preceding_person(self):
        text = src.clean_text(TEAM_HTML)
        people = src.extract_people(text)
        self.assertEqual(src.nearest_person(text, "0499 038 901", people)[0],
                         "Murray Cox")
        self.assertEqual(src.nearest_person(text, "0412 999 888", people)[0],
                         "Sarah Nguyen")

    def test_company_switchboard_is_never_attributed_to_a_person(self):
        """A footer 'Office' line sits after the team list, so nearest-person
        would otherwise hand it to whoever was listed last."""
        text = src.clean_text(TEAM_HTML)
        people = src.extract_people(text)
        self.assertEqual(src.nearest_person(text, "(02) 9326 4488", people),
                         ("", ""))

    def test_distant_name_is_not_attributed(self):
        text = "Jane Smith Director " + ("filler text " * 40) + "0499 038 901"
        self.assertEqual(
            src.nearest_person(text, "0499 038 901", [("Jane Smith", "Director")]),
            ("", ""))


class TestLinkAndPdfDiscovery(unittest.TestCase):
    def test_finds_link_the_seed_path_list_could_not_guess(self):
        links = src.discover_links(TEAM_HTML, "https://alldiscox.com.au/",
                                   "alldiscox.com.au")
        self.assertIn("https://alldiscox.com.au/our-people", links)

    def test_never_leaves_the_official_domain(self):
        links = src.discover_links(TEAM_HTML, "https://alldiscox.com.au/",
                                   "alldiscox.com.au")
        self.assertFalse(any("facebook.com" in u for u in links))

    def test_pdfs_on_own_domain_are_found(self):
        self.assertEqual(
            src.discover_pdfs(TEAM_HTML, "https://alldiscox.com.au/",
                              "alldiscox.com.au"),
            ["https://alldiscox.com.au/docs/capability.pdf"])

    def test_same_site_accepts_subdomain_rejects_stranger(self):
        self.assertTrue(src.same_site("https://www.x.com.au/a", "x.com.au"))
        self.assertTrue(src.same_site("https://docs.x.com.au/a", "x.com.au"))
        self.assertFalse(src.same_site("https://other.com.au/a", "x.com.au"))


class TestSourceClassification(unittest.TestCase):
    def test_ranking_inputs(self):
        self.assertEqual(src.classify_source_type("https://x.com.au/team", "x.com.au"),
                         ev.SRC_OFFICIAL_SITE)
        self.assertEqual(src.classify_source_type("https://x.com.au/a.pdf", "x.com.au"),
                         ev.SRC_OFFICIAL_PDF)
        self.assertEqual(src.classify_source_type(
            "https://www.fairtrading.nsw.gov.au/a", "x.com.au"), ev.SRC_GOV)
        self.assertEqual(src.classify_source_type(
            "https://strata.community/members", "x.com.au"), ev.SRC_ASSOCIATION)
        self.assertEqual(src.classify_source_type(
            "https://www.yellowpages.com.au/a", "x.com.au"), ev.SRC_LISTING)


# ── provenance ──────────────────────────────────────────────────────────────

class TestProvenance(unittest.TestCase):
    def _ev(self, **kw):
        base = dict(account_id="lead:acct:x", business_name="X Pty Ltd",
                    raw_number="0499 038 901", e164="+61499038901",
                    kind="mobile", tier=ph.TIER_P0,
                    source_url="https://x.com.au/team", source_domain="x.com.au",
                    source_type=ev.SRC_OFFICIAL_SITE,
                    context_snippet="Murray Cox Strata Manager M: 0499 038 901",
                    person="Murray Cox", role="Strata Manager", run_id=RUN)
        base.update(kw)
        return ev.Evidence(**base)

    def test_official_site_is_verified_confidence(self):
        self.assertEqual(self._ev().confidence, ev.CONF_VERIFIED)

    def test_government_source_is_verified(self):
        self.assertEqual(self._ev(source_type=ev.SRC_GOV).confidence,
                         ev.CONF_VERIFIED)

    def test_single_listing_is_weak_but_two_sources_make_it_probable(self):
        self.assertEqual(self._ev(source_type=ev.SRC_LISTING).confidence,
                         ev.CONF_WEAK)
        self.assertEqual(
            self._ev(source_type=ev.SRC_LISTING, corroborations=2).confidence,
            ev.CONF_PROBABLE)

    def test_verified_at_requires_an_actual_snippet(self):
        self.assertTrue(self._ev().verified_at)
        self.assertEqual(self._ev(context_snippet="").verified_at, "",
                         "a number with no source text is not verified")

    def test_evidence_id_is_deterministic_so_rerun_does_not_duplicate(self):
        self.assertEqual(self._ev().evidence_id, self._ev().evidence_id)
        self.assertNotEqual(self._ev().evidence_id,
                            self._ev(source_url="https://x.com.au/contact").evidence_id)

    def test_recording_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            self.assertTrue(ev.record_evidence(conn, self._ev()))
            self.assertFalse(ev.record_evidence(conn, self._ev()),
                             "same number from same URL is one observation")
            n = conn.execute("SELECT COUNT(*) FROM painting_contact_evidence").fetchone()[0]
            self.assertEqual(n, 1)
            conn.close()

    def test_audit_trail_answers_where_did_this_come_from(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            ev.record_evidence(conn, self._ev())
            row = conn.execute("SELECT * FROM painting_contact_evidence").fetchone()
            self.assertEqual(row["source_url"], "https://x.com.au/team")
            self.assertEqual(row["source_type"], ev.SRC_OFFICIAL_SITE)
            self.assertIn("0499 038 901", row["context_snippet"])
            self.assertEqual(row["person"], "Murray Cox")
            conn.close()


class TestConflictDetection(unittest.TestCase):
    def test_same_person_same_kind_different_number_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            ev.record_evidence(conn, ev.Evidence(
                account_id="a1", business_name="X", raw_number="0499 038 901",
                e164="+61499038901", kind="mobile", tier=ph.TIER_P0,
                source_url="https://x.com.au/a", source_domain="x.com.au",
                source_type=ev.SRC_OFFICIAL_SITE, person="Murray Cox",
                role="Director", context_snippet="x"))
            note = ev.detect_conflict(conn, "lead", "a1", "Murray Cox",
                                      "+61411222333")
            self.assertIn("CONFLICT", note)
            conn.close()

    def test_desk_line_plus_mobile_is_not_a_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            ev.record_evidence(conn, ev.Evidence(
                account_id="a1", business_name="X", raw_number="02 9326 4488",
                e164="+61293264488", kind="landline", tier=ph.TIER_P2,
                source_url="https://x.com.au/a", source_domain="x.com.au",
                source_type=ev.SRC_OFFICIAL_SITE, person="Murray Cox",
                role="Director", context_snippet="x"))
            self.assertEqual(
                ev.detect_conflict(conn, "lead", "a1", "Murray Cox", "+61499038901"),
                "", "a person legitimately has both a desk line and a mobile")
            conn.close()


# ── append semantics ────────────────────────────────────────────────────────

class TestAppendSemantics(unittest.TestCase):
    def test_existing_contact_is_preserved_and_new_one_appended(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            _account(conn, "a1", "X Pty Ltd", contact="1300 322 213 | info@x.com.au")
            cand = ph.extract_candidates("0499 038 901")[0].with_attribution(
                person="Murray Cox", role="Director")
            added = rs.apply_to_account(conn, account_id="a1", candidates=[cand])
            got = conn.execute("SELECT contact_channel FROM painting_b2b_accounts"
                               " WHERE account_id='a1'").fetchone()[0]
            self.assertIn("1300 322 213", got, "existing value must survive")
            self.assertIn("info@x.com.au", got)
            self.assertIn("Murray Cox (Director) 0499 038 901", got)
            self.assertEqual(len(added), 1)
            conn.close()

    def test_rerun_does_not_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            _account(conn, "a1", "X Pty Ltd", contact="02 9326 4488")
            cand = ph.extract_candidates("0499 038 901")[0]
            rs.apply_to_account(conn, account_id="a1", candidates=[cand])
            second = rs.apply_to_account(conn, account_id="a1", candidates=[cand])
            self.assertEqual(second, [], "already-present number must not re-append")
            got = conn.execute("SELECT contact_channel FROM painting_b2b_accounts"
                               " WHERE account_id='a1'").fetchone()[0]
            self.assertEqual(got.count("0499 038 901"), 1)
            conn.close()

    def test_equivalent_format_is_recognised_as_already_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            _account(conn, "a1", "X", contact="+61 499 038 901")
            cand = ph.extract_candidates("0499 038 901")[0]
            self.assertEqual(rs.apply_to_account(conn, account_id="a1",
                                                 candidates=[cand]), [])
            conn.close()

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            _account(conn, "a1", "X", contact="02 9326 4488")
            cand = ph.extract_candidates("0499 038 901")[0]
            rs.apply_to_account(conn, account_id="a1", candidates=[cand],
                                dry_run=True)
            got = conn.execute("SELECT contact_channel FROM painting_b2b_accounts"
                               " WHERE account_id='a1'").fetchone()[0]
            self.assertEqual(got, "02 9326 4488")
            conn.close()

    def test_a_contact_is_never_truncated_in_half(self):
        """The column caps at 220 chars and the first live apply run wrote
        'Jay Pennay (Property Manag' - a number sliced away entirely. A
        contact that does not fit whole is left out; the evidence table
        keeps it in full."""
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            _account(conn, "a1", "X", contact="Z" * 200)
            cand = ph.extract_candidates("0499 038 901")[0].with_attribution(
                person="Averyveryverylongname Person", role="Managing Director")
            rs.apply_to_account(conn, account_id="a1", candidates=[cand])
            got = conn.execute("SELECT contact_channel FROM painting_b2b_accounts"
                               " WHERE account_id='a1'").fetchone()[0]
            self.assertLessEqual(len(got), 220)
            self.assertNotIn("0499 038 90", got.rstrip("1"),
                             "a partial phone number must never be stored")
            self.assertEqual(got, "Z" * 200, "unchanged when nothing fits")
            conn.close()

    def test_when_room_is_tight_the_highest_value_contact_wins_it(self):
        """With only enough room for one, the attributed P0 mobile must take
        it and the bare P1 must be the one left to the evidence table - the
        field exists to tell the owner who to ring first."""
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            _account(conn, "a1", "X", contact="Y" * 150)
            bare = ph.extract_candidates("0499 038 901")[0]
            attributed = ph.extract_candidates("0411 222 333")[0].with_attribution(
                person="A Very Long Name Indeed Here", role="Managing Director")
            added = rs.apply_to_account(conn, account_id="a1",
                                        candidates=[bare, attributed])
            got = conn.execute("SELECT contact_channel FROM painting_b2b_accounts"
                               " WHERE account_id='a1'").fetchone()[0]
            self.assertIn("0411 222 333", got, "the P0 contact should win the room")
            self.assertNotIn("0499 038 901", got)
            self.assertLessEqual(len(got), 220)
            self.assertEqual(len(added), 1)
            conn.close()

    def test_stronger_tier_is_appended_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            _account(conn, "a1", "X", contact="")
            mobile = ph.extract_candidates("0499 038 901")[0].with_attribution(
                person="Murray Cox", role="Director")
            office = ph.extract_candidates("02 9326 4488")[0]
            added = rs.apply_to_account(conn, account_id="a1",
                                        candidates=[office, mobile])
            self.assertIn("0499 038 901", added[0],
                          "P0 mobile should lead the contact field")
            conn.close()


# ── target selection, checkpoint and resume ─────────────────────────────────

class TestTargetSelection(unittest.TestCase):
    def _seed(self, conn):
        _account(conn, "a1", "No Phone Co", contact="")
        _account(conn, "a2", "Office Only Co", contact="1300 322 213")
        _account(conn, "a3", "Has Mobile Co", contact="0499 038 901")

    def test_groups_are_assigned_correctly_and_c_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            self._seed(conn)
            got = {t.account_id: t.group for t in st.select_targets(conn)}
            self.assertEqual(got, {"a1": "A", "a2": "B"})
            conn.close()

    def test_only_no_phone_filter(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            self._seed(conn)
            ids = [t.account_id for t in st.select_targets(conn, only_no_phone=True)]
            self.assertEqual(ids, ["a1"])
            conn.close()

    def test_group_a_is_prioritised_over_group_b(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            self._seed(conn)
            self.assertEqual(st.select_targets(conn)[0].account_id, "a1")
            conn.close()

    def test_repeatedly_failed_lead_is_backed_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            self._seed(conn)
            for _ in range(st.MAX_ATTEMPTS_BEFORE_BACKOFF):
                ev.save_state(conn, account_id="a1", tenant="lead",
                              business_name="No Phone Co", segment="strata",
                              outcome=ev.OUT_NO_PUBLIC_NUMBER,
                              stop_reason=st.STOP_EXHAUSTED, best_tier="",
                              sources_checked=5, urls_seen=[], people_found=[],
                              numbers_found=0, run_id=RUN)
            conn.commit()
            ids = [t.account_id for t in st.select_targets(conn)]
            self.assertNotIn("a1", ids)
            self.assertIn("a1", [t.account_id for t in
                                 st.select_targets(conn, include_backed_off=True)])
            conn.close()

    def test_blocked_lead_is_exempt_from_backoff(self):
        """A host block is a fact about the host that day, not evidence that
        the company publishes no number - so it must stay retryable."""
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            self._seed(conn)
            for _ in range(st.MAX_ATTEMPTS_BEFORE_BACKOFF + 1):
                ev.save_state(conn, account_id="a1", tenant="lead",
                              business_name="No Phone Co", segment="strata",
                              outcome=ev.OUT_BLOCKED, stop_reason=st.STOP_BLOCKED,
                              best_tier="", sources_checked=0, urls_seen=[],
                              people_found=[], numbers_found=0, run_id=RUN)
            conn.commit()
            self.assertIn("a1", [t.account_id for t in st.select_targets(conn)])
            conn.close()


class TestCheckpointAndResume(unittest.TestCase):
    def test_state_is_saved_after_each_lead(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            ev.save_state(conn, account_id="a1", tenant="lead",
                          business_name="X", segment="strata",
                          outcome=ev.OUT_FOUND, stop_reason=st.STOP_P0_FOUND,
                          best_tier=ph.TIER_P0, sources_checked=3,
                          urls_seen=["https://x.com.au/team"],
                          people_found=["Murray Cox (Director)"],
                          numbers_found=1, run_id=RUN)
            conn.commit()
            s = ev.load_state(conn, "a1")
            self.assertEqual(s["last_outcome"], ev.OUT_FOUND)
            self.assertEqual(s["attempts"], 1)
            conn.close()

    def test_attempts_accumulate_across_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            for _ in range(3):
                ev.save_state(conn, account_id="a1", tenant="lead",
                              business_name="X", segment="strata",
                              outcome=ev.OUT_NO_PUBLIC_NUMBER,
                              stop_reason=st.STOP_EXHAUSTED, best_tier="",
                              sources_checked=4, urls_seen=[], people_found=[],
                              numbers_found=0, run_id=RUN)
            conn.commit()
            self.assertEqual(ev.load_state(conn, "a1")["attempts"], 3)
            conn.close()

    def test_interrupted_run_resumes_without_redoing_finished_leads(self):
        """Simulates a crash after lead 1 of 2: the next run must pick up the
        unfinished lead, not start over."""
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            _account(conn, "a1", "First Co", contact="")
            _account(conn, "a2", "Second Co", contact="")
            for _ in range(st.MAX_ATTEMPTS_BEFORE_BACKOFF):
                ev.save_state(conn, account_id="a1", tenant="lead",
                              business_name="First Co", segment="strata",
                              outcome=ev.OUT_NO_PUBLIC_NUMBER,
                              stop_reason=st.STOP_EXHAUSTED, best_tier="",
                              sources_checked=6, urls_seen=[], people_found=[],
                              numbers_found=0, run_id=RUN)
            conn.commit()
            remaining = [t.account_id for t in st.select_targets(conn)]
            self.assertEqual(remaining, ["a2"])
            conn.close()


# ── stopping policy ─────────────────────────────────────────────────────────

class TestStoppingPolicy(unittest.TestCase):
    def test_p0_stops_immediately_with_an_explainable_reason(self):
        s = st.ResearchState(unexplored=["https://x.com.au/more"])
        s.candidates = [ph.extract_candidates("0499 038 901")[0].with_attribution(
            person="Murray Cox", role="Director")]
        stop, reason = st.should_stop(s, request_budget=14)
        self.assertTrue(stop)
        self.assertEqual(reason, st.STOP_P0_FOUND)

    def test_bare_mobile_keeps_going_while_a_people_page_is_unexplored(self):
        s = st.ResearchState(unexplored=["https://x.com.au/our-team"])
        s.candidates = ph.extract_candidates("0499 038 901")
        stop, _ = st.should_stop(s, request_budget=14)
        self.assertFalse(stop, "a people page could still attribute this mobile")

    def test_bare_mobile_stops_when_no_attributing_source_remains(self):
        s = st.ResearchState(unexplored=["https://x.com.au/privacy"])
        s.candidates = ph.extract_candidates("0499 038 901")
        stop, reason = st.should_stop(s, request_budget=14)
        self.assertTrue(stop)
        self.assertEqual(reason, st.STOP_MOBILE_NO_BETTER)

    def test_budget_exhaustion_is_reported_as_such(self):
        s = st.ResearchState(requests_used=14, unexplored=["https://x.com.au/a"])
        stop, reason = st.should_stop(s, request_budget=14)
        self.assertTrue(stop)
        self.assertEqual(reason, st.STOP_BUDGET)

    def test_exhausted_source_space(self):
        stop, reason = st.should_stop(st.ResearchState(), request_budget=14)
        self.assertTrue(stop)
        self.assertEqual(reason, st.STOP_EXHAUSTED)

    def test_consecutive_dead_paths_stop_the_lead_early(self):
        """Live runs showed every lead spending its whole budget on guessed
        paths that 404 on sites which do not use those conventions."""
        s = st.ResearchState(unexplored=["https://x.com.au/a", "https://x.com.au/b"],
                             consecutive_misses=st.MAX_CONSECUTIVE_MISSES)
        stop, reason = st.should_stop(s, request_budget=14)
        self.assertTrue(stop)
        self.assertEqual(reason, st.STOP_DEAD_PATHS)

    def test_a_few_misses_do_not_stop_the_lead(self):
        s = st.ResearchState(unexplored=["https://x.com.au/a"], consecutive_misses=2)
        stop, _ = st.should_stop(s, request_budget=14)
        self.assertFalse(stop)

    def test_blocked_everywhere_is_distinguished_from_nothing_found(self):
        s = st.ResearchState(blocked_hosts=3, had_any_success=False)
        stop, reason = st.should_stop(s, request_budget=14)
        self.assertTrue(stop)
        self.assertEqual(reason, st.STOP_BLOCKED)


class TestOutcomeDifferentiation(unittest.TestCase):
    """'Found nothing' and 'could not look' need different retry policies."""

    def test_no_website_on_record(self):
        self.assertEqual(
            st.outcome_for(st.ResearchState(), had_website=False,
                           robots_blocked=False), ev.OUT_NO_WEBSITE)

    def test_robots_disallowed(self):
        self.assertEqual(
            st.outcome_for(st.ResearchState(), had_website=True,
                           robots_blocked=True), ev.OUT_ROBOTS)

    def test_blocked_by_host(self):
        s = st.ResearchState(blocked_hosts=2, had_any_success=False)
        self.assertEqual(st.outcome_for(s, had_website=True, robots_blocked=False),
                         ev.OUT_BLOCKED)

    def test_read_the_site_and_it_genuinely_has_no_number(self):
        s = st.ResearchState(had_any_success=True, sources_checked=5)
        self.assertEqual(st.outcome_for(s, had_website=True, robots_blocked=False),
                         ev.OUT_NO_PUBLIC_NUMBER)

    def test_found(self):
        s = st.ResearchState(had_any_success=True)
        s.candidates = ph.extract_candidates("0499 038 901")
        self.assertEqual(st.outcome_for(s, had_website=True, robots_blocked=False),
                         ev.OUT_FOUND)


# ── end-to-end, offline ─────────────────────────────────────────────────────

class TestResearcherEndToEnd(unittest.TestCase):
    def _fetch(self, pages: dict):
        def fetch(url):
            for frag, body in pages.items():
                if url.rstrip("/").endswith(frag.rstrip("/")):
                    return {"ok": True, "kind": "ok", "status": 200,
                            "body": body, "url": url}
            return {"ok": False, "kind": "error", "status": 404,
                    "body": None, "url": url}
        return fetch

    def test_full_pipeline_finds_attributes_and_records_with_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            _account(conn, "a1", "Alldis and Cox",
                     website="https://alldiscox.com.au", contact="1300 322 213")
            r = rs.ContactResearcher(
                conn, run_id=RUN, read_pdfs=False,
                fetch=self._fetch({"alldiscox.com.au": TEAM_HTML}))
            rep = r.research(st.LeadTarget(
                account_id="a1", business_name="Alldis and Cox",
                website="https://alldiscox.com.au", segment="strata",
                contact_channel="1300 322 213", group="B"))

            self.assertEqual(rep["outcome"], ev.OUT_FOUND)
            self.assertEqual(rep["best_tier"], ph.TIER_P0)
            found = {c["raw"]: c for c in rep["candidates"]}
            self.assertEqual(found["0499 038 901"]["person"], "Murray Cox")
            # provenance actually landed
            row = conn.execute(
                "SELECT * FROM painting_contact_evidence WHERE e164='+61499038901'"
            ).fetchone()
            self.assertTrue(row["source_url"])
            self.assertIn("0499 038 901", row["context_snippet"])
            self.assertEqual(row["confidence"], ev.CONF_VERIFIED)
            # state checkpointed
            self.assertEqual(ev.load_state(conn, "a1")["last_outcome"], ev.OUT_FOUND)
            conn.close()

    def test_blocked_site_is_recorded_as_blocked_not_as_no_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            _account(conn, "a1", "Blocked Co", website="https://blocked.com.au")
            r = rs.ContactResearcher(
                conn, run_id=RUN, read_pdfs=False,
                fetch=lambda u: {"ok": False, "kind": "blocked_403",
                                 "status": 403, "body": None, "url": u})
            rep = r.research(st.LeadTarget(
                account_id="a1", business_name="Blocked Co",
                website="https://blocked.com.au", segment="strata",
                contact_channel="", group="A"))
            self.assertEqual(rep["outcome"], ev.OUT_BLOCKED)
            conn.close()

    def test_robots_disallow_is_honoured_and_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            _account(conn, "a1", "Robots Co", website="https://robots.com.au")
            r = rs.ContactResearcher(
                conn, run_id=RUN, read_pdfs=False,
                fetch=lambda u: {"ok": False, "kind": "robots_disallowed",
                                 "status": None, "body": None, "url": u})
            rep = r.research(st.LeadTarget(
                account_id="a1", business_name="Robots Co",
                website="https://robots.com.au", segment="strata",
                contact_channel="", group="A"))
            self.assertEqual(rep["outcome"], ev.OUT_ROBOTS)
            conn.close()

    def test_lead_without_website_is_not_researched_blindly(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            _account(conn, "a1", "No Site Co", website="")
            calls = []
            r = rs.ContactResearcher(
                conn, run_id=RUN, read_pdfs=False,
                fetch=lambda u: calls.append(u) or {"ok": False, "kind": "error",
                                                    "body": None, "url": u})
            rep = r.research(st.LeadTarget(
                account_id="a1", business_name="No Site Co", website="",
                segment="strata", contact_channel="", group="A"))
            self.assertEqual(rep["outcome"], ev.OUT_NO_WEBSITE)
            self.assertEqual(calls, [], "must not invent a URL to fetch")
            conn.close()

    def test_links_the_site_really_publishes_beat_speculative_seeded_paths(self):
        """Regression for a real efficiency bug seen on the first live run:
        every request in the per-lead budget was spent on guessed paths
        (/team, /staff, /our-people...) that all 404'd, so the people page
        the homepage actually linked to was never fetched. A link the site
        publishes must be tried before a path we merely hoped existed."""
        home = ('<a href="/who-we-are">Who We Are</a>'
                '<p>Head office 02 9326 4488</p>')
        who = "<h3>Jane Smith</h3><p>Director</p><p>M: 0499 111 222</p>"
        order: list[str] = []

        def fetch(url):
            order.append(url)
            if url.rstrip("/").endswith("who-we-are"):
                return {"ok": True, "kind": "ok", "status": 200, "body": who, "url": url}
            if url.rstrip("/") in ("https://x.com.au", "https://x.com.au/"):
                return {"ok": True, "kind": "ok", "status": 200, "body": home, "url": url}
            return {"ok": False, "kind": "error", "status": 404, "body": None, "url": url}

        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            _account(conn, "a1", "X", website="https://x.com.au")
            r = rs.ContactResearcher(conn, run_id=RUN, read_pdfs=False,
                                     fetch=fetch, request_budget=14)
            rep = r.research(st.LeadTarget(
                account_id="a1", business_name="X", website="https://x.com.au",
                segment="strata", contact_channel="", group="A"))
            self.assertEqual(rep["best_tier"], ph.TIER_P0)
            self.assertEqual(order[1], "https://x.com.au/who-we-are",
                             f"discovered link must be fetched 2nd, got {order[:3]}")
            conn.close()

    def test_directory_page_numbers_are_discarded_not_attributed(self):
        """Regression for the worst bug the first live run produced: a lead
        whose recorded website was a strata DIRECTORY yielded 61 'direct
        office' numbers, every one belonging to a different business. A page
        carrying many numbers cannot be attributed to one company, so its
        numbers are dropped wholesale rather than guessed between."""
        directory = "<p>" + " ".join(
            f"Company {i} (02) 9{i:03d} 4{i:03d}" for i in range(1, 15)) + "</p>"
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            _account(conn, "a1", "Directory Co", website="https://dir.com.au")
            r = rs.ContactResearcher(
                conn, run_id=RUN, read_pdfs=False,
                fetch=self._fetch({"dir.com.au": directory}))
            rep = r.research(st.LeadTarget(
                account_id="a1", business_name="Directory Co",
                website="https://dir.com.au", segment="strata",
                contact_channel="", group="A"))
            self.assertEqual(rep["candidates"], [],
                             "a directory's numbers belong to other companies")
            self.assertNotEqual(rep["outcome"], ev.OUT_FOUND)
            conn.close()

    def test_normal_contact_page_with_a_few_numbers_is_still_accepted(self):
        """The directory guard must not reject a genuine contact page that
        legitimately lists office + fax + after-hours + a couple of people."""
        page = ("<p>Office 02 9326 4488. After hours 02 9326 4499.</p>"
                "<h3>Jane Smith</h3><p>Director</p><p>M: 0499 111 222</p>")
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            _account(conn, "a1", "Real Co", website="https://real.com.au")
            r = rs.ContactResearcher(conn, run_id=RUN, read_pdfs=False,
                                     fetch=self._fetch({"real.com.au": page}))
            rep = r.research(st.LeadTarget(
                account_id="a1", business_name="Real Co",
                website="https://real.com.au", segment="strata",
                contact_channel="", group="A"))
            self.assertEqual(rep["best_tier"], ph.TIER_P0)
            conn.close()

    def test_pdf_font_metric_garbage_never_reaches_an_account(self):
        """Regression for the worst batch-run defect: a capability-statement
        PDF's internal font-width array ('...1004[ 507 507 507] 1008[ 507
        507]...') put '507 507 507' and '715 433 453' into a real account.
        With PDF numbers requiring a contact label, none survive."""
        home = '<a href="/doc.pdf">Capability Statement</a><p>Our services</p>'
        garbage_pdf_text = ("endobj 114 0 obj [ 226 0 0 250 268 268 252 859 "
                            "894[ 303 303] 1004[ 507 507 507] 1008[ 507 507] "
                            "715 433 453 ] endobj 115 0 obj")
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            _account(conn, "a1", "Stratawide", website="https://sw.com.au")
            r = rs.ContactResearcher(
                conn, run_id=RUN, read_pdfs=True,
                fetch=self._fetch({"sw.com.au": home}),
                fetch_bin=lambda u: {"ok": True, "kind": "ok",
                                     "body": b"%PDF-fake", "url": u})
            # bypass the real pypdf parse; return the garbage extraction text
            import ofn.enrichment.sources as _s
            orig = _s.read_pdf_text
            _s.read_pdf_text = lambda data, **k: garbage_pdf_text
            try:
                rep = r.research(st.LeadTarget(
                    account_id="a1", business_name="Stratawide",
                    website="https://sw.com.au", segment="strata",
                    contact_channel="", group="A"))
            finally:
                _s.read_pdf_text = orig
            self.assertEqual([c for c in rep["candidates"]], [],
                             "no font-metric digit run may be stored as a phone")
            conn.close()

    def test_switchboard_only_site_yields_p3_and_says_so(self):
        html = "<p>Call us on 1300 322 213</p>"
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            _account(conn, "a1", "Switchboard Co", website="https://sb.com.au")
            r = rs.ContactResearcher(conn, run_id=RUN, read_pdfs=False,
                                     fetch=self._fetch({"sb.com.au": html}))
            rep = r.research(st.LeadTarget(
                account_id="a1", business_name="Switchboard Co",
                website="https://sb.com.au", segment="strata",
                contact_channel="", group="A"))
            self.assertEqual(rep["best_tier"], ph.TIER_P3)
            self.assertEqual(rep["outcome"], ev.OUT_FOUND)
            conn.close()


class TestDerivedPerformanceModel(unittest.TestCase):
    def test_report_renders_without_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            self.assertIn("source-performance", ls.render_report(conn))
            conn.close()

    def test_stats_are_derived_from_evidence_not_a_parallel_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = _db(tmp)
            ev.record_evidence(conn, ev.Evidence(
                account_id="a1", business_name="X", raw_number="0499 038 901",
                e164="+61499038901", kind="mobile", tier=ph.TIER_P0,
                source_url="https://x.com.au/our-team", source_domain="x.com.au",
                source_type=ev.SRC_OFFICIAL_SITE, person="Murray Cox",
                role="Director", context_snippet="x"))
            conn.commit()
            perf = ls.source_performance(conn)
            self.assertEqual(perf[0]["source_type"], ev.SRC_OFFICIAL_SITE)
            self.assertEqual(perf[0]["mobiles"], 1)
            self.assertEqual(perf[0]["attributed"], 1)
            pats = ls.url_pattern_performance(conn)
            self.assertEqual(pats[0]["pattern"], "/our-team")
            conn.close()


if __name__ == "__main__":
    unittest.main()
