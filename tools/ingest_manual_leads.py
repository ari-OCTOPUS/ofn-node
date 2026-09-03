#!/usr/bin/env python3
"""Ingest manually-collected B2B leads into painting_b2b_accounts.

Usage:
    cd ~/Desktop/OFN_Elahe_repo/ofn-node
    source .venv/bin/activate
    python tools/ingest_manual_leads.py
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
    # ── Already inserted (will upsert / update) ──
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
            "State Manager NSW Service Ops (Buildings) role open. "
            "BMS, HVAC, Fire/Safety, Maintenance. "
            "Office: 3 Richardson Pl, North Ryde NSW 2113."
        ),
    },

    # ── NEW ──

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
            "Strata Management company. "
            "7/558 Pacific Hwy, St Leonards NSW 2065."
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
            "$51.4B funds under mgmt. $12.8B dev pipeline. "
            "Asset & Property Mgmt, Facilities Mgmt, Service Providers. "
            "Level 30, Quay Quarter Tower, 50 Bridge St, Sydney NSW 2000."
        ),
    },
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
            "Senior Manager Property Portfolio role. "
            "Property Portfolio Mgmt, Asset & Project Mgmt, Leasing, Service Providers. "
            "No direct phone/email found yet — needs enrichment."
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
            "Strata & Facility Mgmt. $30B+ property value. 201-500 employees. "
            "Repairs & Maintenance, Quotes & Work Orders. "
            "Level 7, 447 Kent St, Sydney NSW 2000."
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
        status = "OK" if result.get("ok") else "FAIL"
        print(f"  [{status}] {rec['business_name']}: "
              f"id={result.get('account')}, "
              f"score={result.get('score')}, "
              f"{result.get('recommendation', result.get('error', ''))}")
        if result.get("ok"):
            ok += 1
    print(f"\nDone: {ok}/{len(LEADS)} upserted into {db}")


if __name__ == "__main__":
    main()
