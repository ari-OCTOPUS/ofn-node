"""
REAL experiment for specs/hybrid_organism.yaml — H-HYBRID-01.

The "hybrid-trainest": the four kernel mechanisms proven in isolation, combined
into ONE cortex organ that learns to predict the LIVE octopus organism's own
behavior from its real event stream (read-only, F:\\backup). This is the
sanctioned Ring-2 self-monitoring / consolidation organ the body's own 2027
backlog marks 🔴 OPEN.

Mechanisms combined:
  WM-gating (H-OWN-03)      select K transferable features from the 10-feature
                            event-context vocabulary (greedy forward selection).
  schema consolidation      consolidate train experience into a bin -> majority
    (H-OWN-04)              next-event library (denoised, reusable).
  RTA geometry (H-GEO-01)   report alignment(coverage x purity) of the gated
                            representation with the target on the future window.
  temporal transfer         the honest self-model test: train on the organism's
    (the kernel ethos)      EARLIER events, predict its LATER behavior
                            (chronological 70/30 split), not a random split.

Task: predict the organism's NEXT event_name from the current event context.

DECISION (what the kernel itself decides): does a bounded-WM, schema-
consolidated self-model understand the body's dynamics better than the majority
baseline, AND does the bottleneck transfer across time better than an unbounded
full-feature model? The decision_rule turns this into DISCARD/OPTIMIZE/INTEGRATE
= "don't attach / attach shadow-only and keep improving / sanctioned to attach
as an observing cortex (still propose-only, behind the owner's Orange gate)".

SCOPE (locked, per the body's hard red line 2027-backlog:20): access /
functional self-monitoring ONLY. NO phenomenal / qualia / sentience claim. The
kernel is afferent-broadband, efferent propose-only; it never writes to the
body, never touches the TCB, never acts outward.
"""
from __future__ import annotations

from collections import Counter
from operator import itemgetter
from random import Random
from typing import List, Sequence, Tuple

from spec_compiler.harness import Condition

from .organism_bridge import FEATURE_ORDER, N_FEATURES, build_dataset

TARGET = "next_event_name"
VAL_FRAC = 0.15                   # last slice of TRAIN used to score gating
PRIMARY_K = 2                     # WM capacity = the minimal sufficient context
                                  # (agent, event_name). NOTE (adversarial
                                  # review): phase_idx = CYCLE.index(agent) is a
                                  # deterministic function of agent, so it never
                                  # subdivides a bin — K=3 was silently K=2. The
                                  # honest minimal set is "who + what", not
                                  # "who/what/where-in-cycle".
# each confirmatory seed is a DIFFERENT chronological cut -> real variance +
# robustness of the self-model to where we cut the body's timeline.
TRAIN_FRACS = (0.60, 0.65, 0.70, 0.75, 0.80)
HYBRID_LOG: dict = {}


def _key(slots: Sequence[int]):
    return itemgetter(*slots) if len(slots) > 1 else (lambda r, _i=slots[0]: (r[_i],))


def _consolidate(X: Sequence[tuple], Y: Sequence[str], slots: Sequence[int]):
    """bin(gated features) -> majority next-event; plus the global majority for
    backoff on unseen bins."""
    key = _key(slots)
    bins: dict = {}
    for x, y in zip(X, Y):
        bins.setdefault(key(x), Counter())[y] += 1
    lib = {}
    for k, c in bins.items():
        best, bn = None, -1
        for a in sorted(c):                       # deterministic tie-break
            if c[a] > bn:
                best, bn = a, c[a]
        lib[k] = best
    gmaj = Counter(Y).most_common(1)[0][0]
    return lib, gmaj


def _score(X, Y, slots, lib, gmaj) -> float:
    """Prediction accuracy: gated-bin majority, backing off to global majority."""
    key = _key(slots)
    hits = 0
    for x, y in zip(X, Y):
        pred = lib.get(key(x), gmaj)
        hits += (pred == y)
    return hits / len(Y) if Y else 0.0


def _alignment(Xtr, Ytr, Xte, Yte, slots) -> float:
    """RTA: fraction of heldout rows whose gated bin was seen in train AND whose
    train-majority equals the true label (coverage x purity)."""
    key = _key(slots)
    lib, _ = _consolidate(Xtr, Ytr, slots)
    hits = tot = 0
    for x, y in zip(Xte, Yte):
        k = key(x)
        tot += 1
        if k in lib and lib[k] == y:
            hits += 1
    return hits / tot if tot else 0.0


def _select_slots(Xfit, Yfit, Xval, Yval, k: int) -> List[int]:
    """WM-gating: greedy forward selection maximizing validation accuracy."""
    selected: List[int] = []
    remaining = list(range(N_FEATURES))
    for _ in range(k):
        best_f, best_s = None, -1.0
        for f in remaining:
            cand = sorted(selected + [f])
            lib, gmaj = _consolidate(Xfit, Yfit, cand)
            s = _score(Xval, Yval, cand, lib, gmaj)
            if s > best_s:
                best_f, best_s = f, s
        selected.append(best_f)
        remaining.remove(best_f)
    return sorted(selected)


