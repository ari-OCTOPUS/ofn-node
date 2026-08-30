"""تست‌های governance — چرخهٔ propose→decide، گیتِ RED و قاعدهٔ NC-3.

ادعاهای امنیتیِ حیاتی:
  • هیچ نقشِ ایجنتی (OCTOPUS/agent) نمی‌تواند تصمیم بگیرد — حتی GREEN.
  • RED فقط با نقشِ owner (SahebZiman).
  • ADMIN فقط تا سقفِ اعطاشده؛ هرگز RED.
  • تلاشِ مسدودشده وضعیتِ proposal را عوض نمی‌کند و در دفتر لاگ می‌شود.
"""
import pytest

from core.store import Store
from core.governance import (
    AGENT_ROLES,
    GovernanceError,
    can_decide,
    decide,
    propose,
)


def _store(tmp_path):
    return Store(tmp_path / "gov.db")


# ── can_decide (منطقِ خالصِ گیت) ─────────────────────────────────────────────

def test_agent_never_decides_any_tier():
    # همهٔ نقش‌های ایجنتی (NC-3) روی همهٔ طبقات باید مسدود باشند — نه فقط دو نمونه.
    for role in AGENT_ROLES:
        for tier in ("GREEN", "YELLOW", "ORANGE", "RED"):
            assert can_decide(role, tier) is False, (role, tier)


def test_owner_can_decide_all_including_red():
    for tier in ("GREEN", "YELLOW", "ORANGE", "RED"):
        assert can_decide("owner", tier) is True


def test_admin_ceiling_and_red_block():
    assert can_decide("admin", "YELLOW") is True             # سقفِ پیش‌فرض
    assert can_decide("admin", "ORANGE") is False            # بالاتر از سقف
    assert can_decide("admin", "ORANGE", admin_ceiling="ORANGE") is True
    assert can_decide("admin", "RED", admin_ceiling="ORANGE") is False  # RED فقط owner


def test_viewer_and_unknown_role_fail_closed():
    assert can_decide("viewer", "GREEN") is False
    assert can_decide("nobody", "GREEN") is False
    assert can_decide("", "GREEN") is False


# ── چرخهٔ کامل روی store ─────────────────────────────────────────────────────

def test_propose_creates_pending_and_ledger_event(tmp_path):
    s = _store(tmp_path)
    p = propose(s, "send_dm", "ziman", "DM batch to warm list", "RED", "octopus")
    assert p["status"] == "pending" and p["risk"] == "RED"
    assert s.get_proposal(p["proposal_id"])["status"] == "pending"
    assert s.verify_ledger()["ok"] is True
    assert len(s.ledger_tail()) == 1


def test_owner_approves_red_issues_decision_id(tmp_path):
    s = _store(tmp_path)
    p = propose(s, "publish", "ziman", "publish post", "RED", "octopus")
    d = decide(s, p["proposal_id"], "approve", "saheb", "owner")
    assert d["decision_id"].startswith("ZIM-DEC-")
    assert s.get_proposal(p["proposal_id"])["status"] == "approved"
    assert s.get_proposal(p["proposal_id"])["decision_id"] == d["decision_id"]
    assert s.verify_ledger()["ok"] is True          # propose + decide، زنجیره سالم


def test_agent_cannot_approve_and_status_unchanged(tmp_path):
    s = _store(tmp_path)
    p = propose(s, "send_dm", "ziman", "x", "GREEN", "octopus")
    with pytest.raises(PermissionError):
        decide(s, p["proposal_id"], "approve", "octopus", "octopus")  # NC-3
    # وضعیت باید هنوز pending باشد، و تلاشِ مسدودشده در دفتر ثبت شده باشد
    assert s.get_proposal(p["proposal_id"])["status"] == "pending"
    kinds = [e["kind"] for e in s.ledger_tail()]
    assert "decide_denied" in kinds


def test_admin_cannot_approve_red(tmp_path):
    s = _store(tmp_path)
    p = propose(s, "publish", "ziman", "x", "RED", "octopus")
    with pytest.raises(PermissionError):
        decide(s, p["proposal_id"], "approve", "human_admin", "admin")
    assert s.get_proposal(p["proposal_id"])["status"] == "pending"


def test_admin_approves_within_ceiling(tmp_path):
    s = _store(tmp_path)
    p = propose(s, "draft", "ziman", "yellow item", "YELLOW", "octopus")
    d = decide(s, p["proposal_id"], "approve", "human_admin", "admin")
    assert d["status"] == "approved"


def test_double_decide_blocked(tmp_path):
    s = _store(tmp_path)
    p = propose(s, "publish", "ziman", "x", "RED", "octopus")
    decide(s, p["proposal_id"], "approve", "saheb", "owner")
    with pytest.raises(GovernanceError):
        decide(s, p["proposal_id"], "reject", "saheb", "owner")   # دیگر pending نیست


def test_invalid_risk_and_outcome(tmp_path):
    s = _store(tmp_path)
    with pytest.raises(GovernanceError):
        propose(s, "x", "ziman", "d", "PURPLE", "octopus")
    p = propose(s, "x", "ziman", "d", "GREEN", "octopus")
    with pytest.raises(GovernanceError):
        decide(s, p["proposal_id"], "yeet", "saheb", "owner")


def test_reject_flow(tmp_path):
    s = _store(tmp_path)
    p = propose(s, "publish", "ziman", "x", "ORANGE", "octopus")
    d = decide(s, p["proposal_id"], "reject", "saheb", "owner")
    assert d["status"] == "rejected"
    assert s.list_proposals(status="rejected")[0]["proposal_id"] == p["proposal_id"]


def test_reserved_ref_is_reused_as_decision_id(tmp_path):
    """رگرسیونِ یافتهٔ #4: ref رزروشده در propose باید همان decision_id در decide شود."""
    s = _store(tmp_path)
    p = propose(s, "publish", "ziman", "x", "RED", "octopus")
    assert p["ref"] and p["ref"].startswith("ZIM-DEC-")
    d = decide(s, p["proposal_id"], "approve", "saheb", "owner")
    assert d["decision_id"] == p["ref"]                       # دوباره‌استفاده، نه سکهٔ نو
    assert s.get_proposal_by_ref(p["ref"])["decision_id"] == p["ref"]


def test_two_same_day_proposals_get_distinct_refs(tmp_path):
    """رگرسیونِ یافتهٔ #5: دو proposalِ هم‌روز نباید ref یکسان (برخورد) بگیرند."""
    s = _store(tmp_path)
    a = propose(s, "publish", "ziman", "A", "RED", "octopus")
    b = propose(s, "publish", "ziman", "B", "RED", "octopus")
    assert a["ref"] != b["ref"]
    # هر ref باید دقیقاً proposalِ خودش را برگرداند (نه آخری را)
    assert s.get_proposal_by_ref(a["ref"])["proposal_id"] == a["proposal_id"]
    assert s.get_proposal_by_ref(b["ref"])["proposal_id"] == b["proposal_id"]
