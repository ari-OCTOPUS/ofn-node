"""governance.py — چرخهٔ propose→decide با نردبانِ ریسک و گیتِ RED.

قواعدِ سختِ سندِ reconciliation:
  • نردبانِ چهارطبقه: GREEN < YELLOW < ORANGE < RED.
  • SahebZiman (نقشِ owner) تنها تأییدکنندهٔ RED است.
  • NC-3: هیچ نقشِ ایجنتی (از جمله OCTOPUS) اختیارِ approve/reject/defer ندارد.
  • ADMINِ انسانی فقط تا سقفِ اعطاشده (پیش‌فرض YELLOW) تصمیم می‌گیرد؛ هرگز RED.
  • هر تصمیم یک ZIM-DEC-id می‌گیرد و در دفترِ evt.v1 ثبت می‌شود (زنجیرهٔ هش).

fail-closed: نقش/ریسکِ ناشناخته → رد. تلاشِ مسدودشده در دفتر لاگ می‌شود ولی
وضعیتِ proposal را عوض نمی‌کند. این ماژول هیچ اکشنِ بیرونی (ارسال/انتشار) ندارد.
"""
from __future__ import annotations

from typing import Optional

RISK_LADDER = ("GREEN", "YELLOW", "ORANGE", "RED")
# نقش‌هایی که هرگز تصمیم نمی‌گیرند (NC-3). همهٔ ایجنت‌ها اینجایند.
AGENT_ROLES = frozenset({"agent", "octopus", "octopus_agent", "zimanleg"})
DEFAULT_ADMIN_CEILING = "YELLOW"
_TERMINAL = {"approve": "approved", "reject": "rejected", "defer": "deferred"}


class GovernanceError(Exception):
    """ورودیِ نامعتبر یا نقضِ چرخهٔ عمر (نه نقضِ اختیار — آن PermissionError است)."""


def risk_rank(risk: str) -> int:
    """رتبهٔ شدت. ریسکِ ناشناخته = شدیدترین (fail-closed)."""
    try:
        return RISK_LADDER.index((risk or "").upper())
    except ValueError:
        return len(RISK_LADDER)


def can_decide(role: str, risk: str, admin_ceiling: str = DEFAULT_ADMIN_CEILING) -> bool:
    """آیا این نقش می‌تواند روی proposalی با این ریسک تصمیم بگیرد؟ fail-closed."""
    role = (role or "").strip().lower()
    if role in AGENT_ROLES:
        return False                       # NC-3 — هیچ ایجنتی approve نمی‌کند
    if role == "owner":                    # SahebZiman — همه، از جمله RED
        return True
    if role == "admin":
        if (risk or "").upper() == "RED":  # RED فقط owner
            return False
        return risk_rank(risk) <= risk_rank(admin_ceiling)
    return False                           # viewer/ناشناخته → رد


# تصمیمِ صریح لازم است برای این طبقات.
_APPROVAL_TIERS = ("ORANGE", "RED")
# طبقاتی که یک proposal می‌سازند و باید با شناسهٔ انسان‌خوانِ ZIM-DEC قابلِ‌اقدام
# باشند (YELLOW هم propose-only است ولی مالک/ادمین می‌تواند تصمیم بگیرد → ref لازم
# دارد تا در /queue با ZIM-DEC نشان داده و approve شود). GREEN خودکار است، ref ندارد.
_REF_TIERS = ("YELLOW", "ORANGE", "RED")


def propose(store, kind: str, project: str, detail: str, risk: str,
            proposed_by: str) -> dict:
    """یک proposalِ pending می‌سازد و رویدادِ propose را در دفتر ثبت می‌کند.

    برای طبقاتِ نیازمندِ تأیید (ORANGE/RED) یک شناسهٔ انسان‌خوانِ ZIM-DEC رزرو
    می‌شود (ref) تا مالک با `/approve ZIM-DEC-…` تأیید کند. این شناسه در همان
    رویدادِ propose ثبت می‌شود تا next_decision_id دوباره آن را ندهد.
    """
    risk = (risk or "").upper()
    if risk not in RISK_LADDER:
        raise GovernanceError(f"invalid risk tier: {risk!r}")
    ref = store.next_decision_id() if risk in _REF_TIERS else None
    evt = store.append_event(kind=f"propose:{kind}", project=project,
                             detail=detail, actor=proposed_by, decision_id=ref)
    p = {
        "proposal_id": evt["event_id"], "kind": kind, "project": project,
        "detail": detail, "risk": risk, "proposed_by": proposed_by,
        "status": "pending", "created_at": evt["ts"],
        "decision_id": None, "decided_by": None, "decided_at": None, "ref": ref,
    }
    store.put_proposal(p)
    return p


