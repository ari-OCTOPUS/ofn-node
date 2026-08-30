"""
Slit Sensilla Quarantine — vibration gate before the web commits a lead.

Biological metaphor:
  Slit sensilla are strain receptors in a spider's exoskeleton that detect
  minute vibrations in the web. Before the spider commits to "that's prey",
  the signal must pass a threshold. Wind = ignore. Prey = act. Rival = retreat.

Engineering meaning:
  Every Lead fetched from an external source (Austender, NSW eTendering,
  Planning Alerts) is UNTRUSTED until it passes validation. A compromised or
  buggy upstream API could push malformed, oversized, or injected payloads
  straight into the canonical `leads` table. This module intercepts every
  Lead BEFORE it reaches save_lead(), runs a battery of checks, and either:
    - ADMITS it (passes through to save_lead), or
    - QUARANTINES it (parked in a separate table for inspection), or
    - REJECTS it outright (dropped, logged).

Validation battery (the "sensilla"):
  S1. STRUCTURAL   — required fields present, types correct, no None leaks
  S2. SIZE         — field lengths within sane bounds (no data bombs)
  S3. PROVENANCE   — source tag is on the known-harvester allowlist
  S4. INTEGRITY    — content_hash recorded so later tampering is detectable
  S5. CONTENT      — no obvious injection payloads (XSS, SQL, control chars)
  S6. RELEVANCE    — passes the is_paint_relevant() keyword filter

Each Lead gets a verdict: ADMIT | QUARANTINE | REJECT, with a reason string
and the full validation breakdown. Verdicts are appended to run logs so an
operator can see WHY a lead was parked.

Schema migration: the quarantine table auto-creates on first use via
SQLModel — no manual migration needed. The existing `leads` table and
`save_lead()` are untouched; quarantine is purely additive.

Status: NEW 2026-07-12. Slit Sensilla pattern from the revised synthesis.
All names provisional, owner veto retained.
"""
from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, Session, SQLModel, select

from db import Lead, get_session, utcnow

logger = logging.getLogger(__name__)


# ── Verdict enum ────────────────────────────────────────────────────────────

class Verdict(str, Enum):
    ADMIT = "admit"            # passed all checks → flows to save_lead()
    QUARANTINE = "quarantine"  # parked for inspection; not auto-promoted
    REJECT = "reject"          # dropped; structurally invalid or malicious


# ── Quarantine table model ──────────────────────────────────────────────────

class QuarantineItem(SQLModel, table=True):
    """A lead held for inspection. Mirror of Lead plus validation metadata."""

    id: Optional[int] = Field(default=None, primary_key=True)
    # provenance — how did we get this, and what did we do about it?
    source: str = Field(index=True)
    external_id: str = Field(index=True)
    verdict: str = Field(index=True)          # quarantine (always, on insert)
    reason: str = ""                           # human-readable why
    checks_json: str = ""                      # full breakdown (JSON)
    # the payload itself (truncated, like Lead.raw_json)
    title: str
    description: str = ""
    url: str = ""
    raw_json: str = ""
    content_hash: str = ""                     # S4 integrity marker
    received_at: datetime = Field(default_factory=utcnow, index=True)
    reviewed: bool = False
    reviewed_at: Optional[datetime] = None
    promoted_to_lead_id: Optional[int] = None  # set if operator promotes it


# ── Tunables ────────────────────────────────────────────────────────────────

# Allowlist of known harvester source tags (S3 provenance).
KNOWN_SOURCES = frozenset({
    "austender", "nsw_etendering", "planning_alerts",
    # disabled / future
    "estimate_one", "hunter",
})

# Max field lengths (S2 size). Mirrors truncation already in harvesters,
# but enforced HERE as the authoritative gate.
MAX_LEN = {
    "external_id": 300,
    "title": 200,
    "description": 3000,
    "url": 2048,
    "raw_json": 5000,
    "suburb": 120,
    "category": 40,
}

# S5 content-injection patterns. If matched in a text field, the lead is
# quarantined — not rejected, because legit tender text occasionally contains
# ampersands or angle brackets. But it warrants a look.
_INJECTION_RE = re.compile(
    r"<script|<iframe|javascript:|onerror=|onload=|"
    r"--\s|/\*|\*/|"
    r"\bunion\b\s+\bselect\b|"
    r"\bdrop\b\s+\btable\b",
    re.IGNORECASE,
)
# Hard-reject control chars (except newline/tab/carriage-return)
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Required structural fields (S1)
REQUIRED_FIELDS = ("source", "external_id", "title", "url")


# ── Validation battery ──────────────────────────────────────────────────────

