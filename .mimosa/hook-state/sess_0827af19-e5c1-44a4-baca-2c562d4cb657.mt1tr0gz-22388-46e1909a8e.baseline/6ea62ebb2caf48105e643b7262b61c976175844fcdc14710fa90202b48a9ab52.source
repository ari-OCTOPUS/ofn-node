"""
REAL experiment for specs/adaptive_forgetting_v2.yaml — EXP-004b / H-OWN-09b.

DECLARED FOLLOW-UP to ADR-015 (adaptive_forgetting v1). v1's machine gate used
the WEAKEST baseline (cumulative / never-forget); against the STRONGER baseline
(FIFO, forgets-by-accident) the confirmatory edge was +0.018 — BELOW the 0.03
SESOI. v2 preregisters the honest hard test:

    PRIMARY (gated) = success(adaptive) − success(FIFO)
                      at EQUAL bounded capacity C, under drift, post-drift heldout.

This is preregistered KNOWING it may DISCARD: v1's raw-decay rule already failed
this bar (+0.018 < 0.03 [FACT: ADR-015 confirmatory, family 965000]). A negative
verdict is a legitimate, reportable outcome. v1 stays untouched; v2 only imports.

THE ONE PRINCIPLED STRENGTHENING (declared A PRIORI, before any v2 pilot data)
-------------------------------------------------------------------------------
v1's retention utility is the recency-DECAYED COUNT of winning re-uses
(util = Σ γ^Δ over hits). Two a-priori biases of a decayed count, both pushing
it AWAY from tracking the current regime — exactly the axis on which FIFO (pure
age) is accidentally strong under a purely temporal drift:

  (i)  frequency conflation — a rule heavily re-used PRE-drift accrues mass that
       outlives its regime (γ=0.98 halves in ~34 ticks; a 10-hit stale rule
       still outweighs a fresh 1-hit rule for ~115 ticks), so stale-but-formerly-
       popular rules are over-retained: precisely the staleness failure the
       mechanism is supposed to fix.
  (ii) tenure asymmetry — a fresh in-regime rule enters at 1.0 and competes
       against incumbents' accumulated mass, so post-drift rules (the ones the
       heldout needs) are under-protected while they build their record.

Fix: utility = recency-decayed HIT-RATE, i.e. decayed hits NORMALIZED by decayed
exposure (ticks spent in the store, same γ):

    rate_k(t) = H_k(t) / E_k(t)
    H_k(t)    = Σ_{hits j} γ^(t−t_j)                       (v1's decayed count)
    E_k(t)    = Σ_{s=born_k..t} γ^(t−s) = (1−γ^(t−born_k+1))/(1−γ)

A stale-popular rule's rate → 0 as recent hit-free exposure accrues regardless
of how big its past mass was (fixes i); a fresh rule starts at rate 1.0 (max)
and is judged only on its own tenure (fixes ii). Same signal (winning re-use),
same γ=0.98, same everything else — ONE change, at the utility definition.
Chosen from the mechanism argument above BEFORE the v2 pilot ran; the pilot only
calibrates prediction.expected, it does not select among candidate rules.

Non-strawman guards:
  - The PRIMARY baseline IS the strong one (FIFO). Under this purely temporal
    drift oldest≈stalest, so FIFO forgets stale rules by accident; v1's rule
    failed to clear it. The metric is genuinely falsifiable (v1 evidence says
    it sits near +0.018, below the gate) and cannot be cleared without the
    mechanism-specific quantity (utility-over-age retention edge).
  - null_unbounded (structural ~0): the SAME adaptive−FIFO delta at capacity ≥
    pool size. No eviction ever fires → both arms retain the whole pool →
    identical stores → delta EXACTLY 0. Proves any edge is capacity-driven.
  - null_nodrift (≤ 0): the recency-necessity null, on the decay knob WITHIN the
    identical rate algorithm (γ=0.98 vs γ=1.0 lifetime rate) on a STATIONARY
    stream. With no drift there are no stale rules, so decaying the evidence can
    only discard information → contrast must be ≤ ~0. DISCLOSED a priori: the
    nodrift contrast is NOT adaptive−FIFO, because utility-gating beats blind
    eviction even without drift (the H-OWN-06 effect; v1 pilot: adaptive−random
    +0.039 with no drift) — that generic effect is not the quantity under test.
    Same discipline as v1's null_nodrift (ADR-015).
  - vs_raw_decay (reported): rate-utility − v1's raw-decay utility at bounded C
    under drift — isolates what the strengthening itself added.
  - v1_rule_vs_fifo (reported): v1's raw-decay rule − FIFO on THIS family — the
    v1-replication reference point for the same universes.

Frozen inheritances from v1 (NOT re-tuned on the v2 pilot): capacity C=90,
γ=0.98, stream lengths 300+120, modality mixes 85/15→15/85, heldout 90% shape,
B_TRAIN=80k, SESOI 0.03 and the DISCARD/OPTIMIZE/INTEGRATE bands.

Determinism: identical scheme to v1 — universe, base policy, streams and event
sequences are CRC-seeded from the seed-index i (the harness RNG is ignored, as
its seed differs by condition name), so every condition sees the identical
universe and differs ONLY in the retention rule. Universes are memoized per
(family, i). PILOT family 948000 (assigned) set prediction.expected, then was
FROZEN; CONFIRMATORY family 953000 is disjoint from the pilot and from every
other family in the repo (948500/953500 second-suite offsets included). No LLM.

CONFIRMATORY OUTCOME (2026-07-14, family 953000 — recorded AFTER the frozen
run; the a-priori text above is preserved unchanged as the preregistration
record). adaptive_advantage_v2 = +0.023 ± 0.021 < SESOI 0.03 →
failure_condition TRIGGERED → VERDICT: REJECTED (DISCARD band), the outcome
the preregistration named as likely [all FACT: run log]. Controls held
(null_unbounded 0.000 exactly; null_nodrift −0.008 ≤ 0). vs_raw_decay =
+0.005 ± 0.020: the hit-rate strengthening is real as a DEFINITION (it does
remove the two biases above) but bought ~nothing vs FIFO here — under a purely
temporal drift oldest≈stalest, so blind age already captures most of the value
of forgetting. v1's OPTIMIZE (ADR-015) stands only for adaptive-vs-never-
forget; the strong claim is rejected. Full record + confirmed caveats:
adr/ADR-021-adaptive-forgetting-v2.md.
"""
from __future__ import annotations

