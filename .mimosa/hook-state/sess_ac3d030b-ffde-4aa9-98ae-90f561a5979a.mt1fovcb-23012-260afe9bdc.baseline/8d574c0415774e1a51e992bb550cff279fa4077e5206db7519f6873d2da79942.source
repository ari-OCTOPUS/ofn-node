"""test_tg_actions.py — رجیستریِ اکشن‌ها (telegram_center/actions.py).

پوشش: همهٔ callbackها با قالب‌های قراردادی سازگارند، جایگذاریِ پارامترها ایمن است،
طبقه‌بندیِ risk/direct/double_confirm درست کار می‌کند، و ورودیِ ناشناخته fail-soft است.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402
ENV = harness.setup("tg-actions")

sys.path.insert(0, str(_HERE.parent / "telegram_center"))
import actions as act   # noqa: E402


def t_a_registry_not_empty():
    assert len(act.ACTIONS) >= 15
    # همهٔ مدخل‌ها schema درست دارند
    for name, e in act.ACTIONS.items():
        assert set(e.keys()) == {"callback", "risk", "direct", "double_confirm",
                                 "verbs", "description"}, (name, e.keys())
        assert e["risk"] in ("read", "low", "medium", "high", "emergency")
        assert isinstance(e["verbs"], tuple) and len(e["verbs"]) >= 1


def t_b_static_callbacks_match_contract():
    """callbackهای بدونِ پارامتر دقیقاً قراردادِ render/center را رعایت می‌کنند."""
    assert act.callback_for("status.refresh") == "mn:st"
    assert act.callback_for("map.show") == "mn:map"
    assert act.callback_for("approvals.show") == "mn:ap"
    assert act.callback_for("missions.show") == "mn:ms"
    assert act.callback_for("map.start") == "map:start"
    assert act.callback_for("budget.apply") == "pw:ba"


def t_c_parametric_callbacks_substitute_leg_and_id():
    assert act.callback_for("leg.pause", leg="lead") == "lg:lead:p"
    assert act.callback_for("leg.resume", leg="ziman") == "lg:ziman:r"
    assert act.callback_for("approval.approve", id="job-123") == "ap:ok:job-123"
    assert act.callback_for("approval.detail", id="x") == "ap:detail:x"
    assert act.callback_for("mission.open", id="M-1") == "ms:open:M-1"
    assert act.callback_for("mission.approve", id="M-1") == "ms:approve:M-1"


def t_d_extra_params_ignored_safely():
    """پارامترهای نامرتبط نباید callback را خراب کنند."""
    cb = act.callback_for("status.refresh", leg="lead", id="x", foo="bar")
    assert cb == "mn:st"


def t_e_risk_classification():
    reads = act.actions_by_risk("read")
    highs = act.actions_by_risk("high")
    emergencies = act.actions_by_risk("emergency")
    assert "status.refresh" in reads
    assert "map.start" in reads        # scan فقط metadata → read
    assert "budget.apply" in highs
    assert "system.panic" in emergencies
    assert "system.stop" in emergencies


def t_f_double_confirm_gating():
    assert act.is_double_confirm("budget.apply") is True
    assert act.is_double_confirm("system.restart") is True
    assert act.is_double_confirm("system.panic") is True
    assert act.is_double_confirm("status.refresh") is False
    assert act.is_double_confirm("leg.pause") is False


def t_g_safe_direct_actions():
    """is_safe_direct فقط برای read-only مستقیم True است."""
    assert act.is_safe_direct("status.refresh") is True
    assert act.is_safe_direct("map.show") is True
    assert act.is_safe_direct("budget.apply") is False     # high risk
    assert act.is_safe_direct("leg.pause") is False        # risk=low نه read


def t_h_unknown_action_fail_soft():
    assert act.get("totally.fake.action") is None
    assert act.callback_for("nonsense") is None
    assert act.is_double_confirm("nonsense") is False
    assert act.is_safe_direct("nonsense") is False
    assert act.actions_by_risk("nonexistent") == []


def t_i_verbs_align_with_dispatch():
    """verb هر اکشن باید با center._handle_callback هم‌خوان باشد (mn/lg/pw/pwc/map/ap)."""
    valid_verbs = {"mn", "lg", "pw", "pwc", "map", "ap", "ms"}
    for name, e in act.ACTIONS.items():
        for v in e["verbs"]:
            assert v in valid_verbs, f"{name}: verb نامعتبر {v}"


def t_j_leg_actions_use_only_known_legs_in_template():
    """callbackهای قالبیِ leg نباید پیشوند/پسوند عجیب بسازند."""
    for leg in ("lead", "ziman", "mining", "studio_pf"):
        cb = act.callback_for("leg.pause", leg=leg)
        assert cb == f"lg:{leg}:p"
        assert len(cb) <= 64   # سقفِ callback_data تلگرام


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_actions: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
