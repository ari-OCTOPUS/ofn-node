"""
REAL experiment for specs/prospective_memory.yaml — H-OWN-05 / EXP-005.

Tests the raw hypothesis: long-horizon agency needs an EXPLICIT memory for
retained INTENTIONS (a "when you later see cue X, do Y" binding) that survives
interruptions, rather than reactively re-reading the current observation. This
is the classic prospective-memory dissociation: an ongoing task consumes the
same limited working register that a delayed intention would need, so under
interruption load a reactive controller LOSES the deferred intention while a
dedicated intention buffer retains it.

Environment (new, deterministic, NO learning, NO LLM): a sequential episode of
T steps. Each step emits one token:
  ("ong", d)         ongoing-task item (an interruption/distractor that must be
                     attended to — it OVERWRITES the shared reactive register).
  ("enc", cue, resp) ENCODE: an instruction to remember "when cue fires later,
                     respond `resp`". `resp` is arbitrary per-intention (a fresh
                     draw), so it cannot be baked into a fixed policy or
                     re-derived from the cue at trigger time — it must be STORED.
  ("trg", cue)       TRIGGER: the deferred cue appears; the correct action is
                     the `resp` bound to `cue` at its encode. This is the PM
                     event that is scored.
Encodes are staggered and each intention's trigger is placed `gap` steps after
its encode, the gap filled by ongoing interruptions. The whole point: the
retention interval between encode and trigger is where the reactive register
gets overwritten.

Two deterministic agents (NO learning; the manipulation is MEMORY ARCHITECTURE,
mirroring homeostasis.py's reactive-vs-anticipatory control-strategy contrast):
  reactive   (= no intention buffer)  a single SHARED FIFO working register of
             capacity K. Every salient token (ongoing item, encoded binding,
             trigger) is pushed onto it, so ongoing interruptions evict pending
             bindings. At a trigger it searches the register for a surviving
             binding for that cue; if found it responds correctly, else it emits
             its best fixed fallback: a deterministic guess over the R responses
             (chance floor 1/R — this is a STRONG, non-strawman baseline: it is
             perfect when interruptions are light and still scores ~1/R when the
             binding is gone). A binding survives iff fewer than K salient
             tokens arrived between its encode and its trigger.
  buffer     (= explicit prospective memory)  a SEPARATE dedicated intention
             buffer of capacity P that stores (cue -> resp) and is NOT touched
             by ongoing items. At a trigger it reads the buffer; if the
             intention is still resident it responds correctly, else it emits
             the SAME deterministic guess. The buffer only evicts when more than
             P intentions are simultaneously pending (FIFO) — so it too could
             miss an intention if intention load exceeded its capacity, and it
             could in principle LOSE to reactive if a binding the reactive
             register still holds were evicted from the small buffer. In the
             confirmatory run this latent tension never binds: buffer completion
             = 1.0, so the buffer's capacity is never the constraint and the
             measured advantage is buffer-vs-no-buffer, not a capacity-pressure
             effect. Declared cost: the buffer carries extra persistent state
             (space/compute) the reactive agent does not.

Because both agents emit the IDENTICAL deterministic guess when they lack the
binding, triggers where both lack it cancel; the advantage is purely the
differential set {buffer-has & reactive-lost} minus {reactive-has & buffer-lost}
— i.e. the marginal value of a dedicated, non-overwritable intention store. This
makes the primary a FALSIFIABLE quantity: it is ~0 when interruptions are light
(reactive register survives — the low_load control, and the DISCRIMINATING check
that makes the result non-trivial), exactly 0 BY CONSTRUCTION when no intention
ever triggers (null control — no PM events are placed, so nothing is scored;
this is a construction zero, not a measured cancellation), and it could in
principle go NEGATIVE only if simultaneously-pending intentions exceeded the
buffer capacity P (a latent design tension that does NOT bind here — the buffer
completes 1.0). So the load-sensitive control is low_load, not null: null is
true by construction, whereas low_load ~0 is a MEASURED result showing the
advantage is interruption-driven, not a free gift of the buffer.

GATED vs REPORTED: the preregistered, machine-gated quantity is
pm_advantage_highload (the spec failure_condition and decision_rule operate on
it). low_load_advantage (same quantity under light interruption load) is a
REPORTED discriminating control that shows the advantage is INTERRUPTION-driven,
not a free gift of the buffer — it should sit in/near the DISCARD band. The
null control pins the zero-point BY CONSTRUCTION (no triggers are placed, so the
completion rate is undefined and reported as 0), not by measured cancellation.

Primary metric: pm_advantage_highload = PM_completion(buffer) −
PM_completion(reactive), micro-averaged over all trigger events in the batch,
under interruption-heavy episodes. Pilot (family 982000) was used to set honest
bands, parameters were then FROZEN and the confirmatory run uses a disjoint seed
family (982600+). Fully deterministic given the batch seed.

SCOPE: C2/C3-flavored (deferred-intention agency), but the metric is functional
task completion ONLY. Forbidden interpretation: intention as felt volition /
phenomenology. Permitted: functional retention of a delayed goal binding.
"""
from __future__ import annotations

