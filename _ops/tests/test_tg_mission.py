"""test_tg_mission.py — Mission Genome و Action Graph برای کنترل تلگرامی اختاپوس.

پوشش: ایجاد mission از متن آزاد، ژنوم action/risk/approval، چرخهٔ state، fitness،
کارت render و fail-soft. صفر شبکه؛ مسیر state به sandbox تست هدایت می‌شود.
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402
ENV = harness.setup("tg-mission")

sys.path.insert(0, str(_HERE.parent / "telegram_center"))
import action_graph  # noqa: E402
import mission       # noqa: E402


_SANDBOX = Path(tempfile.mkdtemp(prefix="octopus-mission-"))


def _reset():
    shutil.rmtree(_SANDBOX, ignore_errors=True)
    _SANDBOX.mkdir(parents=True, exist_ok=True)
    mission._STATE_DIR = _SANDBOX / "missions"
    mission._MISSIONS_JSON = mission._STATE_DIR / "missions.json"
    mission._AUDIT_JSONL = mission._STATE_DIR / "mission-audit.jsonl"


# ─── Action Graph ────────────────────────────────────────────────────────────────
def t_a_action_graph_known_actions_have_safety_contract():
    g = action_graph.all_actions()
    for aid in ("status.refresh", "map.scan", "code.plan", "code.patch", "doctor.review",
                "epistemics.review", "code.test", "code.apply", "evolution.propose"):
        assert aid in g, f"action missing: {aid}"
        assert g[aid]["risk"] in ("read", "low", "medium", "high")
        assert isinstance(g[aid]["requires_approval"], bool)
    assert g["code.apply"]["requires_approval"] is True
    assert g["code.apply"]["rollback"] is True
    assert g["code.patch"]["requires_approval"] is False  # propose/shadow فقط


def t_b_action_graph_unknown_fails_closed():
    u = action_graph.get("does.not.exist")
    assert u["risk"] == "high"
    assert u["requires_approval"] is True
    assert action_graph.requires_owner_approval("does.not.exist") is True


def t_c_action_graph_intent_mapping_and_autonomy_level():
    assert action_graph.action_for_intent("scan_metadata")["action_id"] == "map.scan"
    assert action_graph.allowed_at_level("status.refresh", 0) is True
    assert action_graph.allowed_at_level("leg.pause", 1) is True
    assert action_graph.allowed_at_level("code.apply", 5) is False, "apply همیشه owner approval می‌خواهد"
    assert action_graph.max_risk(["status.refresh", "code.plan", "code.apply"]) == "high"


# ─── Mission creation / lifecycle ────────────────────────────────────────────────
def t_d_create_self_coding_mission_has_required_pipeline():
    _reset()
    m = mission.create_mission("اختاپوس، منوی تلگرامو بهتر کن و دکمه‌هاشو درست کن")
    assert m["id"].startswith("M-")
    assert m["mission_type"] == "self_coding"
    assert m["risk"] == "high", "pipeline شامل code.apply است پس risk نهایی high است"
    actions = m["actions"]
    for aid in ("code.plan", "code.patch", "doctor.review", "epistemics.review", "code.test", "code.apply"):
        assert aid in actions
    assert m["approval"] == "required"
    assert m["rollback"]["available"] is True
    assert mission._MISSIONS_JSON.exists()
    saved = json.loads(mission._MISSIONS_JSON.read_text("utf-8"))
    assert len(saved["missions"]) == 1


def t_e_create_evolution_mission_has_tournament_actions():
    _reset()
    m = mission.create_mission("سه جهش برای بهتر شدن کنترل تلگرام پیشنهاد بده")
    assert m["mission_type"] == "evolution"
    assert "evolution.propose" in m["actions"]
    assert "evolution.select" in m["actions"]
    assert m["approval"] == "required"


def t_f_preference_mission_is_low_readish_and_no_apply():
    _reset()
    m = mission.create_mission("از این به بعد منوی طولانی نده")
    assert m["mission_type"] == "preference"
    assert "code.apply" not in m["actions"]
    assert m["approval"] == "not_required"


def t_g_lifecycle_records_tests_reviews_owner_and_fitness():
    _reset()
    m = mission.create_mission("callback تلگرامو درست کن")
    mid = m["id"]
    assert mission.set_state(mid, "planned", "طرح ساخته شد")["state"] == "planned"
    assert mission.record_test(mid, "test_tg_center", True, "green")["state"] == "tested"
    assert mission.record_review(mid, "doctor", True, "low blast radius")["doctor_review"]["ok"] is True
    assert mission.record_review(mid, "epistemics", True, "tests cover callbacks")["epistemic_review"]["ok"] is True
    assert mission.set_owner_verdict(mid, True)["state"] == "approved"
    refreshed = mission.refresh_fitness(mid)
    assert refreshed["fitness"]["score"] > 0.5, refreshed["fitness"]
    assert refreshed["fitness"]["tests_passed"] is True
    assert refreshed["fitness"]["owner_acceptance"] is True


def t_h_failed_test_lowers_fitness():
    _reset()
    m = mission.create_mission("یه patch بساز")
    mid = m["id"]
    mission.record_test(mid, "test_tg_center", False, "red")
    mission.record_review(mid, "doctor", False, "unsafe")
    refreshed = mission.refresh_fitness(mid)
    assert refreshed["fitness"]["score"] < 0.0
    assert refreshed["fitness"]["tests_passed"] is False


def t_i_list_get_and_cockpit_summary():
    _reset()
    m1 = mission.create_mission("وضعیت mission")
    m2 = mission.create_mission("تلگرامو بهتر کن")
    recent = mission.list_missions(limit=2)
    assert recent[0]["id"] == m2["id"] and recent[1]["id"] == m1["id"]
    assert mission.get(m1["id"])["id"] == m1["id"]
    summary = mission.cockpit_summary()
    assert summary["priority"] is not None
    assert summary["counts"].get("created", 0) >= 2


def t_j_mission_card_for_list_and_detail():
    _reset()
    m = mission.create_mission("منوی تلگرامو بهتر کن")
    txt, kb = mission.mission_card()
    assert "Mission Genome" in txt and kb
    flat = [b["callback_data"] for row in kb for b in row]
    assert any(c.startswith("ms:open:") for c in flat)
    txt2, kb2 = mission.mission_card(m["id"])
    assert m["id"] in txt2
    flat2 = [b["callback_data"] for row in kb2 for b in row]
    assert f"ms:approve:{m['id']}" in flat2
    assert f"ms:reject:{m['id']}" in flat2


# ─── Safety / fail-soft ──────────────────────────────────────────────────────────
def t_k_containment_redacts_banned_intent():
    _reset()
    m = mission.create_mission("این متن onlyfans نباید echo شود")
    assert "onlyfans" not in m["owner_intent"].lower()
    assert "redacted" in m["owner_intent"]


def t_l_invalid_state_and_missing_id_fail_soft():
    _reset()
    m = mission.create_mission("یک تست")
    assert mission.set_state(m["id"], "not-a-state") is None
    assert mission.get("missing") is None
    assert mission.record_test("missing", "x", True) is None
    assert isinstance(mission.cockpit_summary(), dict)


def t_m_apply_after_green_tests_becomes_code_apply_request():
    assert mission.infer_mission_type("اگر تستا سبزه اعمال کن") == "code_apply_request"
    m = mission.create_mission("اگر تستا سبزه اعمال کن")
    assert "code.apply" in m["actions"]
    assert m["approval"] == "required"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_mission: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
