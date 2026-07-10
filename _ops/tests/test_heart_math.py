"""test_heart_math.py — HH-P0: قفلِ ریاضیِ SOG (اعتبارسنجیِ مستقلِ MC).

Gate-A: بازتولیدِ anchorها + DARE crosscheck + شاهدِ MCِ هسته (قراردادِ ۵٪) +
شاهدِ نویِ E_shadow + شاهدِ دنبالهٔ S_L برای I_pred + ساختاری (بدونِ importِ پول،
بدونِ literalِ anchor در مسیرِ production). همه‌چیز deterministic (seedهای ثابت).
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))            # _ops/
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("heart-math")   # env قبل از importِ opslib-خورها (ایزولاسیون)

from heart import sog_math as sm    # noqa: E402

# خروجی‌های شاهد یک‌بار محاسبه می‌شوند (deterministic؛ اندازهٔ تستی)
CORE = sm.mc_witness_core(T=120_000)
IPRED = sm.mc_witness_i_pred(n_windows=8_000)
DARE = sm.dare_crosscheck(n_draws=60)
GATES = sm.evaluate_gates(CORE, IPRED, DARE)


def t_anchors_reproduced():
    """هر ۱۱ anchorِ منتشرشدهٔ synthesis §C با خطای نسبی <5e-4 بازتولید شود."""
    assert GATES["anchors"]["ok"], GATES["anchors"]["rel_errs"]
    worst = max(GATES["anchors"]["rel_errs"].values())
    assert worst < 5e-4, f"بدترین anchor rel_err={worst}"


def t_sigma_z2_from_primitives():
    """Gate-A: σ_z² از primitiveها ساخته می‌شود نه literal — تغییرِ sd باید σ_z² را ببرد."""
    a = sm.solve_floors(0.5, 0.5, 0.1, 0.05, 0.1)["sigma_z2"]
    b = sm.solve_floors(0.5, 0.5, 0.1, 0.05, 0.2)["sigma_z2"]
    assert b > a, "σ_z² به primitiveها حساس نیست — literal مشکوک"


def t_dare_crosscheck():
    """closed-form در برابرِ fixed-point: بیشینهٔ خطای نسبی <1e-9."""
    assert GATES["dare_crosscheck"]["ok"], DARE


def t_mc_core_five_checks():
    """Var(ν)/Var(ν_b)/corr²/mean(ex)/Var(ex) همه در ۵٪ (قراردادِ مالک)."""
    assert GATES["mc_core"]["ok"], GATES["mc_core"]["rel_errs"]


def t_e_shadow_witness():
    """شاهدِ نو (کاری که 4.py نکرده): گپِ log-lossِ null-vs-blind + Var(z)≈σ_z²."""
    w = GATES["e_shadow_witness"]
    assert w["var_z_ok"], f"Var(z) دور از σ_z²: {w['var_z_rel_err']}"
    assert w["logloss_gap"]["ok"], w["logloss_gap"]
    assert GATES["e_shadow_locked"] is True


def t_i_pred_sequence_witness():
    """دنبالهٔ S_L (جوهرِ I_pred) تجربی≈تحلیلی در هر offset + دُم→S_b."""
    w = GATES["i_pred_witness"]
    bad = [x for x in w["seq"] if not x["ok"]]
    assert not bad, bad
    assert w["tail_ok"]
    assert GATES["i_pred_locked"] is True


def t_identity_chain_rule():
    """اتحاد: ½log(σ_z²/S) = E_shadow + Δ_self (بسته‌شدنِ عددی)."""
    fl = sm.solve_floors(**sm.CANONICAL)
    lhs = sm.identity_total(fl)
    rhs = sm.e_shadow(fl) + sm.delta_self(fl)
    assert abs(lhs - rhs) < 1e-12


def t_identifiability():
    """E_shadow>0 ⟺ λ·ρ≠0؛ ρ=0 یا λ=0 → E_shadow=0 دقیق."""
    z1 = sm.e_shadow(sm.solve_floors(0.0, 0.5, 0.1, 0.05, 0.1))
    z2 = sm.e_shadow(sm.solve_floors(0.5, 0.0, 0.1, 0.05, 0.1))
    pos = sm.e_shadow(sm.solve_floors(0.5, 0.5, 0.1, 0.05, 0.1))
    assert abs(z1) < 1e-12 and abs(z2) < 1e-12 and pos > 0


def t_lock_file_shape_and_honesty():
    """run_lock (کوچک، در vault موقتِ تست): schema + وضعیتِ un-collapsible + provenance."""
    out = Path(ENV["OPS_DIR"]) / "state" / "sim" / "PULSE-EQUATIONS-LOCKED.json"
    rec = sm.run_lock(out_path=out, full=False, write=True)
    assert out.exists()
    on_disk = json.loads(out.read_text("utf-8"))
    assert on_disk["schema"] == "PULSE-EQUATIONS-LOCKED.v1"
    for k in ("delta_self", "e_shadow", "i_pred"):
        assert on_disk["status"][k] in ("locked", "excluded-unlocked")
    assert on_disk["status"]["i_pred_gates_nothing"] is True
    assert on_disk["provenance"]["code_sha256"] not in ("", "unavailable")
    assert on_disk["full_run"] is False   # صادق: این lockِ تستی است نه رسمی
    # read_lock همان را برگرداند؛ مسیرِ غایب → {}
    assert sm.read_lock(out)["schema"] == "PULSE-EQUATIONS-LOCKED.v1"
    assert sm.read_lock(Path(ENV["OPS_DIR"]) / "state" / "no-such.json") == {}


def t_structural_no_money_imports_no_anchor_literals():
    """ساختاری: هیچ importِ پول/گیت؛ هیچ literalِ anchor در مسیرِ محاسبه."""
    src = Path(sm.__file__).read_text("utf-8")
    for bad in ("import organ_gate", "import money_gate", "import budget_gate",
                "import chrono", "from organ_gate", "from money_gate"):
        assert bad not in src, f"import ممنوع: {bad}"
    # literalهای anchor فقط در دیکشنریِ PUBLISHED_ANCHORS (witness) مجازند
    body_after = src.split("PUBLISHED_ANCHORS", 2)[-1]
    payload = body_after.split("}", 1)[1]   # بعد از بسته‌شدنِ دیکشنری
    for lit in ("0.122520", "0.804719", "0.012553", "0.0144179"):
        assert lit not in payload, f"literal anchor در مسیرِ محاسبه: {lit}"


def t_failed_witness_reports_excluded():
    """صداقت: اگر شاهد شکست بخورد، وضعیت excluded-unlocked شود نه سبزِ دروغ."""
    fake_core = json.loads(json.dumps(CORE))
    fake_core["emp"]["var_z"] = fake_core["theory"]["var_z"] * 1.5   # خرابِ عمدی
    g = sm.evaluate_gates(fake_core, IPRED, DARE)
    assert g["e_shadow_locked"] is False
    assert g["delta_self_locked"] is True    # خرابیِ E_shadow دلتا را آلوده نمی‌کند


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run([(n, f) for n, f in checks])
    print(f"\n{'✅' if not failed else '❌'} test_heart_math: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