import zlib
from collections import OrderedDict, deque
from random import Random
from typing import Dict, List, Tuple

from spec_compiler.harness import Condition

# ---------------------------------------------------------------- constants (FROZEN)
R = 4                     # deferred-response alphabet (chance floor 1/R = 0.25)
N_INTENTIONS = 8          # prospective intentions per episode
K_REACTIVE = 8            # shared reactive working register capacity
P_BUFFER = 6              # dedicated intention-buffer capacity (< K on purpose:
                          # lets the buffer LOSE when it evicts a binding the
                          # reactive register still holds -> primary can be <= 0)
STAGGER = 3               # steps between consecutive encodes (creates overlap)
ENC_START = 2
TAIL = 3
N_TASKS = 60              # episodes per seed (matches homeostasis; fast)
# interruption-load regimes (gap = steps from an intention's encode to its
# trigger; a reactive binding survives iff gap <= K_REACTIVE):
GAP_HIGH = (3, 18)        # interruption-HEAVY: many gaps exceed K -> reactive loses
GAP_LOW = (1, 7)          # light load: all gaps <= K -> reactive survives
PM_BASE_SEED = 982_600    # CONFIRMATORY family (disjoint from pilot 982_000)

PM_LOG: dict = {}


# ---------------------------------------------------------------- environment
class PMEpisode:
    __slots__ = ("uid", "steps", "truth")

    def __init__(self, uid: int, steps: list, truth: Dict[int, int]):
        self.uid = uid          # episode id (drives the deterministic guess)
        self.steps = steps      # list of token tuples
        self.truth = truth      # cue -> true resp (ground truth for scoring)


def _free(events: dict, pos: int) -> int:
    """First free timeline position >= pos (deterministic collision handling)."""
    while pos in events:
        pos += 1
    return pos


def _draw_gap(rng: Random, regime: str) -> int:
    lo, hi = GAP_LOW if regime == "low" else GAP_HIGH
    return rng.randint(lo, hi)


def make_episode(uid: int, rng: Random, regime: str) -> PMEpisode:
    """Build one deterministic episode. regime in {'high','low','null'}.
    'null' places encodes but NO triggers (intentions never fire) -> pm_total=0.
    """
    truth = {cue: rng.randrange(R) for cue in range(N_INTENTIONS)}
    events: Dict[int, tuple] = {}
    for j in range(N_INTENTIONS):
        enc_pos = _free(events, ENC_START + j * STAGGER)
        events[enc_pos] = ("enc", j, truth[j])
        g = _draw_gap(rng, regime)           # keep RNG stream identical across regimes
        if regime == "null":
            continue                          # intention encoded but never triggered
        trg_pos = _free(events, enc_pos + g)
        events[trg_pos] = ("trg", j)
    T = (max(events) if events else 0) + TAIL + 1
    steps: list = []
    for pos in range(T):
        steps.append(events[pos] if pos in events else ("ong", rng.randrange(R)))
    return PMEpisode(uid, steps, truth)


def build_batch(seed: int, regime: str) -> List[PMEpisode]:
    return [make_episode(seed * 1000 + i, Random(seed * 100_003 + i * 7919), regime)
            for i in range(N_TASKS)]


# ---------------------------------------------------------------- agents
def _guess(uid: int, idx: int) -> int:
    """Deterministic, reproducible fallback response when the binding is absent
    (same for BOTH agents, so shared-guess triggers cancel in the advantage)."""
    return zlib.crc32(f"{uid}:{idx}".encode()) % R