import zlib
from random import Random
from typing import Dict, List, Set, Tuple

from spec_compiler.harness import Condition

from .adaptive_forgetting import (
    B_TRAIN, CAPACITY, DECAY, EARLY_SHAPE, HELDOUT_N, HELDOUT_SHAPE,
    LATE_SHAPE, SLOTS, STREAM_EARLY, STREAM_LATE, UNBOUNDED,
    _draw_stream, _partition, _success, build_events, replay,
)
from .gridworld_wm import build_suite, train

# ---------------------------------------------------------------- constants
AFV2_CONF_SEED = 953_000   # CONFIRMATORY family (disjoint from all others incl.
                           # its own +500 second-suite offset 953500+)
AFV2_PILOT_SEED = 948_000  # assigned PILOT family (948000+ / 948500+); set
                           # prediction.expected, then FROZEN — never confirmatory

AFV2_LOG: dict = {}
_UNIVERSE_CACHE: dict = {}   # (base_seed, i) -> (ev_drift, ev_nodrift, key_action, heldout)


# ---------------------------------------------------------------- the ONE change
def replay_rate(events: List[List[tuple]], capacity: int,
                decay: float = DECAY) -> Set[tuple]:
    """v2 retention rule: bounded store evicting the lowest recency-decayed
    HIT-RATE = decayed hits / decayed exposure (ticks in store, same decay).
    decay=1.0 degenerates to the lifetime mean hit-rate (no recency) — the
    cumulative-rate arm of the nodrift null. Deterministic given events."""
    hits: Dict[tuple, float] = {}   # decayed hit mass at tick `last[k]`
    last: Dict[tuple, int] = {}     # tick of the last hit-update
    born: Dict[tuple, int] = {}     # insertion tick
    store: Dict[tuple, None] = {}

    def rate(k: tuple, tick: int) -> float:
        h = hits[k] * (decay ** (tick - last[k]))
        if decay == 1.0:
            e = float(tick - born[k] + 1)
        else:
            e = (1.0 - decay ** (tick - born[k] + 1)) / (1.0 - decay)
        return h / e

    for tick, keys in enumerate(events):
        for k in keys:
            if k in store:
                hits[k] = hits[k] * (decay ** (tick - last[k])) + 1.0
                last[k] = tick
                continue
            if len(store) >= capacity:
                victim = min(store, key=lambda kk: rate(kk, tick))
                del store[victim], hits[victim], last[victim], born[victim]
            store[k] = None
            hits[k] = 1.0
            last[k] = tick
            born[k] = tick
    return set(store)