def _splits(train_frac: float):
    X, Y = build_dataset(TARGET)
    n = len(X)
    n_tr = int(n * train_frac)
    n_fit = int(n_tr * (1 - VAL_FRAC))
    return (X[:n_fit], Y[:n_fit], X[n_fit:n_tr], Y[n_fit:n_tr],
            X[:n_tr], Y[:n_tr], X[n_tr:], Y[n_tr:])


def _run_all(k: int, train_frac: float):
    Xfit, Yfit, Xval, Yval, Xtr, Ytr, Xte, Yte = _splits(train_frac)
    gmaj_tr = Counter(Ytr).most_common(1)[0][0]
    base = sum(1 for y in Yte if y == gmaj_tr) / len(Yte)
    # honest zero-mechanism baseline: group-by the single feature the target is
    # a shifted copy of (current event_name) — the fair reference, not majority.
    en_slot = (FEATURE_ORDER.index("event_name"),)
    lib_e, gm_e = _consolidate(Xtr, Ytr, en_slot)
    single_feat = _score(Xte, Yte, en_slot, lib_e, gm_e)
    all_slots = tuple(range(N_FEATURES))                # unlimited: full-feature
    lib_u, gm_u = _consolidate(Xtr, Ytr, all_slots)
    unlimited = _score(Xte, Yte, all_slots, lib_u, gm_u)
    slots = _select_slots(Xfit, Yfit, Xval, Yval, k)    # hybrid: gated + consolidation
    lib_h, gm_h = _consolidate(Xtr, Ytr, slots)
    hybrid = _score(Xte, Yte, slots, lib_h, gm_h)
    align = _alignment(Xtr, Ytr, Xte, Yte, slots)
    return {"baseline": base, "single_feat": single_feat, "unlimited": unlimited,
            "hybrid": hybrid, "gain": hybrid - base,
            "gain_over_single": hybrid - single_feat,
            "hybrid_vs_unlimited": hybrid - unlimited,
            "alignment": align, "slots": [FEATURE_ORDER[s] for s in slots]}


def _make(name: str, kind: str) -> Condition:
    counter = {"i": 0}

    def run(_rng: Random) -> float:
        i = counter["i"]
        counter["i"] += 1
        frac = TRAIN_FRACS[i % len(TRAIN_FRACS)]     # each seed = a temporal cut
        r = _run_all(PRIMARY_K, frac)
        HYBRID_LOG.setdefault(name, []).append({"seed_index": i, "train_frac": frac, **r})
        if kind == "selfpred":
            return r["hybrid"]                        # reported: raw self-prediction accuracy
        if kind == "gain_over_single":
            return r["gain_over_single"]             # reported: gain over the fair single-feature baseline
        return r["hybrid_vs_unlimited"]              # PRIMARY (the falsifiable content)

    return Condition(name, run, name)


def hybrid_organism() -> Tuple[List[Condition], str]:
    # PRIMARY is now the WM-bottleneck temporal-transfer advantage — the actual
    # falsifiable content of the hypothesis (it CAN be <= 0). The raw
    # self-prediction accuracy and the fair-baseline gain are REPORTED context,
    # not gated (adversarial review 2026-07-14: gating on absolute accuracy was
    # clearable by a trivial 2-column lookup — a non-falsifiable gate).
    conditions = [
        _make("hybrid_selfpred", "selfpred"),          # reported: raw accuracy (~0.95, trivially high)
        _make("gain_over_single", "gain_over_single"),  # reported: over the fair single-feature baseline
        _make("bottleneck_advantage", "vs_unlimited"),  # PRIMARY: WM-bottleneck vs full-feature on the future
    ]
    return conditions, "bottleneck_advantage"


# ---------------------------------------------------------------- smoke
if __name__ == "__main__":
    import json
    from .organism_bridge import export_snapshot
    export_snapshot()
    print("Temporal-cut sweep on the organism's real event stream (K=%d fixed):" % PRIMARY_K)
    print(f"{'frac':>6}{'baseline':>10}{'unlimited':>11}{'hybrid':>9}"
          f"{'vs_unlim':>10}{'align':>8}")
    for frac in TRAIN_FRACS:
        r = _run_all(PRIMARY_K, frac)
        print(f"{frac:>6.2f}{r['baseline']:>10.3f}{r['unlimited']:>11.3f}{r['hybrid']:>9.3f}"
              f"{r['hybrid_vs_unlimited']:>+10.3f}{r['alignment']:>8.3f}")
    print("\nK sensitivity at frac=0.70:")
    for k in range(2, 8):
        r = _run_all(k, 0.70)
        print(f"  K={k}: hybrid={r['hybrid']:.3f} vs_unlim={r['hybrid_vs_unlimited']:+.3f} "
              f"slots={r['slots']}")
