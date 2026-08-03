#!/usr/bin/env python3
"""sog_math.py — HH-P0: قفلِ ریاضیِ SOG با اعتبارسنجیِ مستقلِ Monte-Carlo.

4.py مالک فقط Δ_self/S/S_b/Var_ex را MC کرده؛ E_shadow و I_pred فقط تحلیلی بودند
(SOG-Synthesis §C: draft/conflicting). این ماژول هر سه را با forward-simulation مستقل
(stdlib RNG — عمداً غیرِ numpy؛ استقلالِ مسیرِ عددی ویژگی است) شاهد می‌گیرد و نتیجه را
در lock-file می‌نویسد: `_ops/state/sim/PULSE-EQUATIONS-LOCKED.json` (نامِ Gate-A از M-HEART).

مدل مرجع: s(t+1)=ρ·s(t)+m(t)+ζ(t) · Y(t)=b(t)+λ·s(t)+ε(t) · b≡0، m=ditherِ N(0,σ_d²).
سه کف: σ_z² (null/iid) ⊃ S_b (blind، نویزِ مؤثر σ_ζ²+σ_d²) ⊃ S (informed، m را می‌داند).

معیارِ صادق: هر شاهد یا در tolerance می‌گذرد یا آن کمیت excluded-unlocked می‌ماند —
هرگز tolerance برای سبزشدن شل نمی‌شود. برای کمیت‌های ریزِ log-gap، گیتِ آماری
`|emp−theory| ≤ max(rel_tol·|theory|, 4·SE)` است تا از MC دقتی بیش از توانش نخواهیم.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import random
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # _ops/heart
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

# نقطهٔ کار canonical (SOG-Synthesis §C — از primitiveها، نه literalِ نتیجه)
CANONICAL = {"rho": 0.5, "lam": 0.5, "se": 0.1, "sz": 0.05, "sd": 0.1}
LOCK_PATH_DEFAULT = opslib.STATE_DIR / "sim" / "PULSE-EQUATIONS-LOCKED.json"
SOURCE_4PY = Path(os.environ.get("SOG_4PY_PATH", r"C:\Users\Armin\Desktop\4D\4.py"))

# anchorهای شاهدِ منتشرشده (۶ رقم اعشارِ synthesis §C) — فقط برای تستِ بازتولید،
# هرگز در مسیرِ محاسبه. tolerance 5e-4: جذبِ گردکردنِ نشر، نه شل‌کردنِ ریاضی.
PUBLISHED_ANCHORS = {
    "P": 0.00325184, "S": 0.01081296, "P_b": 0.01526172, "S_b": 0.01381543,
    "sigma_z2": 0.0141667, "delta_self": 0.122520, "e_shadow": 0.012553,
    "identity": 0.135073, "i_pred": 0.0144179, "var_ex": 0.217327,
    "ceiling": 0.804719,
}


# ─── هستهٔ تحلیلی (از primitiveها) ───────────────────────────────────────────────
def p_closed(rho: float, lam: float, se2: float, sz2: float) -> float:
    """حل بسته‌شکلِ DAREِ اسکالر (بازتولید مستقل از 4.py/core.model)."""
    if lam == 0.0:
        return sz2 / (1.0 - rho * rho)
    c = se2 * (1.0 - rho * rho)
    disc = (c - sz2 * lam * lam) ** 2 + 4.0 * lam * lam * sz2 * se2
    return ((sz2 * lam * lam - c) + math.sqrt(disc)) / (2.0 * lam * lam)


def p_iter(rho: float, lam: float, se2: float, sz2: float, iters: int = 8000) -> float:
    """همان DARE با fixed-point iteration — چکِ متقاطعِ closed-form (بلاک ۱ 4.py)."""
    P = sz2
    for _ in range(iters):
        S = lam * lam * P + se2
        P = rho * rho * P * se2 / S + sz2
    return P


def solve_floors(rho: float, lam: float, se: float, sz: float, sd: float) -> dict:
    """سه کفِ اطلاعاتی + گین‌ها، همه از primitiveها (σ_z² literal ممنوع — Gate-A)."""
    se2, sz2, sd2 = se * se, sz * sz, sd * sd
    szp2 = sz2 + sd2
    P = p_closed(rho, lam, se2, sz2)
    S = lam * lam * P + se2
    K = P * lam / S if S else 0.0
    Pb = p_closed(rho, lam, se2, szp2)
    Sb = lam * lam * Pb + se2
    Kb = Pb * lam / Sb if Sb else 0.0
    sigma_z2 = lam * lam * szp2 / (1.0 - rho * rho) + se2
    return {"P": P, "S": S, "K": K, "P_b": Pb, "S_b": Sb, "K_b": Kb,
            "sigma_z2": sigma_z2, "se2": se2, "sz2": sz2, "sd2": sd2, "szp2": szp2}


def delta_self(fl: dict) -> float:
    """Δ_self = ½·log(S_b/S) — ارزشِ دسترسیِ اول‌شخص [nat/گام]."""
    return 0.5 * math.log(fl["S_b"] / fl["S"])


def e_shadow(fl: dict) -> float:
    """E_shadow = ½·log(σ_z²/S_b) — دیدپذیریِ سایه [nat/گام]."""
    return 0.5 * math.log(fl["sigma_z2"] / fl["S_b"])


def identity_total(fl: dict) -> float:
    """اتحادِ زنجیره: ½·log(σ_z²/S) = E_shadow + Δ_self."""
    return 0.5 * math.log(fl["sigma_z2"] / fl["S"])


def var_excess(fl: dict) -> float:
    """Var(excess) = 1 − S/S_b."""
    return 1.0 - fl["S"] / fl["S_b"]


def delta_self_ceiling(sz: float, sd: float) -> float:
    """سقفِ Δ_self در λ→∞: ½·ln(1+σ_d²/σ_ζ²)."""
    return 0.5 * math.log(1.0 + (sd * sd) / (sz * sz))


def i_pred_riccati(rho: float, lam: float, se: float, sz: float, sd: float,
                   n_terms: int = 50) -> dict:
    """I_pred = ½·Σ_{L≥0} log(S_L/S_b) — excess entropy با Riccatiِ زمان‌متغیر
    (فیلترِ blind از priorِ stationary). خروجی: total + دنبالهٔ S_L (برای شاهدِ MC)."""
    se2 = se * se
    szp2 = sz * sz + sd * sd
    fl = solve_floors(rho, lam, se, sz, sd)
    Sb = fl["S_b"]
    P = szp2 / (1.0 - rho * rho)      # واریانسِ stationary حالتِ blind
    total, terms, s_seq = 0.0, [], []
    for _ in range(n_terms):
        S_L = lam * lam * P + se2
        s_seq.append(S_L)
        term = 0.5 * math.log(S_L / Sb)
        terms.append(term)
        total += term
        P = rho * rho * P * se2 / S_L + szp2
        if abs(term) < 1e-12:
            break
    return {"total": total, "terms": terms, "s_seq": s_seq, "S_b": Sb}


# ─── شاهدهای Monte-Carlo (مستقل: RNGِ stdlib، پیاده‌سازیِ از-نو) ─────────────────
def dare_crosscheck(n_draws: int = 300, seed: int = 7) -> dict:
    """closed-form در برابرِ iteration روی قرعه‌های تصادفی — بیشینهٔ خطای نسبی."""
    rng = random.Random(seed)
    worst = 0.0
    for _ in range(n_draws):
        rho = rng.uniform(0.05, 0.95)
        lam = rng.uniform(0.05, 2.0)
        se2 = rng.uniform(1e-4, 0.05)
        sz2 = rng.uniform(1e-5, 0.05)
        pc = p_closed(rho, lam, se2, sz2)
        pi = p_iter(rho, lam, se2, sz2)
        worst = max(worst, abs(pc - pi) / pc)
    return {"n_draws": n_draws, "seed": seed, "max_rel_err": worst}


def mc_witness_core(rho: float = None, lam: float = None, se: float = None,
                    sz: float = None, sd: float = None,
                    T: int = 1_200_000, burn: int = 4000, seed: int = 123) -> dict:
    """بازتولیدِ مستقلِ بلاک MCِ 4.py + شاهدِ نویِ E_shadow روی همان مسیر.

    دوقلوی Kalman (informed سیاستِ dither را می‌داند؛ blind فقط میانگینِ صفر) +
    excessِ per-step برای Δ_self و excessِ null-در-برابر-blind برای E_shadow."""
    c = CANONICAL
    rho = c["rho"] if rho is None else rho
    lam = c["lam"] if lam is None else lam
    se = c["se"] if se is None else se
    sz = c["sz"] if sz is None else sz
    sd = c["sd"] if sd is None else sd
    fl = solve_floors(rho, lam, se, sz, sd)
    S, K, Sb, Kb, sigma_z2 = fl["S"], fl["K"], fl["S_b"], fl["K_b"], fl["sigma_z2"]
    lnr = 0.5 * math.log(Sb / S)
    lnr_shadow = 0.5 * math.log(sigma_z2 / Sb)
    rng = random.Random(seed)
    gauss = rng.gauss
    s_ = sh = shb = 0.0
    n = 0
    s_nu = s_nu2 = s_nub = s_nub2 = s_x = 0.0
    s_ex = s_ex2 = s_exs = s_exs2 = 0.0
    s_z = s_z2 = 0.0
    for t in range(T + burn):
        m = gauss(0.0, sd)
        z = lam * s_ + gauss(0.0, se)
        nu = z - lam * sh
        nub = z - lam * shb
        if t >= burn:
            n += 1
            ex = lnr + nub * nub / (2.0 * Sb) - nu * nu / (2.0 * S)
            exs = lnr_shadow + z * z / (2.0 * sigma_z2) - nub * nub / (2.0 * Sb)
            s_nu += nu; s_nu2 += nu * nu
            s_nub += nub; s_nub2 += nub * nub
            s_x += nu * nub
            s_ex += ex; s_ex2 += ex * ex
            s_exs += exs; s_exs2 += exs * exs
            s_z += z; s_z2 += z * z
        s_ = rho * s_ + m + gauss(0.0, sz)
        sh = rho * (sh + K * nu) + m
        shb = rho * (shb + Kb * nub)

    def _mv(sm, sm2):
        mean = sm / n
        return mean, sm2 / n - mean * mean

    m_nu, v_nu = _mv(s_nu, s_nu2)
    m_nub, v_nub = _mv(s_nub, s_nub2)
    m_ex, v_ex = _mv(s_ex, s_ex2)
    m_exs, v_exs = _mv(s_exs, s_exs2)
    m_z, v_z = _mv(s_z, s_z2)
    corr2 = ((s_x / n - m_nu * m_nub) ** 2) / (v_nu * v_nub)
    return {
        "T": n, "burn": burn, "seed": seed,
        "emp": {"var_nu": v_nu, "var_nub": v_nub, "corr2": corr2,
                "mean_ex": m_ex, "var_ex": v_ex,
                "mean_exs": m_exs, "var_z": v_z},
        "theory": {"var_nu": S, "var_nub": Sb, "corr2": S / Sb,
                   "mean_ex": lnr, "var_ex": var_excess(fl),
                   "mean_exs": lnr_shadow, "var_z": sigma_z2},
        "se": {"mean_ex": math.sqrt(v_ex / n), "mean_exs": math.sqrt(v_exs / n)},
    }


def mc_witness_i_pred(rho: float = None, lam: float = None, se: float = None,
                      sz: float = None, sd: float = None,
                      n_windows: int = 50_000, l_max: int = 10,
                      tail_from: int = 30, window_len: int = 40,
                      seed: int = 2026) -> dict:
    """شاهدِ MCِ دنبالهٔ S_L (جوهرِ I_pred): پنجره‌های مستقل، فیلترِ blindِ سردشروع
    از priorِ stationary؛ واریانسِ تجربیِ innovation در هر offsetِ L باید S_Lِ Riccati
    باشد؛ دُمِ همگرا (L≥tail_from) باید S_b باشد."""
    c = CANONICAL
    rho = c["rho"] if rho is None else rho
    lam = c["lam"] if lam is None else lam
    se = c["se"] if se is None else se
    sz = c["sz"] if sz is None else sz
    sd = c["sd"] if sd is None else sd
    se2 = se * se
    szp2 = sz * sz + sd * sd
    prior = szp2 / (1.0 - rho * rho)
    rng = random.Random(seed)
    gauss = rng.gauss
    sums = [0.0] * (l_max + 1)
    sums2 = [0.0] * (l_max + 1)
    tail_sum = tail_sum2 = 0.0
    tail_n = 0
    sd_prior = math.sqrt(prior)
    for _ in range(n_windows):
        s_ = gauss(0.0, sd_prior)      # شروع از توزیعِ stationary (شاملِ dither)
        sh = 0.0
        P = prior
        for L in range(window_len):
            z = lam * s_ + gauss(0.0, se)
            nu = z - lam * sh
            S_L = lam * lam * P + se2
            if L <= l_max:
                sums[L] += nu
                sums2[L] += nu * nu
            elif L >= tail_from:
                tail_sum += nu
                tail_sum2 += nu * nu
                tail_n += 1
            K_L = P * lam / S_L
            sh = rho * (sh + K_L * nu)
            P = rho * rho * P * se2 / S_L + szp2
            s_ = rho * s_ + gauss(0.0, sd) + gauss(0.0, sz)
    emp_seq = []
    for L in range(l_max + 1):
        mean = sums[L] / n_windows
        emp_seq.append(sums2[L] / n_windows - mean * mean)
    tmean = tail_sum / tail_n
    emp_tail = tail_sum2 / tail_n - tmean * tmean
    ana = i_pred_riccati(rho, lam, se, sz, sd)
    return {"n_windows": n_windows, "l_max": l_max, "seed": seed,
            "emp_s_seq": emp_seq, "analytic_s_seq": ana["s_seq"][: l_max + 1],
            "emp_tail_var": emp_tail, "S_b": ana["S_b"],
            "i_pred_analytic": ana["total"]}


# ─── گیت‌ها و قفل ───────────────────────────────────────────────────────────────
def _rel(a: float, b: float) -> float:
    return abs(a - b) / abs(b) if b else abs(a - b)


def _stat_gate(emp: float, theory: float, se_: float, rel_tol: float) -> dict:
    """گیتِ صادق برای کمیتِ ریز: پاس اگر در rel_tol یا در 4·SE (هرکدام گشادتر)."""
    err = abs(emp - theory)
    lim = max(rel_tol * abs(theory), 4.0 * se_)
    return {"emp": emp, "theory": theory, "abs_err": err, "limit": lim,
            "rel_err": _rel(emp, theory), "se": se_, "ok": err <= lim}


def evaluate_gates(core: dict, ipred: dict, dare: dict) -> dict:
    """همهٔ گیت‌های Gate-A روی خروجی‌های شاهد. هیچ side-effect."""
    fl = solve_floors(**CANONICAL)
    gates: dict = {}
    # ۱) DARE closed-form vs iteration
    gates["dare_crosscheck"] = {"max_rel_err": dare["max_rel_err"],
                                "ok": dare["max_rel_err"] < 1e-9}
    # ۲) بازتولیدِ anchorهای منتشرشده (گردکردنِ نشر → 5e-4)
    computed = {
        "P": fl["P"], "S": fl["S"], "P_b": fl["P_b"], "S_b": fl["S_b"],
        "sigma_z2": fl["sigma_z2"], "delta_self": delta_self(fl),
        "e_shadow": e_shadow(fl), "identity": identity_total(fl),
        "i_pred": i_pred_riccati(**CANONICAL)["total"],
        "var_ex": var_excess(fl),
        "ceiling": delta_self_ceiling(CANONICAL["sz"], CANONICAL["sd"]),
    }
    anchor_errs = {k: _rel(computed[k], PUBLISHED_ANCHORS[k]) for k in computed}
    gates["anchors"] = {"rel_errs": anchor_errs, "computed": computed,
                        "ok": max(anchor_errs.values()) < 5e-4}
    # ۳) هستهٔ MC (قراردادِ ۵٪ مالک — verify_against_model)
    e, th = core["emp"], core["theory"]
    core_checks = {k: _rel(e[k], th[k]) for k in ("var_nu", "var_nub", "corr2",
                                                  "mean_ex", "var_ex")}
    gates["mc_core"] = {"rel_errs": core_checks,
                       "ok": max(core_checks.values()) < 0.05}
    # ۴) شاهدِ E_shadow — سه‌پایه: Var(z) تنگ + Var(ν_b) (در هسته) + گپِ log-loss آماری
    var_z_ok = _rel(e["var_z"], th["var_z"]) < 0.02
    exs_gate = _stat_gate(e["mean_exs"], th["mean_exs"], core["se"]["mean_exs"], 0.05)
    gates["e_shadow_witness"] = {"var_z_rel_err": _rel(e["var_z"], th["var_z"]),
                                 "var_z_ok": var_z_ok, "logloss_gap": exs_gate,
                                 "ok": var_z_ok and exs_gate["ok"]}
    # ۵) شاهدِ I_pred — دنبالهٔ S_L در max(2.5%, 4·SE_var) + دُمِ S_b
    W = ipred["n_windows"]
    seq_checks = []
    for L, (emp_v, ana_v) in enumerate(zip(ipred["emp_s_seq"],
                                           ipred["analytic_s_seq"])):
        se_var = ana_v * math.sqrt(2.0 / W)      # SE واریانسِ نمونه برای گاوسی
        lim = max(0.025 * ana_v, 4.0 * se_var)
        seq_checks.append({"L": L, "emp": emp_v, "analytic": ana_v,
                           "ok": abs(emp_v - ana_v) <= lim})
    tail_ok = _rel(ipred["emp_tail_var"], ipred["S_b"]) < 0.025
    gates["i_pred_witness"] = {"seq": seq_checks, "tail_ok": tail_ok,
                               "ok": all(x["ok"] for x in seq_checks) and tail_ok}
    # جمع‌بندی — وضعیتِ un-collapsible per کمیت
    gates["delta_self_locked"] = gates["mc_core"]["ok"] and gates["anchors"]["ok"] \
        and gates["dare_crosscheck"]["ok"]
    gates["e_shadow_locked"] = bool(gates["e_shadow_witness"]["ok"]
                                    and gates["delta_self_locked"])
    gates["i_pred_locked"] = bool(gates["i_pred_witness"]["ok"]
                                  and gates["delta_self_locked"])
    return gates


# ─── C8: اصالتِ صادق — «قابلِ راستی‌آزمایی» یعنی هش، نه رشتهٔ حاضر ───────────────
UNAVAILABLE = "unavailable"          # خروجیِ _sha256_file روی OSError
PROV_VERIFIED = "VERIFIED"
PROV_MISMATCH = "MISMATCH"
PROV_UNVERIFIABLE = "UNVERIFIABLE"
LOCK_STATE_KEY = "lock_state"
LOCK_UNKNOWN = "UNKNOWN"
_HEXDIGITS = frozenset("0123456789abcdef")


class ProvenanceUnverifiable(RuntimeError):
    """اصالتِ منبع قابلِ راستی‌آزمایی نیست ⇒ قفل **نوشته نمی‌شود**."""

    def __init__(self, digest: object, path: object) -> None:
        self.digest = digest
        self.path = path
        super().__init__(
            f"source_4py_sha256={digest!r} (path={path}) قابلِ راستی‌آزمایی نیست — "
            "lock نوشته نشد (fail-closed)")


def is_verifiable_digest(value: object) -> bool:
    """فقط sha256ِ ۶۴نویسه‌ایِ hex «قابلِ راستی‌آزمایی» است.

    رشتهٔ لفظیِ `"unavailable"` **صریحاً** رد می‌شود (ردِ صریح مقدم بر چکِ طول تا نیت
    خوانده شود): آن مقدار truthy و غیرِ null است، پس هم گاردِ «null نباشد» و هم گاردِ
    «کلید حاضر باشد» از کنارش رد می‌شوند و قفلی نوشته می‌شود که هنوز سه گیت را
    `locked` نشان می‌دهد — همان سبزِ کاذبی که C8 می‌بندد."""
    if not isinstance(value, str):
        return False
    s = value.strip().lower()
    if s == UNAVAILABLE:
        return False
    return len(s) == 64 and set(s) <= _HEXDIGITS


def _sha256_file(p: Path) -> str:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return UNAVAILABLE


def source_4py_path() -> Path:
    """مسیرِ 4.py در **لحظهٔ فراخوانی** (env برنده)؛ SOURCE_4PY فقط پیش‌فرضِ ماژول است."""
    return Path(os.environ.get("SOG_4PY_PATH") or str(SOURCE_4PY))


def source_provenance(lock: dict | None = None, source: Path | None = None) -> str:
    """برچسبِ اصالتِ 4.py در برابرِ هشِ ثبت‌شده در خودِ قفل. هرگز استثنا نمی‌دهد.

    VERIFIED فقط اگر فایل باشد **و** دقیقاً به هشِ ثبت‌شده بخورد؛ MISMATCH اگر باشد و
    نخورد (پس یک 4.pyِ بازیابی‌شده از نسخه‌ای ناشناخته نمی‌تواند سبزِ کاذب بسازد)؛
    در بقیهٔ حالت‌ها UNVERIFIABLE. هشِ مرجع از قفل خوانده می‌شود، هیچ‌جا hardcode نیست."""
    try:
        rec = read_lock() if lock is None else lock
        recorded = ((rec or {}).get("provenance") or {}).get("source_4py_sha256")
        if not is_verifiable_digest(recorded):
            return PROV_UNVERIFIABLE
        p = source if source is not None else source_4py_path()
        if not p.exists():
            return PROV_UNVERIFIABLE
        actual = _sha256_file(p)
        if not is_verifiable_digest(actual):
            return PROV_UNVERIFIABLE
        if actual.strip().lower() != recorded.strip().lower():
            return PROV_MISMATCH
        return PROV_VERIFIED
    except Exception:  # noqa: BLE001 — برچسبِ اصالت هرگز ضربان را نمی‌کشد
        return PROV_UNVERIFIABLE


def run_lock(out_path: Path | None = None, full: bool = True,
             write: bool = True) -> dict:
    """اجرای کاملِ Gate-A و نوشتنِ lock-file (اتمیک) + NOTE به ledger.
    full=False فقط برای توسعه/تست — lock واقعی همیشه با full=True.

    **fail-closed (C8):** اگر هشِ منبع قابلِ راستی‌آزمایی نباشد، `ProvenanceUnverifiable`
    می‌دهد — پیش از هر MC و پیش از هر نوشتن، پس قفلِ موجود بایت‌به‌بایت دست‌نخورده
    می‌ماند. قفلی که اصالتش قابلِ اثبات نیست، نباید سه گیت را `locked` اعلام کند."""
    src_path = source_4py_path()
    src_digest = _sha256_file(src_path)
    if not is_verifiable_digest(src_digest):
        raise ProvenanceUnverifiable(src_digest, src_path)
    T = 1_200_000 if full else 120_000
    n_windows = 50_000 if full else 8_000
    core = mc_witness_core(T=T)
    ipred = mc_witness_i_pred(n_windows=n_windows)
    dare = dare_crosscheck(n_draws=300 if full else 60)
    gates = evaluate_gates(core, ipred, dare)
    fl = solve_floors(**CANONICAL)
    record = {
        "ts": opslib.now_iso(),
        "schema": "PULSE-EQUATIONS-LOCKED.v1",
        "full_run": full,
        "operating_point": CANONICAL,
        "floors": {k: fl[k] for k in ("P", "S", "K", "P_b", "S_b", "K_b", "sigma_z2")},
        "values": gates["anchors"]["computed"],
        "gates": gates,
        "status": {
            "delta_self": "locked" if gates["delta_self_locked"] else "excluded-unlocked",
            "e_shadow": "locked" if gates["e_shadow_locked"] else "excluded-unlocked",
            "i_pred": "locked" if gates["i_pred_locked"] else "excluded-unlocked",
            "i_pred_gates_nothing": True,      # M-HEART: I_pred هرگز authorization نیست
        },
        "mc": {"core_T": core["T"], "core_seed": core["seed"],
               "ipred_windows": ipred["n_windows"], "ipred_seed": ipred["seed"],
               "dare": dare},
        "provenance": {
            "code_sha256": _sha256_file(Path(__file__)),
            "source_4py_sha256": src_digest,   # گاردِ بالا تضمین کرده hexِ ۶۴نویسه‌ای است
            "method": "independent stdlib-RNG forward-simulation (نه بازاجرای numpy)",
        },
    }
    if write:
        out = out_path or LOCK_PATH_DEFAULT
        out.parent.mkdir(parents=True, exist_ok=True)
        with opslib.LockedJson(out) as lj:
            lj.write(record)
        opslib.ledger_note("SOG_MATH_LOCK", {
            "e_shadow": record["status"]["e_shadow"],
            "i_pred": record["status"]["i_pred"],
            "delta_self": record["status"]["delta_self"],
            "full_run": full, "lock_file": str(out.name),
        }, actor="heart-sog-math")
    return record


def _lock_unknown(p: Path, reason: str) -> dict:
    """نشانگرِ صریحِ «ورودی غایب است» — نه {}، نه صفر، نه سبز."""
    return {LOCK_STATE_KEY: LOCK_UNKNOWN, "reason": reason, "path": str(p)}


def lock_is_unknown(lock: dict | None) -> bool:
    """آیا این خروجیِ read_lock به‌جای قفل، نشانگرِ UNKNOWN است؟"""
    return isinstance(lock, dict) and lock.get(LOCK_STATE_KEY) == LOCK_UNKNOWN


def read_lock(path: Path | None = None) -> dict:
    """خواندنِ lock-file. غایب/خراب → نشانگرِ صریحِ **UNKNOWN**، نه `{}`.

    fail-softِ قبلی یک ورودیِ **غایب** را به ورودیِ **تهی** ترجمه می‌کرد و پایین‌دست
    آن را «مشکلی نیست» می‌خواند. حالا غیاب یک نوع دارد. مسیرِ موفق دست‌نخورده است —
    رکورد بی‌هیچ کلیدِ تزریقی برمی‌گردد، پس هیچ مصرف‌کننده‌ای تغییرِ عددی نمی‌بیند
    (`lock.get("status")` روی UNKNOWN هم مثل قبل None می‌دهد ⇒ همان fail-closed)."""
    p = path or LOCK_PATH_DEFAULT
    try:
        if not p.exists():
            return _lock_unknown(p, "missing")
        rec = json.loads(p.read_text("utf-8"))
    except (OSError, ValueError) as e:
        return _lock_unknown(p, type(e).__name__)
    if not isinstance(rec, dict):
        return _lock_unknown(p, "not-a-mapping")
    return rec


if __name__ == "__main__":
    try:
        rec = run_lock(full=True)
    except ProvenanceUnverifiable as e:      # fail-closed: قفلِ روی دیسک دست نخورد
        print(json.dumps({"error": "provenance_unverifiable", "detail": str(e),
                          "lock_written": False,
                          "sog_provenance": source_provenance()},
                         ensure_ascii=False, indent=2))
        sys.exit(2)
    print(json.dumps({"status": rec["status"],
                      "gates_ok": {k: v for k, v in rec["gates"].items()
                                   if k.endswith("_locked")}},
                     ensure_ascii=False, indent=2))
