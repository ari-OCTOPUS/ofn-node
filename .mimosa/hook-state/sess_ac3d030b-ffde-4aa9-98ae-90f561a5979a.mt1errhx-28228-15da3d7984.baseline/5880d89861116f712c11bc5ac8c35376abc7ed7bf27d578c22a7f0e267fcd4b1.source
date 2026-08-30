"""
Data models -- Brushline
All entities from MVP s4. Stored in SQLite (database.py).
PII policy: phone/email ONLY in leads table, hash-ref in audit (INV-2).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


# -- Enums --------------------------------------------------------------------

class DraftType(str, Enum):
    SPEED_TO_LEAD = "speed_to_lead"
    FOLLOWUP = "followup"
    REVIEW_RESPONSE = "review_response"
    SUBURB_PAGE = "suburb_page"
    CAPTION = "caption"
    GBP_POST = "gbp_post"
    BLOG_OUTLINE = "blog_outline"
    CAPITAL_WORKS_ASSESSMENT = "capital_works_assessment"


class GateStatus(str, Enum):
    PASS = "pass"
    SOFT_FLAG = "soft_flag"
    HARD_BLOCK = "hard_block"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"       # content modified by operator -> may REGATE (KB-05)


class ApprovalPriority(str, Enum):
    """KB-05 s3 -- priority drives display order and SLA deadline."""
    CRITICAL = "critical"   # speed-to-lead, SLA 15 min
    HIGH = "high"           # negative review response, SLA 2h
    MEDIUM = "medium"       # quote follow-up, SLA same day
    LOW = "low"             # social/content, SLA 24-48h


class SyncStatus(str, Enum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"


class ConsentMethod(str, Enum):
    EXPRESS = "express"
    INFERRED_BUSINESS = "inferred_business_relationship"  # Spam Act s.7


class AuditEventType(str, Enum):
    ENQUIRY_RECEIVED = "ENQUIRY_RECEIVED"
    DRAFT_CREATED = "DRAFT_CREATED"
    GATE_CHECK = "GATE_CHECK"
    APPROVAL_SUBMITTED = "APPROVAL_SUBMITTED"
    APPROVAL_DECISION = "APPROVAL_DECISION"
    PUBLISH = "PUBLISH"
    SYNC = "SYNC"
    COST_EVENT = "COST_EVENT"
    KILL_SWITCH_ACTIVATED = "KILL_SWITCH_ACTIVATED"
    KILL_SWITCH_DEACTIVATED = "KILL_SWITCH_DEACTIVATED"
    SPEND_CAP_EXCEEDED = "SPEND_CAP_EXCEEDED"
    CONTENT_TASK_KICKOFF = "CONTENT_TASK_KICKOFF"
    APPROVAL_SLA_EXPIRED = "APPROVAL_SLA_EXPIRED"
    APPROVAL_EDIT_TRIVIAL = "APPROVAL_EDIT_TRIVIAL"
    APPROVAL_EDIT_REGATE = "APPROVAL_EDIT_REGATE"
    APPROVAL_REQUEUED_AFTER_REGATE = "APPROVAL_REQUEUED_AFTER_REGATE"
    UNAUTHORISED_ACCESS = "UNAUTHORISED_ACCESS"


# -- Entities (MVP s4) ----------------------------------------------------------

@dataclass
class Lead:
    """
    Core lead entity. PII fields: name, phone, email (INV-2).
    Only sync_* tools may push PII to ServiceM8/Tradify, after consent.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    phone: str = ""                           # PII -- never in audit payload
    email: Optional[str] = None              # PII -- only with express consent
    suburb: str = ""
    service_type: str = ""
    source_channel: str = ""                 # e.g. "gbp", "referral", "ads"
    consent_status: Optional[str] = None
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConsentRecord:
    """APP7 / Spam Act consent evidence."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    lead_id: str = ""
    method: ConsentMethod = ConsentMethod.EXPRESS
    timestamp: datetime = field(default_factory=datetime.utcnow)
    evidence: str = ""   # "web form submission", "existing client since 2025-01"


@dataclass
class Draft:
    """
    All content is draft-only until approved (INV-1).
    No auto-publish/send/sync from this model.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    lead_id: Optional[str] = None
    draft_type: DraftType = DraftType.SPEED_TO_LEAD
    content: str = ""
    agent_id: str = ""                        # e.g. "C_content"
    model_used: str = ""                      # e.g. "claude-haiku-4-5-20251001"
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GateResult:
    """
    Output of Constitution Gate (KB-07).
    HARD_BLOCK means draft cannot be approved until rewritten.
    SOFT_FLAG is a warning -- operator decides.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    draft_id: str = ""
    status: GateStatus = GateStatus.PASS
    acl_ok: bool = True           # no false/unsubstantiated claims (ACL s29)
    spam_consent_ok: bool = True  # consent verified (Spam Act)
    sender_id_ok: bool = True     # ABN + unsubscribe link present
    privacy_ok: bool = True       # no PII leak
    sovereignty_ok: bool = True   # sensitive data not leaving AU (INV-2)
    flags: list = field(default_factory=list)  # list of flag strings
    round_num: int = 1            # gate retry round; max = GATE_MAX_ROUNDS (3)
    checked_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ApprovalAction:
    """
    Human approval decision (KB-05).
    Every draft must have an APPROVED ApprovalAction before any external action.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    draft_id: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    operator_chat_id: Optional[int] = None   # Telegram chat ID of approver
    edited_content: Optional[str] = None     # filled if EDITED (triggers REGATE)
    reason: Optional[str] = None             # required for REJECTED
    acted_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    priority: ApprovalPriority = ApprovalPriority.LOW   # KB-05 s3, set at submit()
    sla_deadline: Optional[datetime] = None             # KB-05 s3
    expired: bool = False                               # SLA breached -> escalated, NOT auto-approved (INV-1)
    regate_status: Optional[str] = None      # GateStatus value if EDIT triggered a REGATE
    regate_draft_id: Optional[str] = None    # new Draft id created for the edited content, if regated


@dataclass
class AuditEntry:
    """
    Hash-chained immutable audit entry (KB-06).
    payload: JSON string, NO raw PII (use hash refs for PII fields).
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    prev_hash: str = ""          # hash of previous entry (genesis = "0"*64)
    entry_hash: str = ""         # SHA-256 of this entry's canonical content
    event_type: str = ""         # AuditEventType value
    entity_id: str = ""          # ID of the audited entity
    payload: str = ""            # JSON -- no raw PII
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SyncJob:
    """
    Record of a sync to ServiceM8 or Tradify (KB-09).
    Only approved leads with consent are synced.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    lead_id: str = ""
    target_system: str = ""              # "servicem8" or "tradify"
    status: SyncStatus = SyncStatus.PENDING
    external_client_id: Optional[str] = None
    external_job_id: Optional[str] = None
    synced_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CostEvent:
    """
    Every LLM / search / image API call logged here (INV-3 spend cap).
    Denominated in both USD (billed) and AUD (capped).
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""         # "llm_call", "search_api", "image_api"
    agent_id: str = ""
    model: str = ""
    cost_usd: float = 0.0
    cost_aud: float = 0.0        # = cost_usd * FX_AUD_USD
    tokens_in: int = 0
    tokens_out: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
