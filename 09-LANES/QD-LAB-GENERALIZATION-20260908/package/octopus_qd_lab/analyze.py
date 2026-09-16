"""Build charts, full-precision genome exports, and local OCTOPUS evidence proposals."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import environment as env
from map_elites import Archive
from experiment import dump_json, digest_file
from octopus_bridge import observe_vitality, make_proposal, verify_ledger

COLORS = {"full": "#20808D", "mutation": "#A84B2F", "random": "#73736C", "crossover": "#944454"}
LABELS = {"full": "Mixed MAP-Elites", "mutation": "Mutation MAP-Elites",
          "random": "Random + archive", "crossover": "Crossover + mutation"}
STYLES = {"full": "-", "mutation": "--", "random": ":", "crossover": "-."}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_tests_record(tests):
    """Reject truthy strings, empty suites, skipped checks, and missing counts."""
    required = {"tests_run", "failures", "errors", "skipped", "successful", "test_hashes", "scope"}
    if not isinstance(tests, dict) or set(tests) != required:
        raise ValueError("Missing or extra test evidence fields")
    for key in ("tests_run", "failures", "errors", "skipped"):
        if type(tests[key]) is not int or tests[key] < 0:
            raise ValueError("Invalid test count")
    if (tests["successful"] is not True or tests["tests_run"] <= 0 or
            any(tests[key] != 0 for key in ("failures", "errors", "skipped"))):
        raise ValueError("Test evidence is not a positive, fully passing suite")
    if not isinstance(tests["test_hashes"], dict) or not tests["test_hashes"]:
        raise ValueError("Missing test source hashes")
    return True


def verify_run_bundle(run_dir, study, study_path):
    """Bind reported metrics to hashed history, receipt payloads, and saved archive.

    This checks consistency under a trusted local manifest. It is not an
    authenticated external attestation and cannot detect a total anchored rewrite.
    """
    r = read_json(run_dir / "run_summary.json")
    files = {"archive.npz", "history.json", "operators.json", "receipts.jsonl"}
    if set(r.get("file_hashes", {})) != files:
        raise ValueError("Missing or unexpected artifact manifest entries")
    mode, seed, config = r["mode"], r["seed"], r["config"]
    if type(seed) is not int or mode not in LABELS or run_dir.name != f"{mode}_seed{seed}":
        raise ValueError("Run identity mismatch")
    if config != study["config"]:
        raise ValueError("Run config differs from frozen study")
    anchor = r["receipt_anchor"]
    count = config["generations"] + 4
    if type(anchor["count"]) is not int or anchor["count"] != count:
        raise ValueError("Unexpected receipt count")
    check = verify_ledger(run_dir / "receipts.jsonl", expected_head=anchor["head"], expected_count=count)
    if not check["valid"]:
        raise ValueError("Invalid ledger")
    check["artifact_hashes_match"] = all(digest_file(run_dir / f) == h for f, h in r["file_hashes"].items())
    if not check["artifact_hashes_match"]:
        raise ValueError("Artifact hash mismatch")
    receipts = [json.loads(line) for line in (run_dir / "receipts.jsonl").read_text(encoding="utf-8").splitlines()]
    first, start, final = receipts[0], receipts[1], receipts[-1]
    if (first["event_type"] != "protocol_bound" or
            first["payload"]["study_sha256"] != digest_file(study_path) or
            first["payload"]["scientific_code_sha256"] != study["scientific_code_sha256"]):
        raise ValueError("Protocol receipt mismatch")
    if start["event_type"] != "run_started" or start["payload"] != dict(seed=seed, mode=mode, config=config):
        raise ValueError("Run-start identity mismatch")
    history = read_json(run_dir / "history.json")
    if len(history) != config["generations"] + 1:
        raise ValueError("Missing generations")
    for generation, (row, receipt) in enumerate(zip(history, receipts[2:-1])):
        if row["gen"] != generation or row["evals"] != config["initial"] + generation * config["batch"]:
            raise ValueError("Generation or evaluation budget mismatch")
        if (receipt["event_type"] != "generation_evaluated" or receipt["event_time"] != generation or
                row != receipt["payload"]["metrics"]):
            raise ValueError("History metrics not bound to generation receipts")
    if (final["event_type"] != "run_completed" or final["payload"]["tests_ok"] is not True or
            final["payload"]["metrics"] != history[-1] or r["final"] != history[-1]):
        raise ValueError("Summary/final-receipt/history metrics disagree")
    for name, key in (("archive.npz", "archive_sha256"), ("history.json", "history_sha256"),
                      ("operators.json", "operators_sha256")):
        if final["payload"][key] != r["file_hashes"][name]:
            raise ValueError("Final receipt is not bound to artifact manifest")
    archive = Archive.load(run_dir / "archive.npz")
    if archive.grid != config["grid"]:
        raise ValueError("Archive grid mismatch")
    recomputed = archive.metrics(seed=2026 + config["generations"])
    for key, value in recomputed.items():
        if not np.isclose(value, history[-1][key], atol=1e-12, rtol=0):
            raise ValueError(f"Archive disagrees with reported {key}")
    for name in ("n_elites", "coverage", "qd_score"):
        if np.any(np.diff([row[name] for row in history]) < -1e-10):
            raise ValueError(f"Non-monotone archive metric: {name}")
    check["metrics_bound_to_history_receipts_and_archive"] = True
    return r, history, check


def draw_maze(ax):
    for x0, y0, x1, y1 in env.WALLS:
        ax.add_patch(Rectangle((x0, y0), x1-x0, y1-y0, color="#28251D", zorder=5))
    for x, y, r in env.PILLARS:
        ax.add_patch(Circle((x, y), r, color="#28251D", zorder=5))
    ax.set(xlim=(0, 1), ylim=(0, 1), aspect="equal", xlabel="Final x / position x", ylabel="Final y / position y")
    ax.grid(False)


def room_masks(bd):
    masks = {
        "A: lower": bd[:, 1] < .30,
        "B: middle": (bd[:, 1] >= .335) & (bd[:, 1] < .62),
        "C: top-left": (bd[:, 1] >= .655) & (bd[:, 0] < .46),
        "D: top-right": (bd[:, 1] >= .655) & (bd[:, 0] >= .495),
    }
    masks["Passages"] = ~np.logical_or.reduce(list(masks.values()))
    return masks


def genome_card(archive, index):
    mask = archive.filled
    genomes, fitness, bd = archive.elites()
    layers = env.unpack(genomes[index])
    i, j = np.argwhere(mask)[index]
    return {
        "id": int(archive.ids[i, j]), "cell": [int(i), int(j)],
        "parents": archive.parents[i, j].tolist(), "operator": str(archive.operators[i, j]),
        "descriptor": bd[index].tolist(), "fitness": float(fitness[index]),
        "first_cell_discovery_generation": int(archive.first_generation[i, j]),
        "last_elite_replacement_generation": int(archive.last_generation[i, j]),
        "genome_order": "row-major W1[6,8], b1[8], W2[8,2], b2[2]",
        "genome": genomes[index].tolist(),
        "W1": layers[0][0].tolist(), "b1": layers[1][0, 0].tolist(),
        "W2": layers[2][0].tolist(), "b2": layers[3][0, 0].tolist(),
        "episode": {key: float(value[i, j]) for key, value in archive.meta.items()},
    }


def assess_hypotheses(study, runs, all_integrity, tests):
    records = json.loads(json.dumps(study["hypotheses"]))
    seeds = study["planned_seeds"]
    index = {(r["mode"], r["seed"]): r for r in runs}
    default_config = {"grid": 64, "batch": 96, "initial": 256, "generations": 500}
    full_budget = all(study["config"][key] == value for key, value in default_config.items())
    comparisons = [("random", records[0]), ("mutation", records[1])]
    for baseline, rec in comparisons:
        required = [(m, s) for s in seeds for m in ("full", baseline)]
        if not full_budget or not all(k in index for k in required):
            rec.update(verdict="UNKNOWN", measured_delta=None, reason="Preregistered full-budget paired runs incomplete")
            continue
        paired = [{"seed": s,
                   "coverage_delta": index["full", s]["final"]["coverage"] - index[baseline, s]["final"]["coverage"],
                   "qd_relative_delta": index["full", s]["final"]["qd_score"] / index[baseline, s]["final"]["qd_score"] - 1}
                  for s in seeds]
        dc = float(np.mean([x["coverage_delta"] for x in paired]))
        dq = float(np.mean([x["qd_relative_delta"] for x in paired]))
        if baseline == "random":
            passed = dc >= .10 and dq >= .10
        else:
            passed = dc >= -.01 and dq >= .02
        rec.update(verdict="SUPPORTED_IN_THIS_LAB" if passed else "REJECTED_BY_THRESHOLD",
                   measured_delta={"mean_coverage_delta": dc, "mean_qd_relative_delta": dq},
                   paired_results=paired,
                   inference_limit="Three seeded runs, same toy environment; no p-value or independent evaluation claim.")
    records[2].update(verdict="PASSED_COVERED_LOCAL_TESTS" if all_integrity and tests["successful"] else "FAILED",
                      measured={"all_integrity": all_integrity, "tests": tests,
                                "production_authorized": False},
                      inference_limit="Only implemented fault tests; not a security certification.")
    return records


def analyze(results, primary_seed=7):
    out = results / "analysis"
    out.mkdir(exist_ok=True)
    study = read_json(results / "study.json")
    tests = read_json(results / "tests.json")
    validate_tests_record(tests)
    runs = []
    histories = {}
    integrity = {}
    for path in sorted(results.glob("*_seed*/run_summary.json")):
        run_dir = path.parent
        r, history, check = verify_run_bundle(run_dir, study, results / "study.json")
        integrity[run_dir.name] = check
        if not check["valid"] or not check["artifact_hashes_match"]:
            raise RuntimeError(f"Fail closed: invalid evidence in {run_dir}")
        runs.append(r)
        histories[r["mode"], r["seed"]] = history
    if not runs:
        raise ValueError("No completed runs")
    primary = results / f"full_seed{primary_seed}"
    archive = Archive.load(primary / "archive.npz")
    full_replay = None
    replay_path = results / "full_archive_replay.json"
    if replay_path.exists():
        full_replay = read_json(replay_path)
        if (full_replay.get("valid") is not True or
                full_replay.get("archive_sha256") != digest_file(primary / "archive.npz") or
                full_replay.get("elites_checked") != int(archive.filled.sum())):
            raise ValueError("Full-archive replay record does not match primary archive")
    G, F, BD = archive.elites()
    mask = archive.filled
    ops = read_json(primary / "operators.json")
    hypothesis_records = assess_hypotheses(study, runs, True, tests)
    evidence = {"integrity_ok": True, "tests_ok": tests["successful"], "evidence_count": len(runs)}
    proposal = make_proposal(evidence)
    proposal["hypothesis_verdicts"] = {r["id"]: r["verdict"] for r in hypothesis_records}
    proposal["integration_status"] = "NOT_CONNECTED_TO_OCTOPUS_CORE"
    proposal["research_sources_status"] = "UPLOADED_MEGAPROMPT_LEADS_NOT_REVALIDATED"

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 12,
                         "axes.titleweight": "bold", "axes.spines.top": False,
                         "axes.spines.right": False, "figure.facecolor": "#F7F6F2",
                         "axes.facecolor": "#FBFBF9", "text.color": "#28251D",
                         "axes.labelcolor": "#28251D", "savefig.dpi": 160})
    # Archive panels use genuine FIRST discovery timestamps.
    fig, axs = plt.subplots(1, 3, figsize=(15.5, 5.2), layout="constrained")
    panels = [
        (archive.fitness, "viridis", "Quality at each behavioral niche", "Fitness", 0, 1),
        (np.where(mask, archive.first_generation, np.nan), "cividis", "First discovery of each niche", "Generation", 0, study["config"]["generations"]),
        (np.where(mask, archive.meta["collision_rate"], np.nan), "magma", "Collision rate of retained elite", "Blocked steps / 320", 0, 1),
    ]
    for ax, (data, cm, title, unit, vmin, vmax) in zip(axs, panels):
        im = ax.imshow(data.T, origin="lower", extent=(0, 1, 0, 1), cmap=cm,
                       vmin=vmin, vmax=vmax, interpolation="nearest")
        draw_maze(ax)
        ax.set_title(title)
        fig.colorbar(im, ax=ax, fraction=.045, pad=.03, label=unit)
    fig.suptitle(f"OCTOPUS QD Lab | {archive.grid} x {archive.grid} archive | seed {primary_seed}\n"
                 "Dark geometry = obstacles; blank niches = no elite", fontsize=14)
    fig.savefig(out / "01_archive_maps.png", bbox_inches="tight")
    plt.close(fig)

    # Mean + min/max across available seeds, NOT a confidence interval.
    fig, axs = plt.subplots(2, 2, figsize=(13, 8.6), layout="constrained")
    for ax, metric, title, unit, factor in (
        (axs[0, 0], "coverage", "Behavioral coverage grows", "All-grid coverage (%)", 100),
        (axs[0, 1], "qd_score", "Quality and diversity together", "Sum of elite fitness", 1),
        (axs[1, 0], "mean_fitness", "Mean quality within the archive", "Mean fitness", 1),
        (axs[1, 1], "bd_entropy", "Distribution across 8 x 8 macro-bins", "Shannon entropy (bits)", 1),
    ):
        for mode in COLORS:
            hs = [h for (m, _), h in histories.items() if m == mode]
            if not hs:
                continue
            x = [v["gen"] for v in hs[0]]
            y = np.array([[v[metric] * factor for v in h] for h in hs])
            ax.plot(x, y.mean(axis=0), color=COLORS[mode], linestyle=STYLES[mode], lw=2,
                    label=f"{LABELS[mode]} (n={len(hs)})")
            if len(hs) > 1:
                ax.fill_between(x, y.min(axis=0), y.max(axis=0), color=COLORS[mode], alpha=.12)
        ax.set(title=title, xlabel="Generation (0 = random initialization)", ylabel=unit)
        ax.grid(axis="y", color="#D4D1CA", alpha=.6)
        if metric in ("coverage", "qd_score"):
            ax.set_ylim(bottom=0)
        if metric == "coverage":
            ax.set_ylim(0, 100)
        if metric == "mean_fitness":
            ax.set_ylim(0, 1)
        if metric == "bd_entropy":
            ax.set_ylim(0, 6.05)
    axs[0, 0].legend(fontsize=9, loc="lower right", frameon=False)
    fig.suptitle("OCTOPUS QD Lab | Evolution versus fresh sampling\n"
                 "Lines = seed means; bands = observed min/max, not confidence intervals", fontsize=14)
    fig.savefig(out / "02_diversity_growth.png", bbox_inches="tight")
    plt.close(fig)

    # Six reproducible exemplar trajectories, separated to avoid overplotting.
    selected = [int(np.argmax(F))]
    while len(selected) < min(6, len(F)):
        d = np.linalg.norm(BD[:, None, :] - BD[selected][None, :, :], axis=-1).min(axis=1)
        d[selected] = -1
        selected.append(int(np.argmax(d)))
    replay_f, replay_bd, replay_info = env.evaluate(G[selected], record_traj=True)
    np.testing.assert_allclose(replay_f, F[selected], atol=1e-12, rtol=0)
    np.testing.assert_allclose(replay_bd, BD[selected], atol=1e-12, rtol=0)
    fig, axs = plt.subplots(2, 3, figsize=(12.6, 8.5), layout="constrained")
    for ax, slot in zip(axs.flat, range(6)):
        if slot >= len(selected):
            ax.set_visible(False)
            continue
        traj = replay_info["traj"][:, slot]
        draw_maze(ax)
        ax.plot(traj[:, 0], traj[:, 1], color="#20808D", lw=1.7)
        ax.plot(*env.START, marker="*", color="#A84B2F", ms=11, zorder=8)
        ax.plot(*traj[-1], marker="o", color="#20808D", ms=6, zorder=8)
        ax.set_title(f"Elite {int(archive.ids[mask][selected[slot]])} | q={replay_f[slot]:.3f}\n"
                     f"BD=({traj[-1,0]:.3f}, {traj[-1,1]:.3f})")
    fig.suptitle("Six brains, six observed behaviors\n"
                 "Highest quality first, then greedy farthest-point selection; star = common start", fontsize=14)
    fig.savefig(out / "03_elite_trajectories.png", bbox_inches="tight")
    plt.close(fig)

    # Genetic structure, descriptive statistics only.
    centered = G - G.mean(axis=0)
    _, S, Vt = np.linalg.svd(centered, full_matrices=False)
    evr = S**2 / np.sum(S**2)
    pc = centered @ Vt[:2].T
    rng = np.random.default_rng(99)
    chosen = rng.choice(len(G), min(300, len(G)), replace=False)
    dg = np.linalg.norm(G[chosen][:, None] - G[chosen][None], axis=2)
    db = np.linalg.norm(BD[chosen][:, None] - BD[chosen][None], axis=2)
    ii = np.triu_indices(len(chosen), 1)
    corr = float(np.corrcoef(dg[ii], db[ii])[0, 1])
    fig, axs = plt.subplots(2, 2, figsize=(12.4, 8.5), layout="constrained")
    sc = axs[0, 0].scatter(pc[:, 0], pc[:, 1], c=BD[:, 1], s=8, cmap="viridis", alpha=.65)
    axs[0, 0].set(title="Genome PCA, colored by final y",
                  xlabel=f"PC1 ({100*evr[0]:.1f}% variance)", ylabel=f"PC2 ({100*evr[1]:.1f}% variance)")
    fig.colorbar(sc, ax=axs[0, 0], label="Final y", fraction=.04)
    axs[0, 1].plot(np.arange(1, len(evr)+1), np.cumsum(evr)*100, color="#20808D")
    axs[0, 1].axhline(90, color="#7A7974", linestyle=":")
    axs[0, 1].set(title="Cumulative genetic variance", xlabel="Number of principal components", ylabel="Explained variance (%)", ylim=(0, 101))
    for (layer, (a, b, _)), color, style in zip(
            env.LAYER_SLICES.items(), ["#20808D", "#A84B2F", "#1B474D", "#944454"], ["-", "--", ":", "-."]):
        axs[1, 0].hist(G[:, a:b].ravel(), bins=60, density=True, histtype="step", label=layer,
                       lw=1.5, color=color, linestyle=style)
    axs[1, 0].set(title="Weight distribution by layer", xlabel="Parameter value", ylabel="Density")
    axs[1, 0].legend(frameon=False)
    axs[1, 1].hexbin(dg[ii], db[ii], gridsize=40, cmap="cividis", mincnt=1)
    axs[1, 1].set(title=f"Genome distance vs. endpoint distance | r={corr:.3f}",
                  xlabel="Euclidean distance in 74 weights", ylabel="Euclidean distance in 2D behavior")
    fig.suptitle("Genetic structure of retained controllers\n"
                 "Correlation is descriptive; neuron permutation symmetry is not removed", fontsize=14)
    fig.savefig(out / "04_genetic_structure.png", bbox_inches="tight")
    plt.close(fig)

    cards = [genome_card(archive, i) for i in selected]
    best = cards[0]
    fig, axs = plt.subplots(1, 4, figsize=(13.5, 4.3), layout="constrained",
                            gridspec_kw={"width_ratios": [3, 1, 1.5, 1]})
    for ax, key, title in zip(axs, ("W1", "b1", "W2", "b2"),
                               ("W1: sensors to hidden", "b1: hidden bias", "W2: hidden to motors", "b2: motor bias")):
        matrix = np.atleast_2d(np.array(best[key]))
        if key in ("b1", "b2"):
            matrix = matrix.T
        im = ax.imshow(matrix, cmap="RdBu_r", vmin=-4, vmax=4, aspect="auto")
        ax.set_title(title, fontsize=10)
        ax.set_xticks(np.arange(matrix.shape[1]))
        ax.set_yticks(np.arange(matrix.shape[0]))
        if key == "W1":
            ax.set_yticklabels(env.INPUT_NAMES)
        for (i, j), value in np.ndenumerate(matrix):
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=8,
                    color="white" if abs(value) > 2.2 else "#28251D")
    fig.colorbar(im, ax=list(axs), shrink=.9, label="Weight")
    fig.suptitle(f"Actual 74-parameter genome | elite {best['id']} | fitness {best['fitness']:.4f}\n"
                 "Shown rounded; exact matrices and genome available in elite_cards.json", fontsize=14)
    fig.savefig(out / "05_best_genome.png", bbox_inches="tight")
    plt.close(fig)

    vitality = [observe_vitality(float(p), float(c), float(t)) for p, c, t in
                zip(archive.meta["path_len"][mask], archive.meta["collision_rate"][mask],
                    archive.meta["turn_effort"][mask])]
    zones = {z: sum(v["status"] == z for v in vitality) for z in ("GREEN", "YELLOW", "RED", "BLACK")}
    rooms = room_masks(BD)
    room_data = {name: {"elites": int(m.sum()), "mean_fitness": float(F[m].mean()) if m.any() else None,
                        "median_first_discovery": float(np.median(archive.first_generation[mask][m])) if m.any() else None,
                        "median_last_replacement": float(np.median(archive.last_generation[mask][m])) if m.any() else None}
                 for name, m in rooms.items()}
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.9), layout="constrained")
    keys = [k for k in ("line", "xover", "mut") if ops[k]["attempts"]]
    rates = [100*ops[k]["admitted"]/ops[k]["attempts"] for k in keys]
    bars = axs[0].bar(keys, rates, color="#20808D", width=.6)
    for bar, value in zip(bars, rates):
        axs[0].text(bar.get_x()+bar.get_width()/2, value+.5, f"{value:.1f}%", ha="center")
    axs[0].set(title="Sequential archive admissions", ylabel="Admitted / attempted (%)", ylim=(0, max(rates)*1.3))
    axs[0].set_xticks(range(len(keys)), ["Iso+LineDD" if k=="line" else "Crossover\n+ mutation" if k=="xover" else "Mutation" for k in keys])
    axs[1].barh(list(room_data), [v["elites"] for v in room_data.values()], color="#20808D")
    axs[1].set(title="Endpoints in rooms and passages", xlabel="Number of elites")
    axs[2].bar(list(zones), list(zones.values()), color="#73736C", hatch="/")
    axs[2].tick_params(axis="x", labelsize=9)
    axs[2].set(title="Observe-only resource proxy", ylabel="Number of elites")
    fig.suptitle("OCTOPUS diagnostics | simulated evidence, not execution authority\n"
                 "Vitality zones are toy indicators; they do not control this experiment", fontsize=14)
    fig.savefig(out / "06_octopus_diagnostics.png", bbox_inches="tight")
    plt.close(fig)

    # Full precision portable exports.
    csv_columns = ["elite_id", "cell_i", "cell_j", "bd_x", "bd_y", "fitness",
                   "first_generation", "last_generation", "parent_a", "parent_b", "operator",
                   *archive.meta, "vitality_zone", *[f"w{i}" for i in range(env.GENOME_DIM)]]
    with (out / "elites_archive.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(csv_columns)
        for k, (i, j) in enumerate(np.argwhere(mask)):
            writer.writerow([int(archive.ids[i,j]), int(i), int(j), *archive.bd[i,j], archive.fitness[i,j],
                             int(archive.first_generation[i,j]), int(archive.last_generation[i,j]),
                             *archive.parents[i,j], archive.operators[i,j],
                             *[values[i,j] for values in archive.meta.values()],
                             vitality[k]["status"], *archive.genomes[i,j]])
    with (out / "history_all_runs.csv").open("w", encoding="utf-8", newline="") as f:
        cols = ["mode", "seed", *next(iter(histories.values()))[0]]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for (mode, seed), h in histories.items():
            for row in h:
                w.writerow(dict(mode=mode, seed=seed, **row))
    aggregate = {}
    for mode in COLORS:
        subset = [r for r in runs if r["mode"] == mode]
        if subset:
            aggregate[mode] = {"n": len(subset), "metrics": {
                name: {"mean": float(np.mean(v)), "std": float(np.std(v, ddof=1)) if len(v)>1 else None,
                       "min": float(np.min(v)), "max": float(np.max(v))}
                for name in ("coverage", "center_free_coverage", "qd_score", "mean_fitness", "n_elites")
                for v in [[r["final"][name] for r in subset]]}}
    summary = {
        "title": "آزمایشگاه تکاملی اختاپوس",
        "study": study, "primary_run": read_json(primary / "run_summary.json"),
        "aggregate": aggregate, "runs": runs, "operators": ops, "rooms": room_data,
        "genetics": {"pca_evr": evr.tolist(), "pca_dims_for_90pct": int(np.searchsorted(np.cumsum(evr), .90)+1),
                     "genotype_behavior_distance_pearson": corr, "distance_sample_size": len(chosen),
                     "layer_stats": {name: {"mean": float(G[:,a:b].mean()), "std": float(G[:,a:b].std()),
                                           "min": float(G[:,a:b].min()), "max": float(G[:,a:b].max())}
                                     for name, (a,b,_) in env.LAYER_SLICES.items()}},
        "vitality_counts": zones, "integrity": integrity, "tests": tests,
        "replay_checked_elites": len(selected), "full_archive_replay": full_replay, "proposal": proposal,
        "hypotheses": hypothesis_records, "elite_cards": cards,
        "limitations": ["Toy navigation, not production OCTOPUS or robot validation.",
                        "Coverage = filled cells / all grid cells. Center-free coverage is only a geometric approximation.",
                        "Activity-weighted smoothness is not shortest-path efficiency; loops can score well.",
                        "Same environment, three seeds, no independent evaluator or statistical significance claim.",
                        "Hash chain is local and unsigned. Local anchors do not prevent total rewrite.",
                        "Architecture and topology fixed at 6-8-2; no neural gradient learning, world model, or real edge deployment.",
                        "Uploaded external project leads are not treated as independently verified evidence."],
    }
    dump_json(out / "summary.json", summary)
    dump_json(out / "hypothesis_records.json", hypothesis_records)
    dump_json(out / "promotion_proposal.json", proposal)
    dump_json(out / "elite_cards.json", cards)
    dump_json(out / "self_model.json", {
        "kind": "STRUCTURAL_SELF_DESCRIPTION_NOT_WORLD_MODEL",
        "core_connected": False, "execution_handles": [],
        "controller": {"architecture": [6,8,2], "activation": "tanh", "parameters": 74},
        "descriptors": ["final_x", "final_y"],
        "archive_role": "Persisted niche-to-controller skill memory; parent reuse is explicitly recorded.",
        "known": ["local evaluated trajectories", "genomes", "local receipt integrity"],
        "unknown": ["real hardware performance", "external task utility", "generalization", "independent audit"],
        "candidate_affordances": [
            {"name": "skill archive", "measured_test": "OQD-H1", "status": "LOCAL_ONLY"},
            {"name": "operator selection", "measured_test": "OQD-H2", "status": "LOCAL_ONLY"},
            {"name": "evidence gate", "measured_test": "OQD-H3", "status": "LOCAL_ONLY"}],
    })
    print(json.dumps({"primary": summary["primary_run"]["final"], "aggregate": aggregate,
                      "hypotheses": [dict(id=h["id"], verdict=h["verdict"]) for h in hypothesis_records],
                      "tests": tests, "replay_checked": len(selected)}, indent=2))
    return summary


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--results", type=Path, default=Path(__file__).resolve().parent / "results")
    p.add_argument("--primary-seed", type=int, default=7)
    args = p.parse_args()
    analyze(args.results, args.primary_seed)
