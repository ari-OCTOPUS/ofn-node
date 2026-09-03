"""
source_registry.py — Autonomous Source Registry for Octopus survival loop.

Philosophy:
  The octopus must find its own food. Owner gives the territory (Sydney painting);
  octopus finds every open water it can reach legally and without login.

  This registry answers one question:
    "What public sources can I harvest RIGHT NOW without asking anyone?"

  Sources are rated by:
    - LIVE: confirmed working as of last probe
    - DEAD: feed ended or blocked
    - UNKNOWN: never probed in this session

  All sources are READ-ONLY public data. No authentication. No scraping behind
  login walls. No terms-of-service violations. Octopus is a reader, not a breaker.

Source taxonomy for Sydney painting:
  T1 — Government tenders / procurement (highest value, lowest competition)
  T2 — Job boards (painting contractors needed = potential subcontract leads)
  T3 — Contract registries (who has paid for painting = warm repeat buyers)
  T4 — Community / classifieds (homeowners = direct customers)
  T5 — Regulatory / licensing (who has a painting licence = potential partners)

Fail-closed contract:
  - probe() never raises: returns UNKNOWN on any error
  - harvest_all() parks failed sources, continues the rest
  - No source write to DB without explicit create_lead/create_tender call
  - All findings go through outbox — never direct email/send
"""
from __future__ import annotations

import logging
import time
import urllib.request
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Optional

log = logging.getLogger(__name__)


class SourceStatus(str, Enum):
    LIVE    = "LIVE"
    DEAD    = "DEAD"
    UNKNOWN = "UNKNOWN"
    BLOCKED = "BLOCKED"   # 403/429 — alive but rate-limited or CDN-walled


@dataclass
class Source:
    id: str
    name: str
    tier: int                      # T1–T5
    probe_url: str                 # HEAD/GET to check liveness
    harvest_module: Optional[str]  # e.g. 'ofn.agents.seek_harvest'
    status: SourceStatus = SourceStatus.UNKNOWN
    last_probed: Optional[str] = None
    last_hit_count: int = 0
    notes: str = ""
    requires_browser: bool = False  # True = needs Chromium on board138
    requires_auth: bool = False     # True = NEVER auto-harvest
    open_data_license: str = ""    # e.g. 'CC-BY-4.0', 'OGL', 'public'