def simulate(ep: PMEpisode) -> Tuple[int, int, int]:
    """Step both agents through one episode. Returns
    (reactive_pm_correct, buffer_pm_correct, pm_total)."""
    reg: deque = deque(maxlen=K_REACTIVE)     # reactive shared FIFO register
    buf: "OrderedDict[int, int]" = OrderedDict()   # dedicated intention buffer (cap P)
    r_correct = b_correct = pm_total = 0

    for idx, step in enumerate(ep.steps):
        kind = step[0]
        if kind == "enc":
            _, cue, resp = step
            reg.append(("intent", cue, resp))            # binding enters shared reg
            buf[cue] = resp                              # and the dedicated buffer
            if len(buf) > P_BUFFER:
                buf.popitem(last=False)                  # FIFO evict oldest intention
        elif kind == "ong":
            reg.append(("ong", step[1]))                 # interruption overwrites reg
        elif kind == "trg":
            _, cue = step
            pm_total += 1
            truth = ep.truth[cue]
            # reactive: search surviving register for the binding
            r_resp = None
            for item in reg:
                if item[0] == "intent" and item[1] == cue:
                    r_resp = item[2]
            if r_resp is None:
                r_resp = _guess(ep.uid, idx)
            r_correct += (r_resp == truth)
            # buffer: read the dedicated store
            b_resp = buf.get(cue)
            if b_resp is None:
                b_resp = _guess(ep.uid, idx)             # identical fallback
            b_correct += (b_resp == truth)
            reg.append(("trg", cue))                     # trigger is also salient
    return r_correct, b_correct, pm_total


def _batch_rates(batch: List[PMEpisode]) -> Tuple[float, float]:
    """Micro-averaged PM completion rates (reactive, buffer) over the batch."""
    r_tot = b_tot = n_tot = 0
    for ep in batch:
        rc, bc, pt = simulate(ep)
        r_tot += rc
        b_tot += bc
        n_tot += pt
    if n_tot == 0:                                       # null control: no triggers
        return 0.0, 0.0
    return r_tot / n_tot, b_tot / n_tot


# ---------------------------------------------------------------- conditions
def _make(name: str, kind: str) -> Condition:
    """kind: 'null' | 'low' | 'high'. Paired: the i-th call of every condition
    uses base seed PM_BASE_SEED+i, so all conditions see identical episode
    families for seed i (regime only changes the load, not the RNG stream)."""
    counter = {"i": 0}

    def run(_rng: Random) -> float:
        i = counter["i"]
        counter["i"] += 1
        seed = PM_BASE_SEED + i
        regime = {"null": "null", "low": "low", "high": "high"}[kind]
        batch = build_batch(seed, regime)
        r_rate, b_rate = _batch_rates(batch)
        adv = b_rate - r_rate
        PM_LOG.setdefault(name, []).append(
            {"seed_index": i, "reactive_rate": round(r_rate, 4),
             "buffer_rate": round(b_rate, 4), "advantage": round(adv, 4)})
        return adv

    return Condition(name, run, name)


def prospective_memory() -> Tuple[List[Condition], str]:
    conditions = [
        _make("null_control", "null"),        # zero-point: intentions never trigger
        _make("low_load_advantage", "low"),   # control: light load -> reactive survives
        _make("pm_advantage_highload", "high"),  # PRIMARY: advantage under heavy load
    ]
    return conditions, "pm_advantage_highload"


REGISTRY_REAL = {"prospective_memory": prospective_memory}


# ---------------------------------------------------------------- smoke / pilot
if __name__ == "__main__":
    import json
    import sys
    import time

    t0 = time.time()
    # PILOT family 982_000 (disjoint from confirmatory 982_600); FROZEN after this.
    PILOT_SEED = 982_000
    n_seeds = 5
    if "--confirm" in sys.argv:
        base, tag = PM_BASE_SEED, "CONFIRMATORY 982600+"
    else:
        base, tag = PILOT_SEED, "PILOT 982000+"

    rows = {"null": [], "low": [], "high": []}
    for s in range(n_seeds):
        for regime in ("null", "low", "high"):
            r_rate, b_rate = _batch_rates(build_batch(base + s, regime))
            rows[regime].append((r_rate, b_rate, b_rate - r_rate))

    def _agg(regime):
        rr = sum(x[0] for x in rows[regime]) / n_seeds
        bb = sum(x[1] for x in rows[regime]) / n_seeds
        aa = sum(x[2] for x in rows[regime]) / n_seeds
        return {"reactive": round(rr, 4), "buffer": round(bb, 4),
                "advantage": round(aa, 4)}

    print(f"# prospective_memory {tag}  ({n_seeds} seeds x {N_TASKS} eps)")
    print(json.dumps({"null_control": _agg("null"),
                      "low_load_advantage": _agg("low"),
                      "pm_advantage_highload": _agg("high")}, indent=1))
    print(f"total {time.time()-t0:.2f}s")
