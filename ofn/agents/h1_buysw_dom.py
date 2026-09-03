"""H1 buy.nsw DOM-batch ingest — the receiving gate for the browser harvester.

The official OCDS feed (tenders.nsw.gov.au) is dead and buy.nsw has no
public API; the WAF blocks every non-browser client. The Chrome extension
(tools/buynsw-harvester, v0.2 — the recovered "for-ari" pack, adopted and
integrated) reads the pages a human is already browsing in Sydney and
exports records. This module is the node-side gate for that export. Only
the transport differs from the API path — the filter, the scorer, and the
store are the SAME ones the dead feed used (h1_buysw rules +
LeadStore.create_tender), so a tender counts as a painting tender for
exactly one reason wherever it came from.

Two producer shapes are accepted, both fail-closed on anything else:

  1. versioned batch  {"schema": "buynsw-harvest-batch/1", "records": [...]}
     (v1 records: notice_uuid/title/location_text/amount_aud/detail_url/...)
  2. extension export {"source": "buysw_web", "count": N, "records": [...]}
     (v2 records: tender_id/kind/title/buyer_name/amount_text/supplier_name/
      contact_email/...; kind=="award" (CAN) also mints a warm buyer lead —
      an agency that has paid for painting will pay again)

Honest accounting: records == accepted + rejected_filter + rejected_dup +
rejected_invalid, or the whole batch is REJECTED before any write. PII in
free text is measured (kernel.scrub) and reported, never silently kept.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Mapping

from ..kernel.scrub import scrub
from .h1_buysw import (
    ACCEPT_KEYWORDS, ACCEPT_REGIONS, MIN_VALUE_AUD, REJECT_KEYWORDS,
    build_score_inputs,
)

BATCH_SCHEMA_V1 = "buynsw-harvest-batch/1"
BATCH_SCHEMA = BATCH_SCHEMA_V1            # back-compat alias (tests/README)
EXPORT_SOURCE_V2 = "buysw_web"
SOURCE_ID_DOM = "buy_nsw_dom"
TENANT = "lead"

_UUID_RE = re.compile(r"/notices/([^/?#]+)", re.IGNORECASE)
_GUID_RE = re.compile(
    r"[0-9A-Fa-f]{8}-?[0-9A-Fa-f]{4}-?[0-9A-Fa-f]{4}"
    r"-?[0-9A-Fa-f]{4}-?[0-9A-Fa-f]{12}")
_MONEY_RE = re.compile(
    r"\$\s?([\d][\d,\s]*(?:\.\d+)?)\s*(m\b|million|k\b)?", re.IGNORECASE)
MAX_RECORDS = 5000          # one human session never exceeds this
_STORE_SCAN_LIMIT = 500     # mirrors h1_harvest.cycle dedup scan
_MAX_ERRORS_KEPT = 10


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _s(value: object) -> str:
    return str(value or "").strip()


def _uuid_from_url(url: object) -> str:
    m = _UUID_RE.search(_s(url))
    return m.group(1) if m else ""


def _parse_amount(value: object) -> float | None:
    """v1 numeric amount, or v2 money text like '$180,000' / '$1.2m'."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    text = _s(value)
    if not text:
        return None
    m = _MONEY_RE.search(text)
    if not m:
        return None
    try:
        num = float(m[1].replace(",", "").replace(" ", ""))
    except ValueError:
        return None
    if m[2] and m[2].lower().startswith("m"):
        return num * 1e6
    if m[2] and m[2].lower() == "k":
        return num * 1e3
    return num


_CLOSING_FORMATS = ("%d-%b-%Y %H:%M", "%d-%b-%Y", "%d %B %Y", "%d %b %Y")

# Salvage rules born from the real 37-record export (Sep-3 pack): results
# cards whose only link text was "See details" still carry the real title
# and the closing date inside the card description, as
# "{TITLE} Closes: {DATE} {TIME} {CATEGORIES} ... {AGENCY}".
_GENERIC_TITLES = frozenset(
    {"see details", "details", "view", "more", "view details"})
_CLOSES_IN_DESC_RE = re.compile(
    r"Closes?\s*:\s*(\d{1,2}[\s-]+\w{3,9}[\s-]+\d{4}(?:\s+\d{1,2}:\d{2})?)",
    re.IGNORECASE)


def _norm_closing(value: object) -> str:
    """The real cards render 'Closes: 21-Sep-2026 15:00' — normalize to ISO
    so deadline-feasibility (D) scores instead of falling back. Passthrough
    for anything unparseable (never invent a date)."""
    text = _s(value)
    for fmt in _CLOSING_FORMATS:
        try:
            return datetime.strptime(text, fmt).replace(
                tzinfo=timezone.utc).isoformat(timespec="minutes")
        except ValueError:
            continue
    return text


