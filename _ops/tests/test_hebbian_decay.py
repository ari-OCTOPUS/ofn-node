"""test_hebbian_decay.py — تأیید DECAY_RATE جدید (0.995).

با 0.995: half-life = ~138 tick = ~2.3 ساعت
با PRUNE_THRESHOLD 0.005: یک association با strength=1.0 بعد از ~1000 tick (~16.6 ساعت) prune می‌شود
قبلاً با 0.95: بعد از ~90 tick (~1.5 ساعت) prune می‌شد

این تست فقط منطق ریاضی را تأیید می‌کند — no network، no organism.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
_NEURAL = _OPS / "neural"
for _p in (str(_OPS), str(_NEURAL)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

results = {"pass": 0, "fail": 0, "details": []}

def check(name, cond):
    if cond:
        results["pass"] += 1
        results["details"].append(f"  ✅ {name}")
    else:
        results["fail"] += 1
        results["details"].append(f"  ❌ {name}")


def main():
    import hebbian

    # ─── Test 1: constants are new values ───
    check("DECAY_RATE is 0.995", hebbian.DECAY_RATE == 0.995)
    check("PRUNE_THRESHOLD is 0.005", hebbian.PRUNE_THRESHOLD == 0.005)

    # ─── Test 2: half-life calculation ───
    # half-life = ln(0.5) / ln(DECAY_RATE) = ln(0.5) / ln(0.995) ≈ 138 ticks
    import math
    half_life = math.log(0.5) / math.log(hebbian.DECAY_RATE)
    check(f"half-life ~{half_life:.0f} ticks (~{half_life/60:.1f}h @ 60s/tick)", 100 < half_life < 200)

    # ─── Test 3: simulate 90 ticks of decay — should NOT prune ───
    strength = 1.0
    for _ in range(90):
        strength *= hebbian.DECAY_RATE
    check(f"after 90 ticks strength={strength:.4f} > PRUNE_THRESHOLD", strength > hebbian.PRUNE_THRESHOLD)

    # ─── Test 4: simulate 500 ticks — should still be alive ───
    strength = 1.0
    for _ in range(500):
        strength *= hebbian.DECAY_RATE
    check(f"after 500 ticks strength={strength:.4f} > PRUNE_THRESHOLD", strength > hebbian.PRUNE_THRESHOLD)

    # ─── Test 5: observe + decay cycle (real workflow) ───
    import tempfile, os
    with tempfile.TemporaryDirectory() as tmp:
        # hebbian.py resolves its persist path from OPS_DIR (env-اول idiom shared
        # with bcm/consolidation/latent_space/sparse_filter — 2026-07-11), not
        # PF_BRAIN_DIR (that one is Project-F's own sandbox var, unrelated to
        # _ops/neural). Setting the wrong var here silently missed the isolation:
        # HebbianAssociator() fell through to "_ops/neural/hebbian.json" beside
        # the module — the tracked live-tree file — so this block was reading/
        # writing production state instead of the temp dir.
        os.environ["OPS_DIR"] = tmp
        # reload to pick up new path
        import importlib
        importlib.reload(hebbian)
        heb = hebbian.HebbianAssociator()

        # observe two signals
        heb.observe(["alpha", "beta"])
        check("observe created association", len(heb.associations) == 1)

        # decay 100 ticks (simulating ~1.7 hours without co-occurrence)
        for _ in range(100):
            heb.decay()
        check("survived 100 ticks of decay", len(heb.associations) == 1)

        # observe again — should reinforce
        heb.observe(["alpha", "beta"])
        a = heb.associations[0]
        check(f"strength reinforced: {a.strength:.3f}", a.strength > 0.05)

    print("test_hebbian_decay — DECAY_RATE 0.995 verification")
    for d in results["details"]:
        print(d)
    print(f"\nPass: {results['pass']}, Fail: {results['fail']}")
    return results["fail"] == 0

if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
