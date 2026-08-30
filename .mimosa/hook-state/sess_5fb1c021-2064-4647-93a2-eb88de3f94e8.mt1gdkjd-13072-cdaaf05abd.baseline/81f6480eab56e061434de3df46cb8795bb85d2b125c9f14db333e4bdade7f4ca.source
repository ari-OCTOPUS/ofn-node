"""test_approval_actuator.py — اکچوایتورِ تصمیم‌های تأییدشده (رفعِ گاف #۱ دبل‌چک).

پوشش: okِ بی‌handler → acknowledged (نه گم‌شدنِ بی‌صدا) + heartbeat (نه decision →
بی‌حلقه با guidance)؛ handlerِ ثبت‌شده → actuated؛ idempotent (marker)؛ no/later
اکچوایت نمی‌شوند؛ کهنهٔ باستانی نادیده؛ dry_run بی‌اثر؛ صفر پول/ارسال/spend.
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("approval-actuator")

import opslib                       # noqa: E402
import approval_actuator as act     # noqa: E402
import events                       # noqa: E402

APPROVALS = opslib.STATE_DIR / "telegram" / "approvals"


def _reset():
    import shutil
    shutil.rmtree(opslib.STATE_DIR / "telegram", ignore_errors=True)
    for rel in ("cortex/actuation-marks.json", "cortex/actuation-latest.json"):
        p = opslib.STATE_DIR / rel
        if p.exists():
            p.unlink()
    if events.LOG.exists():
        events.LOG.unlink()
    act.HANDLERS.clear()


def _approval(did, verdict="ok", ts=None):
    APPROVALS.mkdir(parents=True, exist_ok=True)
    rec = {"id": did, "verdict": verdict, "ts": ts or opslib.now_iso(),
           "source": "tg-center"}
    (APPROVALS / f"{did}.json").write_text(json.dumps(rec, ensure_ascii=False), "utf-8")


def t_a_unhandled_ok_acknowledged_not_silent():
    """okِ بی‌handler → acknowledged + heartbeat؛ دورِ دوم idempotent."""
    _reset()
    _approval("appr-abc", "ok")
    d = act.run()
    assert d["n_unactuated"] == 1 and d["new_acknowledged"] == 1
    names = [e.get("event_name") for e in events.recent(10)]
    assert "system.heartbeat" in names           # visible، نه decision (بی‌حلقه)
    d2 = act.run()
    assert d2["new_acknowledged"] == 0 and d2["n_unactuated"] == 1   # marker → یک‌بار


def t_b_registered_handler_actuates():
    """handlerِ ثبت‌شده روی prefix → صدا می‌شود، actuated علامت می‌خورد، idempotent."""
    _reset()
    called = {"n": 0, "rec": None}

    def h(rec):
        called["n"] += 1
        called["rec"] = rec

    act.register("lead-", h)
    _approval("lead-001", "ok")
    d = act.run()
    assert called["n"] == 1 and called["rec"]["id"] == "lead-001"
    assert d["new_actuated"] == 1 and d["n_unactuated"] == 0
    act.run()
    assert called["n"] == 1                       # idempotent


def t_c_no_and_later_not_actuated():
    """no = ردشده، later = معطل — هیچ‌کدام اکچوایت/acknowledged نمی‌شوند."""
    _reset()
    _approval("appr-no", "no")
    _approval("appr-later", "later")
    d = act.run()
    assert d["n_unactuated"] == 0 and d["new_acknowledged"] == 0
    s = act.scan()
    assert "appr-no" in s["rejected"] and "appr-later" in s["later"]


def t_d_ancient_skipped():
    """approvalِ کهنه‌تر از پنجره → نادیده (backlogِ باستانی سروصدا نکند)."""
    _reset()
    _approval("appr-old", "ok", ts="2020-01-01T00:00:00")
    d = act.run()
    assert d["n_unactuated"] == 0 and d["new_acknowledged"] == 0


def t_e_dry_run_no_write_no_call():
    """dry_run: handler صدا نمی‌شود و marker نوشته نمی‌شود."""
    _reset()
    called = {"n": 0}
    act.register("lead-", lambda rec: called.__setitem__("n", called["n"] + 1))
    _approval("lead-x", "ok")
    _approval("appr-y", "ok")
    act.run(dry_run=True)
    assert called["n"] == 0
    assert not (opslib.STATE_DIR / "cortex" / "actuation-marks.json").exists()


def t_f_no_money_no_external():
    """ساختاری: propose-only — هیچ الگوی پول/ارسال/spend/شبکه."""
    src = Path(act.__file__).read_text("utf-8")
    for bad in ("reserve", "settle", "budget_gate", "TgClient", ".send(",
                "urllib", "requests", "socket"):
        assert bad not in src, f"actuator نباید {bad} داشته باشد (propose-only)"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_approval_actuator: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
