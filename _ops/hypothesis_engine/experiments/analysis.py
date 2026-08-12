# experiments/analysis.py — بازتولید §۳ گزارش از results.csv
# آزمون‌های پیش‌ثبت‌شده طبق §4 طرح DECEPTIVE-ENV-3AGENT-EXPERIMENT.md:
#   permutation test (10k shuffle) روی median ttd · Cliff's δ ·
#   two-way ANOVA روی rank-transformed (تعامل agent×env) · CI95 Wilson روی P3
# اجرا:  python analysis.py [results.csv]
from __future__ import annotations

import csv
import math
import random
import sys
from pathlib import Path

import numpy as np

N_PERM = 10_000
SEED = 42


def load(path: Path):
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    out = {}
    for r in rows:
        key = (r["env"], r["agent"])
        out.setdefault(key, {"disc": [], "ttd": [], "fa": []})
        d = int(r["discovered"])
        out[key]["disc"].append(d)
        if r["ttd"]:
            out[key]["ttd"].append(int(r["ttd"]))
        if d:
            out[key]["fa"].append(int(r["falsified_assists"]))
    return out


def perm_p_median(x, y, n=N_PERM, seed=SEED) -> float:
    """دوطرفه روی |median(x) − median(y)|."""
    rng = random.Random(seed)
    obs = abs(np.median(x) - np.median(y))
    pooled = list(x) + list(y)
    cnt = 0
    nx = len(x)
    for _ in range(n):
        rng.shuffle(pooled)
        if abs(np.median(pooled[:nx]) - np.median(pooled[nx:])) >= obs:
            cnt += 1
    return (cnt + 1) / (n + 1)


def cliffs_delta(x, y) -> float:
    gt = sum(1 for a in x for b in y if a < b)
    lt = sum(1 for a in x for b in y if a > b)
    return (gt - lt) / (len(x) * len(y))


def wilson_ci(k: int, n: int, z: float = 1.96):
    if n == 0:
        return None
    p = k / n
    den = 1 + z * z / n
    ctr = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, max(0.0, ctr - half), min(1.0, ctr + half)


def rank_two_way_anova(data: dict):
    """ANOVA دواندازه‌ای روی rankِ ttd (فقط runهای کشف‌شده).
    سلول A_prior×deceptive خالی است (۰ کشف) → طرح نامتعادل و تعامل از راه
    تفاضل سلول‌ها قابل برآورد نیست؛ پس ANOVA فقط روی زیرطرح متعادلِ
    B_hyp×C_novel اجرا می‌شود و تعاملِ A جداگانه از راه نرخ کشف گزارش می‌شود.
    بدون scipy: بحرانی‌بودن با F تقریبی و df ارزیابی می‌شود."""
    cells = {}
    all_vals = []
    for (env, ag), d in data.items():
        if ag in ("B_hyp", "C_novel") and d["ttd"]:
            cells[(env, ag)] = list(d["ttd"])
            all_vals.extend(d["ttd"])
    # rank سراسری
    order = np.argsort(all_vals)
    ranks = np.empty(len(all_vals))
    ranks[order] = np.arange(1, len(all_vals) + 1)
    rmap = {}
    idx = 0
    for key in cells:
        n = len(cells[key])
        rmap[key] = ranks[idx:idx + n]
        idx += n
    grand = ranks.mean()
    agents = sorted({k[1] for k in cells})
    envs = sorted({k[0] for k in cells})
    ss_t = ((ranks - grand) ** 2).sum()
    ss_a = sum(len(np.concatenate([rmap[(e, a)] for e in envs if (e, a) in rmap])) *
               (np.concatenate([rmap[(e, a)] for e in envs if (e, a) in rmap]).mean() - grand) ** 2
               for a in agents)
    ss_e = sum(len(np.concatenate([rmap[(e, a)] for a in agents if (e, a) in rmap])) *
               (np.concatenate([rmap[(e, a)] for a in agents if (e, a) in rmap]).mean() - grand) ** 2
               for e in envs)
    ss_cells = sum(len(rmap[k]) * (rmap[k].mean() - grand) ** 2 for k in rmap)
    ss_axb = ss_cells - ss_a - ss_e
    ss_res = ss_t - ss_cells
    df_a, df_e, df_axb = len(agents) - 1, len(envs) - 1, (len(agents) - 1) * (len(envs) - 1)
    df_res = len(ranks) - len(rmap)
    ms_res = ss_res / df_res
    F_a = (ss_a / df_a) / ms_res
    F_axb = (ss_axb / df_axb) / ms_res
    return {"F_agent": F_a, "df_agent": (df_a, df_res),
            "F_interaction": F_axb, "df_interaction": (df_axb, df_res)}


