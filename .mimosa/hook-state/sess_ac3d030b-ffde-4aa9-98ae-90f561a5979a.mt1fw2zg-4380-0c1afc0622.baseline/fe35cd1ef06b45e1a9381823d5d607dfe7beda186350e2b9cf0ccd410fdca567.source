"""تست‌های ShadowGate (G11) — تضمینِ propose-only سرتاسری، fail-closed.

ادعای مرکزی: تا وقتی shadow روشن است، هیچ‌چیز اجرا نمی‌شود — حتی proposalِ approved.
"""
import pytest

from core.authz import Authz, Role, User
from core.command_registry import CommandRegistry
from core.governance import decide_by_ref
from core.shadow import ShadowGate
from core.store import Store


def _gate(tmp_path):
    store = Store(tmp_path / "sh.db")
    authz = Authz([User("admin", "آری", Role.ADMIN, telegram_chat_id=111,
                        ziman_role="owner")])
    return ShadowGate(store, CommandRegistry.load(), authz), store


def test_shadow_on_by_default(tmp_path):
    gate, _ = _gate(tmp_path)
    assert gate.is_shadow_on() is True


def test_green_command_is_read_only_no_proposal(tmp_path):
    gate, store = _gate(tmp_path)
    r = gate.submit("/status", "show status", actor_role="viewer")
    assert r["status"] == "read_only" and r["executed"] is False
    assert store.list_proposals() == []       # هیچ proposalی ساخته نشد


def test_unknown_command_denied(tmp_path):
    gate, _ = _gate(tmp_path)
    r = gate.submit("/nope", "x", actor_role="owner")
    assert r["status"] == "denied" and r["executed"] is False


def test_red_command_creates_proposal_only(tmp_path):
    gate, store = _gate(tmp_path)
    r = gate.submit("/approve", "publish post", actor_chat_id=111)  # نقش=owner
    assert r["status"] == "proposed" and r["executed"] is False
    assert r["ref"].startswith("ZIM-DEC-")
    assert len(store.list_proposals(status="pending")) == 1


def test_cannot_execute_while_shadow_on_even_if_approved(tmp_path):
    gate, store = _gate(tmp_path)
    sub = gate.submit("/policy", "change policy X", actor_chat_id=111)  # ORANGE
    ref = sub["ref"]
    # مالک تأیید می‌کند (owner)
    decide_by_ref(store, ref, "approve", "admin", "owner")
    assert store.get_proposal_by_ref(ref)["status"] == "approved"
    # اما چون shadow روشن است، اجرا هنوز ممنوع است
    ce = gate.can_execute(ref)
    assert ce["execute"] is False
    assert "shadow" in ce["reason"].lower()


def test_execute_allowed_only_after_owner_turns_shadow_off_and_approved(tmp_path):
    gate, store = _gate(tmp_path)
    sub = gate.submit("/policy", "change Y", actor_chat_id=111)
    ref = sub["ref"]
    decide_by_ref(store, ref, "approve", "admin", "owner")
    gate.set_shadow(False, actor_role="owner")            # فقط owner می‌تواند
    ce = gate.can_execute(ref)
    assert ce["execute"] is True
    assert ce["decision_id"] == store.get_proposal_by_ref(ref)["decision_id"]


def test_non_owner_cannot_disable_shadow(tmp_path):
    gate, _ = _gate(tmp_path)
    with pytest.raises(PermissionError):
        gate.set_shadow(False, actor_role="admin")
    assert gate.is_shadow_on() is True


def test_agent_role_default_for_programmatic_call(tmp_path):
    gate, store = _gate(tmp_path)
    # بدونِ chat یا role → ایجنت؛ proposal ساخته می‌شود ولی نقشِ پیشنهاددهنده agent
    r = gate.submit("/approve", "x")
    assert r["role"] == "agent" and r["status"] == "proposed"
    p = store.get_proposal(r["proposal_id"])
    assert p["proposed_by"] == "agent"


# ── پوششِ نیمهٔ دومِ propose-only: با shadowِ خاموش هم فقط approved اجرا می‌شود ──

def test_shadow_off_pending_proposal_cannot_execute(tmp_path):
    gate, store = _gate(tmp_path)
    sub = gate.submit("/policy", "pending item", actor_chat_id=111)  # ORANGE، pending
    gate.set_shadow(False, actor_role="owner")
    ce = gate.can_execute(sub["ref"])
    assert ce["execute"] is False               # هنوز approve نشده
    assert "not approved" in ce["reason"].lower()


def test_shadow_off_rejected_proposal_cannot_execute(tmp_path):
    gate, store = _gate(tmp_path)
    sub = gate.submit("/policy", "to reject", actor_chat_id=111)
    decide_by_ref(store, sub["ref"], "reject", "admin", "owner")
    gate.set_shadow(False, actor_role="owner")
    ce = gate.can_execute(sub["ref"])
    assert ce["execute"] is False


def test_shadow_off_unknown_ref_fail_closed(tmp_path):
    gate, _ = _gate(tmp_path)
    gate.set_shadow(False, actor_role="owner")
    ce = gate.can_execute("ZIM-DEC-20260712-9999")
    assert ce["execute"] is False
    assert "unknown" in ce["reason"].lower()


def test_yellow_proposal_is_actionable_via_queue_handle(tmp_path):
    """رگرسیونِ یافتهٔ #2: YELLOW باید با شناسهٔ نشان‌داده در /queue قابلِ approve باشد."""
    from core.governance import pending_summary
    gate, store = _gate(tmp_path)
    sub = gate.submit("/product", "add product draft", actor_chat_id=111)  # YELLOW
    assert sub["status"] == "proposed"
    handle = pending_summary(store)[0]["ref"]     # همان چیزی که مالک می‌بیند
    assert handle and handle.startswith("ZIM-DEC-")
    d = decide_by_ref(store, handle, "approve", "admin", "owner")
    assert d["status"] == "approved"


def test_non_owner_set_shadow_writes_audit_event(tmp_path):
    gate, store = _gate(tmp_path)
    try:
        gate.set_shadow(False, actor_role="admin")
    except PermissionError:
        pass
    kinds = [e["kind"] for e in store.ledger_tail()]
    assert "shadow_denied" in kinds
