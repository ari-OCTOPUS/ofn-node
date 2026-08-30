#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_action_durability — دفترِ idempotency و replay باید restart را زنده بمانند.

شکافِ ثبت‌شده (INTEGRATION-MANIFEST §۴ + ممیزی ۰۷-۳۱): planner دفترِ idempotency
و nonceها را می‌گرفت ولی صداکنندهٔ زنده همیشه `{}`/`set()` می‌داد ⇒ هر restart
حفاظتِ replay را صفر می‌کرد و crash وسطِ چرخه = اجرای دوبارهٔ همان عمل.

حالا: دفتر از `action-ledger.jsonl` روی دیسک بارگذاری می‌شود؛ replay ِ همان
چرخه = NOOP ِ صادق (نه اجرای دوم، نه mission ِ failed ِ دروغ)؛ تعارضِ
same-id/different-payload = BLOCK.
"""
import json
import os
import sys
from pathlib import Path

import harness

ENV = harness.setup("action-durability")

assert os.environ.get("OCTOPUS_STATE_DIR"), \
    "harness ِ این نسخه OCTOPUS_STATE_DIR را pin نمی‌کند — نشتِ حافظه به درختِ زنده"

_OPS = Path(__file__).resolve().parent.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

import goal_action_bridge as gab  # noqa: E402
import prereg  # noqa: E402

NOW = 1_785_400_000.0


def _flag(on: bool):
    if on:
        os.environ[gab.FLAG] = "1"
    else:
        os.environ.pop(gab.FLAG, None)


def _fresh():
    for name in ("missions.jsonl", "action-ledger.jsonl", "used-nonces.json",
                 "memory-consolidated.json", "verdicts.jsonl", "prereg.jsonl"):
        try:
            (gab._state_dir() / name).unlink()
        except OSError:
            pass
    rdir = gab._state_dir() / "action_receipts"
    if rdir.exists():
        for f in rdir.iterdir():
            try:
                f.unlink()
            except OSError:
                pass


def _proposal() -> dict:
    return {"goal": "رخدادِ بازیابی در تصمیم دیده شود", "goal_key": "kdur",
            "goal_source": "self", "direction": "جهتِ آزمون",
            "method": "روشِ آزمونِ ۱", "method_index": 0,
            "metric_path": "state/neural/recall-trend.jsonl",
            "metric_key": "events", "baseline": 0.0,
            "target": {"op": ">", "value": 0.0},
            "candidate_key": "recall-events", "deadline_cycles": 2}


def _register(cycle: str) -> dict:
    p = prereg.register(_proposal(), cycle=cycle, now=NOW)
    assert p.get("ok"), p
    return p


def _receipts() -> list:
    rdir = gab._state_dir() / "action_receipts"
    return sorted(rdir.iterdir()) if rdir.exists() else []


def _spy_executor():
    sys.path.insert(0, str(_OPS / "action_bridge"))
    import executor as _ex
    calls = []
    real = _ex.execute
    _ex.execute = lambda *a, **k: (calls.append(1), real(*a, **k))[1]
    return _ex, real, calls


# ── replay = NOOP، نه اجرای دوم ─────────────────────────────────────────────
def t_replay_of_the_same_cycle_is_a_noop_not_a_second_execution():
    """crash بعد از execute و قبل از حکم ⇒ beat ِ بعدی همان چرخه را دوباره
    می‌راند. با دفترِ persisted: دومی NOOP است — رسیدِ نو ساخته نمی‌شود، دفترِ
    mission ردیفِ دوم نمی‌گیرد، و ok=True چون کار واقعاً انجام شده بود."""
    _fresh()
    _flag(True)
    _ex, real, calls = _spy_executor()
    try:
        cyc = "2026-07-31#1"
        _register(cyc)
        r1 = gab.run_for_cycle(cyc, now=NOW)
        assert r1.get("ok") is True and r1.get("receipt_status") == "EXECUTED", r1
        n_rec = len(_receipts())
        n_calls = len(calls)
        n_missions = len(gab._missions_path().read_text("utf-8").splitlines())

        r2 = gab.run_for_cycle(cyc, now=NOW + 60)
        assert r2.get("ok") is True, r2
        assert r2.get("status") == "NOOP", r2
        assert r2.get("reason") == "duplicate-replay", r2
        assert len(calls) == n_calls, "executor برای replay دوباره صدا خورد!"
        assert len(_receipts()) == n_rec, "replay رسیدِ نو ساخت!"
        rows = gab._missions_path().read_text("utf-8").splitlines()
        assert len(rows) == n_missions, ("replay ردیفِ mission ِ دوم نوشت", rows)
    finally:
        _ex.execute = real
        _flag(False)


def t_the_ledger_loader_survives_corrupt_lines():
    """دفترِ نیمه‌خوانا بهتر از هیچ است: خطِ خراب skip می‌شود و ردیف‌های سالم
    همچنان replay را می‌گیرند."""
    _fresh()
    _flag(True)
    try:
        cyc = "2026-07-31#2"
        _register(cyc)
        r1 = gab.run_for_cycle(cyc, now=NOW)
        assert r1.get("ok") is True, r1
        with open(gab._ledger_path(), "a", encoding="utf-8") as f:
            f.write("{corrupt json line\n")
            f.write("[1,2,3]\n")
        led = gab._load_ledger()
        assert led, "دفترِ سالم خالی برگشت"
        r2 = gab.run_for_cycle(cyc, now=NOW + 60)
        assert r2.get("status") == "NOOP", r2
    finally:
        _flag(False)


def t_same_action_id_with_a_different_payload_is_a_conflict_not_a_noop():
    """جهشِ معنایی که idempotency را می‌کشد: کسی payload را عوض کند و
    action_id را نگه دارد. باید CONFLICT/BLOCK شود، نه NOOP و نه اجرا."""
    _fresh()
    _flag(True)
    _ex, real, calls = _spy_executor()
    try:
        cyc = "2026-07-31#3"
        _register(cyc)
        r1 = gab.run_for_cycle(cyc, now=NOW)
        assert r1.get("ok") is True, r1
        led = gab._load_ledger()
        assert led
        key = next(iter(led))
        aid = key.rsplit(":", 1)[0]   # action_id خودش دونقطه دارد (act:<sha>)
        # دفتر را با همان action_id ولی امضای متفاوت بازنویسی کن
        fake = {"schema": "action-receipt.v1", "action_id": aid,
                "idempotency_key": f"{aid}:{'0' * 32}", "status": "EXECUTED"}
        gab._ledger_path().write_text(
            json.dumps(fake, ensure_ascii=False) + "\n", "utf-8")
        n_calls = len(calls)
        r2 = gab.run_for_cycle(cyc, now=NOW + 60)
        assert r2.get("ok") is False, r2
        assert "idempotency-conflict" in str(r2.get("reason")), r2
        assert len(calls) == n_calls, "CONFLICT ولی executor صدا خورد!"
    finally:
        _ex.execute = real
        _flag(False)


# ── nonceها ─────────────────────────────────────────────────────────────────
def t_nonces_roundtrip_and_corruption_is_an_empty_set():
    _fresh()
    assert gab._save_nonces({"n2", "n1"}) is True
    assert gab._load_nonces() == {"n1", "n2"}
    gab._nonces_path().write_text("{not json", "utf-8")
    assert gab._load_nonces() == set(), "فایلِ خراب باید set ِ خالی بدهد"


# ── زنجیرهٔ trace روی envelope ──────────────────────────────────────────────
def t_the_mission_envelope_now_carries_cycle_and_prereg_ids():
    """join ِ پرونده بدونِ حدس: cycle_id/prereg_id روی خودِ ردیفِ mission —
    و envelope همچنان از mission_contract.validate پاس می‌شود."""
    _fresh()
    _flag(True)
    try:
        cyc = "2026-07-31#4"
        _register(cyc)
        r = gab.run_for_cycle(cyc, now=NOW)
        assert r.get("ok") is True, r
        rows = [json.loads(x) for x in
                gab._missions_path().read_text("utf-8").splitlines()]
        m = rows[-1]
        assert m.get("cycle_id") == cyc, m
        assert m.get("prereg_id") == f"{cyc}:kdur", m   # قراردادِ prereg.v1
        import mission_contract as mc
        assert mc.validate(m) == [], mc.validate(m)
    finally:
        _flag(False)


def t_flag_off_is_still_a_total_noop_with_the_new_code():
    _fresh()
    _flag(False)
    r = gab.run_for_cycle("2026-07-31#9", now=NOW)
    assert r == {"schema": gab.SCHEMA, "cycle_id": "2026-07-31#9",
                 "ok": False, "reason": "flag-off"}, r
    assert not gab._missions_path().exists()
    assert not gab._nonces_path().exists(), "flag-off فایلِ nonce ساخت!"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_action_durability: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
