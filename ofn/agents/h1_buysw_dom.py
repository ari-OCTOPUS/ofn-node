"""H1 buy.nsw DOM-batch ingest — the receiving gate for the Chrome harvester.

The official OCDS feed (tenders.nsw.gov.au) is dead and buy.nsw has no
public API; the WAF blocks every non-browser client. The Chrome extension
(tools/buynsw-harvester) therefore reads the pages a human is already
browsing in Sydney and exports a batch JSON file. This module is the
node-side gate for that file. Only the transport differs from the API
path — the filter, the scorer, and the store are the SAME ones the dead
feed used (h1_buysw.filter_painting_tender / build_score_inputs), so a
tender counts as a painting tender for exactly one reason wherever it
came from.

Contract: batch JSON "buynsw-harvest-batch/1" as built by the extension's
mapping.js (keys pinned by tests/test_h1_buynsw_dom.py — change both sides
in one commit). Records that fail shape validation are counted as
rejected_invalid, never silently dropped: no vacuous pass.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Mapping

from .h1_buysw import build_score_inputs, filter_painting_tender

BATCH_SCHEMA = "buynsw-harvest-batch/1"
SOURCE_ID_DOM = "buy_nsw_dom"
TENANT = "lead"

_UUID_RE = re.compile(r"/notices/([^/?#]+)", re.IGNORECASE)
_SPLIT_RE = re.compile(r"[,;/]| and ", re.IGNORECASE)
MAX_RECORDS = 5000          # one human session never exceeds this
_STORE_SCAN_LIMIT = 500     # mirrors h1_harvest.cycle dedup scan


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _uuid_from_url(url: object) -> str:
    m = _UUID_RE.search(str(url or ""))
    return m.group(1) if m else ""


def dom_to_parsed(rec: Mapping) -> dict | None:
    """Extension record → the parsed shape h1_buysw's gates consume.

    Returns None when title or a usable identity (notice_uuid / detail_url
    UUID) is missing — the extension contract makes both mandatory.
    """
    title = str(rec.get("title") or "").strip()
    uuid = str(rec.get("notice_uuid") or "").strip() or _uuid_from_url(
        rec.get("detail_url"))
    if not title or not uuid:
        return None

    location_text = str(rec.get("location_text") or "").strip()
    regions = [t for t in (
        p.strip().lower() for p in _SPLIT_RE.split(location_text)) if t]

    amount = rec.get("amount_aud")
    try:
        amount = float(amount) if amount is not None else None
    except (TypeError, ValueError):
        amount = None

    return {
        "tender_id": f"{SOURCE_ID_DOM}:{uuid}",
        "title": title,
        "description": str(rec.get("raw_text") or ""),
        "buyer_name": str(rec.get("buyer_name") or ""),
        "location": location_text,
        "regions": regions,
        "closing_at": str(rec.get("closing_at") or ""),
        "amount": amount,
        "unspsc_codes": [],          # DOM cards carry no UNSPSC classification
        "source": SOURCE_ID_DOM,
        "source_url": str(rec.get("detail_url") or ""),
        "access_mode": "owner_upload",
        "evidence_status": "unverified",
        "status": "scored",
        "rftuuid": uuid,
    }


def _rejected(reason: str, **counts) -> dict:
    base = {"status": "REJECTED", "reason": reason, "records": 0,
            "accepted": 0, "rejected_filter": 0, "rejected_dup": 0,
            "rejected_invalid": 0, "created": []}
    base.update(counts)
    return base


def ingest_batch(payload: object, store) -> dict:
    """Validate one batch, run the shared gates, create new tenders.

    Accounting is honest by construction: records == accepted +
    rejected_filter + rejected_dup + rejected_invalid, or the whole batch
    is REJECTED before any write. Idempotent: tender_ids already in the
    store are counted as rejected_dup, never recreated.
    """
    if not isinstance(payload, Mapping):
        return _rejected("payload is not a JSON object")
    if payload.get("schema") != BATCH_SCHEMA:
        return _rejected(
            f"unknown schema: {payload.get('schema')!r} != {BATCH_SCHEMA!r}")
    records = payload.get("records")
    if not isinstance(records, list):
        return _rejected("records is not a list")
    if not records:
        return _rejected("records is empty")
    if len(records) > MAX_RECORDS:
        return _rejected(f"records over cap: {len(records)} > {MAX_RECORDS}")

    existing = {t.get("tender_id") for t in (
        store.tenders(TENANT, limit=_STORE_SCAN_LIMIT) or [])}
    now_iso = _now_iso()
    accepted = rejected_filter = rejected_dup = rejected_invalid = 0
    created: list[str] = []

    for rec in records:
        if not isinstance(rec, Mapping):
            rejected_invalid += 1
            continue
        parsed = dom_to_parsed(rec)
        if parsed is None:
            rejected_invalid += 1
            continue
        if not filter_painting_tender(parsed):
            rejected_filter += 1
            continue
        if parsed["tender_id"] in existing:
            rejected_dup += 1
            continue
        result = store.create_tender(TENANT, {
            "tender_id": parsed["tender_id"],
            "source": parsed["source"],
            "source_url": parsed["source_url"],
            "title": parsed["title"],
            "buyer_name": parsed["buyer_name"],
            "location": parsed["location"],
            "closing_at": parsed["closing_at"],
            "access_mode": parsed["access_mode"],
            "evidence_status": parsed["evidence_status"],
            "status": parsed["status"],
            "score_inputs": build_score_inputs(parsed),
        }, now_iso=now_iso)
        if result.get("ok"):
            accepted += 1
            created.append(parsed["tender_id"])
            existing.add(parsed["tender_id"])
        else:
            rejected_invalid += 1

    return {"status": "DONE", "schema": BATCH_SCHEMA,
            "records": len(records), "accepted": accepted,
            "rejected_filter": rejected_filter,
            "rejected_dup": rejected_dup,
            "rejected_invalid": rejected_invalid,
            "created": created}
