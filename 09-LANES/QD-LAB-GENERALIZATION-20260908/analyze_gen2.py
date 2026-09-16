"""Analysis + verdicts for OCTOPUS-QD-LAB-GEN-v2 per preregistered rules."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "results_gen2"
PRIMARY = ["full_seed7", "full_seed11", "full_seed23"]
ROBUST = ["mutation_seed7", "mutation_seed11", "mutation_seed23"]
FAMS = {"A": ["A1", "A2"], "B": ["B1", "B2"], "C": ["C1", "C2"]}
FAULTS = ["N05", "N10", "N20", "S75", "S50"]
FAULT_LABEL = {"N05": "noise σ=.05", "N10": "noise σ=.10", "N20": "noise σ=.20",
               "S75": "speed ×0.75", "S50": "speed ×0.50"}

rows = json.loads((OUT / "rows_gen2.json").read_text(encoding="utf-8"))


def get(archive, cond):
    for r in rows:
        if r["archive"] == archive and r["condition"] == cond:
            return r
    raise KeyError((archive, cond))


# ---------- H6 ----------
h6_pairs, fam_adv = [], {f: [] for f in FAMS}
for run in PRIMARY:
    clean = get(run, "CLEAN")["mean_fitness"]
    for fam, mazes in FAMS.items():
        for m in mazes:
            e = get(run, f"H6-{m}")["mean_fitness"]
            rnd = get(run, f"H6-{m}-RANDOM")["mean_fitness"]
            h6_pairs.append({"archive": run, "family": fam, "maze": m, "elite": e,
                             "random": rnd, "retention": e / clean, "advantage": e - rnd})
            fam_adv[fam].append(e - rnd)
mean_ret = sum(p["retention"] for p in h6_pairs) / len(h6_pairs)
mean_adv = sum(p["advantage"] for p in h6_pairs) / len(h6_pairs)
family_bound = [f for f in FAMS if sum(fam_adv[f]) / len(fam_adv[f]) <= 0.05]
h6_verdict = ("SUPPORTED_IN_THIS_LAB" if (mean_ret >= 0.75 and mean_adv >= 0.15)
              else "REJECTED_BY_THRESHOLD" if (mean_ret < 0.75 or mean_adv < 0.15) else "UNKNOWN")

h6_robust = []
for run in ROBUST:
    clean = get(run, "CLEAN")["mean_fitness"]
    for fam, mazes in FAMS.items():
        for m in mazes:
            e = get(run, f"H6-{m}")["mean_fitness"]
            h6_robust.append({"archive": run, "family": fam, "maze": m,
                              "elite": e, "retention": e / clean})
robust_mean = sum(r["retention"] for r in h6_robust) / len(h6_robust)

# ---------- H7 ----------
h7 = {ft: [] for ft in FAULTS}
h7_pairs = []
for run in PRIMARY:
    clean = get(run, "CLEAN")["mean_fitness"]
    for ft in FAULTS:
        v = get(run, f"H7-{ft}")["mean_fitness"]
        h7[ft].append(v)
        h7_pairs.append({"archive": run, "fault": ft, "elite": v, "retention": v / clean})
h7_primary = sum(h7["N10"]) / len(h7["N10"])
h7_means = {ft: sum(v) / len(v) for ft, v in h7.items()}
collapses = [ft for ft in FAULTS if h7_means[ft] < 0.50]
h7_verdict = ("SUPPORTED_IN_THIS_LAB" if h7_primary >= 0.80
              else "REJECTED_BY_THRESHOLD" if h7_primary < 0.80 else "UNKNOWN")

records = [
    {
        "id": "OQD-H6",
        "claim": "Elites retain meaningful quality on out-of-family mazes (generic reactive skill).",
        "threshold": {"mean_retention_over_all_pairs": 0.75, "mean_elite_minus_random": 0.15},
        "measured_delta": {
            "mean_retention": mean_ret, "mean_advantage": mean_adv, "n_pairs": len(h6_pairs),
            "retention_range": [min(p["retention"] for p in h6_pairs), max(p["retention"] for p in h6_pairs)],
            "advantage_range": [min(p["advantage"] for p in h6_pairs), max(p["advantage"] for p in h6_pairs)],
            "per_family_mean_advantage": {f: sum(fam_adv[f]) / len(fam_adv[f]) for f in FAMS},
            "family_bound_labels": family_bound,
            "robustness_mutation_archives_mean_retention": robust_mean,
        },
        "verdict": h6_verdict,
        "paired_results": h6_pairs,
        "robustness_results": h6_robust,
        "inference_limit": "Out-of-family = different obstacle grammar, same arena/start corner/sensors/metric; no hardware or real-world claim.",
    },
    {
        "id": "OQD-H7",
        "claim": "Elites tolerate moderate sensor noise (E5-style fault) on the source maze.",
        "threshold": {"mean_retention_at_N10": 0.80},
        "measured_delta": {
            "n10_mean_retention": h7_primary,
            "ladder_mean_retention": h7_means,
            "collapse_conditions": collapses,
            "n_pairs": len(h7_pairs),
        },
        "verdict": h7_verdict,
        "paired_results": h7_pairs,
        "inference_limit": "Gaussian noise on normalized sensor distance + speed-authority scaling only; one factor per condition; no other fault modes tested.",
    },
]
(OUT / "hypothesis_records_gen2.json").write_text(
    json.dumps(records, indent=1, ensure_ascii=False), encoding="utf-8")

# ---------- charts ----------
plt.rcParams.update({"figure.facecolor": "#faf8f2", "axes.facecolor": "#faf8f2",
                     "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold"})
colors = {"full_seed7": "#1d7f8e", "full_seed11": "#b3402b", "full_seed23": "#4a7a2c"}

fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.6), dpi=150)
fam_names = {"A": "A: open pillar arena", "B": "B: vertical chambers", "C": "C: dense forest"}
for run in PRIMARY:
    xs, ys = [], []
    for fi, (fam, mazes) in enumerate(FAMS.items()):
        for m in mazes:
            xs.append(fi + (0.1 if run == "full_seed11" else -0.1 if run == "full_seed7" else 0))
            ys.append(next(p["retention"] for p in h6_pairs if p["archive"] == run and p["maze"] == m))
    ax[0].scatter(xs, ys, color=colors[run], label=run, s=42, zorder=3)
for fi, fam in enumerate(FAMS):
    vals = [p["retention"] for p in h6_pairs if p["family"] == fam]
    ax[0].plot([fi - .25, fi + .25], [np.mean(vals)] * 2, color="#333", lw=2, zorder=2)
ax[0].axhline(0.75, color="#b3402b", ls="--", lw=1, label="threshold 0.75")
ax[0].set_xticks(range(3), [fam_names[f] for f in FAMS], fontsize=8)
ax[0].set_ylim(0, 1.1)
ax[0].set_title("H6: retention on out-of-family mazes")
ax[0].set_ylabel("mean elite fitness / clean source fitness")
ax[0].legend(fontsize=8)
ax[0].grid(alpha=.25)

x = np.arange(3)
for fi, fam in enumerate(FAMS):
    e = np.mean([p["elite"] for p in h6_pairs if p["family"] == fam])
    r = np.mean([p["random"] for p in h6_pairs if p["family"] == fam])
    ax[1].bar(fi - .2, e, .38, color="#1d7f8e")
    ax[1].bar(fi + .2, r, .38, color="#9a9a9a")
    ax[1].text(fi, max(e, r) + .03, f"Δ={e-r:+.2f}", ha="center", fontsize=9)
ax[1].set_xticks(x, [fam_names[f] for f in FAMS], fontsize=8)
ax[1].set_title("H6: elites vs fresh random (mean of 3 archives)")
ax[1].set_ylabel("mean fitness")
ax[1].grid(alpha=.25, axis="y")
fig.suptitle("OCTOPUS QD Lab GEN-v2 | out-of-family transfer | this platform, one mode", y=1.02)
fig.tight_layout()
fig.savefig(OUT / "gen3_h6_outfamily.png", bbox_inches="tight")

fig, ax = plt.subplots(figsize=(8.6, 4.6), dpi=150)
for run in PRIMARY:
    vals = [next(p["retention"] for p in h7_pairs if p["archive"] == run and p["fault"] == ft) for ft in FAULTS]
    ax.plot(range(len(FAULTS)), vals, "o-", color=colors[run], label=run)
ax.plot(range(len(FAULTS)), [h7_means[ft] for ft in FAULTS], "s--", color="#333", label="mean", lw=2)
ax.axhline(0.80, color="#4a7a2c", ls="--", lw=1, label="H7 threshold 0.80 (at N10)")
ax.axvline(1, color="#b3402b", ls=":", lw=1.2)
ax.text(1.02, 0.06, "primary", rotation=90, fontsize=8, color="#b3402b")
ax.set_xticks(range(len(FAULTS)), [FAULT_LABEL[ft] for ft in FAULTS], fontsize=9)
ax.set_ylim(0, 1.05)
ax.set_title("H7: fault-injection ladder on source maze (E5-style)")
ax.set_ylabel("retention vs clean")
ax.legend(fontsize=8)
ax.grid(alpha=.25)
fig.tight_layout()
fig.savefig(OUT / "gen4_h7_faults.png", bbox_inches="tight")

print("VERDICTS: H6 =", h6_verdict, f"(ret={mean_ret:.4f}, adv={mean_adv:.4f}, family_bound={family_bound})")
print("          H7 =", h7_verdict, f"(N10={h7_primary:.4f})  ladder:",
      {k: round(v, 4) for k, v in h7_means.items()}, " collapses:", collapses)
