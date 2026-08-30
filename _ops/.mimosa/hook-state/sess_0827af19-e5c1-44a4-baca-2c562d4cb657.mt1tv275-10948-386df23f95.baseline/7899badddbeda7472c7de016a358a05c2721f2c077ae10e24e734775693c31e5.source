"""test_part_loops.py — لوپِ یادگیری+خود-تغییرِ هر بخش (جلسه ۴۶).

هر بخش observe→learn→propose؛ ارکستریتور همه را می‌چرخاند، persist می‌کند،
رویداد emit می‌کند، و پیشنهادها به improve/خانه می‌روند. propose-only.
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("part-loops")

import part_loops as pl   # noqa: E402
import opslib             # noqa: E402


def t_a_run_all_every_part_reports():
    d = pl.run_all(beat=10)
    assert d["schema"] == "part-loops.v1"
    ids = {p["id"] for p in d["parts"]}
    assert {"heart", "cortex", "doctor", "money", "learning", "legs", "self"} <= ids
    assert all("status" in p and "name" in p for p in d["parts"])
    # persist شد
    disk = json.loads(pl.OUT.read_text("utf-8"))
    assert disk["n_proposals"] == d["n_proposals"]


def t_b_learn_triggers_proposal():
    """پولِ نزدیکِ سقف → پیشنهادِ بخشِ پول (لوپ واقعاً «یاد می‌گیرد»)."""
    with opslib.LockedJson(opslib.STATE_DIR / "telemetry-latest.json") as lj:
        lj.write({"month": {"aud": 26.0}})
    d = pl.run_all(beat=11)
    money = next(p for p in d["parts"] if p["id"] == "money")
    assert money["status"] == "🔴"
    assert any(p["part"] == "پول" for p in d["proposals"])


def t_c_proposals_are_propose_only_shape():
    d = pl.run_all(beat=12)
    for p in d["proposals"]:
        assert set(p) >= {"part", "title", "action", "change_level", "auto_ok"}
        assert p["change_level"] in ("tune", "reconfig", "code")
        # فقط knobِ tune می‌تواند auto باشد (نه code/reconfig)
        if p["auto_ok"]:
            assert p["change_level"] == "tune"


def t_d_one_bad_part_does_not_kill_loop():
    """اگر یک probe خطا دهد، بقیه بخش‌ها همچنان گزارش می‌دهند (fail-soft)."""
    orig = pl.LOOPS[0]
    def boom():
        raise RuntimeError("x")
    pl.LOOPS[0] = boom
    try:
        d = pl.run_all(beat=13)
        assert len(d["parts"]) == len(pl.LOOPS)   # همهٔ بخش‌ها ردیف دارند
    finally:
        pl.LOOPS[0] = orig


def t_e_improve_consumes_part_proposals():
    import improve
    with opslib.LockedJson(pl.OUT) as lj:
        lj.write({"schema": "part-loops.v1", "n_proposals": 1,
                  "proposals": [{"part": "قلب", "title": "تستِ بخش",
                                 "action": "کاری بکن", "change_level": "reconfig",
                                 "auto_ok": False}]})
    d = improve.run(write=False, use_local_brain=False)
    blob = json.dumps(d, ensure_ascii=False)
    assert "قلب: تستِ بخش" in blob   # پیشنهادِ بخش به digest رفت


def t_f_ops_dashboard_shows_parts():
    sys.path.insert(0, str(_HERE.parent / "live"))
    import server
    pl.run_all(beat=14)
    st = server.ops_state()
    assert "parts" in st and len(st["parts"]) >= 5
    assert all("status" in p and "name" in p for p in st["parts"])


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_part_loops: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