def decide(store, proposal_id: str, outcome: str, actor_id: str,
           actor_role: str, admin_ceiling: str = DEFAULT_ADMIN_CEILING) -> dict:
    """approve/reject/defer یک proposal با گیتِ اختیار. یک ZIM-DEC-id برمی‌گرداند.

    اگر نقش اجازه نداشته باشد → PermissionError و ثبتِ تلاشِ مسدودشده در دفتر؛
    وضعیتِ proposal تغییر نمی‌کند (fail-closed).
    """
    outcome = (outcome or "").strip().lower()
    if outcome not in _TERMINAL:
        raise GovernanceError(f"invalid outcome: {outcome!r}")
    p = store.get_proposal(proposal_id)
    if not p:
        raise GovernanceError(f"unknown proposal: {proposal_id}")
    if p["status"] != "pending":
        raise GovernanceError(f"proposal already {p['status']}")

    if not can_decide(actor_role, p["risk"], admin_ceiling):
        store.append_event(
            kind="decide_denied", project=p["project"],
            detail=f"{actor_id} (role={actor_role}) blocked from {outcome} on "
                   f"{p['risk']} proposal {proposal_id}",
            actor=actor_id)
        raise PermissionError(
            f"role {actor_role!r} may not {outcome} a {p['risk']} proposal")

    # شناسهٔ رزروشده در زمانِ propose را دوباره استفاده کن؛ وگرنه تازه بگیر.
    decision_id = p.get("ref") or store.next_decision_id()
    evt = store.append_event(
        kind=f"decide:{outcome}", project=p["project"],
        detail=f"{outcome} {proposal_id}: {p['detail']}",
        actor=actor_id, decision_id=decision_id)
    p.update(status=_TERMINAL[outcome], decision_id=decision_id,
             decided_by=actor_id, decided_at=evt["ts"])
    store.put_proposal(p)
    return {
        "decision_id": decision_id, "proposal_id": proposal_id,
        "outcome": outcome, "status": _TERMINAL[outcome],
        "decided_by": actor_id, "risk": p["risk"], "ledger_seq": evt["seq"],
    }


def decide_by_ref(store, ref: str, outcome: str, actor_id: str,
                  actor_role: str, admin_ceiling: str = DEFAULT_ADMIN_CEILING) -> dict:
    """مثلِ decide اما با شناسهٔ نمایش‌دادهٔ /queue.

    handle می‌تواند ZIM-DEC ref (برای YELLOW/ORANGE/RED) یا proposal_id (ULID) باشد؛
    هر دو را می‌پذیرد تا هر آیتمی که در صف نشان داده شده واقعاً قابلِ‌اقدام باشد.
    """
    p = store.get_proposal_by_ref(ref) or store.get_proposal(ref)
    if not p:
        raise GovernanceError(f"unknown decision ref: {ref}")
    return decide(store, p["proposal_id"], outcome, actor_id, actor_role,
                  admin_ceiling)


def pending_summary(store, project: Optional[str] = None) -> list[dict]:
    """فهرستِ proposalهای در انتظار برای دایجستِ /queue (فقط-خواندنی)."""
    out = []
    for p in store.list_proposals(status="pending"):
        if project and p.get("project") != project:
            continue
        out.append({"ref": p.get("ref") or p.get("proposal_id"),
                    "risk": p.get("risk"), "kind": p.get("kind"),
                    "detail": (p.get("detail") or "")[:80],
                    "proposed_by": p.get("proposed_by")})
    return out
