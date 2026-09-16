#!/usr/bin/env python3
"""Mandatory guard: one authoritative Telegram canary verdict, no conflicting closure surface."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
LOOPS = _OPS / "state" / "loops"
AUTH = LOOPS / "TELEGRAM-CANARY-AUTHORITATIVE-VERDICT.json"
SUPERSEDED = [
    LOOPS / "TELEGRAM-CANARY-RECONCILIATION-2026-08-21.json",
    LOOPS / "TELEGRAM-PRODUCTION-VERDICT.json",
]


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def t_a_authoritative_verdict_exists_and_is_scoped():
    d = _read(AUTH)
    v = d["authoritative_verdict"]
    assert v["TELEGRAM_CENTER_DURABLE_TRANSPORT_LOOP"] == "PRODUCTION_CLOSED"
    assert v["TELEGRAM_COMMAND_COVERAGE"] == "PRODUCTION_CLOSED"
    assert v["TELEGRAM_EVENT_BRIDGE_PATH"] == "IN_PROGRESS"
    assert v["WAVE1"] == "LOCKED"
    # closure must be evidence-backed, never claimed
    wc = d["window_20260821_C"]
    assert wc["verifier_confirmed"] is True
    assert wc["guard_wired_at_runtime"] is True
    assert wc["uncertain_send_outcomes"] == 0
    assert (LOOPS / "TELEGRAM-WINDOW-C-VERDICT.json").is_file()
    assert (LOOPS / "canary-coverage-2026-08-21-C" / "AUDIT.json").is_file()


def t_b_every_old_verdict_points_to_authority():
    expected = "_ops/state/loops/TELEGRAM-CANARY-AUTHORITATIVE-VERDICT.json"
    for p in SUPERSEDED:
        d = _read(p)
        assert d.get("SUPERSEDED_BY") == expected, (p, d.get("SUPERSEDED_BY"))
        assert "effective_claim" in d, p


def t_c_duplicate_effect_and_content_are_not_conflated():
    d = _read(AUTH)["corrected_classification"]
    assert d["duplicate_effect"]["observed"] == 0
    assert d["duplicate_effect"]["verdict"] == "PASS"
    assert d["duplicate_content"]["observed"].startswith("1 pair")
    assert d["duplicate_content"]["verdict"] == "NOT_A_FAILURE — observation only"


def t_d_no_artifact_may_claim_command_coverage_closed():
    d = _read(AUTH)
    # closure lives only in the authoritative verdict; every subordinate
    # artifact keeps its historical open-claim pointer
    assert d["authoritative_verdict"]["TELEGRAM_COMMAND_COVERAGE"] == "PRODUCTION_CLOSED"
    for p in SUPERSEDED:
        old = _read(p)
        effective = str(old.get("effective_claim") or "")
        assert "command coverage OPEN" in effective, (p, effective)
    # the window-C verifier artifact exists, is confirmed, and is scoped
    vc = _read(LOOPS / "TELEGRAM-WINDOW-C-VERDICT.json")
    assert vc.get("confirmed") is True
    assert "CANARY-COVERAGE-20260821-C" in str(vc.get("scope") or "")


def t_e_registry_matches_authoritative_scope():
    d = _read(LOOPS / "LOOP-REGISTRY.json")
    by = {e.get("seam_id"): e for e in d.get("entries") or []}
    assert by["S-T01"]["status"] == "production_closed"
    assert by["S-T02"]["status"] == "in_progress"
    inc = {i.get("loop_id"): i for i in d.get("incidents") or []}
    assert inc["LOOP-TELEGRAM-UNOWNED-INSTANT-ALERT"]["status"] == "CONTAINED_VERIFIED"
    assert inc["LOOP-TELEGRAM-COMMAND-COVERAGE"]["status"] == "PRODUCTION_CLOSED"
    assert inc["LOOP-RUNNING-CODE-DRIFT"]["status"] == "PRODUCTION_CLOSED"


def t_f_verifier_regeneration_cannot_broaden_or_erase():
    sys.path.insert(0, str(_OPS / "telegram_center"))
    import verify_production_canary as vpc
    prev = {
        "SUPERSEDED_BY": "_ops/state/loops/TELEGRAM-CANARY-AUTHORITATIVE-VERDICT.json",
        "effective_claim": "refer to authoritative verdict; transport "
                           "PRODUCTION_CLOSED, command coverage OPEN",
        "scope": "durable transport only",
        "AUTHORITATIVE_VERDICT": "_ops/state/loops/"
                                  "TELEGRAM-CANARY-AUTHORITATIVE-VERDICT.json",
        "generated_at": "2026-08-21T03:30:00Z",
        "confirmed": False,
        "failed_checks": ["stuck_intents"],
        "production_closed": False,
        "command_coverage": "CLOSED",  # foreign claim — must NOT survive
    }
    regen = vpc.merge_preserved(prev, {"confirmed": True, "failed_checks": [],
                                       "production_closed": True,
                                       "generated_at": "2026-08-21T05:00:00Z"})
    for key in ("SUPERSEDED_BY", "effective_claim", "scope",
                "AUTHORITATIVE_VERDICT"):
        assert regen.get(key) == prev[key], key
    hist = regen["historical_result"]
    assert hist["previous_confirmed"] is False
    assert hist["previous_failed_checks"] == ["stuck_intents"]
    assert hist["previous_production_closed"] is False
    # a foreign closure claim from the old file cannot leak into the
    # regenerated verdict, and the authoritative pointer stays intact
    assert "command_coverage" not in regen
    assert regen["AUTHORITATIVE_VERDICT"].endswith(
        "TELEGRAM-CANARY-AUTHORITATIVE-VERDICT.json")


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"  OK  {fn.__name__}")
        except Exception as e:
            failed += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\ntest_telegram_verdict_conflict: {len(tests) - failed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