def _salvage(title: str, description: str, closing_at: str) -> tuple[str, str]:
    """Recover title/closing from the description when the link text was a
    generic click-through label or the closing field came back empty.
    Idempotent on good records."""
    if title.lower() in _GENERIC_TITLES or not title:
        desc = description
        m = _CLOSES_IN_DESC_RE.search(desc)
        if m and m.start() > 3:
            title = desc[:m.start()].strip()[:200]
        elif len(desc) > 10:
            title = desc[:150].strip()
    if not closing_at:
        m = _CLOSES_IN_DESC_RE.search(description)
        if m:
            closing_at = m.group(1).strip()
    return title, closing_at


def _normalize(rec: Mapping) -> dict | None:
    """Either producer's record → one internal shape (or None if invalid).

    v2 detection: the extension's normalize() always emits tender_id and
    kind; v1 always emits notice_uuid/detail_url.
    """
    is_v2 = bool(rec.get("tender_id") or rec.get("kind")
                 or rec.get("channel") == "buysw_web")
    if is_v2:
        title = _s(rec.get("title"))
        description = _s(rec.get("description"))
        uuid = _s(rec.get("uuid"))
        tender_id = _s(rec.get("tender_id")) or (
            f"{SOURCE_ID_DOM}:{uuid}" if uuid else "")
        title, closing_text = _salvage(
            title, description, _s(rec.get("closing_at")))
        if not title or not tender_id:
            return None
        return {
            "tender_id": tender_id[:160],
            "title": title,
            "description": description,
            "buyer_name": _s(rec.get("buyer_name")),
            "location": _s(rec.get("location")),
            "category": _s(rec.get("category")),
            "closing_at": _norm_closing(closing_text),
            "amount": _parse_amount(rec.get("amount_aud")
                                    if "amount_aud" in rec
                                    else rec.get("amount_text")),
            "detail_url": _s(rec.get("source_url")),
            "kind": _s(rec.get("kind")) or "opportunity",
            "supplier_name": _s(rec.get("supplier_name")),
            "contact_email": _s(rec.get("contact_email")),
            "contact_phone": _s(rec.get("contact_phone")),
            "abn": _s(rec.get("abn")),
        }

    title = _s(rec.get("title"))
    uuid = _s(rec.get("notice_uuid")) or _uuid_from_url(rec.get("detail_url"))
    if not title or not uuid:
        return None
    return {
        "tender_id": f"{SOURCE_ID_DOM}:{uuid}"[:160],
        "title": title,
        "description": _s(rec.get("raw_text")),
        "buyer_name": _s(rec.get("buyer_name")),
        "location": _s(rec.get("location_text")),
        "category": "",
        "closing_at": _norm_closing(rec.get("closing_at")),
        "amount": _parse_amount(rec.get("amount_aud")),
        "detail_url": _s(rec.get("detail_url")),
        "kind": "opportunity",
        "supplier_name": "", "contact_email": "", "contact_phone": "",
        "abn": "",
    }


def _regions_of(rec: Mapping) -> list[str]:
    geo_text = " ".join(
        (rec["location"], rec["title"], rec["buyer_name"])).lower()
    return [r for r in ACCEPT_REGIONS if r in geo_text]


def passes_filter(rec: Mapping) -> bool:
    """Same deterministic rules as h1_buysw, keyword/geo/value only (no
    UNSPSC exists on web pages). Reject list wins over accept list."""
    text = " ".join((rec["title"], rec["description"], rec["category"],
                     rec["buyer_name"])).lower()
    if any(rk in text for rk in REJECT_KEYWORDS):
        return False
    if not any(ak in text for ak in ACCEPT_KEYWORDS):
        return False
    # Geography: an explicitly stated location outside the service area
    # rejects; no location at all passes (scored G=0.3, like the OCDS path).
    if rec["location"] and not _regions_of(rec):
        return False
    if rec["amount"] is not None and rec["amount"] < MIN_VALUE_AUD:
        return False
    return True


def _tender_payload(rec: Mapping) -> dict:
    return {
        "tender_id": rec["tender_id"],
        "source": EXPORT_SOURCE_V2 if rec["kind"] else SOURCE_ID_DOM,
        "source_url": rec["detail_url"],
        "title": rec["title"],
        "buyer_name": rec["buyer_name"],
        "location": rec["location"],
        "closing_at": rec["closing_at"],
        "access_mode": "owner_upload",
        "evidence_status": "unverified",
        "status": "scored",
        "score_inputs": build_score_inputs({
            "title": rec["title"],
            "description": rec["description"],
            "regions": _regions_of(rec),
            "closing_at": rec["closing_at"],
            "amount": rec["amount"],
            "unspsc_codes": [],
        }),
    }


