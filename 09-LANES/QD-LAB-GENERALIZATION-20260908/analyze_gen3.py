"""Analysis + verdict for OCTOPUS-QD-LAB-GEN-v3 (H8) per preregistered rules."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "results_gen3"
SEEDS = [7, 11, 23]
GENS = list(range(151))
CHECKPOINTS = (50, 150)

rows = json.loads((OUT / "rows_gen3.json").read_text(encoding="utf-8"))


def series(arm, metric, gen):
    return np.array([next(r[metric] for r in rows if r["arm"] == arm and r["seed"] == s and r["gen"] == gen)
                     for s in SEEDS])


def curve(arm, metric):
    return np.array([[next(r[metric] for r in rows if r["arm"] == arm and r["seed"] == s and r["gen"] == g)
                      for s in SEEDS] for g in GENS])  # (gen, seed)


t_qd_50, r_qd_50 = series("T", "qd_score", 50).mean(), series("R", "qd_score", 50).mean()
t_qd_150, r_qd_150 = series("T", "qd_score", 150).mean(), series("R", "qd_score", 150).mean()
t_cov_50, r_cov_50 = series("T", "coverage", 50).mean(), series("R", "coverage", 50).mean()

cond1 = t_qd_50 >= 1.10 * r_qd_50
cond2 = t_qd_150 >= 1.10 * r_qd_150
cond3 = (t_cov_50 - r_cov_50) >= 0.05
kill = (t_qd_50 <= r_qd_50) and (t_qd_150 <= r_qd_150)
verdict = ("SUPPORTED_IN_THIS_LAB" if (cond1 and cond2 and cond3)
           else "REJECTED_BY_THRESHOLD" if not (cond1 and cond2 and cond3) else "UNKNOWN")

f_qd_150 = series("F", "qd_score", 150).mean()
f_cov_150 = series("F", "coverage", 150).mean()

record = {
    "id": "OQD-H8",
    "claim": "Archive parent selection accelerates diversity/quality growth in a new environment relative to fresh random initialization.",
    "threshold": {"T_qd_at_50_ge_R": 1.10, "T_qd_at_150_ge_R": 1.10,
                  "T_cov_minus_R_cov_at_50_min": 0.05},
    "measured_delta": {
        "mean_qd_T_50": t_qd_50, "mean_qd_R_50": r_qd_50, "ratio_50": t_qd_50 / r_qd_50,
        "mean_qd_T_150": t_qd_150, "mean_qd_R_150": r_qd_150, "ratio_150": t_qd_150 / r_qd_150,
        "mean_cov_T_50": t_cov_50, "mean_cov_R_50": r_cov_50, "cov_delta_50": t_cov_50 - r_cov_50,
        "conditions_met": {"qd50_ge_10pct": bool(cond1), "qd150_ge_10pct": bool(cond2),
                           "cov50_delta_ge_5pp": bool(cond3)},
        "kill_label_triggered": bool(kill),
        "per_seed_qd_150": {a: series(a, "qd_score", 150).tolist() for a in ("T", "R", "F")},
        "per_seed_cov_150": {a: series(a, "coverage", 150).tolist() for a in ("T", "R", "F")},
        "gen0_baseline": {a: {"coverage": series(a, "coverage", 0).tolist(),
                              "qd_score": series(a, "qd_score", 0).tolist()} for a in ("T", "R", "F")},
        "F_descriptive_final": {"mean_qd_150": f_qd_150, "mean_cov_150": f_cov_150},
    },
    "verdict": verdict,
    "inference_limit": "One held-out maze (B1), mutation-only operators, 3 seeds, no p-values; gen-0 structural head start of T is recorded as caveat; no mission-level value claim.",
}
(OUT / "hypothesis_records_gen3.json").write_text(
    json.dumps(record, indent=1, ensure_ascii=False), encoding="utf-8")

# ---------- charts ----------
plt.rcParams.update({"figure.facecolor": "#faf8f2", "axes.facecolor": "#faf8f2",
                     "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold"})
arm_col = {"T": "#1d7f8e", "R": "#b3402b", "F": "#7a7a7a"}
arm_lab = {"T": "T transfer-seed", "R": "R random-seed", "F": "F frozen parents"}

fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.6), dpi=150)
for metric, axx, title, ylab in (("qd_score", ax[0], "QD-score growth on maze B1", "QD (sum elite fitness)"),
                                 ("coverage", ax[1], "Coverage growth on maze B1", "coverage = filled/4096")):
    c = {a: curve(a, metric) for a in ("T", "R", "F")}
    for a in ("T", "R", "F"):
        m = c[a].mean(axis=1)
        axx.fill_between(GENS, c[a].min(axis=1), c[a].max(axis=1), color=arm_col[a], alpha=.15)
        axx.plot(GENS, m, color=arm_col[a], lw=2, label=arm_lab[a])
    for g in CHECKPOINTS:
        axx.axvline(g, color="#333", ls=":", lw=1)
    axx.set_title(title)
    axx.set_xlabel("generation")
    axx.set_ylabel(ylab)
    axx.legend(fontsize=8)
    axx.grid(alpha=.25)
fig.suptitle("OCTOPUS QD Lab GEN-v3 | archive-consumption intervention | bands = min–max over seeds 7/11/23", y=1.02)
fig.tight_layout()
fig.savefig(OUT / "gen5_h8_growth.png", bbox_inches="tight")

fig, ax = plt.subplots(figsize=(8.6, 4.6), dpi=150)
tm = np.array([[r.get("migrant_parent_share", np.nan) for s in SEEDS
                if (r := next((x for x in rows if x["arm"] == "T" and x["seed"] == s and x["gen"] == g), None)) is not None]
               for g in range(1, 151)])
mean_share = np.nanmean(tm, axis=1)
ax.fill_between(range(1, 151), np.nanmin(tm, axis=1), np.nanmax(tm, axis=1), color="#1d7f8e", alpha=.15)
ax.plot(range(1, 151), mean_share, color="#1d7f8e", lw=2, label="T: immigrant-parent share (accumulation)")
ax.plot(range(1, 151), np.ones(150), color="#7a7a7a", ls="--", lw=1.5,
        label="F: 100% frozen parents forever (pure consumption)")
ax.set_xlabel("generation")
ax.set_ylabel("share of parents drawn from gen-0 immigrants")
ax.set_title("Memory composition: does the local archive take over from the immigrants?")
ax.set_ylim(0, 1.05)
ax.legend(fontsize=8)
ax.grid(alpha=.25)
fig.tight_layout()
fig.savefig(OUT / "gen6_h8_migrant_share.png", bbox_inches="tight")

print("VERDICT:", verdict,
      f"| qd50 T/R = {t_qd_50:.1f}/{r_qd_50:.1f} (ratio {t_qd_50/r_qd_50:.3f}, cond1={bool(cond1)})",
      f"| qd150 T/R = {t_qd_150:.1f}/{r_qd_150:.1f} (ratio {t_qd_150/r_qd_150:.3f}, cond2={bool(cond2)})",
      f"| cov50 delta = {t_cov_50-r_cov_50:+.4f} (cond3={bool(cond3)})",
      f"| kill={bool(kill)} | F final qd={f_qd_150:.1f} cov={f_cov_150:.4f}")
print("T migrant share: gen1=%.2f gen25=%.2f gen50=%.2f gen150=%.2f" %
      (mean_share[0], mean_share[24], mean_share[49], mean_share[149]))