# ---------------------------------------------------------------- universe
def _universe_v2(i: int, base_seed: int = AFV2_CONF_SEED):
    """Identical construction to v1's _universe (ADR-015), rebuilt here with a
    (family, i) cache key so v2 can never poison v1's per-i cache and the pilot
    family can never alias the confirmatory one. Returns
    (ev_drift, ev_nodrift, key_action, heldout)."""
    key = (base_seed, i)
    if key in _UNIVERSE_CACHE:
        return _UNIVERSE_CACHE[key]
    pool = (build_suite(base_seed + i) + build_suite(base_seed + 500 + i))
    color, shape = _partition(pool)
    n_shape_h = round(HELDOUT_N * HELDOUT_SHAPE)
    n_color_h = HELDOUT_N - n_shape_h
    held = shape[-n_shape_h:] + color[-n_color_h:]
    color_tr, shape_tr = color[:-n_color_h], shape[:-n_shape_h]
    Q_base: dict = {}
    train(Q_base, color_tr + shape_tr, SLOTS, B_TRAIN,
          Random(zlib.crc32(f"base|{base_seed}|{i}".encode())))
    srng = Random(zlib.crc32(f"stream|{base_seed}|{i}".encode()))
    early = _draw_stream(color_tr, shape_tr, STREAM_EARLY, EARLY_SHAPE, srng)
    late = _draw_stream(color_tr, shape_tr, STREAM_LATE, LATE_SHAPE, srng)
    ev, ka = build_events(Q_base, early + late, SLOTS,
                          Random(zlib.crc32(f"roll|{base_seed}|{i}".encode())))
    nrng = Random(zlib.crc32(f"streamNod|{base_seed}|{i}".encode()))
    e2 = _draw_stream(color_tr, shape_tr, STREAM_EARLY, HELDOUT_SHAPE, nrng)
    l2 = _draw_stream(color_tr, shape_tr, STREAM_LATE, HELDOUT_SHAPE, nrng)
    ev2, ka2 = build_events(Q_base, e2 + l2, SLOTS,
                            Random(zlib.crc32(f"rollNod|{base_seed}|{i}".encode())))
    for k, v in ka2.items():
        ka.setdefault(k, v)      # actions are Q_base-deterministic -> consistent merge
    out = (ev, ev2, ka, held)
    _UNIVERSE_CACHE[key] = out
    return out


# ---------------------------------------------------------------- conditions
def _make(name: str, kind: str, base_seed: int = AFV2_CONF_SEED) -> Condition:
    counter = {"i": 0}

    def run(_rng: Random) -> float:
        i = counter["i"]
        counter["i"] += 1
        ev, ev2, ka, held = _universe_v2(i, base_seed)

        if kind == "null_unbounded":
            # SAME contrast as the primary (rate-adaptive vs FIFO) with NO
            # capacity pressure: no eviction fires -> identical stores -> 0.
            a = _success(replay_rate(ev, UNBOUNDED), ka, held)
            b = _success(replay(ev, UNBOUNDED, "fifo"), ka, held)
        elif kind == "null_nodrift":
            # recency-necessity null on a STATIONARY stream: identical rate
            # algorithm, decay on vs off. No drift -> no stale rules -> decay
            # only discards evidence -> must be <= ~0.
            a = _success(replay_rate(ev2, CAPACITY), ka, held)
            b = _success(replay_rate(ev2, CAPACITY, decay=1.0), ka, held)
        elif kind == "vs_raw_decay":
            # reported: what did the ONE strengthening add over v1's raw-decay
            # utility, same universes, same capacity, under drift?
            a = _success(replay_rate(ev, CAPACITY), ka, held)
            b = _success(replay(ev, CAPACITY, "adaptive"), ka, held)
        elif kind == "v1_rule_vs_fifo":
            # reported: v1's rule vs FIFO on THIS family (replication reference
            # for ADR-015's +0.018 sub-SESOI confirmatory edge).
            a = _success(replay(ev, CAPACITY, "adaptive"), ka, held)
            b = _success(replay(ev, CAPACITY, "fifo"), ka, held)
        else:                                    # PRIMARY: rate-adaptive − FIFO
            a = _success(replay_rate(ev, CAPACITY), ka, held)
            b = _success(replay(ev, CAPACITY, "fifo"), ka, held)

        delta = a - b
        AFV2_LOG.setdefault(name, []).append(
            {"seed_index": i, "family": base_seed, "treat": round(a, 3),
             "baseline": round(b, 3), "delta": round(delta, 3)})
        return delta

    return Condition(name, run, name)


def adaptive_forgetting_v2() -> Tuple[List[Condition], str]:
    conditions = [
        _make("null_unbounded", "null_unbounded"),      # control: no pressure -> exactly 0
        _make("null_nodrift", "null_nodrift"),          # control: no drift -> <= ~0
        _make("vs_raw_decay", "vs_raw_decay"),          # reported: the strengthening's own delta
        _make("v1_rule_vs_fifo", "v1_rule_vs_fifo"),    # reported: v1 replication reference
        _make("adaptive_advantage_v2", "primary"),      # PRIMARY: rate-adaptive − FIFO @ C
    ]
    return conditions, "adaptive_advantage_v2"


REGISTRY_REAL = {"adaptive_forgetting_v2": adaptive_forgetting_v2}


