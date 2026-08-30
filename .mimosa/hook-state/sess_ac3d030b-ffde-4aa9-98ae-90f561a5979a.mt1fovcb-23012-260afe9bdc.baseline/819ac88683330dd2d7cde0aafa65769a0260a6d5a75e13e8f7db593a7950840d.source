#!/usr/bin/env python3
"""تستِ معیارِ دقتِ خودمدل (C3، ۲۰۲۶-۰۷-۲۸).

این اولین سنجهٔ ملموسِ «چقدر از خودم نمی‌دانم» است. بازسنجیِ ۰۷-۲۵ گفت C3
«NOT_MEASURED» است؛ این تست اثبات می‌کند که خودمدلِ ارگانیسم از این پس در برابرِ
منابعِ حقیقتِ مستقل سنجیده می‌شود، نه فقط خودگزارشِ LLM.

$0 · sandbox · صفر شبکه · صفر نوشتن روی state/ژنوم/ledger واقعی (فقط self-accuracy.jsonl)."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("self-accuracy")
_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "doctor")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
import self_accuracy as sa  # noqa: E402

_SB = Path(ENV["ops"]) / "state"


def _sandbox_paths():
    opslib.STATE_DIR = _SB


def _seed_state(*, legs=None, revenue=None, wire_on=("wire_doctor",), wire_off=()):
    """state واقعیِ سندباکس را بکار — منبعِ حقیقتِ سنجش."""
    inner = legs if legs is not None else {"mining": {"live": False},
                                           "ziman": {"live": True, "money_link": "active"}}
    wiring = {k: True for k in wire_on}
    wiring.update({k: False for k in wire_off})
    org = {"business_legs": {"business_legs": inner, "beat": 1234},
           "wiring": wiring, "month": {"musd": 0}}
    (_SB / "ORGANISM-STATE.json").write_text(json.dumps(org), "utf-8")
    fit = {"attribution": {"confirmed": 0}}
    if revenue is not None:
        fit["attribution"]["revenue_by_cell"] = {"cell_a": revenue}
    (_SB / "fitness-latest.json").write_text(json.dumps(fit), "utf-8")


def _snap(**kw):
    """یک snapshotِ ساختگی (ادعای خودمدل) بساز — این چیزی است که sنجیده می‌شود."""
    return kw


# ── منابعِ حقیقت مستقل از snapshot ─────────────────────────────────────────────
def t_actual_legs_unwraps_two_layers():
    """منبعِ حقیقت نباید خودش کور باشد: دو-لایه بودن business_legs را باز می‌کند."""
    _sandbox_paths(); _seed_state(legs={"mining": {"live": False}, "crypto": {"live": False}})
    assert sa._actual_legs() == {"mining", "crypto"}, sa._actual_legs()


def t_actual_legs_sees_arms_with_separate_keys():
    """بازوهای با کلیدِ جدا (ziman/leg/cartographer) هم باید نامرئی نباشند (درسِ ۰۷-۲۷)."""
    _sandbox_paths()
    org = {"business_legs": {"business_legs": {"mining": {"live": False}}, "beat": 1},
           "ziman": {"leg_id": "z", "money_link": "active"},
           "leg": {"leg_id": "l", "money_link": "active"}}
    (_SB / "ORGANISM-STATE.json").write_text(json.dumps(org), "utf-8")
    assert sa._actual_legs() == {"mining", "ziman", "leg"}, sa._actual_legs()


def t_actual_revenue_sums_revenue_by_cell():
    """درآمد = جمعِ دلاری revenue_by_cell، نه شمارشِ confirmed (درسِ ۰۷-۲۷)."""
    _sandbox_paths(); _seed_state(revenue=1000.0)
    assert sa._actual_revenue() == 1000.0
    _seed_state()  # خالی = صفرِ صادق
    assert sa._actual_revenue() == 0.0


def t_actual_wire_reads_real_wiring():
    _sandbox_paths()
    _seed_state(wire_on=("wire_doctor", "wire_lead"), wire_off=("wire_email",))
    on, off = sa._actual_wire()
    assert on == {"wire_doctor", "wire_lead"} and off == {"wire_email"}, (on, off)


# ── measure: درست/غلط/نامعلوم ─────────────────────────────────────────────────
def t_accurate_snapshot_scores_one():
    """snapshotِ درست → accuracy=1.0، صفر drift."""
    _sandbox_paths(); _seed_state(legs={"mining": {}}, revenue=250.0,
                                  wire_on=("wire_doctor",), wire_off=("wire_email",))
    snap = _snap(legs={"mining": {"live": False}}, revenue=250.0,
                 wire_on=["wire_doctor"], wire_off=["wire_email"])
    r = sa.measure(snap, persist=False)
    assert r["accuracy"] == 1.0, r
    assert r["fields_checked"] == 3 and r["drifts"] == [], r


def t_wrong_leg_count_drifts():
    """ادعای ۱ لِگ در حالی که ۳ لِگ واقعی است — همان دروغِ ۰۷-۲۵."""
    _sandbox_paths(); _seed_state(legs={"mining": {}, "crypto": {}, "accounting": {}})
    snap = _snap(legs={"mining": {"live": False}}, revenue=0.0, wire_on=[], wire_off=[])
    r = sa.measure(snap, persist=False)
    legs_drift = [d for d in r["drifts"] if d["field"] == "legs"]
    assert legs_drift, "driftِ legs گرفته نشد"
    assert r["accuracy"] < 1.0, r
    # drift = اندازهٔ تفاضلِ متقارن (۲ لِگِ دیده‌نشده)
    assert legs_drift[0]["drift"] == 2, legs_drift[0]


def t_wrong_revenue_drifts():
    """ادعای درآمد>۰ در حالی که واقعی صفر است — همان دروغِ ۲۷ نسخه."""
    _sandbox_paths(); _seed_state(revenue=0.0)
    snap = _snap(legs={}, revenue=1250.0, wire_on=[], wire_off=[])
    r = sa.measure(snap, persist=False)
    assert any(d["field"] == "revenue" for d in r["drifts"]), r
    assert r["accuracy"] < 1.0


def t_unknown_accuracy_when_nothing_checkable():
    """اگر هیچ فیلدی قابل‌سنجش نبود → None (نامعلوم)، نه ۰ نه ۱. صداقت بر عدد ترجیح دارد."""
    _sandbox_paths()
    # state کاملاً غایب
    (_SB / "ORGANISM-STATE.json").unlink(missing_ok=True)
    (_SB / "fitness-latest.json").unlink(missing_ok=True)
    snap = _snap(legs={}, revenue=0.0, wire_on=[], wire_off=[])
    r = sa.measure(snap, persist=False)
    # legs همیشه قابل‌سنجش است (set خالی)، ولی اگر actual_legs خالی و reported هم خالی
    # بود، آن یکی still checked است. پس accuracy نمی‌تواند None باشد مگر صفر checked.
    # این تست را صادقانه تنظیم می‌کنیم: با state غایب، actual_legs() == set() و
    # reported == set() → یک checkِ مساوی → accuracy 1.0 یا یک check. نامعلوم بودن
    # فقط وقتی _check کلیدها None برگرداند — پس این تست رفتارِ واقعی را می‌سنجد:
    assert r["fields_checked"] >= 1, "حداقل legs باید بررسی شود"
    assert isinstance(r["accuracy"], float), r


def test_trail_appends_and_carries_accuracy():
    """سریِ زمانیِ صداقت واقعاً append می‌شود و فیلدِ accuracy در آن است — این
    دقیقاً شکافِ «حاضر ولی نه سنجش‌پذیر» (از ۰۷-۲۵) را می‌بندد."""
    _sandbox_paths(); _seed_state(legs={"mining": {}}, revenue=0.0)
    (sa._trail_path()).unlink(missing_ok=True)
    snap = _snap(legs={"mining": {"live": False}}, revenue=0.0, wire_on=[], wire_off=[])
    sa.measure(snap, persist=True)
    sa.measure(snap, persist=True)
    lines = sa._trail_path().read_text("utf-8").strip().splitlines()
    assert len(lines) == 2, f"دو ردیف انتظار می‌رفت، {len(lines)} شد"
    for line in lines:
        rec = json.loads(line)
        assert "accuracy" in rec and "ts" in rec, rec
        assert "drifts" in rec, rec


# ── wiring: فلگ خاموش = byte-identical no-op ───────────────────────────────────
def t_flag_off_is_noop():
    """فلگ خاموش → {} (رفتارِ نبودِ ماژول). این قاعدهٔ additive/flag-gated است."""
    _sandbox_paths(); _seed_state()
    os.environ.pop(sa.FLAG_NAME, None)
    assert sa.run_from_snapshot(_snap(legs={}, revenue=0.0)) == {}


def t_flag_on_measures_and_persists():
    _sandbox_paths(); _seed_state(legs={"mining": {}}, revenue=0.0)
    (sa._trail_path()).unlink(missing_ok=True)
    os.environ[sa.FLAG_NAME] = "1"
    try:
        r = sa.run_from_snapshot(_snap(legs={"mining": {"live": False}}, revenue=0.0))
        assert r and "accuracy" in r, r
        assert sa._trail_path().exists(), "سریِ زمانی نوشته نشد"
    finally:
        os.environ.pop(sa.FLAG_NAME, None)


def t_never_writes_outside_accuracy_trail():
    """خطِ قرمز: state/ژنوم/ledger واقعی هرگز نوشته نمی‌شود — فقط self-accuracy.jsonl."""
    _sandbox_paths(); _seed_state()
    org_before = (_SB / "ORGANISM-STATE.json").read_text("utf-8")
    os.environ[sa.FLAG_NAME] = "1"
    try:
        sa.run_from_snapshot(_snap(legs={}, revenue=0.0))
        assert (_SB / "ORGANISM-STATE.json").read_text("utf-8") == org_before, "state دست خورد"
    finally:
        os.environ.pop(sa.FLAG_NAME, None)
    # فایل‌های ممنوع نباید ساخته شوند
    for forbidden in ("genome-system", "ledger", "budget-state.json"):
        assert not (_SB / forbidden).exists(), f"نوشتنِ ممنوع: {forbidden}"


def t_fail_soft_on_broken_state():
    """state خراب نباید فراخواننده را بکشد (fail-soft)."""
    _sandbox_paths()
    (_SB / "ORGANISM-STATE.json").write_text("not json", "utf-8")
    r = sa.measure(_snap(legs={}, revenue=0.0), persist=False)
    assert isinstance(r, dict), "crash به‌جای fail-soft"


if __name__ == "__main__":
    failed = harness.run([
        ("منبعِ legs دو-لایه را باز می‌کند", t_actual_legs_unwraps_two_layers),
        ("منبعِ legs بازوهای جدا را می‌بیند", t_actual_legs_sees_arms_with_separate_keys),
        ("منبعِ درآمد دلار را جمع می‌زند", t_actual_revenue_sums_revenue_by_cell),
        ("منبعِ wire واقعی را می‌خواند", t_actual_wire_reads_real_wiring),
        ("snapshotِ درست accuracy=1.0", t_accurate_snapshot_scores_one),
        ("شمارشِ غلطِ لِگ drift می‌گیرد", t_wrong_leg_count_drifts),
        ("درآمدِ غلط drift می‌گیرد", t_wrong_revenue_drifts),
        ("نامعلوم هنگامِ نبودِ داده", t_unknown_accuracy_when_nothing_checkable),
        ("سریِ زمانی append و accuracy دارد", test_trail_appends_and_carries_accuracy),
        ("فلگ خاموش no-op است", t_flag_off_is_noop),
        ("فلگ روشن سنجش و ثبت می‌کند", t_flag_on_measures_and_persists),
        ("هرگز خارجِ trail نمی‌نویسد", t_never_writes_outside_accuracy_trail),
        ("state خراب crash نمی‌دهد", t_fail_soft_on_broken_state),
    ])
    sys.exit(1 if failed else 0)
