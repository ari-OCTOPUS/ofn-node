"""TaskEnvelope v1 — the one place a run is born.

The blueprint's hardest-won rule lives here: the arm does not mint its own
run_id. `create_envelope()` is the trust boundary's factory; it takes the
randomness as an argument (`rand`) precisely so the kernel stays pure and
the boundary (adapters/service layer, which owns os.urandom) stays the only
minter. A run_id is an identity, and identity collisions were a real bug in
the sister project (two different contradictions both called C-008 on
2026-08-15) — so the format is strict and the store rejects strangers.

Kernel purity: no clock, no I/O, no randomness. Everything arrives as an
argument; validation fails closed via FailClosedError.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping, Tuple

from .errors import FailClosedError
from .events import is_forbidden_effect_name
from .routing import Rung

RISK_TIERS = ("GREEN", "YELLOW", "RED")
AUTHORITY_LEVELS = ("A0", "A1", "A2", "A3")

RUN_ID_RE = re.compile(r"^run-[0-9]{10,12}-[a-z0-9]{10,}$")
SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
DEADLINE_ISO_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"
)
# Capturing form of the same grammar. The loose regex is the shape gate;
# this one plus the civil-date check is the calendar gate. datetime is
# not imported: the kernel purity wall forbids it (clock lives on the
# type). Integer civil→unix is deterministic and has no now().
_DEADLINE_PARSE_RE = re.compile(
    r"^(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})T"
    r"(?P<h>\d{2}):(?P<min>\d{2}):(?P<s>\d{2})"
    r"(?:\.\d+)?"
    r"(?:Z|(?P<sign>[+-])(?P<oh>\d{2}):(?P<om>\d{2}))$"
)
_MONTH_DAYS = (0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

# Deliberately conservative: external authority rides the deepest rung, so
# it inherits the smallest cap (DEFAULT_CAPS[REMOTE_DEEP] == 5). If this
# mapping ever loosens, that is a policy change and belongs in a review.
_AUTHORITY_TO_RUNG: Mapping[str, Rung] = {
    "A0": Rung.RULES,
    "A1": Rung.LOCAL,
    "A2": Rung.REMOTE,
    "A3": Rung.REMOTE_DEEP,
}


def rung_for_authority(level: str) -> Rung:
    try:
        return _AUTHORITY_TO_RUNG[level]
    except KeyError:
        raise FailClosedError(f"unknown authority level: {level!r}") from None


def require_epoch_s(value: object, name: str = "now_epoch_s") -> int:
    """Exact int, not bool/float/str. ``int("178")`` and ``int(True)``
    are not a clock the boundary supplied — they are coercions."""
    if type(value) is not int:
        raise FailClosedError(f"{name} must be int: {value!r}")
    if value < 0:
        raise FailClosedError(f"{name} must be non-negative: {value!r}")
    return value


def is_sealed_tool_name(name: object) -> bool:
    """Exact forbidden names plus case-fold and hyphen aliases.

    A second witness at the envelope so ``Send_Authorized`` /
    ``send-authorized`` cannot ride an allowlist. UNKNOWN names stay
    unknown — this does not invent a send.
    """
    if not isinstance(name, str):
        return False
    if is_forbidden_effect_name(name):
        return True
    folded = name.strip().lower().replace("-", "_")
    return is_forbidden_effect_name(folded)


def _is_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _days_in_month(year: int, month: int) -> int:
    if month == 2 and _is_leap(year):
        return 29
    return _MONTH_DAYS[month]


def _days_from_civil(year: int, month: int, day: int) -> int:
    """Days since 1970-01-01 (Hinnant civil calendar). No clock."""
    y = year - (1 if month <= 2 else 0)
    era = y // 400 if y >= 0 else (y - 399) // 400
    yoe = y - era * 400
    doy = (153 * (month + (-3 if month > 2 else 9)) + 2) // 5 + day - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    return era * 146097 + doe - 719468


def deadline_epoch_s(deadline_iso: str) -> int:
    """Parse a timezone-aware ISO-8601 deadline to unix seconds.

    Regex-shaped but impossible dates (month 13, day 31 in April,
    hour 99) fail closed. Fractional seconds are floored, matching
    ``int(datetime.timestamp())`` in the store adapter. Naive stamps
    are not accepted — the regex already requires Z or an offset.
    """
    if not isinstance(deadline_iso, str):
        raise FailClosedError(f"deadline_iso not a string: {deadline_iso!r}")
    if not DEADLINE_ISO_RE.match(deadline_iso):
        raise FailClosedError(f"deadline_iso not ISO-8601: {deadline_iso!r}")
    m = _DEADLINE_PARSE_RE.match(deadline_iso)
    if m is None:
        raise FailClosedError(f"deadline_iso not parseable: {deadline_iso!r}")
    year = int(m.group("y"))
    month = int(m.group("m"))
    day = int(m.group("d"))
    hour = int(m.group("h"))
    minute = int(m.group("min"))
    second = int(m.group("s"))
    if month < 1 or month > 12:
        raise FailClosedError(f"deadline_iso month out of range: {deadline_iso!r}")
    if day < 1 or day > _days_in_month(year, month):
        raise FailClosedError(f"deadline_iso day out of range: {deadline_iso!r}")
    if hour > 23 or minute > 59 or second > 59:
        raise FailClosedError(f"deadline_iso clock out of range: {deadline_iso!r}")
    if m.group("sign") is None:
        offset_s = 0
    else:
        oh = int(m.group("oh"))
        om = int(m.group("om"))
        if oh > 14 or om > 59:
            raise FailClosedError(
                f"deadline_iso offset out of range: {deadline_iso!r}")
        offset_s = oh * 3600 + om * 60
        if m.group("sign") == "-":
            offset_s = -offset_s
    return _days_from_civil(year, month, day) * 86400 + hour * 3600 + minute * 60 + second - offset_s


def deadline_still_open(deadline_iso: str, now_epoch_s: int) -> bool:
    """True only while ``now < deadline``. Equal means the window closed.

    No clock is read — both sides arrive as arguments. This is the
    factory-side witness of the store's append-time deadline gate.
    """
    now = require_epoch_s(now_epoch_s)
    return now < deadline_epoch_s(deadline_iso)


def mint_run_id(now_epoch_s: int, rand: str) -> str:
    """Format a run_id from boundary-supplied time and randomness.

    The kernel formats; it does not generate. `rand` must be at least ten
    lowercase hex/base32-ish characters — os.urandom(8).hex() at the call
    site is the intended shape.
    """
    now = require_epoch_s(now_epoch_s)
    if not isinstance(rand, str):
        raise FailClosedError(f"rand must be a string: {rand!r}")
    run_id = f"run-{now}-{rand}"
    if not RUN_ID_RE.match(run_id):
        raise FailClosedError(f"refusing malformed run_id: {run_id!r}")
    return run_id


@dataclass(frozen=True)
class TaskEnvelope:
    """The signed contract a run executes under.

    acceptance_criteria_hash is hashed BEFORE any output exists — the
    pre-registration rule (Aspect 6): a metric that can never go red is
    not a metric, and acceptance you write after the fact is not
    acceptance.
    """

    version: int
    run_id: str
    goal: str
    risk_tier: str
    authority_level: str
    idempotency_key: str
    acceptance_criteria_hash: str
    budget_tokens: int
    budget_aud_cents: int
    deadline_iso: str
    allowed_tools: Tuple[str, ...]
    parent_evidence: Tuple[str, ...]
    rollback_plan: str | None = None
    rollback_ref: str | None = None

    def __post_init__(self) -> None:
        if self.version != 1:
            raise FailClosedError(f"unsupported envelope version: {self.version!r}")
        if not RUN_ID_RE.match(self.run_id or ""):
            raise FailClosedError(f"run_id not minted at the boundary: {self.run_id!r}")
        if not (self.goal or "").strip():
            raise FailClosedError("goal is required")
        if self.risk_tier not in RISK_TIERS:
            raise FailClosedError(f"unknown risk tier: {self.risk_tier!r}")
        if self.authority_level not in AUTHORITY_LEVELS:
            raise FailClosedError(f"unknown authority level: {self.authority_level!r}")
        if not (self.idempotency_key or "").strip():
            raise FailClosedError("idempotency_key is required")
        if not SHA256_HEX_RE.match(self.acceptance_criteria_hash or ""):
            raise FailClosedError(
                "acceptance_criteria_hash must be a sha256 hex digest "
                "(hash it BEFORE the run, not after)"
            )
        for name, value in (("budget_tokens", self.budget_tokens),
                            ("budget_aud_cents", self.budget_aud_cents)):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise FailClosedError(f"{name} must be a non-negative int: {value!r}")
        # Calendar parse, not just the regex: 2026-13-40T99:99:99Z
        # matches the shape gate and must still fail closed.
        deadline_epoch_s(self.deadline_iso or "")
        for tool in self.allowed_tools:
            if not isinstance(tool, str) or not tool.strip():
                raise FailClosedError(f"allowed_tools entries must be names: {tool!r}")
            if is_sealed_tool_name(tool):
                raise FailClosedError(
                    f"allowed_tools cannot name a sealed effect: {tool!r}")
        for evidence_id in self.parent_evidence:
            if not isinstance(evidence_id, str) or not evidence_id.strip():
                raise FailClosedError(
                    f"parent_evidence entries must be ids: {evidence_id!r}")
        # The irreversible tier does not run without a way back — and the
        # way back must be a registered artifact, not a promise in prose.
        if self.authority_level == "A3":
            if not (self.rollback_plan or "").strip():
                raise FailClosedError(
                    "rollback_plan is required_for_external (authority A3)")
            if not (self.rollback_ref or "").strip():
                raise FailClosedError(
                    "rollback_ref is required_for_external (authority A3) — "
                    "an id of a registered rollback artifact, not prose")

    def tool_allowed(self, tool: str) -> bool:
        """Capability check. A sealed send/ready name is never a tool.

        An empty allowlist is unrestricted for ordinary tools (the
        store still refuses sealed names). A non-empty list is a
        closed set — anything not named is refused.
        """
        if not isinstance(tool, str) or not tool.strip():
            raise FailClosedError(f"tool name required: {tool!r}")
        if is_sealed_tool_name(tool):
            return False
        if not self.allowed_tools:
            return True
        return tool in self.allowed_tools

    def rung(self) -> Rung:
        return rung_for_authority(self.authority_level)

    def may_spend(self, budget, now_epoch_s: int) -> bool:
        """Wiring to CallBudget — the envelope never bypasses the cap."""
        return budget.allows(self.rung(), now_epoch_s)

    def may_consume_tokens(self, already_consumed: int, request: int) -> bool:
        """Per-run token ceiling. Independent of the node-level quota —
        both must pass. ``budget_tokens == 0`` authorizes no spend
        (request 0 is a no-op and is allowed)."""
        for name, value in (("already_consumed", already_consumed),
                            ("request", request)):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise FailClosedError(
                    f"{name} must be a non-negative int: {value!r}")
        if self.budget_tokens == 0:
            return request == 0
        return already_consumed + request <= self.budget_tokens

    def deadline_open(self, now_epoch_s: int) -> bool:
        """Factory/store witness: equal-to-deadline is closed."""
        return deadline_still_open(self.deadline_iso, now_epoch_s)

    def may_consume_aud(self, already_consumed: int, request: int) -> bool:
        """Per-run money ceiling in cents. Same shape as tokens:
        ``budget_aud_cents == 0`` authorizes no spend. This is not
        ``send_authorized`` — a fitting spend still cannot leave the
        node without a later, scoped owner grant."""
        for name, value in (("already_consumed", already_consumed),
                            ("request", request)):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise FailClosedError(
                    f"{name} must be a non-negative int: {value!r}")
        if self.budget_aud_cents == 0:
            return request == 0
        return already_consumed + request <= self.budget_aud_cents


def create_envelope(
    *,
    goal: str,
    risk_tier: str,
    authority_level: str,
    idempotency_key: str,
    acceptance_criteria_hash: str,
    now_epoch_s: int,
    rand: str,
    deadline_iso: str,
    budget_tokens: int = 0,
    budget_aud_cents: int = 0,
    allowed_tools: Tuple[str, ...] = (),
    parent_evidence: Tuple[str, ...] = (),
    rollback_plan: str | None = None,
    rollback_ref: str | None = None,
) -> TaskEnvelope:
    """The boundary's only sanctioned constructor. Arms call this; they
    cannot inject a run_id because the parameter does not exist.

    A run cannot be born already expired: ``now_epoch_s >= deadline``
    fails closed here so the store's append-time gate is not the first
    witness. Ready ≠ authorized — this check never grants a send.
    """
    now = require_epoch_s(now_epoch_s)
    env = TaskEnvelope(
        version=1,
        run_id=mint_run_id(now, rand),
        goal=goal,
        risk_tier=risk_tier,
        authority_level=authority_level,
        idempotency_key=idempotency_key,
        acceptance_criteria_hash=acceptance_criteria_hash,
        budget_tokens=budget_tokens,
        budget_aud_cents=budget_aud_cents,
        deadline_iso=deadline_iso,
        allowed_tools=tuple(allowed_tools),
        parent_evidence=tuple(parent_evidence),
        rollback_plan=rollback_plan,
        rollback_ref=rollback_ref,
    )
    if not env.deadline_open(now):
        raise FailClosedError(
            f"deadline already closed at mint: now={now} >= {deadline_iso!r} "
            "(equal means the window is closed)")
    return env
