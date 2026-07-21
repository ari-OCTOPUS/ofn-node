"""test_effector_gate_bridge.py — Trust-Engine P0: گاردِ stalenessِ releasable (D6).

می‌بندد شکافی را که راستی‌آزماییِ متخاصمِ فاز B گرفت: chrono.sweep_stale_effects فقط
pending را جارو می‌کند؛ releasable(=send_pending) هرگز منقضی نمی‌شد. گارد در لایهٔ bridge،
chrono دست‌نخورده.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "legs"))

import harness
ENV = harness.setup("effector-gate-bridge")

import importlib                        # noqa: E402
import chrono                           # noqa: E402
importlib.reload(chrono)
import effector_gate_bridge as egb      # noqa: E402
importlib.reload(egb)

_H_MS = 3_600_000


def _fresh_gate():
    db = chrono.ChronoDB(ENV["OPS_DIR"] + "/state/t-bridge.db")
    return chrono.EffectorGate(db), db


def _released_effect(gate):
    """یک effect بساز، release کن (releasable با release_ref)."""
    eid = gate.request("send", "lead-msg-1", beat=1)
    gate.release_gated_effects({"hash": "human-append-abc"})   # coarse release
    return eid


def t_a_fresh_settles():
    gate, db = _fresh_gate()
    eid = _released_effect(gate)
    now = 1_000_000_000_000
    egb.mark_released(eid, now_ms=now)
    r = egb.settle_fresh(gate, eid, now_ms=now + 1 * _H_MS, max_age_hours=24)
    assert r["settled"] is True, r
    assert gate.status_of(eid) == "settled"


def t_b_stale_refused_not_settled():
    """release شده ولی > پنجره → settle نه؛ اثر در جهان نمی‌رود."""
    gate, db = _fresh_gate()
    eid = _released_effect(gate)
    now = 1_000_000_000_000
    egb.mark_released(eid, now_ms=now)
    r = egb.settle_fresh(gate, eid, now_ms=now + 100 * _H_MS, max_age_hours=24)   # ۱۰۰h > ۲۴h
    assert r["settled"] is False and r["reason"] == "stale_refused", r
    assert r["age_hours"] > 24
    assert gate.status_of(eid) == "releasable"   # هرگز settle نشد
    # رویدادِ communication.failed(stale_refused) نوشته شد
    import json
    ev = Path(egb._events())
    recs = [json.loads(l) for l in open(ev, encoding="utf-8")]
    assert any(x["event_type"] == "communication.failed" and
               x["payload"].get("kind") == "stale_refused" for x in recs)


def t_c_no_release_ts_fails_closed():
    """release_ts ثبت نشده → تازگی قابلِ اثبات نیست → refuse (fail-closed)."""
    gate, db = _fresh_gate()
    eid = _released_effect(gate)
    r = egb.settle_fresh(gate, eid, now_ms=1_000_000_000_000, max_age_hours=24)
    assert r["settled"] is False and r["reason"] == "no_release_ts", r
    assert gate.status_of(eid) == "releasable"


def t_d_non_releasable_refused():
    """effectِ pending (release‌نشده) → settle_fresh refuse (fail-closed)."""
    gate, db = _fresh_gate()
    eid = gate.request("send", "lead-msg-2", beat=1)   # pending، release نشده
    egb.mark_released(eid, now_ms=1_000_000_000_000)   # حتی با mark، وضعیت pending است
    r = egb.settle_fresh(gate, eid, now_ms=1_000_000_000_000, max_age_hours=24)
    assert r["settled"] is False and r["reason"].startswith("not_releasable"), r


def t_f_remark_cannot_refresh_stale():
    """رگرسیونِ متخاصم: یک effectِ کهنه با re-markِ زمانِ تازه نباید settle شود (first-write-wins)."""
    gate, db = _fresh_gate()
    eid = _released_effect(gate)
    t0 = 1_000_000_000_000
    egb.mark_released(eid, now_ms=t0)                 # اولین ثبت = زمانِ واقعیِ release
    egb.mark_released(eid, now_ms=t0 + 100 * _H_MS)   # تلاش برای «تازه‌سازی» → باید نادیده شود
    r = egb.settle_fresh(gate, eid, now_ms=t0 + 100 * _H_MS, max_age_hours=24)
    assert r["settled"] is False and r["reason"] == "stale_refused", r
    assert gate.status_of(eid) == "releasable"        # هرگز settle نشد


def t_g_corrupt_release_ts_refuses_never_raises():
    """رگرسیونِ متخاصم: release_ts خراب/غیرعددی → refuse، هرگز throw (قراردادِ always-dict)."""
    import json
    gate, db = _fresh_gate()
    eid = _released_effect(gate)
    store = egb._release_store()
    store.parent.mkdir(parents=True, exist_ok=True)
    for bad in ("CORRUPT", {"nested": 1}, "12.5abc"):
        store.write_text(json.dumps({str(eid): bad}), "utf-8")
        try:
            r = egb.settle_fresh(gate, eid, now_ms=1_000_000_000_000, max_age_hours=24)
        except Exception as e:  # noqa: BLE001
            assert False, f"settle_fresh نباید throw کند روی {bad!r}: {type(e).__name__}"
        assert r["settled"] is False and r["reason"] == "bad_release_ts", (bad, r)
        assert gate.status_of(eid) == "releasable"


def t_h_future_release_ts_refused():
    """رگرسیونِ متخاصم: ts آینده (عمرِ منفی) نباید «تازه» تلقی شود."""
    gate, db = _fresh_gate()
    eid = _released_effect(gate)
    egb.mark_released(eid, now_ms=1_000_000_000_000 + 500 * _H_MS)   # آینده
    r = egb.settle_fresh(gate, eid, now_ms=1_000_000_000_000, max_age_hours=24)
    assert r["settled"] is False and r["reason"] == "future_release_ts", r
    assert gate.status_of(eid) == "releasable"


def t_i_settle_emits_effect_settled_not_communication_sent():
    """رگرسیونِ صداقتِ audit (دموِ 2026-07-21): settleِ موفق باید effect.settled بزند نه
    communication.sent — چون هیچ transportی هنوز نفرستاده (NOT_ARMED). لاگ نباید بگوید «sent»."""
    import json
    gate, db = _fresh_gate()
    eid = _released_effect(gate)
    now = 1_000_000_000_000
    egb.mark_released(eid, now_ms=now)
    r = egb.settle_fresh(gate, eid, now_ms=now + 1 * _H_MS, max_age_hours=24)
    assert r["settled"] is True
    ev = Path(egb._events())
    recs = [json.loads(l) for l in open(ev, encoding="utf-8")]
    types = [x["event_type"] for x in recs]
    assert "effect.settled" in types, types
    assert "communication.sent" not in types, "settle نباید communication.sent بزند (گمراه‌کننده)"


def t_e_chrono_untouched():
    """ساختاری: bridge هرگز schemaِ chrono را mutate نمی‌کند؛ فقط API عمومی‌اش را صدا می‌زند.
    (ذکرِ نامِ sweep_stale_effects در docstring مجاز است — چیزی که بلوک می‌کنیم فراخوانی/SQL است.)"""
    src = Path(egb.__file__).read_text("utf-8")
    # هیچ SQL مستقیم یا فراخوانیِ sweep: chrono مالکِ انحصاریِ جدولِ gated_effect است
    assert "db.ex(" not in src and "UPDATE " not in src and "INSERT " not in src
    assert ".sweep_stale_effects(" not in src
    # فقط status_of/settle از API عمومیِ گیت
    assert "gate.settle(" in src and "gate.status_of(" in src


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_effector_gate_bridge: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
