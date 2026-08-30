"""test_budget_judge — WAVE W1، معیارهای پذیرشِ §۸ قراردادِ GENOME LOCK.

چهار چیز باید **ساختاراً** غیرممکن باشد، نه قراردادی:
  ۱) رزروِ ۱۰٪ مالک به هیچ پایی برسد — با هیچ ورودی‌ای.
  ۲) یک پا بتواند همه‌چیز را ببلعد (runaway).
  ۳) فشارِ میزبان به لایهٔ **تندتر** ختم شود (باید یکنواخت کاهش یابد).
  ۴) ورودیِ خراب استثنا بدهد یا تخصیصِ رهاشده بسازد.

و یک قیدِ Heart v1: این ماژول هرگز نمی‌تواند DORMANT انتخاب کند — خوابِ کامل
فقط از مسیرِ مجازِ fail-closed می‌آید.
"""
import json
import math
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("budget-judge")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "heart")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib          # noqa: E402
import budget_judge as bj  # noqa: E402

_LIVE = {"lead": {"u": 0.9, "r": 0.0}, "mining": {"u": 0.3, "r": 0.2}}


# ─── ۱: رزروِ مالک تخطی‌ناپذیر ──────────────────────────────────────────────
def t_the_owner_reserve_can_never_be_allocated():
    """معیارِ پذیرشِ ۱. با **هر** ورودی، مجموع نباید از سهمِ ارگانیسم رد شود."""
    cases = [
        _LIVE,
        {"a": {"u": 1.0, "r": 0.0}},
        {f"leg{i}": {"u": 1.0, "r": 0.0} for i in range(50)},
        {"greedy": {"u": 1e9, "r": -1e9}},
        {"inf": {"u": float("inf"), "r": float("-inf")}},
        {"nan": {"u": float("nan"), "r": float("nan")}},
        {"neg": {"u": -5, "r": -5}},
        {"": {"u": 1.0, "r": 0.0}},
        {"x": "نه‌دیکشنری"},
        {},
        None,
    ]
    for sig in cases:
        alloc = bj.allocate(sig)
        total = sum(alloc.values()) if alloc else 0.0
        assert total <= bj.ORGANISM_SHARE + 1e-9, \
            f"رزروِ مالک خورده شد: total={total} با {str(sig)[:60]}"
        assert total >= 0.0
        for k, v in alloc.items():
            assert math.isfinite(v) and v >= 0.0, (k, v)


def t_a_giant_weight_cannot_eat_the_reserve():
    alloc = bj.allocate(_LIVE, weights={"lead": 1e12, "mining": 1e-12})
    assert sum(alloc.values()) <= bj.ORGANISM_SHARE + 1e-9, alloc
    assert alloc["lead"] <= bj.CEIL + 1e-9, alloc


def t_the_plan_always_declares_the_reserve():
    p = bj.plan(state={}, load={"cpu_pct": 10, "ram_pct": 10, "known": True},
                api={"headroom": 1.0, "known": True})
    assert p["owner_reserve"] == bj.OWNER_RESERVE == 0.10
    assert p["organism_share"] + p["owner_reserve"] == 1.0
    assert p["allocated_total"] <= p["organism_share"] + 1e-9


# ─── ۲: runaway غیرممکن ────────────────────────────────────────────────────
def t_no_single_organ_can_run_away():
    """معیارِ پذیرشِ ۳. حتی وقتی فقط یک پا سیگنال دارد، سقف رعایت می‌شود."""
    alloc = bj.allocate({"lead": {"u": 1.0, "r": 0.0}})
    assert alloc["lead"] <= bj.CEIL + 1e-9, alloc


def t_every_organ_gets_a_floor_or_nothing():
    """کفِ سهم یعنی هیچ پایی گرسنه رها نمی‌شود — یا سهم دارد یا اصلاً نیست."""
    alloc = bj.allocate({f"l{i}": {"u": 0.5, "r": 0.0} for i in range(6)})
    for k, v in alloc.items():
        assert v > 0.0, (k, v)


# ─── ۳: کاهشِ یکنواخت زیرِ فشار ─────────────────────────────────────────────
def t_more_pressure_never_yields_a_faster_layer():
    """معیارِ پذیرشِ ۲. یکنواختی: بارِ بیشتر → لایهٔ مساوی یا کندتر، هرگز تندتر."""
    order = {"L0": 0, "L1": 1, "L2": 2, "DORMANT": 3}
    prev = -1
    for cpu in range(0, 101, 5):
        layer, _ = bj.pulse_layer({"cpu_pct": cpu, "ram_pct": 0, "known": True}, 1.0)
        rank = order[layer]
        assert rank >= prev, f"cpu={cpu} لایه را تندتر کرد: {layer}"
        prev = rank


def t_the_hang_threshold_forces_scale_down():
    """معیارِ پذیرشِ ۲ صریح: بارِ خطرناک باید L2 بدهد."""
    for load in ({"cpu_pct": bj.CPU_MAX, "ram_pct": 0, "known": True},
                 {"cpu_pct": 0, "ram_pct": bj.RAM_MAX, "known": True},
                 {"cpu_pct": 99, "ram_pct": 99, "known": True}):
        layer, why = bj.pulse_layer(load, 1.0)
        assert layer == "L2", (load, layer)
        assert why, "دلیل ثبت نشد"


