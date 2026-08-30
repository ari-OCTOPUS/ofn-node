#!/usr/bin/env python3
"""W-C: fixture-only observatory pipeline tests.

Covers determinism, duplicate rejection, tamper detection, outcome-blindness
(future-data leakage probe), copied-baseline detection, missing-data policy,
unresolved exclusion, scorer independence (static import analysis), as_of
ordering and receipt immutability. Fixture-only: no network, no live API,
no runtime database, no superiority claim.
"""
from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

OBS = Path(__file__).resolve().parent.parent / "octopus_observation"

from octopus_observation import (        # noqa: E402
    obs_fixture, producer_strategy, producer_persistence, scorer,
    verifier, fixture_run)

FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    assert cond, f"{name}: {detail}"


def expect_raises(name: str, exc, fn, *a, **kw):
    try:
        fn(*a, **kw)
        check(name, False, "no exception raised")
    except exc:
        check(name, True)
    except Exception as e:  # noqa: BLE001
        check(name, False, f"wrong exception {type(e).__name__}: {e}")


def test_determinism():
    print("[1] fixture determinism")
    a = obs_fixture.build_fixture(n=30, seed=7, unresolved=3)
    b = obs_fixture.build_fixture(n=30, seed=7, unresolved=3)
    check("identical builds", a == b)
    check("provenance stable",
          obs_fixture.provenance_hash(a) == obs_fixture.provenance_hash(b))


def test_duplicate_rejected():
    print("[2] duplicate claim IDs fail")
    claims = obs_fixture.build_fixture(n=5, seed=1, unresolved=0)
    dup = claims + [dataclasses.replace(claims[0])]
    expect_raises("duplicate id", obs_fixture.FixtureError,
                  obs_fixture._validate, dup)


def test_tamper_detected():
    print("[3] tampered fixture fails provenance check")
    claims = obs_fixture.build_fixture(n=10, seed=2, unresolved=2)
    prov = obs_fixture.provenance_hash(claims)
    payload = [dataclasses.asdict(c) for c in claims]
    payload[3]["feature_a"] = 0.999999          # tamper
    expect_raises("tamper", obs_fixture.FixtureError,
                  obs_fixture.load_claims, payload, prov)
    clean = obs_fixture.load_claims([dataclasses.asdict(c) for c in claims], prov)
    check("clean reload passes", len(clean) == 10)


def test_outcome_blind_and_scorer_uses_outcome():
    print("[4] producers outcome-blind; scorer consumes outcomes")
    claims = obs_fixture.build_fixture(n=20, seed=3, unresolved=2)
    strat = [producer_strategy.predict(c) for c in claims]
    pers = [producer_persistence.predict(c) for c in claims]
    flipped = [dataclasses.replace(c, outcome=None if c.outcome is None
                                   else 1 - c.outcome) for c in claims]
    check("strategy unchanged on outcome flip",
          strat == [producer_strategy.predict(c) for c in flipped])
    check("persistence unchanged on outcome flip",
          pers == [producer_persistence.predict(c) for c in flipped])
    by_id = {c.claim_id: c.outcome for c in claims}
    s1 = scorer.score([(p["claim_id"], p["prediction"], by_id[p["claim_id"]])
                       for p in strat])
    s2 = scorer.score([(p["claim_id"], p["prediction"],
                        None if by_id[p["claim_id"]] is None
                        else 1 - by_id[p["claim_id"]]) for p in strat])
    check("scorer reacts to swapped outcomes", s1["brier"] != s2["brier"],
          f"{s1['brier']} == {s2['brier']}")


def test_missing_data_policy():
    print("[5] missing-data policy")
    claims = obs_fixture.build_fixture(n=5, seed=4, unresolved=0)
    broken = [dataclasses.asdict(c) for c in claims]
    broken[2]["observed_at"] = ""
    expect_raises("missing observed_at", obs_fixture.FixtureError,
                  obs_fixture.load_claims, broken)
    half = [dataclasses.asdict(c) for c in claims]
    half[1]["resolved_at"], half[1]["outcome"] = None, 1
    expect_raises("unresolved policy", obs_fixture.FixtureError,
                  obs_fixture.load_claims, half)
    late = [dataclasses.asdict(c) for c in claims]
    late[0]["resolved_at"] = "2026-01-01T00:00:00Z"   # before observed_at
    expect_raises("resolution ordering", obs_fixture.FixtureError,
                  obs_fixture.load_claims, late)


