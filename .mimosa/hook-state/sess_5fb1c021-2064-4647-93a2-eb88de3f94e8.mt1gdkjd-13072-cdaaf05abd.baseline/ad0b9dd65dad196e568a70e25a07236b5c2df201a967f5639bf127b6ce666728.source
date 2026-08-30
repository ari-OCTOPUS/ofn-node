# -*- coding: utf-8 -*-
"""آزمون مغز تکاملی (فاز ۴) — propose/TTL/resolve/گارد privacy، بدون شبکه."""
from datetime import datetime, timedelta

from core.gateway import Gateway, GatewayError
from core.memory import Memory
from evolution.brain import CHANGELOG, EvolutionBrain

_PROPOSAL = ("عنوان: بهبود کش\nمشکل: تکرار تحقیق\nراه‌حل: TTL دوبرابر\n"
             "ریسک: کهنگی\nاثر: کاهش هزینه\nبرگشت: مقدار قبلی")


class FakeGW:
    def llm(self, prompt, system="", tier="cheap", business="", max_tokens=900, use_cache=True):
        return _PROPOSAL


def test_propose_parse_and_pending(td):
    m = Memory(td / "core.db")
    b = EvolutionBrain(m, FakeGW())
    pid = b.propose()
    rows = m.pending_proposals()
    assert rows and rows[0][0] == pid and rows[0][1] == "بهبود کش"
    assert m.unnotified_proposals()          # کارت باید برود


def test_resolve_approved_writes_changelog(td):
    m = Memory(td / "core.db")
    b = EvolutionBrain(m, FakeGW())
    pid = b.propose()
    before = CHANGELOG.read_text(encoding="utf-8") if CHANGELOG.exists() else ""
    msg = b.resolve(pid, "approved")
    after = CHANGELOG.read_text(encoding="utf-8")
    assert f"#{pid}" in msg and f"evo/{pid}" in after and len(after) > len(before)
    assert m.get_proposal(pid)[7] == "approved"
    # verdict دوم روی حل‌شده بی‌اثر (fail-closed)
    assert "باز نیست" in b.resolve(pid, "rejected")


def test_resolve_rejected(td):
    m = Memory(td / "core.db")
    b = EvolutionBrain(m, FakeGW())
    pid = b.propose()
    b.resolve(pid, "rejected")
    assert m.get_proposal(pid)[7] == "rejected"
    assert not m.pending_proposals()


def test_ttl_expire(td):
    m = Memory(td / "core.db")
    pid = m.add_proposal("کهنه", "p", "s", "r", "i", "rb")
    old = (datetime.now() - timedelta(days=31)).isoformat(timespec="seconds")
    with m._lock:
        m._c.execute("UPDATE proposals SET ts=? WHERE id=?", (old, pid))
        m._c.commit()
    assert m.expire_proposals(30) == 1
    assert m.get_proposal(pid)[7] == "expired"


def test_projectf_never_reaches_fugu(td):
    """گارد privacy کشف pass-2: pool ی Fugu Ultra ثابت است."""
    m = Memory(td / "core.db")
    g = Gateway(m, {"SAKANA_API_KEY": "x", "FUGU_BUDGET_MONTHLY": "40"})
    try:
        g.llm("تحلیل", tier="escalate", business="projectf", use_cache=False)
        raise AssertionError("باید GatewayError privacy می‌داد")
    except GatewayError as e:
        assert "Project-F" in str(e)


def test_signals_exclude_projectf_on_escalate(td):
    m = Memory(td / "core.db")
    from core.contracts import Brief, Feedback
    bid = m.add_brief(Brief(business="projectf", title="t", opportunity="o",
                            why="w", action="a", source="s"))
    m.add_feedback(Feedback(brief_id=bid, useful=True))
    b = EvolutionBrain(m, FakeGW())
    sig_esc = b.collect_signals(include_projectf=False)
    sig_all = b.collect_signals(include_projectf=True)
    assert "projectf" not in sig_esc["feedback"]
    assert "projectf" in sig_all["feedback"]
