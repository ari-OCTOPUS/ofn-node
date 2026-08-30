"""test_calibration_loop.py — تعمیرِ لوپِ واسنجی (برنامه ۶، 2026-07-16).

مسئله: واسنجیِ خود ساختاراً کور بود (n=0 ابدی) — record_intent رکوردِ بی‌بیت
می‌نوشت، measure بیتِ moved را محاسبه می‌کرد ولی هرگز persist نمی‌کرد، و تنها
key ادعا («self_model.coherence») با هیچ حقیقتی جفت نمی‌شد (فضای نامِ disjoint).

اثبات می‌کند (بدونِ هیچ تغییری در calibration_probe — عمداً):
  * measure() حالا رکوردِ بستار {ts, key, moved} به outcomes.jsonl الحاق می‌کند.
  * record_intent زیرِ CORTEX_SELF_MONITOR ادعای id-کلیددار صادر می‌کند —
    key ادعا == key حقیقت → جفت‌سازیِ probe کار می‌کند (n>0).
  * فلگ خاموش (پیش‌فرض) → صفر نوشتنِ ادعا (byte-identical).
  * بستار کران‌دار است: بیتِ بی‌تغییر دوباره نوشته نمی‌شود؛ بیتِ عوض‌شده
    به‌روزرسانی می‌شود («تازه‌ترین حقیقت» در probe برنده است).

صفر نوشتن روی مسیرهای زنده: harness.setup همهٔ stateها را به tmp می‌برد.
اجرا: REAL_VAULT=<worktree> PYTHONIOENCODING=utf-8 python test_calibration_loop.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("calibration-loop")

import goal_directed as gd       # noqa: E402
import calibration_probe as cp   # noqa: E402
import opslib                    # noqa: E402


def _flag(on: bool) -> None:
    if on:
        os.environ["CORTEX_SELF_MONITOR"] = "1"
    else:
        os.environ.pop("CORTEX_SELF_MONITOR", None)


def _seed_fitness(confirmed: int, cells: dict | None = None) -> None:
    with opslib.LockedJson(opslib.STATE_DIR / "fitness-latest.json") as lj:
        lj.write({"attribution": {"confirmed": confirmed,
                                  "revenue_by_cell": cells or {}}})


def _outcome_rows() -> list[dict]:
    if not gd.OUTCOMES.exists():
        return []
    return [json.loads(ln) for ln in
            gd.OUTCOMES.read_text("utf-8").splitlines() if ln.strip()]


def _closures(key: str) -> list[dict]:
    return [r for r in _outcome_rows() if r.get("key") == key and "moved" in r]


def t_a_closure_persisted_flag_off_no_claims():
    """measure بیتِ moved را persist می‌کند (بی‌قید)؛ فلگ خاموش → صفر ادعا."""
    _flag(False)
    _seed_fitness(0)
    gd.record_intent([{"id": "flagoff-1", "title": "لیدِ نقاشی",
                       "serves_goal": "درآمد", "impact": 3.0}])
    m = gd.measure()
    assert m["tracked"] >= 1 and m["moved"] is False, m
    cl = _closures("flagoff-1")
    assert cl, "رکوردِ بستار نوشته نشد"
    assert isinstance(cl[-1]["moved"], bool) and cl[-1]["moved"] is False
    # فلگ خاموش → لِجِرِ ادعا حتی ساخته نمی‌شود (byte-identical)
    assert not gd.SELF_CLAIMS.exists(), "فلگ خاموش ولی ادعا نوشته شد"


def t_b_flag_on_claim_key_matches_truth_key():
    """زیرِ فلگ: ادعای id-کلیددار صادر می‌شود و با حقیقتِ بستار هم‌فضا است."""
    _flag(True)
    try:
        gd.record_intent([{"id": "cal-1", "title": "لیدِ Ziman",
                           "serves_goal": "درآمد", "impact": 3.0}])
        assert gd.SELF_CLAIMS.exists(), "فلگ روشن ولی ادعایی نوشته نشد"
        rows = [json.loads(ln) for ln in
                gd.SELF_CLAIMS.read_text("utf-8").splitlines() if ln.strip()]
        rec = [r for r in rows if r.get("key") == "cal-1"]
        assert rec, f"ادعای cal-1 غایب: {rows}"
        assert 0.0 <= float(rec[-1]["confidence"]) <= 1.0
        gd.measure()                          # بستار برای cal-1 نوشته می‌شود
        truth = cp._load_truth()
        assert "cal-1" in truth, f"حقیقتِ cal-1 غایب: {sorted(truth)}"
        assert truth["cal-1"]["y"] in (0, 1)
    finally:
        _flag(False)


def t_c_probe_pairs_n_gt_0_and_truth_refreshes():
    """کلِ لوپ: probe جفت پیدا می‌کند (n>0)؛ حرکتِ درآمد → y به 1 تازه می‌شود."""
    _flag(True)
    try:
        _seed_fitness(0)
        gd.record_intent([{"id": "cal-2", "title": "لیدِ نقاشی",
                           "serves_goal": "درآمد", "impact": 3.0}])
        gd.measure()                          # بستار: moved=False → y=0
        res = cp.probe(persist=False)
        assert res["n"] >= 1, f"probe هنوز کور است: {res}"
        graded = {g["key"]: g["y"] for g in res["graded"]}
        assert "cal-2" in graded and graded["cal-2"] == 0, graded
        assert res["brier"] is not None
        # درآمد حرکت کرد → بستارِ تازه، y=1 (تازه‌ترین حقیقت برنده)
        _seed_fitness(3, {"lead": 500})
        gd.measure()
        res2 = cp.probe(persist=False)
        g2 = {g["key"]: g["y"] for g in res2["graded"]}
        assert g2.get("cal-2") == 1, g2
    finally:
        _flag(False)


def t_d_closure_growth_is_bounded():
    """بیتِ بی‌تغییر دوباره نوشته نمی‌شود — measureِ مکرر فایل را باد نمی‌کند."""
    n0 = len([r for r in _outcome_rows() if "moved" in r])
    gd.measure()
    gd.measure()
    n1 = len([r for r in _outcome_rows() if "moved" in r])
    assert n1 == n0, f"بستارِ تکراری نوشته شد: {n0} → {n1}"


def t_e_measure_contract_unchanged():
    """قراردادِ measure برای مصرف‌کننده‌ها (improve.run) دست‌نخورده است."""
    m = gd.measure()
    for k in ("tracked", "moved", "now"):
        assert k in m, m
    assert isinstance(m["moved"], bool)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_calibration_loop: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
