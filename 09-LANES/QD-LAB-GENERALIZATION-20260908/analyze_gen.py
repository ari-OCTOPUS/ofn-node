"""Analysis + verdicts for OCTOPUS-QD-LAB-GEN-v1, strictly per preregistered rules."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "results_gen"
PRIMARY = ["full_seed7", "full_seed11", "full_seed23"]
ROBUST = ["mutation_seed7", "mutation_seed11", "mutation_seed23"]
MAZES = [f"m{i}" for i in range(1, 7)]
SHIFTS = ["s(0.04,0.06)", "s(0.08,0.06)", "s(0.06,0.04)", "s(0.06,0.08)"]

rows = json.loads((OUT / "rows_gen.json").read_text(encoding="utf-8"))


def get(archive, cond):
    for r in rows:
        if r["archive"] == archive and r["condition"] == cond:
            return r
    raise KeyError((archive, cond))


# ---------- H4 ----------
h4_ret, h4_adv, h4_rows = [], [], []
for run in PRIMARY:
    src = get(run, "SOURCE")["mean_fitness"]
    for m in MAZES:
        e = get(run, f"H4-{m}")["mean_fitness"]
        rnd = get(run, f"H4-{m}-RANDOM")["mean_fitness"]
        h4_ret.append(e / src)
        h4_adv.append(e - rnd)
        h4_rows.append({"archive": run, "maze": m, "elite": e, "random": rnd,
                        "retention": e / src, "advantage": e - rnd})
mean_ret = sum(h4_ret) / len(h4_ret)
mean_adv = sum(h4_adv) / len(h4_adv)
kill = mean_adv <= 0.05
if mean_ret >= 0.75 and mean_adv >= 0.15:
    h4_verdict = "SUPPORTED_IN_THIS_LAB"
elif mean_ret < 0.75 or mean_adv < 0.15:
    h4_verdict = "REJECTED_BY_THRESHOLD"
else:
    h4_verdict = "UNKNOWN"

h4_robust = []
for run in ROBUST:
    src = get(run, "SOURCE")["mean_fitness"]
    for m in MAZES:
        e = get(run, f"H4-{m}")["mean_fitness"]
        h4_robust.append({"archive": run, "maze": m, "elite": e, "retention": e / src})
robust_mean_ret = sum(r["retention"] for r in h4_robust) / len(h4_robust)

# ---------- H5 ----------
h5_rows = []
for run in PRIMARY:
    src = get(run, "SOURCE")["mean_fitness"]
    for s in SHIFTS:
        e = get(run, f"H5-{s}")["mean_fitness"]
        h5_rows.append({"archive": run, "shift": s, "elite": e, "retention": e / src})
h5_rets = [r["retention"] for r in h5_rows]
h5_mean = sum(h5_rets) / len(h5_rets)
h5_min = min(h5_rets)
h5_verdict = ("SUPPORTED_IN_THIS_LAB" if h5_mean >= 0.90 and h5_min >= 0.80
              else "REJECTED_BY_THRESHOLD" if (h5_mean < 0.90 or h5_min < 0.80) else "UNKNOWN")

# ---------- DESC combined (descriptive only) ----------
desc_rows = []
for run in PRIMARY:
    for m in MAZES:
        d = get(run, f"DESC-{m}-comb")["mean_fitness"]
        h4e = get(run, f"H4-{m}")["mean_fitness"]
        desc_rows.append({"archive": run, "maze": m, "combined": d,
                          "h4_same_maze": h4e, "combined_retention": d / get(run, "SOURCE")["mean_fitness"]})

records = [
    {
        "id": "OQD-H4",
        "claim": "Elites retain meaningful quality on unseen mazes (transferable skill, not pure memorization).",
        "threshold": {"mean_retention_over_mazes_and_archives": 0.75,
                      "mean_elite_minus_random_over_mazes_and_archives": 0.15},
        "measured_delta": {"mean_retention": mean_ret, "mean_advantage": mean_adv,
                           "n_pairs": len(h4_ret),
                           "retention_range": [min(h4_ret), max(h4_ret)],
                           "advantage_range": [min(h4_adv), max(h4_adv)],
                           "robustness_mutation_archives_mean_retention": robust_mean_ret},
        "verdict": h4_verdict,
        "kill_condition_triggered": kill,
        "paired_results": h4_rows,
        "robustness_results": h4_robust,
        "inference_limit": "Toy 2D point-robot mazes from one grammar; 3 archives; same platform/mode for all conditions; no p-values; local lab only.",
    },
    {
        "id": "OQD-H5",
        "claim": "On the SAME maze, elites tolerate small start perturbations.",
        "threshold": {"mean_retention_over_shifts_and_archives": 0.90, "min_single_retention": 0.80},
        "measured_delta": {"mean_retention": h5_mean, "min_retention": h5_min, "n_pairs": len(h5_rets)},
        "verdict": h5_verdict,
        "paired_results": h5_rows,
        "inference_limit": "0.02-unit start shifts on the source maze only; no claim about large relocations.",
    },
]
(OUT / "hypothesis_records_gen.json").write_text(
    json.dumps(records, indent=1, ensure_ascii=False), encoding="utf-8")
(OUT / "descriptive_combined.json").write_text(
    json.dumps(desc_rows, indent=1), encoding="utf-8")

# ---------- charts ----------
plt.rcParams.update({"figure.facecolor": "#faf8f2", "axes.facecolor": "#faf8f2",
                     "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold"})
colors = {"full_seed7": "#1d7f8e", "full_seed11": "#b3402b", "full_seed23": "#4a7a2c"}

fig, ax = plt.subplots(1, 2, figsize=(12, 4.4), dpi=150)
for run in PRIMARY:
    vals = [next(r["retention"] for r in h4_rows if r["archive"] == run and r["maze"] == m) for m in MAZES]
    ax[0].plot(MAZES, vals, "o-", label=run, color=colors[run])
ax[0].axhline(0.75, color="#b3402b", ls="--", lw=1, label="preregistered threshold 0.75")
ax[0].set_ylim(0, 1.05)
ax[0].set_title("H4: quality retention on unseen mazes")
ax[0].set_ylabel("mean elite fitness / source-maze fitness")
ax[0].legend(fontsize=8)
ax[0].grid(alpha=.25)

import numpy as np
x = np.arange(len(MAZES))
elite_means = [np.mean([r["elite"] for r in h4_rows if r["maze"] == m]) for m in MAZES]
rand_means = [np.mean([r["random"] for r in h4_rows if r["maze"] == m]) for m in MAZES]
ax[1].bar(x - .2, elite_means, .38, label="elites (mean of 3 archives)", color="#1d7f8e")
ax[1].bar(x + .2, rand_means, .38, label="fresh random n=256", color="#9a9a9a")
for run in PRIMARY:
    vals = [next(r["elite"] for r in h4_rows if r["archive"] == run and r["maze"] == m) for m in MAZES]
    ax[1].scatter(x - .2, vals, color="#0b3944", s=14, zorder=3)
ax[1].set_xticks(x, MAZES)
ax[1].set_title("H4: elites vs fresh-random baseline per maze")
ax[1].set_ylabel("mean fitness")
ax[1].legend(fontsize=8)
ax[1].grid(alpha=.25, axis="y")
fig.suptitle("OCTOPUS QD Lab GEN-v1 | held-out maze transfer | all values this platform, batch mode", y=1.02)
fig.tight_layout()
fig.savefig(OUT / "gen1_h4_transfer.png", bbox_inches="tight")

fig, ax = plt.subplots(1, 2, figsize=(12, 4.4), dpi=150)
for run in PRIMARY:
    vals = [next(r["retention"] for r in h5_rows if r["archive"] == run and r["shift"] == s) for s in SHIFTS]
    ax[0].plot(range(len(SHIFTS)), vals, "o-", label=run, color=colors[run])
ax[0].axhline(0.90, color="#4a7a2c", ls="--", lw=1, label="mean threshold 0.90")
ax[0].axhline(0.80, color="#b3402b", ls=":", lw=1.2, label="min threshold 0.80")
ax[0].set_xticks(range(len(SHIFTS)), [s.replace("s", "Δ", 1) for s in SHIFTS], fontsize=8)
ax[0].set_ylim(0, 1.05)
ax[0].set_title("H5: retention under 0.02 start shifts (source maze)")
ax[0].set_ylabel("retention vs source start")
ax[0].legend(fontsize=8)
ax[0].grid(alpha=.25)

for run in PRIMARY:
    h4v = [next(r["retention"] for r in h4_rows if r["archive"] == run and r["maze"] == m) for m in MAZES]
    dv = [next(r["combined_retention"] for r in desc_rows if r["archive"] == run and r["maze"] == m) for m in MAZES]
    ax[1].plot(MAZES, h4v, "o--", color=colors[run], alpha=.8)
    ax[1].plot(MAZES, dv, "s-", color=colors[run], label=f"{run} (combined)")
ax[1].set_title("Descriptive: maze + shifted start (0.08,0.08) vs maze only")
ax[1].set_ylabel("retention")
ax[1].legend(fontsize=7)
ax[1].grid(alpha=.25)
fig.suptitle("OCTOPUS QD Lab GEN-v1 | start robustness and combined shift", y=1.02)
fig.tight_layout()
fig.savefig(OUT / "gen2_h5_and_combined.png", bbox_inches="tight")
print("VERDICTS:", h4_verdict, h5_verdict, "| H4 mean_ret=%.4f mean_adv=%.4f | H5 mean=%.4f min=%.4f"
      % (mean_ret, mean_adv, h5_mean, h5_min))