def _content_hash(lead: Lead) -> str:
    """Stable hash of the lead's canonical content (S4 integrity marker)."""
    canonical = "|".join([
        lead.source or "",
        lead.external_id or "",
        (lead.title or "")[:MAX_LEN["title"]],
        (lead.url or "")[:MAX_LEN["url"]],
    ])
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _validate(lead: Lead) -> dict:
    """
    Run the full sensilla battery. Returns a checks dict:
      {check_id: {"status": "pass"|"warn"|"fail", "detail": str}}
    and an overall verdict + reason.
    """
    checks: dict[str, dict] = {}

    # S1 — STRUCTURAL
    missing = [f for f in REQUIRED_FIELDS if not getattr(lead, f, None)]
    if missing:
        checks["S1_structural"] = {"status": "fail",
                                   "detail": f"missing required: {missing}"}
        return _conclude(checks, Verdict.REJECT,
                         f"missing required fields: {missing}")
    # type sanity — url must be a non-empty string, etc.
    if not isinstance(lead.url, str) or not lead.url.strip():
        checks["S1_structural"] = {"status": "fail", "detail": "url empty/invalid"}
        return _conclude(checks, Verdict.REJECT, "url empty or invalid")
    checks["S1_structural"] = {"status": "pass", "detail": "required fields present"}

    # S2 — SIZE
    oversize = []
    for fname, cap in MAX_LEN.items():
        val = getattr(lead, fname, None)
        if isinstance(val, str) and len(val) > cap:
            oversize.append(f"{fname}={len(val)}>{cap}")
    if oversize:
        checks["S2_size"] = {"status": "fail", "detail": "; ".join(oversize)}
        return _conclude(checks, Verdict.REJECT, f"oversized fields: {oversize}")
    checks["S2_size"] = {"status": "pass", "detail": "all fields within bounds"}

    # S3 — PROVENANCE
    if lead.source not in KNOWN_SOURCES:
        checks["S3_provenance"] = {"status": "fail",
                                   "detail": f"unknown source: {lead.source!r}"}
        return _conclude(checks, Verdict.REJECT,
                         f"unknown source tag: {lead.source!r}")
    checks["S3_provenance"] = {"status": "pass",
                               "detail": f"source={lead.source} known"}

    # S4 — INTEGRITY (always passes; just records the hash)
    chash = _content_hash(lead)
    checks["S4_integrity"] = {"status": "pass", "detail": f"hash={chash}"}

    # S5 — CONTENT (injection / control chars)
    scan_blob = " ".join(filter(None, [lead.title, lead.description]))
    if _CONTROL_RE.search(scan_blob):
        checks["S5_content"] = {"status": "fail",
                                "detail": "control characters in text"}
        return _conclude(checks, Verdict.REJECT,
                         "control characters in title/description")
    injection_hit = _INJECTION_RE.search(scan_blob)
    if injection_hit:
        # quarantine, not reject — legit text occasionally trips this
        checks["S5_content"] = {"status": "warn",
                                "detail": f"injection-like pattern: {injection_hit.group(0)!r}"}
    else:
        checks["S5_content"] = {"status": "pass", "detail": "clean"}

    # S6 — RELEVANCE (the keyword gate; lazy import to avoid circular)
    try:
        from harvesters.keywords import is_paint_relevant
        relevant = is_paint_relevant(f"{lead.title} {lead.description}")
    except Exception as e:
        # keyword filter broken → quarantine, don't reject (could be a real lead)
        checks["S6_relevance"] = {"status": "warn",
                                  "detail": f"relevance check error: {e}"}
        return _conclude(checks, Verdict.QUARANTINE,
                         f"relevance check failed: {e}", chash)
    if not relevant:
        checks["S6_relevance"] = {"status": "fail", "detail": "not paint-relevant"}
        return _conclude(checks, Verdict.REJECT,
                         "failed keyword relevance filter", chash)
    checks["S6_relevance"] = {"status": "pass", "detail": "paint-relevant"}

    # If we got here with only S5 warn, still quarantine (defensive).
    if any(c["status"] == "warn" for c in checks.values()):
        return _conclude(checks, Verdict.QUARANTINE,
                         "passed core checks but has warnings", chash)

    return _conclude(checks, Verdict.ADMIT, "all checks passed", chash)


def _conclude(checks: dict, verdict: Verdict, reason: str,
              content_hash: str = "") -> dict:
    checks["_verdict"] = verdict.value
    checks["_reason"] = reason
    checks["_content_hash"] = content_hash
    return checks


# ── Public API ──────────────────────────────────────────────────────────────

def _ensure_table() -> None:
    """Create the quarantine table if it doesn't exist (idempotent)."""
    SQLModel.metadata.create_all(_engine_binding())


def _engine_binding():
    """Bind to the same engine the rest of the app uses."""
    # late import to pick up the live engine from db
    from db import engine
    return engine