def t_low_api_headroom_also_slows_down():
    layer, _ = bj.pulse_layer({"cpu_pct": 0, "ram_pct": 0, "known": True}, 0.05)
    assert layer in ("L1", "L2"), layer


def t_this_module_can_never_choose_dormant():
    """Heart v1: خوابِ کامل فقط از مسیرِ مجازِ fail-closed، نه از قاضیِ بودجه."""
    for cpu in (0, 50, 99, 1e9):
        for ram in (0, 50, 99, 1e9):
            for h in (0.0, 0.5, 1.0):
                layer, _ = bj.pulse_layer(
                    {"cpu_pct": cpu, "ram_pct": ram, "known": True}, h)
                assert layer != "DORMANT", (cpu, ram, h)


# ─── ۴: totality — هیچ ورودی‌ای نباید بترکاند ──────────────────────────────
def t_hostile_input_never_raises():
    for load in ({}, None, {"cpu_pct": "خیلی"}, {"cpu_pct": float("nan")},
                 {"ram_pct": None}, {"cpu_pct": float("inf")}):
        for h in (None, "x", float("nan"), -1, 2):
            layer, why = bj.pulse_layer(load if isinstance(load, dict) else {}, h)
            assert layer in bj.PULSE_LAYERS and isinstance(why, str)


def t_plan_survives_a_missing_world():
    p = bj.plan(state={}, load={}, api={})
    assert p["schema"] == bj.SCHEMA
    assert isinstance(p["organ_pct"], dict)
    assert p["allocated_total"] <= p["organism_share"] + 1e-9
    assert p["reasons"], "نقشه بدونِ دلیل ساخته شد"


def t_clamp01_is_total():
    for v in (None, "x", float("nan"), float("inf"), float("-inf"), -5, 5, 0.5):
        out = bj.clamp01(v)
        assert 0.0 <= out <= 1.0 and math.isfinite(out), (v, out)


# ─── ۵: dry-run پیش‌فرض، نوشتن فقط با فلگ ──────────────────────────────────
def t_default_is_dry_run_and_writes_nothing():
    """معیارِ پذیرشِ ۴: فلگ خاموش → رفتارِ ارگانیسم بایت‌به‌بایت."""
    os.environ.pop(bj.FLAG, None)
    for p in (bj.PLAN_PATH, bj.LEDGER_PATH):
        try:
            p.unlink()
        except OSError:
            pass
    r = bj.emit()
    assert r["ok"] and r["written"] is False, r
    assert not bj.PLAN_PATH.exists() and not bj.LEDGER_PATH.exists()
    assert r["plan"]["dry_run"] is True


def t_armed_writes_atomically_with_a_hash_chain():
    """معیارِ پذیرشِ ۵: با فلگ، هر بیت یک نقشه."""
    os.environ[bj.FLAG] = "1"
    try:
        for p in (bj.PLAN_PATH, bj.LEDGER_PATH):
            try:
                p.unlink()
            except OSError:
                pass
        a = bj.emit()
        assert a["written"] is True and a["plan"]["dry_run"] is False
        assert bj.PLAN_PATH.exists()
        b = bj.emit()
        assert b["plan"]["prev_sha256"], "زنجیرهٔ hash بسته نشد"
        rows = [json.loads(x) for x in
                bj.LEDGER_PATH.read_text("utf-8").splitlines() if x.strip()]
        assert len(rows) == 2, rows
        assert rows[0].get("prev_sha256") == ""
        assert rows[1]["prev_sha256"] != ""
        assert not bj.PLAN_PATH.with_suffix(".json.tmp").exists(), "فایلِ موقت ماند"
    finally:
        os.environ.pop(bj.FLAG, None)


def t_a_read_only_disk_does_not_kill_the_judge():
    """قضاوت باید انجام شود حتی وقتی ثبت نمی‌شود — fail-soft، با آلارم."""
    os.environ[bj.FLAG] = "1"
    real = bj.PLAN_PATH
    try:
        bj.PLAN_PATH = Path("Z:/nope/budget-plan.json")
        r = bj.emit()
        assert r["written"] is False, r
        assert r["plan"]["schema"] == bj.SCHEMA, "قضاوت هم از بین رفت"
    finally:
        bj.PLAN_PATH = real
        os.environ.pop(bj.FLAG, None)


# ─── ۶: مرزِ معماری ────────────────────────────────────────────────────────
def t_the_judge_never_writes_the_pulse_period():
    """Heart v1: Awareness هرگز periodِ خام را نمی‌نویسد — فقط لایه پیشنهاد می‌دهد."""
    src = Path(bj.__file__).read_text("utf-8")
    for forbidden in ("period_s =", "CHRONO_PERIOD", "heart_set_apply",
                      "cardiac-budget.json"):
        assert forbidden not in src, f"قاضیِ بودجه ضربان را مستقیم دست می‌زند: {forbidden}"


def t_the_judge_does_not_act_only_judges():
    import ast
    tree = ast.parse(Path(bj.__file__).read_text("utf-8"))
    banned = {"subprocess", "urllib", "requests", "socket"}
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (banned & imported), sorted(banned & imported)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_budget_judge: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