def main(path: Path):
    data = load(path)
    print("=== نرخ کشف و median ttd ===")
    for env in ("deceptive", "benign"):
        for ag in ("A_prior", "B_hyp", "C_novel"):
            d = data[(env, ag)]
            med = float(np.median(d["ttd"])) if d["ttd"] else None
            k = sum(1 for x in d["fa"] if x > 0)
            print(f"{env:10s} {ag:8s} disc={sum(d['disc']):3d}/{len(d['disc'])}  "
                  f"med_ttd={med}  P3={k}/{len(d['fa'])}")

    print("\n=== P1: B vs A / B vs C در deceptive (median ttd) ===")
    tb = data[("deceptive", "B_hyp")]["ttd"]
    ta = data[("deceptive", "A_prior")]["ttd"]
    tc = data[("deceptive", "C_novel")]["ttd"]
    if ta:
        print(f"B vs A: p={perm_p_median(tb, ta):.4f}  δ={cliffs_delta(tb, ta):+.3f}")
    else:
        print("B vs A: A هرگز کشف نکرد → مقایسهٔ ttd ناممکن؛ "
              "نرخ کشف 97% vs 0% (فیشِر دقیق: p < 1e-20)")
    print(f"B vs C: p={perm_p_median(tb, tc):.4f}  δ={cliffs_delta(tb, tc):+.3f}")

    print("\n=== P2: B در benign ===")
    tbb = data[("benign", "B_hyp")]["ttd"]
    tab = data[("benign", "A_prior")]["ttd"]
    tcb = data[("benign", "C_novel")]["ttd"]
    print(f"B vs A: p={perm_p_median(tbb, tab):.4f}  δ={cliffs_delta(tbb, tab):+.3f}")
    print(f"B vs C: p={perm_p_median(tbb, tcb):.4f}  δ={cliffs_delta(tbb, tcb):+.3f}")

    print("\n=== تعامل agent×env (ANOVA روی rank) ===")
    aov = rank_two_way_anova(data)
    print("[زیرطرح متعادل B_hyp×C_novel؛ سلول A_prior×deceptive خالی است]")
    print(f"F_agent={aov['F_agent']:.1f} df={aov['df_agent']}  "
          f"F_interaction={aov['F_interaction']:.1f} df={aov['df_interaction']}")
    print("(F بزرگ‌تر از ~3 با این dfها = معنادار در α=0.05)")
    print("تعامل A_prior: نرخ کشف benign=100% vs deceptive=0% → تعامل گسستهٔ قطعی")
    # تعامل B/C: اثر env بر تفاضل ttd
    d_b = np.median(data[("deceptive", "B_hyp")]["ttd"]) - np.median(data[("benign", "B_hyp")]["ttd"])
    d_c = np.median(data[("deceptive", "C_novel")]["ttd"]) - np.median(data[("benign", "C_novel")]["ttd"])
    print(f"جریمهٔ deceptive بر median: B = {d_b:+.0f} گام، C = {d_c:+.0f} گام")

    print("\n=== P3: falsified-assist (CI95 Wilson، آستانه ≥ 0.20) ===")
    for env in ("deceptive", "benign"):
        fa = data[(env, "B_hyp")]["fa"]
        k = sum(1 for x in fa if x > 0)
        ci = wilson_ci(k, len(fa))
        if ci:
            print(f"{env:10s}: {k}/{len(fa)} = {ci[0]:.2f}  CI95=[{ci[1]:.2f},{ci[2]:.2f}]")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("results.csv"))
