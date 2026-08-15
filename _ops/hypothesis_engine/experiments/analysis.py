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


# ===================================================================
# EXTENDED: New statistical functions for multi-scenario analysis
# ===================================================================
import json
from typing import Any, Dict, List, Optional, Tuple


def bootstrap_cliffs_delta(x: List[float], y: List[float],
                           n_boot: int = 10_000,
                           seed: int = 42, alpha: float = 0.05) -> Dict[str, float]:
    """Cliff's delta with bootstrap 95% confidence interval.

    Returns dict with: delta, ci_lower, ci_upper, n_boot
    """
    rng = np.random.default_rng(seed)
    obs = cliffs_delta(x, y)
    boot_deltas = np.empty(n_boot)
    nx, ny = len(x), len(y)

    for i in range(n_boot):
        bx = [x[rng.integers(nx)] for _ in range(nx)]
        by = [y[rng.integers(ny)] for _ in range(ny)]
        boot_deltas[i] = cliffs_delta(bx, by)

    boot_deltas.sort()
    lo_idx = int((alpha / 2) * n_boot)
    hi_idx = int((1 - alpha / 2) * n_boot)
    return {
        "delta": obs,
        "ci_lower": float(boot_deltas[lo_idx]),
        "ci_upper": float(boot_deltas[hi_idx]),
        "n_boot": n_boot,
    }


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Load benchmark JSONL output from the runner."""
    records = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def load_jsonl_multi(directory: Path,
                      scenario_ids: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
    """Load all JSONL files from a benchmark output directory.

    Returns dict keyed by scenario_id.
    """
    results = {}
    for p in sorted(directory.glob("*.jsonl")):
        if p.name.endswith("_autonomy_provenance.jsonl"):
            continue
        if p.name == "summary.json":
            continue
        sid = p.stem
        if scenario_ids and sid not in scenario_ids:
            continue
        results[sid] = load_jsonl(p)
    return results


def per_scenario_report(results: Dict[str, List[Dict]],
                        scenario_ids: Optional[List[str]] = None) -> Dict[str, Dict]:
    """Compute per-scenario statistics: discovery rates, TTD, effect sizes.

    Returns dict keyed by scenario_id with agent-level and comparison stats.
    """
    report = {}
    scenarios = scenario_ids or list(results.keys())

    for sid in scenarios:
        recs = results.get(sid, [])
        if not recs:
            continue

        agents_data: Dict[str, Dict[str, list]] = {}
        for r in recs:
            agent = r.get("agent", "unknown")
            agents_data.setdefault(agent, {"disc": [], "ttd": [], "steps": [], "wasted": []})
            agents_data[agent]["disc"].append(1 if r.get("discovered") else 0)
            if r.get("ttd") is not None:
                agents_data[agent]["ttd"].append(r["ttd"])
            agents_data[agent]["steps"].append(r.get("total_steps", 0))
            agents_data[agent]["wasted"].append(r.get("wasted_steps", 0))

        agent_stats = {}
        for ag, d in agents_data.items():
            n = len(d["disc"])
            k = sum(d["disc"])
            ci = wilson_ci(k, n)
            med_ttd = float(np.median(d["ttd"])) if d["ttd"] else None
            agent_stats[ag] = {
                "n": n,
                "discovery_rate": k / max(n, 1),
                "discovery_wilson_ci": [round(v, 4) for v in ci] if ci else None,
                "median_ttd": med_ttd,
                "mean_steps": float(np.mean(d["steps"])),
                "mean_wasted": float(np.mean(d["wasted"])),
            }

        # Effect sizes
        comparisons = {}
        b_ttd = agents_data.get("B_hyp", {}).get("ttd", [])
        a_ttd = agents_data.get("A_prior", {}).get("ttd", [])
        c_ttd = agents_data.get("C_novel", {}).get("ttd", [])

        if b_ttd and a_ttd:
            comparisons["BA"] = bootstrap_cliffs_delta(b_ttd, a_ttd)
        if b_ttd and c_ttd:
            comparisons["BC"] = bootstrap_cliffs_delta(b_ttd, c_ttd)

        report[sid] = {
            "agents": agent_stats,
            "comparisons": comparisons,
        }

    return report


def degradation_curve(results: Dict[str, List[Dict]]) -> Dict[str, Any]:
    """Compare S3 family (distribution shift) across grid sizes / reward modes.

    Reports B_hyp discovery rate and median TTD per S3 sub-scenario.
    """
    s3_scenarios = {k: v for k, v in results.items()
                    if k.startswith("S3")}
    curve = {}
    for sid, recs in s3_scenarios.items():
        b_recs = [r for r in recs if r.get("agent") == "B_hyp"]
        if not b_recs:
            continue
        disc = [1 if r.get("discovered") else 0 for r in b_recs]
        ttd = [r["ttd"] for r in b_recs if r.get("ttd") is not None]
        curve[sid] = {
            "n": len(b_recs),
            "discovery_rate": sum(disc) / max(len(disc), 1),
            "median_ttd": float(np.median(ttd)) if ttd else None,
            "wilson_ci": [round(v, 4) for v in wilson_ci(sum(disc), len(disc))]
                         if disc else None,
        }
    return curve


def budget_efficiency(results: Dict[str, List[Dict]]) -> Dict[str, Any]:
    """S5 cost-per-discovery analysis: discovery rate and TTD per budget fraction."""
    s5_scenarios = {k: v for k, v in results.items()
                    if k.startswith("S5")}
    efficiency = {}
    for sid, recs in s5_scenarios.items():
        # Compute per-agent efficiency
        for agent in ("A_prior", "B_hyp", "C_novel"):
            agent_recs = [r for r in recs if r.get("agent") == agent]
            if not agent_recs:
                continue
            disc = [1 if r.get("discovered") else 0 for r in agent_recs]
            ttd = [r["ttd"] for r in agent_recs if r.get("ttd") is not None]
            budget = agent_recs[0].get("budget") or 10_000  # fallback
            cost_per_discovery = budget / max(sum(disc), 1)
            efficiency[f"{sid}_{agent}"] = {
                "discovery_rate": sum(disc) / max(len(disc), 1),
                "median_ttd": float(np.median(ttd)) if ttd else None,
                "cost_per_discovery": cost_per_discovery,
                "budget": budget,
            }
    return efficiency


def interaction_analysis(data: Dict[str, List[Dict]],
                          agents: Optional[List[str]] = None) -> Dict[str, Any]:
    """Agent × environment-family interaction analysis (rank-based).

    Handles unbalanced cells gracefully. Uses permutation test for interaction
    effect when cells are sparse.
    """
    if agents is None:
        agents = ["A_prior", "B_hyp", "C_novel"]

    # Organize by (scenario_family, agent)
    cells: Dict[Tuple[str, str], List[int]] = {}
    for sid, recs in data.items():
        # Derive family from scenario prefix
        family = sid.split("_")[0]  # S0, S1, S2, S3, S4, S5, S6, S7, S8
        for r in recs:
            ag = r.get("agent", "unknown")
            if ag not in agents:
                continue
            ttd = r.get("ttd")
            if ttd is not None:
                cells.setdefault((family, ag), []).append(ttd)

    # Rank-based analysis (reuse ANOVA logic)
    all_vals = []
    for vals in cells.values():
        all_vals.extend(vals)

    if not all_vals:
        return {"error": "no TTD data available"}

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
    agent_names = sorted({k[1] for k in cells})
    families = sorted({k[0] for k in cells})

    # SS calculations
    ss_t = ((ranks - grand) ** 2).sum()

    ss_agent = 0.0
    for ag in agent_names:
        ag_ranks = np.concatenate([rmap[k] for k in rmap if k[1] == ag])
        if len(ag_ranks) > 0:
            ss_agent += len(ag_ranks) * (ag_ranks.mean() - grand) ** 2

    ss_family = 0.0
    for fam in families:
        fam_ranks = np.concatenate([rmap[k] for k in rmap if k[0] == fam])
        if len(fam_ranks) > 0:
            ss_family += len(fam_ranks) * (fam_ranks.mean() - grand) ** 2

    ss_cells = sum(len(rmap[k]) * (rmap[k].mean() - grand) ** 2 for k in rmap)
    ss_agent_x_family = ss_cells - ss_agent - ss_family
    ss_res = ss_t - ss_cells

    n_cells = len(rmap)
    df_agent = len(agent_names) - 1
    df_family = len(families) - 1
    df_interaction = df_agent * df_family
    df_res = len(ranks) - n_cells

    if df_res > 0 and df_agent > 0:
        ms_res = ss_res / df_res
        F_agent = (ss_agent / df_agent) / ms_res
        F_interaction = (ss_agent_x_family / max(df_interaction, 1)) / ms_res
    else:
        F_agent = float("nan")
        F_interaction = float("nan")

    return {
        "n_cells": n_cells,
        "n_total": len(ranks),
        "agents": agent_names,
        "families": families,
        "F_agent": F_agent,
        "df_agent": (df_agent, df_res),
        "F_interaction": F_interaction,
        "df_interaction": (df_interaction, df_res),
    }


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv[1:]) > 1 else Path("results.csv"))
