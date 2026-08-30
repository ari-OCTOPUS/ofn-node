"""test_business_brain.py — «مغزِ دوم» عملیاتِ کسب‌وکار (جلسه ۴۶).

Lead-نقاشی سیگنالِ واقعیِ درآمد را می‌خواند و پیشنهادِ لید می‌دهد؛ Project-F content-free
(هرگز هویت/پلتفرم/محتوا)؛ propose-only (هیچ auto)؛ به improve/داشبورد می‌رود.
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("business-brain")

import business_brain as bb   # noqa: E402
import opslib                # noqa: E402


def t_a_two_businesses_report():
    d = bb.run_all(beat=1)
    assert d["schema"] == "business-brain.v1" and d["brain"] == "second (business ops)"
    ids = {p["id"] for p in d["projects"]}
    assert {"lead-naghshi", "project-f"} == ids


def t_b_lead_reads_real_revenue_and_proposes():
    """صفر درآمد → پیشنهادِ ثبتِ لید؛ درآمدِ ثبت‌شده → 🟢."""
    with opslib.LockedJson(opslib.STATE_DIR / "fitness-latest.json") as lj:
        lj.write({"attribution": {"confirmed": 0, "revenue_by_cell": {}},
                  "authoritative": False, "experience_span_days": 3})
    d = bb.run_all(beat=2)
    lead = next(p for p in d["projects"] if p["id"] == "lead-naghshi")
    assert lead["status"] == "🟡"
    assert any("لید" in p["action"] for p in d["proposals"])
    # درآمدِ تأییدشده → سبز
    with opslib.LockedJson(opslib.STATE_DIR / "fitness-latest.json") as lj:
        lj.write({"attribution": {"confirmed": 2, "revenue_by_cell": {"lead.doer": 500}},
                  "authoritative": True, "experience_span_days": 30})
    d2 = bb.run_all(beat=3)
    assert next(p for p in d2["projects"] if p["id"] == "lead-naghshi")["status"] == "🟢"


def t_c_projectf_is_content_free():
    """Project-F هرگز هویت/پلتفرم/محتوا — فقط وضعیت/شمار/مهلت."""
    d = bb.run_all(beat=4)
    blob = json.dumps(d, ensure_ascii=False)
    for banned in ("OnlyFans", "onlyfans", "اونلی", "صبا", "media", "photo", "video"):
        assert banned not in blob, f"نشتِ محتوا/هویت: {banned}"
    pf = next(p for p in d["projects"] if p["id"] == "project-f")
    assert pf.get("content_free") is True


def t_d_projectf_pause_surfaces_content_free():
    (opslib.STATE_DIR / "projectf-paused.flag").write_text("x", "utf-8")
    try:
        d = bb.run_all(beat=5)
        pf = next(p for p in d["projects"] if p["id"] == "project-f")
        assert pf["status"] == "⏸"
        assert any(p["part"] == "Project-F" for p in d["proposals"])
    finally:
        (opslib.STATE_DIR / "projectf-paused.flag").unlink()


def t_e_business_never_auto():
    """پیشنهادهای کسب‌وکار همیشه propose-only (auto_ok=False) — درآمد/پول دستِ مالک."""
    with opslib.LockedJson(opslib.STATE_DIR / "fitness-latest.json") as lj:
        lj.write({"attribution": {"confirmed": 0, "revenue_by_cell": {}}})
    d = bb.run_all(beat=6)
    assert d["proposals"] and all(p["auto_ok"] is False for p in d["proposals"])


def t_f_improve_and_dashboard_consume_business():
    import improve
    with opslib.LockedJson(bb.OUT) as lj:
        lj.write({"schema": "business-brain.v1", "n_proposals": 1,
                  "proposals": [{"part": "Lead-نقاشی", "title": "یه لید بده",
                                 "action": "/lead", "change_level": "reconfig",
                                 "auto_ok": False}]})
    dd = improve.run(write=False, use_local_brain=False)
    blob = json.dumps(dd, ensure_ascii=False)
    assert "Lead-نقاشی: یه لید بده" in blob and "business" in blob
    # داشبورد
    sys.path.insert(0, str(_HERE.parent / "live"))
    import server
    bb.run_all(beat=7)
    st = server.ops_state()
    assert "business" in st and len(st["business"]) == 2


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_business_brain: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
