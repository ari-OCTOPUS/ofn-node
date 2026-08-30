"""test_tg_mission_runner.py — Runner v0: اجرای ایزوله، allowlist، evidence، fail-closed.

پوشش ماتریسِ blueprint: allowlist-only اجرا می‌شود · اکشن owner-gated skip می‌شود ·
تستِ سبز → record_test(passed) + artifact · تستِ قرمز → failed و apply-path بسته ·
status=passed بدون artifact ممکن نیست · duplicate run رد می‌شود · containment در artifact ·
worktree ناموجود fail-soft. همه با hookهای تزریقی — صفر شبکه، صفر git واقعی، صفر لمسِ vault زنده.
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
ENV = harness.setup("tg-mission-runner")

sys.path.insert(0, str(_HERE.parent / "telegram_center"))
import mission          # noqa: E402
import mission_runner   # noqa: E402


_SANDBOX = Path(tempfile.mkdtemp(prefix="octopus-runner-"))


def _reset():
    """state missionها را به sandbox می‌برد (مثل test_tg_mission) + یک vault fake."""
    shutil.rmtree(_SANDBOX, ignore_errors=True)
    _SANDBOX.mkdir(parents=True, exist_ok=True)
    mission._STATE_DIR = _SANDBOX / "missions"
    mission._MISSIONS_JSON = mission._STATE_DIR / "missions.json"
    mission._AUDIT_JSONL = mission._STATE_DIR / "mission-audit.jsonl"
    vault = _SANDBOX / "vault"
    (vault / "_ops").mkdir(parents=True, exist_ok=True)
    return vault


def _fake_hooks(*, test_rc=0, wt_ok=True):
    """hookهای تزریقی: worktree = یک پوشهٔ tmp؛ run_test = rc ثابت؛ بدون git واقعی."""
    made = {}

    def wt_add(vault):
        if not wt_ok:
            return None
        wt = Path(tempfile.mkdtemp(prefix="fake-wt-"))
        made["wt"] = wt
        return wt

    def wt_remove(vault, wt):
        made["removed"] = True
        shutil.rmtree(wt, ignore_errors=True)
        return True

    def run_test(wt, name):
        return (test_rc, f"[fake] {name} rc={test_rc}\n✅ ok" if test_rc == 0 else f"[fake] {name}\n❌ boom")

    def diff_stat(target):
        return "_ops/telegram_center/x.py | 2 +-"

    return {"worktree_add": wt_add, "worktree_remove": wt_remove,
            "run_test": run_test, "diff_stat": diff_stat}, made


# ─── allowlist / scope ────────────────────────────────────────────────────────
def t_a_allowlist_is_read_low_only():
    for a in mission_runner.ALLOWLIST:
        assert a in ("code.plan", "code.test", "code.diff", "doctor.review", "epistemics.review")
    # هیچ اکشنِ mutating در allowlist نیست
    for banned in ("code.patch", "code.apply", "code.rollback", "evolution.select"):
        assert banned not in mission_runner.ALLOWLIST


def t_b_verification_mission_runs_and_records_green():
    vault = _reset()
    m = mission.create_mission("تستا رو verify کن")   # → verification: code.test + doctor.review
    assert m["mission_type"] == "verification"
    hooks, made = _fake_hooks(test_rc=0)
    out = mission_runner.run_mission(m["id"], vault_root=vault, hooks=hooks,
                                     tests=("test_tg_actions.py",))
    assert out["ok"] is True, out
    assert made.get("removed") is True, "worktree باید cleanup شود"
    fresh = mission.get(m["id"])
    assert fresh["tests"] and fresh["tests"][-1]["passed"] is True
    assert fresh["fitness"]["tests_passed"] is True
    # doctor.review هم ثبت شده
    assert fresh["doctor_review"] is not None and fresh["doctor_review"]["ok"] is True


def t_c_red_test_marks_failed_and_no_apply():
    vault = _reset()
    m = mission.create_mission("تستا رو verify کن")
    hooks, _ = _fake_hooks(test_rc=1)
    out = mission_runner.run_mission(m["id"], vault_root=vault, hooks=hooks,
                                     tests=("test_tg_actions.py",))
    assert out["ok"] is False
    fresh = mission.get(m["id"])
    assert fresh["tests"][-1]["passed"] is False
    # code.apply هرگز در نتایج نیست (allowlist اجازه نمی‌دهد)
    ran = [r["action"] for r in out["results"]]
    assert "code.apply" not in ran and "code.patch" not in ran


def t_d_owner_gated_actions_are_skipped_never_run():
    vault = _reset()
    m = mission.create_mission("منوی تلگرامو بهتر کن و دکمه‌هاشو درست کن")  # self_coding: شامل code.apply/patch
    assert m["mission_type"] == "self_coding"
    hooks, _ = _fake_hooks(test_rc=0)
    out = mission_runner.run_mission(m["id"], vault_root=vault, hooks=hooks,
                                     tests=("test_tg_actions.py",))
    skipped_actions = {s["action"] for s in out["skipped"]}
    assert "code.apply" in skipped_actions
    assert "code.patch" in skipped_actions
    ran = {r["action"] for r in out["results"]}
    assert ran.isdisjoint({"code.apply", "code.patch"})
    # code.apply دلیلش owner-gated است
    reasons = {s["action"]: s["reason"] for s in out["skipped"]}
    assert reasons["code.apply"] == "owner-gated"


def t_e_artifacts_written_and_run_json_valid():
    vault = _reset()
    m = mission.create_mission("verify کن")
    hooks, _ = _fake_hooks(test_rc=0)
    out = mission_runner.run_mission(m["id"], vault_root=vault, hooks=hooks)
    art = Path(out["artifacts"])
    rj = art / "run.json"
    assert rj.exists(), "run.json باید نوشته شود"
    data = json.loads(rj.read_text("utf-8"))
    assert data["status"] == "done"
    assert data["mid"] == m["id"]


def t_f_epistemic_check_detects_missing_artifact():
    _reset()
    ok, why = mission_runner._epistemic_check(Path(tempfile.mkdtemp(prefix="empty-")))
    assert ok is False and "run.json missing" in why


def t_g_epistemic_check_flags_containment_leak():
    _reset()
    art = Path(tempfile.mkdtemp(prefix="leak-"))
    (art / "run.json").write_text('{"status":"done"}', "utf-8")
    (art / "bad.log").write_text("this mentions onlyfans somewhere", "utf-8")
    ok, why = mission_runner._epistemic_check(art)
    assert ok is False and "containment-leak" in why


def t_h_duplicate_running_refused():
    vault = _reset()
    m = mission.create_mission("verify کن")
    runs = mission_runner._runs_dir(vault, m["id"])
    (runs / "run-old").mkdir(parents=True, exist_ok=True)
    (runs / "run-old" / "run.json").write_text(
        json.dumps({"status": "running", "mid": m["id"]}), "utf-8")
    out = mission_runner.run_mission(m["id"], vault_root=vault, hooks=_fake_hooks()[0])
    assert out["ok"] is False and out["refused"] == "duplicate_run"


def t_i_worktree_unavailable_is_fail_soft():
    vault = _reset()
    m = mission.create_mission("verify کن")
    hooks, _ = _fake_hooks(wt_ok=False)
    out = mission_runner.run_mission(m["id"], vault_root=vault, hooks=hooks)
    # اجرا نمی‌ترکد؛ code.test با error ثبت می‌شود، کلِ run failed
    assert out["ok"] is False
    test_rec = [r for r in out["results"] if r["action"] == "code.test"]
    assert test_rec and test_rec[0].get("error") == "worktree_unavailable"


def t_j_missing_mission_and_bad_state_refused():
    vault = _reset()
    assert mission_runner.run_mission("M-nope", vault_root=vault)["refused"] == "mission_not_found"
    m = mission.create_mission("verify کن")
    mission.set_state(m["id"], "done")
    assert mission_runner.run_mission(m["id"], vault_root=vault)["refused"] == "state_not_eligible"


def t_k_dry_run_executes_nothing():
    vault = _reset()
    m = mission.create_mission("منوی تلگرامو بهتر کن")   # self_coding
    out = mission_runner.run_mission(m["id"], vault_root=vault, dry_run=True)
    assert out["ok"] is True and out["dry_run"] is True
    assert "code.plan" in out["would_run"]
    # هیچ artifact و هیچ record_test رخ نداده
    assert mission.get(m["id"])["tests"] == []


def t_l_runnable_missions_filters_by_state_and_allowlist():
    _reset()
    m1 = mission.create_mission("verify کن")               # eligible (created + code.test)
    mission.create_mission("منوی بهتر")                     # self_coding created — هم allowlisted دارد
    done = mission.create_mission("verify کن")
    mission.set_state(done["id"], "done")                   # خارج
    ids = {m["id"] for m in mission_runner.runnable_missions()}
    assert m1["id"] in ids
    assert done["id"] not in ids


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_mission_runner: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
