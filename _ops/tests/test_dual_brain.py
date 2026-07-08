#!/usr/bin/env python3
"""تست DualBrain — Thinking + Communication ($0 آفلاین).

ThinkingBrain: فکر/تحلیل/قیمت — خروجی: Thought (داده، نه متن).
CommBrain: ارتباط/کپشن/DM — خروجی: Message (متن، human-gated).
تفکیک: اگر Comm خراب شد، Thinking کار می‌کند.
Ethics-Guard: forbidden terms blocked. λ_persist<0.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("dual-brain")
_BRAIN = Path(r"F:\backup\03 - Projects\اونلی فنز\brain")
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from dual_brain import (DualBrain, ThinkingBrain, CommBrain, Thought, Message,  # noqa: E402
                         LAMBDA_PERSIST, COMPLIANCE_RULES, ETHICS_RULES,
                         FORBIDDEN_TERMS, _scan_forbidden, _check_compliance)


def _full_checks():
    return {**{r: True for r in COMPLIANCE_RULES},
            **{r: True for r in ETHICS_RULES}}


# ════════════════════════════════════════════════════════════════════════════════
# ThinkingBrain
# ════════════════════════════════════════════════════════════════════════════════

def t_thinking_strategy():
    """استراتژی: wall/PPV split."""
    tb = ThinkingBrain()
    t = tb.think_strategy()
    assert t.kind == "strategy" and "wall_pct" in t.data


def t_thinking_price_bandit():
    """قیمت: contextual bandit سه‌لایه."""
    tb = ThinkingBrain()
    t = tb.think_price(content_type="premium", time_slot="evening")
    assert t.data["price"] > 0 and t.data["tier"] in ("low", "mid", "premium")
    # evening > morning
    morning = tb.think_price(time_slot="morning")
    assert t.data["price"] > morning.data["price"]


def t_thinking_price_learns_from_history():
    """bandit: از نتایجِ تأییدشده یاد می‌گیرد."""
    tb = ThinkingBrain()
    historical = [{"outcome": "approved", "price": 20}, {"outcome": "approved", "price": 22}]
    t = tb.think_price(historical_data=historical)
    # base باید به سمت ۲۰-۲۲ تنظیم شده باشد
    assert t.data["base"] >= 15, f"base should adapt: {t.data['base']}"


def t_thinking_schedule():
    """زمان‌بندی."""
    tb = ThinkingBrain()
    t = tb.think_schedule("reddit")
    assert "best" in t.data and "AEST" in t.data["best"]


def t_thinking_risk():
    """تحلیل ریسک."""
    tb = ThinkingBrain()
    t = tb.think_risk("custom video", partner_stress=0.8)
    risks = t.data["risks"]
    assert any(r["risk"] == "partner-burnout" for r in risks)


def t_thinking_process_blocked_by_guard():
    """Guard fail → Thought blocked."""
    tb = ThinkingBrain()
    thoughts = tb.process("test", checks={})
    assert thoughts[0].kind == "blocked"


def t_thinking_process_all():
    """process: همه تحلیل‌ها."""
    tb = ThinkingBrain()
    thoughts = tb.process("test", checks=_full_checks())
    kinds = [t.kind for t in thoughts]
    assert "strategy" in kinds and "price" in kinds and "schedule" in kinds


# ════════════════════════════════════════════════════════════════════════════════
# CommBrain
# ════════════════════════════════════════════════════════════════════════════════

def t_comm_caption():
    """کپشن از Thought."""
    cb = CommBrain()
    thought = Thought(kind="price", data={"tier": "premium"})
    msg = cb.caption(thought)
    assert msg.kind == "caption" and msg.human_gated is True


def t_comm_dm_80_20():
    """DM: 80% relationship / 20% sales."""
    cb = CommBrain()
    thought = Thought(kind="price", data={})
    msg = cb.dm_draft(thought, recipient_segment="vip")
    assert msg.kind == "dm" and msg.human_gated is True


def t_comm_brief_for_saba():
    """بریف برای صبا."""
    cb = CommBrain()
    thoughts = [ThinkingBrain().think_strategy(), ThinkingBrain().think_price()]
    msg = cb.brief_for_saba(thoughts)
    assert msg.kind == "brief_saba" and "محدودهٔ صبا" in msg.text


def t_comm_report_for_ari():
    """گزارش برای آری."""
    cb = CommBrain()
    thoughts = [ThinkingBrain().think_price(), ThinkingBrain().think_risk("test")]
    msg = cb.report_for_ari(thoughts, drafts_count=3)
    assert msg.kind == "report_ari" and "money" in msg.text.lower() or "λ_persist" in msg.text


# ════════════════════════════════════════════════════════════════════════════════
# Ethics-Guard در Comm
# ════════════════════════════════════════════════════════════════════════════════

def test_scan_forblocked_terms():
    """اسکنِ forbidden terms."""
    assert "sydney" in _scan_forbidden("come visit me in sydney")
    assert "persian" in _scan_forbidden("I am persian girl")
    assert "paypal" in _scan_forbidden("pay via paypal")
    assert _scan_forbidden("cozy feet content") == []


def test_comm_blocks_forbidden():
    """CommBrain متنِ دارای forbidden را block می‌کند."""
    cb = CommBrain()
    passed, violations = cb._guard_text("I live in tehran and accept crypto")
    assert passed is False
    assert "tehran" in violations and "crypto" in violations


def test_comm_clean_text_passes():
    """متنِ تمیز pass می‌کند."""
    cb = CommBrain()
    passed, violations = cb._guard_text("cozy feet content for you")
    assert passed is True and violations == []


# ════════════════════════════════════════════════════════════════════════════════
# DualBrain integration
# ════════════════════════════════════════════════════════════════════════════════

def test_dual_process_and_communicate():
    """دورِ کامل: Thinking → Comm."""
    db = DualBrain()
    result = db.process_and_communicate("test draft", checks=_full_checks(),
                                         drafts_count=2)
    assert "thoughts" in result and "messages" in result
    assert result["blocked"] is False
    # حداقل یک brief_saba و یک report_ari
    kinds = [m["kind"] for m in result["messages"]]
    assert "brief_saba" in kinds and "report_ari" in kinds


def test_dual_blocked_by_guard():
    """Guard fail → blocked."""
    db = DualBrain()
    result = db.process_and_communicate("test", checks={})
    assert result["blocked"] is True


def test_dual_all_messages_human_gated():
    """همه Messages human_gated=True."""
    db = DualBrain()
    result = db.process_and_communicate("test", checks=_full_checks())
    for m in result["messages"]:
        assert m["human_gated"] is True


def test_dual_no_pii_in_messages():
    """صفر PII/رسانه در خروجی."""
    db = DualBrain()
    result = db.process_and_communicate("test", checks=_full_checks())
    for m in result["messages"]:
        for forbidden in ("name", "email", "phone", "photo", "video", "media"):
            assert forbidden.lower() not in m["text"].lower(), \
                f"PII leak: {forbidden} in {m['text']}"


def t_dual_lambda_persist_negative():
    """λ_persist منفی."""
    assert LAMBDA_PERSIST == -1.0


def test_dual_thinking_comm_separation():
    """تفکیک: Thinking داده می‌دهد، Comm متن می‌دهد."""
    db = DualBrain()
    thoughts = db.thinking.process("test", checks=_full_checks())
    messages = [db.comm.caption(t) for t in thoughts if t.kind in ("price", "strategy")]
    # Thinking خروجی‌اش dict است (داده)
    assert isinstance(thoughts[0].data, dict)
    # Comm خروجی‌اش str است (متن)
    assert all(isinstance(m.text, str) for m in messages)


def test_dual_tone_switch():
    """Comm tone قابل‌تغییر."""
    cb = CommBrain()
    cb.set_tone("professional")
    assert cb._tone == "professional"
    cb.set_tone("invalid")   # → fallback warm
    assert cb._tone == "warm"


if __name__ == "__main__":
    failed = harness.run([
        # Thinking
        ("[T] strategy", t_thinking_strategy),
        ("[T] price bandit", t_thinking_price_bandit),
        ("[T] price learns", t_thinking_price_learns_from_history),
        ("[T] schedule", t_thinking_schedule),
        ("[T] risk", t_thinking_risk),
        ("[T] process blocked", t_thinking_process_blocked_by_guard),
        ("[T] process all", t_thinking_process_all),
        # Comm
        ("[C] caption", t_comm_caption),
        ("[C] DM 80/20", t_comm_dm_80_20),
        ("[C] brief saba", t_comm_brief_for_saba),
        ("[C] report ari", t_comm_report_for_ari),
        # Ethics
        ("[E] scan forbidden", test_scan_forblocked_terms),
        ("[E] blocks forbidden", test_comm_blocks_forbidden),
        ("[E] clean passes", test_comm_clean_text_passes),
        # Dual
        ("[D] process+comm", test_dual_process_and_communicate),
        ("[D] blocked by guard", test_dual_blocked_by_guard),
        ("[D] all human-gated", test_dual_all_messages_human_gated),
        ("[D] no PII", test_dual_no_pii_in_messages),
        ("[D] λ_persist", t_dual_lambda_persist_negative),
        ("[D] T/C separation", test_dual_thinking_comm_separation),
        ("[D] tone switch", test_dual_tone_switch),
    ])
    sys.exit(1 if failed else 0)
