#!/usr/bin/env python3
"""Ingest manually-collected B2B leads into painting_b2b_accounts.

Usage:
    cd ~/Desktop/OFN_Elahe_repo/ofn-node   # or board138 worktree
    source .venv/bin/activate
    python tools/ingest_manual_leads.py

Uses existing LeadStore.create_account() upsert (ON CONFLICT DO UPDATE).
No schema changes. No network I/O. Collection-only.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from ofn.adapters.lead_store import LeadStore  # noqa: E402

TENANT = "lead"


def _db_path() -> str:
    p = os.environ.get("OFN_PAINTING_DB")
    if p:
        return p
    default = Path.home() / ".local" / "share" / "ofn" / "painting.sqlite"
    if default.exists():
        return str(default)
    return str(REPO / "painting.sqlite")


LEADS = [
    # ── STRATA ──
    {
        "business_name": "RD Facilities Management",
        "segment": "strata",
        "suburb": "Seven Hills",
        "service_area": "Sydney metropolitan area, NSW",
        "website": "https://rdfm.com.au",
        "contact_channel": (
            "1800 507 552 | admin@rdfm.com.au | "
            "Alpesh Prajapati (Director) | "
            "Bhagyawanti Prajapati (CEO)"
        ),
        "evidence_url": "https://rdfm.com.au",
        "stage": "discovered",
        "outreach_permission": "unknown",
        "notes": (
            "RELEVANCE: 8/10. APPROACH: Direct. "
            "Est. 2010. 250+ sites. Strata/Govt/Commercial. "
            "Cleaning, Building Mgmt, Maintenance, Security, Pest, Garden, Waste, "
            "High Pressure Cleaning, Mould Remediation, General Maintenance. "
            "ISO 9001/14001/45001. 24/7 emergency. "
            "23/45 Powers Rd, Seven Hills NSW 2147."
        ),
    },
    {
        "business_name": "Bright and Duggan Group",
        "segment": "strata",
        "suburb": "St Leonards",
        "service_area": "Sydney",
        "website": "https://bright-duggan.com.au",
        "contact_channel": "1300 092 863 | customercare@bright-duggan.com.au",
        "evidence_url": "https://linkedin.com/company/bright-duggann/",
        "stage": "discovered",
        "outreach_permission": "unknown",
        "notes": (
            "RELEVANCE: 8/10. APPROACH: Direct. "
            "Strata Management company. "
            "7/558 Pacific Hwy, St Leonards NSW 2065."
        ),
    },
    {
        "business_name": "Smarter Communities",
        "segment": "strata",
        "suburb": "Sydney CBD",
        "service_area": "Sydney",
        "website": "https://smartercommunities.com.au",
        "contact_channel": "1800 519 642 | info@smartercommunities.com.au",
        "evidence_url": "https://linkedin.com/company/smarter-communities/",
        "stage": "discovered",
        "outreach_permission": "unknown",
        "notes": (
            "RELEVANCE: 9/10. APPROACH: Direct. "
            "Strata & Facility Mgmt. $30B+ property value. 201-500 employees. "
            "Repairs & Maintenance, Quotes & Work Orders. "
            "Level 7, 447 Kent St, Sydney NSW 2000."
        ),
    },

    # ── COMMERCIAL ──
    {
        "business_name": "ESR Group",
        "segment": "commercial",
        "suburb": "Sydney CBD",
        "service_area": "NSW, SA",
        "website": "https://au.esr.com",
        "contact_channel": (
            "Fergus Adamson (GM Property Services NSW) "
            "M:+61 415 784 898 O:+61 2 9186 4727 fergus.adamson@esr.com | "
            "Nicole Stephens (Regional Mgr Property Mgmt) "
            "M:+61 429 479 141 O:+61 2 9186 4746 nicole.stephens@esr.com"
        ),
        "evidence_url": "https://linkedin.com/company/esrgroup/",
        "stage": "discovered",
        "outreach_permission": "unknown",
        "notes": (
            "RELEVANCE: 8/10. APPROACH: Direct. "
            "A$22.9B+ AUM, 195 assets. Industrial/commercial/logistics. "
            "Main phone: +61 2 9186 4700. "
            "HQ: Level 13, 39 Martin Place, Sydney NSW 2000."
        ),
    },
    {
        "business_name": "Siemens Australia - Smart Infrastructure",
        "segment": "commercial",
        "suburb": "North Ryde",
        "service_area": "NSW",
        "website": "https://siemens.com",
        "contact_channel": (
            "Buildings Service NSW: 1300 782 379 | "
            "Building Products: 1300 773 948 buildingproducts.sales.au@siemens.com | "
            "General: 137 222"
        ),
        "evidence_url": "https://linkedin.com/company/siemens/",
        "stage": "discovered",
        "outreach_permission": "unknown",
        "notes": (
            "RELEVANCE: 7/10. APPROACH: Direct. "
            "State Manager NSW Service Ops (Buildings) role open. "
            "BMS, HVAC, Fire/Safety, Maintenance. "
            "Office: 3 Richardson Pl, North Ryde NSW 2113."
        ),
    },
    {
        "business_name": "SGCH",
        "segment": "commercial",
        "suburb": "Liverpool",
        "service_area": "Sydney, Melbourne, Brisbane",
        "website": "https://sgch.com.au",
        "contact_channel": "1800 573 370 | office@sgch.com.au",
        "evidence_url": "https://linkedin.com/company/sgch/",
        "stage": "discovered",
        "outreach_permission": "unknown",
        "notes": (
            "RELEVANCE: 8/10. APPROACH: Direct. "
            "Community housing provider. 7,000+ homes. $4.6B assets managed. "
            "Property care, repairs & maintenance, property condition monitoring. "
            "Level 4, 50 Scott St, Liverpool NSW 2170."
        ),
    },
    {
        "business_name": "Dexus",
        "segment": "commercial",
        "suburb": "Sydney CBD",
        "service_area": "NSW",
        "website": "https://dexus.com",
        "contact_channel": "+61 2 9017 1100",
        "evidence_url": "https://linkedin.com/company/dexus-group/",
        "stage": "discovered",
        "outreach_permission": "unknown",
        "notes": (
            "RELEVANCE: 8/10. APPROACH: Direct. "
            "$51.4B funds under mgmt. $12.8B dev pipeline. "
            "Asset & Property Mgmt, Facilities Mgmt, Service Providers. "
            "Level 30, Quay Quarter Tower, 50 Bridge St, Sydney NSW 2000."
        ),
    },
    {
        "business_name": "Woolworths Group",
        "segment": "commercial",
        "suburb": "Bella Vista",
        "service_area": "National (NSW focus)",
        "website": "https://woolworthsgroup.com.au",
        "contact_channel": "+61 2 8885 0000 | Decision maker in Property/Asset/Facilities/Procurement TBD",
        "evidence_url": "https://linkedin.com/company/woolworths-group/",
        "stage": "discovered",
        "outreach_permission": "unknown",
        "notes": (
            "RELEVANCE: 7/10. APPROACH: Direct or Vendor Panel. "
            "Assistant Asset Manager role. National portfolio of owned/controlled "
            "shopping centres & retail properties. 10,001+ employees. "
            "Vendor Mgmt, Facility Managers, External Property Managers, "
            "Maintenance, Capital & Operating Expenditure, OH&S. "
            "1 Woolworths Way, Bella Vista NSW 2153."
        ),
    },
    {
        "business_name": "Cushman and Wakefield Sydney",
        "segment": "commercial",
        "suburb": "Sydney CBD",
        "service_area": "ANZ",
        "website": "https://cushmanwakefield.com",
        "contact_channel": "+61 2 8243 9999 | Jon McCormick (Head of IFM & Asset Services ANZ)",
        "evidence_url": "https://linkedin.com/company/cushman-&-wakefield/",
        "stage": "discovered",
        "outreach_permission": "unknown",
        "notes": (
            "RELEVANCE: 8/10. APPROACH: Direct. "
            "Global real estate services. Facilities Mgmt & Asset Services. "
            "Decision maker: Jon McCormick, Head of IFM & Asset Services ANZ. "
            "They outsource maintenance/painting to contractors — we are that contractor. "
            "Level 22, 1 O Connell St, Sydney NSW 2000."
        ),
    },

    # ── GOVERNMENT ──
    {
        "business_name": "NSW Department of Planning Housing and Infrastructure",
        "segment": "government",
        "suburb": "Parramatta",
        "service_area": "NSW",
        "website": "https://dphi.nsw.gov.au",
        "contact_channel": "",
        "evidence_url": "https://linkedin.com/company/nswdphi/",
        "stage": "discovered",
        "outreach_permission": "unknown",
        "notes": (
            "RELEVANCE: 7/10. APPROACH: Panel/Tender. "
            "Senior Manager Property Portfolio role. "
            "Property Portfolio Mgmt, Asset & Project Mgmt, Leasing, Service Providers. "
            "No direct phone/email found yet — needs enrichment."
        ),
    },
    {
        "business_name": "Sydney Water",
        "segment": "government",
        "suburb": "Parramatta",
        "service_area": "Greater Sydney (12,700 km2)",
        "website": "https://sydneywater.com.au",
        "contact_channel": "13 20 92",
        "evidence_url": "https://linkedin.com/company/sydney-water/",
        "stage": "discovered",
        "outreach_permission": "unknown",
        "notes": (
            "RELEVANCE: 7/10. APPROACH: Panel/Tender — government utility, "
            "entry via panel/tender not direct outreach. "
            "Property Asset Program Manager role open — "
            "asset lifecycle, maintenance program, contractor oversight. "
            "Thousands of assets/buildings. "
            "ACTION: Look for panel/vendor registration on sydneywater procurement portal. "
            "1 Smith St, Parramatta NSW 2150."
        ),
    },
    {
        "business_name": "City of Canterbury Bankstown",
        "segment": "government",
        "suburb": "Bankstown",
        "service_area": "Canterbury-Bankstown LGA",
        "website": "https://cbcity.nsw.gov.au",
        "contact_channel": "02 9707 9000 | council@cbcity.nsw.gov.au",
        "evidence_url": "https://linkedin.com/company/city-of-canterbury-bankstown/",
        "stage": "discovered",
        "outreach_permission": "unknown",
        "notes": (
            "RELEVANCE: 7/10. APPROACH: Panel/Tender. "
            "Local council — Tier1 metro LGA in our service area. "
            "Council buildings, community facilities, parks infrastructure. "
            "66-72 Rickard Rd, Bankstown NSW 2200."
        ),
    },

    # ── SUBCONTRACTOR PATHWAY ──
    {
        "business_name": "Downer Group",
        "segment": "subcontractor",
        "suburb": "North Ryde",
        "service_area": "National",
        "website": "https://downergroup.com",
        "contact_channel": "+61 2 9468 9700 | info@downergroup.com",
        "evidence_url": "https://linkedin.com/company/downer/",
        "stage": "discovered",
        "outreach_permission": "unknown",
        "notes": (
            "RELEVANCE: 6/10. APPROACH: SUBCONTRACTOR PATHWAY — NOT a direct client. "
            "Owns Spotless Group. Gets FM contracts from govt/hospitals/schools/defence "
            "(300+ sites, PPP 25yr contracts) then subcontracts painting to trade partners. "
            "DO NOT cold call a Property Manager — look for Procurement/Supply Chain/"
            "Trade Partner Onboarding portal instead. Vendor/panel registration is the entry. "
            "Completely different outreach strategy from strata/commercial. "
            "39 Delhi Rd, North Ryde NSW 2113."
        ),
    },
]


def main() -> None:
    db = _db_path()
    print(f"DB: {db}")
    store = LeadStore(db)
    now = datetime.now(timezone.utc).isoformat()
    ok = 0
    for rec in LEADS:
        result = store.create_account(TENANT, rec, now_iso=now)
        tag = "OK" if result.get("ok") else "FAIL"
        print(f"  [{tag}] {rec['business_name']}: "
              f"id={result.get('account')}, "
              f"score={result.get('score')}, "
              f"{result.get('recommendation', result.get('error', ''))}")
        if result.get("ok"):
            ok += 1
    print(f"\nDone: {ok}/{len(LEADS)} upserted into {db}")


if __name__ == "__main__":
    main()
