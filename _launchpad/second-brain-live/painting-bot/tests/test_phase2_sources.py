"""Phase 2 — data-source tests. No network, no real keys.

Run:  pytest tests/ -q
"""
from datetime import datetime

from harvesters import ALL
from harvesters.austender import AusTenderHarvester, parse_release, parse_releases
from harvesters.keywords import is_paint_relevant
from harvesters.nsw_etendering import (
    NswEtenderingHarvester,
    entries_to_leads,
    parse_feed,
)
from harvesters.planning_alerts import NSW_AUTHORITIES, PlanningAlertsHarvester


def _rel(title="Repainting of building facade", desc="External painting works",
         state="NSW", ocid="prcltrqst-x-1", amount=120000):
    return {
        "ocid": ocid,
        "tender": {
            "title": title,
            "description": (desc + (f" Delivery: {state}" if state else "")),
            "value": {"amount": amount, "currency": "AUD"},
            "tenderPeriod": {"endDate": "2026-08-01T17:00:00Z"},
            "documents": [{"url": "https://www.tenders.gov.au/atm/show/x-1"}],
        },
        "buyer": {"name": "Dept of Test"},
    }


# ---------------- keywords ----------------

def test_keywords_positive():
    assert is_paint_relevant("Facade REPAINTING and remedial works")
    assert is_paint_relevant("protective coating renewal")
    assert is_paint_relevant("internal decoration & make good")


def test_keywords_negative():
    assert not is_paint_relevant("supply of office stationery")
    assert not is_paint_relevant("")
    assert not is_paint_relevant(None)


# ---------------- austender (OCDS) ----------------

def test_austender_parses_relevant_nsw_release():
    lead = parse_release(_rel())
    assert lead is not None
    assert lead.source == "austender"
    assert lead.external_id == "prcltrqst-x-1"
    assert lead.value_aud == 120000
    assert lead.deadline == datetime(2026, 8, 1, 17, 0)
    assert lead.url.startswith("https://www.tenders.gov.au/atm/show/")
    assert "Buyer: Dept of Test" in lead.description
    assert lead.category == "gov"


def test_austender_skips_non_paint():
    assert parse_release(_rel(title="Supply of laptops", desc="IT hardware")) is None


def test_austender_skips_other_state_only():
    assert parse_release(_rel(state="VIC")) is None
    assert parse_release(_rel(state="Queensland")) is None


def test_austender_keeps_unknown_state():
    assert parse_release(_rel(state="")) is not None


def test_austender_state_regex_word_boundaries():
    # "service" contains "vic" — must NOT be treated as Victoria
    rel = _rel(state="")
    rel["tender"]["description"] = "External painting works for public service buildings"
    assert parse_release(rel) is not None


def test_austender_package_filtering():
    pkg = {
        "releases": [_rel(), _rel(title="Stationery", desc="paper clips", ocid="x-2")],
        "links": {"next": None},
    }
    leads = parse_releases(pkg)
    assert len(leads) == 1


def test_austender_handles_junk_defensively():
    assert parse_releases({}) == []
    assert parse_releases({"releases": [None, {}, {"tender": {}}]}) == []
    minimal = {"ocid": "x", "tender": {"title": "painting", "description": ""}}
    lead = parse_release(minimal)
    assert lead is not None and lead.value_aud is None and lead.deadline is None


# ---------------- nsw_etendering (RSS/Atom) ----------------

RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>NSW eTendering</title>
<item>
  <title>RFT 2026/123 - Repainting of School Buildings</title>
  <link>https://www.tenders.nsw.gov.au/?event=public.rft.show&amp;RFTUUID=abc</link>
  <description><![CDATA[<p>External repaint &amp; remedial works</p>]]></description>
  <guid>rft-abc</guid>
</item>
<item>
  <title>RFT 2026/124 - Catering Services</title>
  <link>https://example.com/rft-124</link>
  <description>Food services</description>
  <guid>rft-def</guid>
</item>
</channel></rss>"""

ATOM_XML = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Painting works - Justice precinct</title>
    <id>urn:x:1</id>
    <link href="https://example.com/1"/>
    <summary>facade coating renewal</summary>
  </entry>
</feed>"""


def test_parse_feed_rss():
    entries = parse_feed(RSS_XML)
    assert len(entries) == 2
    assert entries[0]["id"] == "rft-abc"
    assert entries[0]["title"].startswith("RFT 2026/123")
    assert "<p>" not in entries[0]["description"]
    assert "repaint" in entries[0]["description"].lower()


def test_parse_feed_atom():
    entries = parse_feed(ATOM_XML)
    assert len(entries) == 1
    assert entries[0]["link"] == "https://example.com/1"
    assert entries[0]["id"] == "urn:x:1"


def test_parse_feed_garbage():
    assert parse_feed("not xml at all") == []
    assert parse_feed("<html><body>Access denied</body></html>") == []


def test_entries_to_leads_filters_keywords():
    leads = entries_to_leads(parse_feed(RSS_XML))
    assert len(leads) == 1  # catering filtered out
    assert leads[0].source == "nsw_etendering"
    assert leads[0].external_id == "rft-abc"


# ---------------- scheduling / quota ----------------

def test_active_harvesters():
    assert [c.name for c in ALL] == ["planning_alerts", "austender", "nsw_etendering"]


def test_per_source_intervals():
    assert PlanningAlertsHarvester.interval_minutes == 180
    assert AusTenderHarvester.interval_minutes == 60
    assert NswEtenderingHarvester.interval_minutes == 60


def test_planning_alerts_daily_quota_respected():
    runs_per_day = (24 * 60) / PlanningAlertsHarvester.interval_minutes
    assert runs_per_day * len(NSW_AUTHORITIES) <= 1000  # free-tier daily cap


def test_scheduler_registers_per_source_jobs():
    # needs apscheduler + telegram installed (runs on the dev machine)
    from scheduler import build_scheduler

    sched = build_scheduler()
    ids = {j.id for j in sched.get_jobs()}
    assert {
        "harvester:planning_alerts",
        "harvester:austender",
        "harvester:nsw_etendering",
        "hunter",
        "digest",
    } <= ids
