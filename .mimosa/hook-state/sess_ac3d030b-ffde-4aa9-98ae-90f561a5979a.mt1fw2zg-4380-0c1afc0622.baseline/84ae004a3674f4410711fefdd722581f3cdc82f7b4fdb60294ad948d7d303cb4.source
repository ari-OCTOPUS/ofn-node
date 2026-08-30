"""
control_plane/contracts.py — قراردادهای استانداردِ black-boxها (Phase 3).

هر ماژول reasoning داخلی‌اش را افشا نمی‌کند، ولی از بیرون با این شکل‌ها
observable/governable می‌شود. این‌ها فقط «شکلِ داده» هستند (dataclass)؛
هیچ رفتاری این‌جا نیست — enforcement در فازهای بعد و flag-gated.

هر schema:  required فیلدها بدونِ default،  optional با default.
failure mode مشترک: producer ناقص → فیلد "UNKNOWN" بماند، هرگز silent-pass نشود.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any

SCHEMA_VERSION = 1

_UNKNOWN = "UNKNOWN"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass
class EventEnvelope:
    """رویدادِ استاندارد — سازگار با brain/events (dashboard_events)."""
    source: str                       # subsystem id (registry)
    event_name: str                   # e.g. task.completed
    summary: str
    timestamp: str = field(default_factory=_now)
    trace_id: str = ""
    agent_id: str = ""
    status: str = "info"              # ok|error|blocked|pending|info|retry
    approval_state: str = "not_required"
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict: return asdict(self)


@dataclass
class StateSnapshot:
    """عکسِ لحظه‌ایِ وضعیتِ یک subsystem (فقط خواندنی)."""
    subsystem_id: str
    state: dict[str, Any]
    timestamp: str = field(default_factory=_now)
    health: str = _UNKNOWN            # OK|WARN|FAIL|UNKNOWN
    source_files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict: return asdict(self)


@dataclass
class ActionEnvelope:
    """نیتِ اجرای یک action — بینِ نیتِ ماژول و اجرای واقعی می‌نشیند."""
    subsystem_id: str
    action_type: str                  # کلیدِ policy.ACTION_POLICY
    description: str
    action_id: str = ""
    timestamp: str = field(default_factory=_now)
    params: dict[str, Any] = field(default_factory=dict)
    risk_tier: str = _UNKNOWN         # low|medium|high|UNKNOWN
    trace_id: str = ""

    def to_dict(self) -> dict: return asdict(self)


@dataclass
class ApprovalRequest:
    """درخواستِ تأییدِ مالک برای یک action high-risk."""
    action: dict[str, Any]            # ActionEnvelope.to_dict()
    requested_by: str
    request_id: str = ""
    timestamp: str = field(default_factory=_now)
    status: str = "pending"           # pending|approved|rejected|expired
    decided_at: str = ""
    decided_by: str = ""
    note: str = ""

    def to_dict(self) -> dict: return asdict(self)


@dataclass
class PolicyResult:
    """خروجیِ ارزیابیِ policy ladder برای یک action."""
    action_type: str
    level: int                        # 0..5
    level_name: str
    requires_approval: bool
    needs_review: bool = False        # ambiguous → true (هرگز silent-pass)
    reason: str = ""
    evaluated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict: return asdict(self)


@dataclass
class HealthSignal:
    subsystem_id: str
    status: str                       # OK|WARN|FAIL|UNKNOWN
    detail: str = ""
    heartbeat_age_s: float | None = None
    timestamp: str = field(default_factory=_now)

    def to_dict(self) -> dict: return asdict(self)


@dataclass
class TraceRecord:
    """زنجیره‌ی رویدادهای یک trace (برای audit/replay)."""
    trace_id: str
    subsystem_id: str = ""
    run_id: str = ""
    events: list[dict] = field(default_factory=list)
    started_at: str = ""
    ended_at: str = ""

    def to_dict(self) -> dict: return asdict(self)


@dataclass
class ReplayRecord:
    """ارجاعِ بازپخش: با چه ورودی/فرمانی می‌شود تصمیم را بازتولید کرد."""
    trace_id: str
    command: str = ""                 # e.g. "python -m ... --seed 7"
    inputs_ref: str = ""              # مسیرِ snapshot ورودی
    deterministic: bool | None = None # None = UNKNOWN
    replay_id: str = ""
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict: return asdict(self)


@dataclass
class RiskAssessment:
    subject: str                      # action/subsystem/channel id
    tier: str                         # low|medium|high
    factors: list[str] = field(default_factory=list)
    assessed_at: str = field(default_factory=_now)

    def to_dict(self) -> dict: return asdict(self)


@dataclass
class CapabilityDeclaration:
    """اعلامِ توانایی‌های یک black box — بدونِ افشای داخل."""
    subsystem_id: str
    capabilities: list[str] = field(default_factory=list)
    accepted_events: list[str] = field(default_factory=list)
    emitted_events: list[str] = field(default_factory=list)
    declared_at: str = field(default_factory=_now)

    def to_dict(self) -> dict: return asdict(self)


@dataclass
class KillSwitchCommand:
    """فرمانِ pause/resume/stop — در v1 هرگز execute نمی‌شود (مسیرِ live غایب)."""
    target: str                       # e.g. "daemon"
    kind: str                         # pause|resume|stop
    issued_by: str
    confirmed: bool = False           # confirmation سخت لازم است
    executed: bool = False            # v1: همیشه False می‌ماند
    timestamp: str = field(default_factory=_now)

    def to_dict(self) -> dict: return asdict(self)


@dataclass
class HumanOverrideRecord:
    """ثبتِ هر جایی که مالک دستی مداخله کرد — برای evidence trail."""
    target: str
    what: str
    why: str
    owner: str = "Armin"
    override_id: str = ""
    timestamp: str = field(default_factory=_now)

    def to_dict(self) -> dict: return asdict(self)