# ---------------------------------------------------------------- smoke / pilot / report
if __name__ == "__main__":
    import json
    import os
    import sys
    import time

    t0 = time.time()

    if "--calibrate" in sys.argv:
        # PILOT: assigned family 948000 (disjoint from the 953000 confirmatory).
        # Purpose: calibrate prediction.expected for the FROZEN primary
        # (rate-adaptive − FIFO @ C=90 under drift) and sanity-check both nulls.
        # The rule itself was fixed a priori (module docstring) — no rule
        # selection happens here. C=90/γ=0.98 are inherited from v1, not swept;
        # the 60/120 rows are diagnostics only, outside any decision.
        SEEDS = 5
        caps = (60, CAPACITY, 120, UNBOUNDED)
        cols = {c: {"rate_fifo": [], "raw_fifo": [], "rate_raw": []} for c in caps}
        nod, unb0 = [], []
        for i in range(SEEDS):
            ev, ev2, ka, held = _universe_v2(i, AFV2_PILOT_SEED)
            for c in caps:
                ra = _success(replay_rate(ev, c), ka, held)
                rw = _success(replay(ev, c, "adaptive"), ka, held)
                fi = _success(replay(ev, c, "fifo"), ka, held)
                cols[c]["rate_fifo"].append(ra - fi)
                cols[c]["raw_fifo"].append(rw - fi)
                cols[c]["rate_raw"].append(ra - rw)
            # nulls at the frozen capacity
            a2 = _success(replay_rate(ev2, CAPACITY), ka, held)
            b2 = _success(replay_rate(ev2, CAPACITY, decay=1.0), ka, held)
            nod.append(a2 - b2)
            u = _success(replay_rate(ev, UNBOUNDED), ka, held) - \
                _success(replay(ev, UNBOUNDED, "fifo"), ka, held)
            unb0.append(u)

        def band(xs):
            m = sum(xs) / len(xs)
            sd = (sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5
            return m, sd

        print(f"# PILOT family {AFV2_PILOT_SEED}  ({SEEDS} seeds)   {time.time()-t0:.1f}s")
        print("PRIMARY (to freeze) = rate-adaptive - FIFO @ C=90 under drift.")
        print(f"{'cap':>9} | {'rate-fifo':>16} | {'raw(v1)-fifo':>14} | {'rate-raw':>12}")
        for c in caps:
            mr, sr = band(cols[c]["rate_fifo"])
            mw, _ = band(cols[c]["raw_fifo"])
            md, _ = band(cols[c]["rate_raw"])
            tag = "UNBOUND" if c == UNBOUNDED else str(c)
            print(f"{tag:>9} | {mr:+.3f} +- {sr:.3f}  | {mw:+.3f}       | {md:+.3f}")
        mn, sn = band(nod)
        mu, su = band(unb0)
        print(f"null_nodrift (rate decay vs decay=1, C={CAPACITY}) : {mn:+.3f} +- {sn:.3f}  (expect <= ~0)")
        print(f"null_unbounded (rate vs fifo, no cap)  : {mu:+.3f} +- {su:.3f}  (expect exactly 0)")
        print(f"per-seed primary @C={CAPACITY}: "
              f"{['%+.3f' % v for v in cols[CAPACITY]['rate_fifo']]}")
        print(f"total {time.time()-t0:.1f}s")

    elif "--report" in sys.argv:
        # CONFIRMATORY (family 953000, never piloted) through the exact rsc.py
        # code path (validate -> run_spec -> format_run) + per-seed diagnostics.
        _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, _root)
        from spec_compiler.model import load_spec
        from spec_compiler.validator import validate, format_report
        from spec_compiler.harness import run_spec, format_run

        spec = load_spec(os.path.join(_root, "specs", "adaptive_forgetting_v2.yaml"))
        rep = validate(spec)
        if not rep.ok:
            print(format_report(rep, title="adaptive_forgetting_v2.yaml"))
            raise SystemExit(1)
        conditions, primary = adaptive_forgetting_v2()
        result = run_spec(spec, conditions, primary=primary)
        print(format_run(result, spec, title="adaptive_forgetting_v2",
                         provenance="[REAL run — gridworld-drift-heldout]"))
        print("\n# per-condition seed values")
        for c in result.conditions:
            print(f"  {c.name:<22}{['%.3f' % v for v in c.values]}")
        print("\n# per-seed log")
        print(json.dumps(AFV2_LOG, indent=1, ensure_ascii=False))
        print(f"\ntotal {time.time()-t0:.1f}s")

    else:
        conditions, primary = adaptive_forgetting_v2()
        for c in conditions:
            v = c.run(Random(0))
            print(f"{c.name:<22} delta={v:+.3f}")
        print(f"total {time.time()-t0:.1f}s")