# ────────────────────────────────────────────────────────────────────────
SOURCES: List[Source] = [

    # ── T1: Government Procurement / Tenders ────────────────────────────────
    Source(
        id="buy_nsw_supplier_register",
        name="buy.nsw Supplier Register",
        tier=1,
        probe_url="https://www.buy.nsw.gov.au/supplier-register",
        harvest_module=None,  # TODO: email-subscription channel (not open API)
        requires_browser=True,
        open_data_license="public",
        notes=(
            "The real replacement for dead h1_harvest. Supplier-registration "
            "nightly email is the sanctioned channel (see nsw_ocp_harvest notes). "
            "Autonomous: subscribe once via email → IMAP listener processes nightly digest."
        ),
    ),
    Source(
        id="buy_nsw_contract_register",
        name="buy.nsw Contract Register (info.buy.nsw)",
        tier=1,
        probe_url="https://www.tenders.nsw.gov.au",
        harvest_module="ofn.agents.ziman_tender_harvest",
        requires_browser=True,
        open_data_license="public",
        notes=(
            "Live NSW tender portal. h1_harvest feed (OCDS) died Feb 2025. "
            "Browser scrape is the only current path. PR #141 implements this."
        ),
    ),
    Source(
        id="nsw_ocp_bulk",
        name="NSW OCP Bulk Download (data.open-contracting.org)",
        tier=1,
        probe_url="https://data.open-contracting.org/en/publication/11",
        harvest_module="ofn.agents.nsw_ocp_harvest",
        open_data_license="CC-BY-3.0-AU",
        notes=(
            "Annual JSONL.gz of NSW contract AWARDS. Painting buyers = warm repeat leads. "
            "Status: PARKED (wrong use as lead module — needs repoint to renewal radar). "
            "Re-wire when renewal-radar feature merges."
        ),
    ),
    Source(
        id="austender_api",
        name="AusTender Federal API (api.tenders.gov.au)",
        tier=1,
        probe_url="https://api.tenders.gov.au/api/contractnotice/search?keyword=painting&limit=1",
        harvest_module=None,
        open_data_license="CC-BY-4.0",
        notes=(
            "Federal procurement. Verified: 0 painting contracts in 30 days. "
            "Still worth quarterly probe — federal agencies do buy painting. "
            "JSON API, no auth. Module stub: ofn.agents.austender_harvest (not yet written)."
        ),
    ),
    Source(
        id="icn_gateway",
        name="Industry Capability Network NSW (icn.org.au)",
        tier=1,
        probe_url="https://gateway.icn.org.au/opportunities?state=NSW&category=painting",
        harvest_module=None,
        open_data_license="public",
        notes=(
            "NSW subcontract opportunities. Good for Ziman — smaller jobs than government. "
            "Requires browser (JS-rendered). Stub ready in #141 pattern."
        ),
        requires_browser=True,
    ),
    Source(
        id="vendorpanel",
        name="VendorPanel (Council & Health procurement)",
        tier=1,
        probe_url="https://www.vendorpanel.com.au/marketplace",
        harvest_module=None,
        open_data_license="public",
        notes=(
            "Councils and health districts post painting/maintenance jobs. "
            "Requires registration (NOT auto-harvestable without owner account). "
            "Action: owner registers Ziman ABN, then IMAP listener handles replies."
        ),
        requires_auth=True,
    ),

    # ── T2: Job Boards ───────────────────────────────────────────────────────────
    Source(
        id="seek_painter_sydney",
        name="Seek.com.au — Painter Jobs Sydney",
        tier=2,
        probe_url="https://www.seek.com.au/painter-jobs/in-sydney-nsw",
        harvest_module="ofn.agents.seek_harvest",
        open_data_license="public",
        notes=(
            "LIVE and working. seek_harvest.py implemented and tested. "
            "Yields painting job postings = potential subcontract leads."
        ),
    ),
    Source(
        id="indeed_painter_sydney",
        name="Indeed.com.au — Painter Sydney",
        tier=2,
        probe_url="https://au.indeed.com/jobs?q=painter&l=Sydney+NSW",
        harvest_module=None,
        open_data_license="public",
        notes=(
            "Parallel to Seek. HTML scrape pattern identical to seek_harvest. "
            "TODO: indeed_harvest.py — copy seek_harvest pattern, change URL + selectors."
        ),
    ),
    Source(
        id="airtasker_painting",
        name="Airtasker — Painting Tasks Sydney",
        tier=2,
        probe_url="https://www.airtasker.com/au/s/?q=painting&location=Sydney%2C+NSW",
        harvest_module=None,
        open_data_license="public",
        notes=(
            "Direct homeowner demand. Budget listed. Tasks = Ziman direct customer. "
            "Requires browser (Cloudflare). PR #141 Chromium pattern applies."
        ),
        requires_browser=True,
    ),
    Source(
        id="hipages_painting",
        name="HiPages — Painting Jobs Sydney",
        tier=2,
        probe_url="https://hipages.com.au/find/painters/sydney",
        harvest_module=None,
        open_data_license="public",
        notes=(
            "Hipages posts homeowner painting requests publicly (before quoting). "
            "JSON API behind UI — probe to confirm. High-quality Ziman leads."
        ),
        requires_browser=True,
    ),
    Source(
        id="servicem8_board",
        name="ServiceM8 Community Job Board",
        tier=2,
        probe_url="https://www.servicem8.com/job-board",
        harvest_module=None,
        open_data_license="public",
        notes="Tradesperson subcontract job board. Relevant for Ziman subcontract angle.",
    ),

    # ── T3: Contract & Award Registries ─────────────────────────────────────────
    Source(
        id="nsw_open_data_contracts",
        name="NSW Open Data Portal — Contracts (data.nsw.gov.au)",
        tier=3,
        probe_url="https://api.data.nsw.gov.au/data/api/3/action/package_search?q=painting+contract&rows=5",
        harvest_module=None,
        open_data_license="CC-BY-4.0",
        notes=(
            "CKAN JSON API. No auth. Painting contract awards = warm repeat buyers. "
            "Same pattern as nsw_ocp_harvest but via CKAN. Stub: data_nsw_harvest.py."
        ),
    ),
    Source(
        id="local_government_tenders",
        name="Local Government Procurement (councils.nsw.gov.au)",
        tier=3,
        probe_url="https://www.councilprocurement.nsw.gov.au",
        harvest_module=None,
        open_data_license="public",
        notes=(
            "32 Greater Sydney councils each have procurement portals. "
            "Octopus action: probe each council domain for tender pages. "
            "High value — councils paint buildings every 3-5 years on contract."
        ),
        requires_browser=True,
    ),

    # ── T4: Community / Classifieds ──────────────────────────────────────────────
    Source(
        id="gumtree_painting_sydney",
        name="Gumtree — Painting Services Sydney",
        tier=4,
        probe_url="https://www.gumtree.com.au/s-services/sydney/painting/k0c18310l3004152",
        harvest_module=None,
        open_data_license="public",
        notes=(
            "Homeowner requests for painting. Lower value but high volume. "
            "HTML scrape: no login needed. Regex pattern same as seek_harvest."
        ),
    ),
    Source(
        id="facebook_marketplace_painting",
        name="Facebook Marketplace — Painting Sydney",
        tier=4,
        probe_url="https://www.facebook.com/marketplace/sydney/search?query=painting",
        harvest_module=None,
        open_data_license="public",
        requires_auth=True,
        notes=(
            "Requires login. NOT auto-harvestable. "
            "Owner can manually export leads — IMAP import pattern."
        ),
    ),
    Source(
        id="nextdoor_painting",
        name="Nextdoor — Sydney Painting Recommendations",
        tier=4,
        probe_url="https://nextdoor.com.au",
        harvest_module=None,
        open_data_license="public",
        requires_auth=True,
        notes="Requires address verification. NOT auto-harvestable. High trust signal.",
    ),

    # ── T5: Regulatory / Licensing ───────────────────────────────────────────────
    Source(
        id="nsw_fairtrading_painter_licence",
        name="NSW Fair Trading — Painter Contractor Licence Register",
        tier=5,
        probe_url="https://www.fairtrading.nsw.gov.au/trades-and-businesses/construction-and-trade-licensing/licence-search",
        harvest_module=None,
        open_data_license="public",
        requires_browser=True,
        notes=(
            "Public register of all licensed painting contractors in NSW. "
            "Use: find partners for subcontracting, verify Ziman licence status, "
            "find competitors in territory."
        ),
    ),
    Source(
        id="abr_abn_lookup",
        name="ABR ABN Lookup (abr.business.gov.au)",
        tier=5,
        probe_url="https://abr.business.gov.au/Search/ResultList?SearchText=painting+contractor+sydney",
        harvest_module=None,
        open_data_license="CC-BY-4.0",
        notes=(
            "Free ABN lookup API. Verify any business before engaging. "
            "Use: validate Ziman ABN 21190030795, verify subcontractors."
        ),
    ),
]


