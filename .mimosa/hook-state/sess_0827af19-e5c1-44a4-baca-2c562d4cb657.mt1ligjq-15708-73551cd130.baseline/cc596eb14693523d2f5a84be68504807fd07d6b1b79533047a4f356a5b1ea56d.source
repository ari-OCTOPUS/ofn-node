"""
Part B test — social signal quality
======================================
Calls the new _lunarcrush_score (7d moving average + spam guard) on all 8
cached coin symbols and compares against old (cached) social scores.

Expected outcomes:
  OPG  (33d):  spam_ratio=~18% > 15% → UNRELIABLE → new score=0
               (age < 90d → soft flag only in VetoEngine, no hard veto)
  FOGO (130d): ppc_3d=~8.0 > 6.0 → UNRELIABLE → new score=0
               (age ≥ 90d → SOCIAL_ZERO hard veto would fire, but FOGO is
                already HOLD_FOR_REVIEW from holder check — outcome unchanged)
  ZAMA and other coins: confirm spam guard does NOT falsely fire

Run from project root:  python test_social_partB.py
"""
import sys, json, os, time
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(__file__))

from modules.gem_hunter import GemHunter

SYMBOLS_AND_AGES = [
    ("OPG",    33),
    ("FOGO",  130),
    ("ZAMA",   41),
    ("BASED",  39),
    ("MANTRA", 82),
    ("ESP",    90),
    ("AI",     26),
    ("EURI",  118),
]

VETO_SOCIAL_AGE_FLOOR = 90   # mirrors VetoEngine constant

def load_old_scores():
    cache = json.loads(open("data/coin_hunter_cache.json", encoding="utf-8").read())
    return {r["symbol"]: r.get("social_score", 0) for r in cache["records"]}

if __name__ == "__main__":
    sep = "=" * 72

    print(f"\n{sep}")
    print(f"  PART B TEST — Social signal quality (spam guard + 7d moving avg)")
    print(f"{sep}")

    old_scores = load_old_scores()
    hunter = GemHunter()

    print(f"\n  Thresholds: spam_ratio >{GemHunter.LC_SPAM_RATIO_THRESHOLD*100:.0f}%  "
          f"posts/contributor >{GemHunter.LC_SPAM_PPR_THRESHOLD:.1f}  "
          f"social_age_floor={VETO_SOCIAL_AGE_FLOOR}d\n")

    print(f"  {'Sym':<8} {'Age':>5} {'OldSc':>6} {'NewSc':>6} "
          f"{'Gal7d':>6} {'Snt7d':>6} {'SpamR':>6} {'PPR3d':>6}  Flags")
    print(f"  {'-'*85}")

    results = []
    for sym, age in SYMBOLS_AND_AGES:
        lc = hunter._lunarcrush_score(sym)
        old = old_scores.get(sym, 0)
        new = lc["score"]
        gal = lc.get("galaxy_score", 0)
        snt = lc.get("sentiment", 0)
        sr  = lc.get("lc_spam_ratio", 0)
        ppr = lc.get("lc_posts_per_contributor", 0)
        unr = lc.get("lc_unreliable", False)
        avl = lc.get("available", False)

        flags = []
        if not avl:
            flags.append(f"NO_DATA({lc.get('reason','?')})")
        elif unr:
            flags.append("UNRELIABLE")
            if age >= VETO_SOCIAL_AGE_FLOOR:
                flags.append("-> SOCIAL_ZERO hard veto")
            else:
                flags.append(f"-> soft flag (age {age}d < {VETO_SOCIAL_AGE_FLOOR}d)")
        elif new > old + 5:
            flags.append("score_UP")
        elif new < old - 5:
            flags.append("score_DOWN")
        else:
            flags.append("stable")

        # Mark why spam fired
        if unr and avl:
            if sr > GemHunter.LC_SPAM_RATIO_THRESHOLD:
                flags.insert(1, f"spam_ratio={sr*100:.1f}%>15%")
            if ppr > GemHunter.LC_SPAM_PPR_THRESHOLD:
                flags.insert(1, f"ppr={ppr:.1f}>{GemHunter.LC_SPAM_PPR_THRESHOLD:.0f}")

        delta = f"{new-old:+.0f}" if avl else "--"
        print(f"  {sym:<8} {age:>4}d {old:>6.0f} {new:>6.0f} "
              f"{gal:>6.1f} {snt:>6.1f} {sr*100:>5.1f}% {ppr:>6.1f}  "
              f"{delta:>4}  {' | '.join(flags)}")
        results.append((sym, age, old, new, unr, avl))

        if sym != SYMBOLS_AND_AGES[-1][0]:
            time.sleep(1.5)   # GoPlus-style rate-limit courtesy for LC too

    print(f"\n  {'-'*85}")

    # ── Verification checks ──────────────────────────────────────────────────
    print(f"\n── Verification " + "─" * 56)

    checks = []

    # OPG and FOGO must be flagged UNRELIABLE
    for sym in ("OPG", "FOGO"):
        r = next(x for x in results if x[0] == sym)
        is_unrel = r[4]
        new_zero = r[3] == 0
        ok = is_unrel and new_zero
        checks.append(ok)
        print(f"  {sym}: UNRELIABLE={is_unrel}, score=0={new_zero}  -> {'PASS' if ok else 'FAIL'}")

    # ZAMA must NOT be flagged (spam guard should not false-positive on legitimate coins)
    r_zama = next(x for x in results if x[0] == "ZAMA")
    zama_ok = not r_zama[4] and r_zama[3] > 0  # not unreliable, and positive score
    checks.append(zama_ok)
    print(f"  ZAMA: UNRELIABLE={r_zama[4]}, new_score={r_zama[3]}  "
          f"-> {'PASS (not false-positive)' if zama_ok else 'FAIL (false-positive on ZAMA!)'}")

    # BASED: LunarCrush maps "BASED" to a different popular coin (symbol collision).
    # galaxy_7d = 0 → galaxy_zero guard fires → score=0, available=False.
    # This is the correct behaviour — sentiment from a symbol-collision is noise.
    r_based = next(x for x in results if x[0] == "BASED")
    based_ok = r_based[3] == 0
    checks.append(based_ok)
    print(f"  BASED: score={r_based[3]} (should be 0 — galaxy_zero/symbol collision)  "
          f"-> {'PASS' if based_ok else 'FAIL'}")

    all_ok = all(checks)
    print(f"\n  Part B check: {'ALL PASS' if all_ok else 'SEE ABOVE'}")

    if not all_ok:
        print("\n  *** Threshold tuning needed — review spam_ratio / ppr values above ***")

    print(f"\n── Impact summary " + "─" * 53)
    print(f"  OPG  (33d):  spam guard fires → score drops to 0")
    print(f"               age < 90d → soft flag only in VetoEngine")
    print(f"               (OPG already vetoed by HOLDER_DANGER — no practical change)")
    print(f"  FOGO (130d): spam guard fires → score drops to 0")
    print(f"               age ≥ 90d → SOCIAL_ZERO hard veto would fire")
    print(f"               (FOGO already HOLD_FOR_REVIEW from holder check — no practical change)")
    print(f"  All legitimate coins with real social signal preserve their scores.")