def test_unresolved_excluded():
    print("[6] unresolved claims excluded explicitly")
    claims = obs_fixture.build_fixture(n=12, seed=5, unresolved=4)
    by_id = {c.claim_id: c.outcome for c in claims}
    strat = [producer_strategy.predict(c) for c in claims]
    m = scorer.score([(p["claim_id"], p["prediction"], by_id[p["claim_id"]])
                      for p in strat])
    check("resolved n", m["n"] == 8, str(m["n"]))
    check("unresolved count", m["unresolved_excluded"] == 4)


def test_copied_baseline_detected():
    print("[7] copied baseline detected")
    claims = obs_fixture.build_fixture(n=10, seed=6, unresolved=0)
    strat = [producer_strategy.predict(c) for c in claims]
    pers = [producer_persistence.predict(c) for c in claims]
    v_ok = verifier.verify(claims, strat, pers,
                           expected_provenance=obs_fixture.provenance_hash(claims))
    check("distinct producers pass", v_ok["ok"] is True, json.dumps(v_ok["checks"]))
    copied = [dict(p) for p in pers]                 # strategy copies persistence
    v_bad = verifier.verify(claims, copied, pers,
                            expected_provenance=obs_fixture.provenance_hash(claims))
    check("copied baseline flagged",
          v_bad["checks"].get("not_copied_baseline") is False)


def test_scorer_independence_static():
    print("[8] scorer/producer import boundaries")
    bad_src = "import producer_strategy\nfrom producer_persistence import x\n"
    hits = verifier.static_import_check(bad_src, verifier.FORBIDDEN_SCORER_IMPORTS)
    check("synthetic violation caught",
          sorted(hits) == ["producer_persistence", "producer_strategy"], str(hits))
    clean = verifier.static_import_check(
        (OBS / "scorer.py").read_text(encoding="utf-8"),
        verifier.FORBIDDEN_SCORER_IMPORTS)
    check("real scorer clean", clean == [], str(clean))
    check("package boundaries clean", verifier.module_boundary_check() == [],
          str(verifier.module_boundary_check()))


def test_as_of_ordering_and_receipt():
    print("[9] as_of ordering + immutable receipt")
    receipt = fixture_run.run_pipeline(n=25, seed=11, unresolved=3,
                                       generated_at_utc="2026-08-30T15:00:00Z")
    check("verification ok", receipt["verification"]["ok"] is True,
          json.dumps(receipt["verification"]))
    check("no superiority claim", receipt["superiority_claim"] is None)
    check("phase labeled fixture-only", receipt["phase"] == "fixture-only")
    again = fixture_run.run_pipeline(n=25, seed=11, unresolved=3,
                                     generated_at_utc="2026-08-30T15:00:00Z")
    check("receipt reproducible", receipt == again)
    body = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    import hashlib
    digest = hashlib.sha256(
        json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    check("receipt hash binds content", digest == receipt["receipt_sha256"])
    check("brier fields present",
          all(receipt[k]["brier"] is not None for k in ("strategy", "persistence"))
          and receipt["strategy"]["n"] == 22)


def main() -> int:
    for fn in (
        test_determinism,
        test_duplicate_rejected,
        test_tamper_detected,
        test_outcome_blind_and_scorer_uses_outcome,
        test_missing_data_policy,
        test_unresolved_excluded,
        test_copied_baseline_detected,
        test_scorer_independence_static,
        test_as_of_ordering_and_receipt,
    ):
        fn()
    if FAILURES:
        print(f"\nOBSERVATORY-FIXTURE: {len(FAILURES)} failure(s)")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("\nOBSERVATORY-FIXTURE: all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