def _lead_payload(rec: Mapping) -> dict | None:
    """Award (CAN) record with a named buyer → warm buyer lead. Contact
    fields are structured; outreach stays gated by the contact-policy path
    (intake is not delivery evidence and cannot close a lead)."""
    buyer = rec["buyer_name"]
    if not buyer:
        return None
    uuid = ""
    m = _GUID_RE.search(rec["tender_id"])
    if m:
        uuid = m.group(0).replace("-", "").upper()
    return {
        "lead_id": f"buysw:{uuid}" if uuid else "",
        "name": buyer,
        "email": rec["contact_email"],
        "phone": rec["contact_phone"],
        "location": rec["location"],
        "job_type": rec["title"] or "painting",
        "source": "buysw_web",
        "url": rec["detail_url"],
        "status": "new",
        "notes": (f"NSW award · supplier={rec['supplier_name'] or ''} · "
                  f"ABN={rec['abn'] or ''} · "
                  f"{rec['amount'] if rec['amount'] is not None else ''}"
                  ).strip(),
        "tags": ["nsw", "buysw", "award"],
    }


def _pii_findings(rec: Mapping) -> int:
    blob = " ".join((rec["description"], rec["title"]))
    return len(scrub(blob).findings)


def _rejected(reason: str) -> dict:
    return {"status": "REJECTED", "reason": reason, "records": 0,
            "accepted": 0, "rejected_filter": 0, "rejected_dup": 0,
            "rejected_invalid": 0, "leads_minted": 0, "pii_findings": 0,
            "created": [], "errors": []}


def ingest_batch(payload: object, store, *, relevance: str = "painting") -> dict:
    """Validate one batch/export, run the shared gates, create tenders
    (and award leads). Idempotent: tender_ids already in the store count
    as rejected_dup, never recreated; leads upsert by the store's
    ON CONFLICT. relevance="painting" applies the shared filter;
    relevance="all" admits everything that passes shape validation."""
    if relevance not in ("painting", "all"):
        return _rejected(f"unknown relevance mode: {relevance!r}")
    if not isinstance(payload, Mapping):
        return _rejected("payload is not a JSON object")

    if payload.get("schema") == BATCH_SCHEMA_V1:
        pass                                        # versioned v1 batch
    elif payload.get("source") == EXPORT_SOURCE_V2:
        declared = payload.get("count")
        if declared is not None and declared != len(
                payload.get("records") or []):
            return _rejected(
                f"count mismatch: declared {declared} != "
                f"{len(payload.get('records') or [])}")
    else:
        return _rejected(
            f"unknown wrapper: need schema={BATCH_SCHEMA_V1!r} or "
            f"source={EXPORT_SOURCE_V2!r}")

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
    leads_minted = pii_findings = 0
    errors: list[str] = []

    for raw in records:
        if not isinstance(raw, Mapping):
            rejected_invalid += 1
            continue
        rec = _normalize(raw)
        if rec is None:
            rejected_invalid += 1
            continue
        if relevance == "painting" and not passes_filter(rec):
            rejected_filter += 1
            continue
        if rec["tender_id"] in existing:
            rejected_dup += 1
            continue

        result = store.create_tender(TENANT, _tender_payload(rec),
                                     now_iso=now_iso)
        if not result.get("ok"):
            rejected_invalid += 1
            if len(errors) < _MAX_ERRORS_KEPT:
                errors.append(result.get("error") or "tender rejected")
            continue

        accepted += 1
        created.append(rec["tender_id"])
        existing.add(rec["tender_id"])
        pii_findings += _pii_findings(rec)

        if rec["kind"].lower() == "award":
            lead = _lead_payload(rec)
            if lead:
                try:
                    lres = store.create_lead(TENANT, lead, now_iso=now_iso)
                    if lres.get("ok"):
                        leads_minted += 1
                except Exception as exc:            # one row never aborts
                    if len(errors) < _MAX_ERRORS_KEPT:
                        errors.append(f"lead: {type(exc).__name__}: {exc}")

    return {"status": "DONE", "records": len(records), "accepted": accepted,
            "rejected_filter": rejected_filter,
            "rejected_dup": rejected_dup,
            "rejected_invalid": rejected_invalid,
            "leads_minted": leads_minted, "pii_findings": pii_findings,
            "created": created, "errors": errors}