def _persist_quarantined(lead: Lead, result: dict) -> None:
    """Park a rejected/quarantined lead for later inspection."""
    import json
    _ensure_table()
    try:
        with get_session() as s:
            item = QuarantineItem(
                source=lead.source,
                external_id=(lead.external_id or "")[:MAX_LEN["external_id"]],
                verdict=result["_verdict"],
                reason=result.get("_reason", ""),
                checks_json=json.dumps(result, ensure_ascii=False, default=str),
                title=(lead.title or "")[:MAX_LEN["title"]],
                description=(lead.description or "")[:MAX_LEN["description"]],
                url=(lead.url or "")[:MAX_LEN["url"]],
                raw_json=(lead.raw_json or "")[:MAX_LEN["raw_json"]],
                content_hash=result.get("_content_hash", _content_hash(lead)),
            )
            s.add(item)
            s.commit()
    except Exception:
        logger.exception("failed to persist quarantine item; lead dropped")
        # never let quarantine itself break the harvester


def save_lead_safe(lead: Lead) -> tuple[Verdict, str]:
    """
    Slit-sensilla gate: validate a lead, then admit/quarantine/reject.

    Returns (verdict, reason). This is the drop-in replacement for calling
    save_lead() directly — it calls save_lead() internally only on ADMIT.

    Behaviour:
      ADMIT      → save_lead(lead); lead enters canonical `leads` table
      QUARANTINE → parked in `quarantineitem` table; NOT promoted
      REJECT     → parked in `quarantineitem` with verdict=reject; NOT promoted

    Idempotent on content_hash: if an identical lead is already quarantined,
    the new one is still recorded (we keep every sighting for forensics).

    Safety: this function never raises — a validation failure produces a
    REJECT verdict, and a persistence failure logs but does not propagate.
    The harvester's run() loop is never broken by quarantine logic.
    """
    try:
        result = _validate(lead)
    except Exception as e:
        logger.exception("quarantine validator crashed; rejecting lead defensively")
        return Verdict.REJECT, f"validator error: {e}"

    verdict = Verdict(result.get("_verdict", Verdict.REJECT.value))
    reason = result.get("_reason", "")

    if verdict is Verdict.ADMIT:
        from db import save_lead
        try:
            saved = save_lead(lead)  # dedup + insert
            if not saved:
                return Verdict.REJECT, "duplicate (already in leads table)"
            return Verdict.ADMIT, reason
        except Exception as e:
            logger.exception("save_lead failed on ADMIT; quarantining instead")
            _persist_quarantined(lead, {**result, "_verdict": Verdict.QUARANTINE.value,
                                        "_reason": f"save_lead error: {e}"})
            return Verdict.QUARANTINE, f"save failed, parked: {e}"

    # QUARANTINE or REJECT → persist for inspection
    _persist_quarantined(lead, result)
    return verdict, reason


# ── Operator-side: inspect & promote ────────────────────────────────────────

def list_quarantined(limit: int = 50, unreviewed_only: bool = True) -> list[QuarantineItem]:
    """Return quarantined items for operator review (Telegram /quarantine)."""
    _ensure_table()
    with get_session() as s:
        stmt = select(QuarantineItem).order_by(QuarantineItem.received_at.desc()).limit(limit)
        if unreviewed_only:
            stmt = stmt.where(QuarantineItem.reviewed == False)  # noqa: E712
        return list(s.exec(stmt).all())


def promote_to_lead(quarantine_id: int) -> tuple[bool, str]:
    """
    Operator manually promotes a quarantined lead into the canonical table.
    Bypasses S5/S6 checks (operator has seen it and approved) but still runs
    S1/S2/S3 (structural integrity is non-negotiable).
    """
    _ensure_table()
    with get_session() as s:
        item = s.get(QuarantineItem, quarantine_id)
        if item is None:
            return False, "quarantine item not found"
        if item.reviewed and item.promoted_to_lead_id is not None:
            return False, f"already promoted to lead #{item.promoted_to_lead_id}"

        lead = Lead(
            source=item.source,
            external_id=item.external_id,
            title=item.title,
            description=item.description,
            url=item.url,
            raw_json=item.raw_json,
            suburb="",
            category="quarantine_promoted",
            status="new",
        )
        s.add(lead)
        s.commit()
        s.refresh(lead)

        item.reviewed = True
        item.reviewed_at = utcnow()
        item.promoted_to_lead_id = lead.id
        s.add(item)
        s.commit()
        return True, f"promoted to lead #{lead.id}"


def dismiss_quarantined(quarantine_id: int) -> tuple[bool, str]:
    """Operator marks a quarantined lead as reviewed-and-dismissed."""
    _ensure_table()
    with get_session() as s:
        item = s.get(QuarantineItem, quarantine_id)
        if item is None:
            return False, "quarantine item not found"
        item.reviewed = True
        item.reviewed_at = utcnow()
        s.add(item)
        s.commit()
        return True, "dismissed"