# ── probe helpers ────────────────────────────────────────────────────────────

def probe_source(source: Source, timeout: int = 8) -> SourceStatus:
    """
    HEAD/GET a source to check liveness. Never raises.
    Returns LIVE, DEAD, BLOCKED, or UNKNOWN.
    """
    from datetime import datetime, timezone
    try:
        req = urllib.request.Request(
            source.probe_url,
            method="HEAD",
            headers={"User-Agent": "octopus-source-probe/1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.getcode()
            source.last_probed = datetime.now(timezone.utc).isoformat()
            if 200 <= code < 400:
                source.status = SourceStatus.LIVE
            elif code in (401, 403, 429):
                source.status = SourceStatus.BLOCKED
            else:
                source.status = SourceStatus.DEAD
    except Exception as exc:  # noqa: BLE001 — probe must never crash
        source.last_probed = datetime.now(timezone.utc).isoformat()
        source.status = SourceStatus.UNKNOWN
        log.debug("probe %s: %s", source.id, exc)
    return source.status


def probe_all(tier_max: int = 5, skip_browser: bool = True) -> List[Source]:
    """
    Probe all sources up to tier_max.
    skip_browser=True: skip sources that need Chromium (use when headless unavailable).
    Returns sources sorted by tier, status.
    """
    results = []
    for src in SOURCES:
        if src.tier > tier_max:
            continue
        if src.requires_auth:
            continue  # never auto-probe auth sources
        if skip_browser and src.requires_browser:
            src.status = SourceStatus.UNKNOWN
            results.append(src)
            continue
        probe_source(src)
        results.append(src)
        time.sleep(0.5)  # polite interval
    return sorted(results, key=lambda s: (s.tier, s.status.value))


def live_sources(tier_max: int = 3) -> List[Source]:
    """Return sources with LIVE status and a harvest_module (auto-harvestable)."""
    return [
        s for s in SOURCES
        if s.status == SourceStatus.LIVE
        and s.harvest_module is not None
        and s.tier <= tier_max
        and not s.requires_auth
    ]


def report() -> str:
    """Human-readable source status report for cockpit / doctor."""
    lines = ["OCTOPUS SOURCE REGISTRY ─ دسترس خودمختار به منابع", ""]
    by_tier: dict[int, List[Source]] = {}
    for s in SOURCES:
        by_tier.setdefault(s.tier, []).append(s)
    tier_names = {
        1: "T1 — مناقصه‌های دولتی",
        2: "T2 — بوردهای کار",
        3: "T3 — ثبت قراردادها",
        4: "T4 — کلاسیفاید محلی",
        5: "T5 — پروانه‌ها و نظارتی",
    }
    icons = {
        SourceStatus.LIVE:    "✅",
        SourceStatus.DEAD:    "❌",
        SourceStatus.BLOCKED: "🚫",
        SourceStatus.UNKNOWN: "❓",
    }
    for tier in sorted(by_tier):
        lines.append(f"## {tier_names.get(tier, f'T{tier}')}")
        for s in by_tier[tier]:
            icon = icons[s.status]
            browser = " [🖥️ browser]" if s.requires_browser else ""
            auth = " [🔒 auth]" if s.requires_auth else ""
            module = f" → {s.harvest_module}" if s.harvest_module else " → stub"
            lines.append(f"  {icon} {s.name}{browser}{auth}{module}")
        lines.append("")
    return "\n".join(lines)
