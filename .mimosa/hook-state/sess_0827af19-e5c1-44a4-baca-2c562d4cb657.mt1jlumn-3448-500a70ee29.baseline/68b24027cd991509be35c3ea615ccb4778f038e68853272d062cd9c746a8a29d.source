# -*- coding: utf-8 -*-
"""تستهای اقتصاد داروینی — گیت ماشینی فاز ۶."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "heart"))

from heart.life_economy import LifeEconomy, EconomyConfig  # noqa: E402


def _eco(tmp: Path):
    return LifeEconomy(state_dir=tmp, cfg=EconomyConfig(
        rent_per_beat=1.0, initial_credit=10.0, sleep_threshold=0.0,
        retire_after_sleep_cycles=3, off_every_n_beats=10))


def test_rent_drains_and_sleeps(tmp_path):
    eco = _eco(tmp_path)
    eco._organ("w")["credits"] = 2.5
    eco.beat(1, ["w"])
    assert eco.organs["w"]["credits"] == 1.5
    eco.beat(2, ["w"])
    assert eco.organs["w"]["credits"] == 0.5
    eco.beat(3, ["w"])
    assert eco.organs["w"]["credits"] == 0.0   # budget_after هرگز منفی نیست
    eco.beat(4, ["w"])
    assert eco.organs["w"]["status"] == "SLEEP"


def test_ten_receipted_beats_budget_never_negative(tmp_path):
    eco = _eco(tmp_path)
    eco._organ("a")["credits"] = 20.0
    receipts = []
    for b in range(1, 11):
        receipts += eco.beat(b, ["a"])
    assert len(receipts) == 10
    assert all(float(r["credit_after"]) >= 0.0 for r in receipts)
    assert all(r["event_type"] == "rent" for r in receipts)
    assert eco.organs["a"]["credits"] == 10.0


def test_off_heartbeat_cadence(tmp_path):
    eco = _eco(tmp_path)
    eco._organ("s")["credits"] = 0.0
    eco._organ("s")["status"] = "SLEEP"
    receipts = eco.beat(10, ["s"])
    offs = [r for r in receipts if r["event_type"] == "heartbeat-off"]
    assert len(offs) == 1 and offs[0]["status"] == "OFF"


def test_self_report_gets_zero_credit(tmp_path):
    eco = _eco(tmp_path)
    before = eco.organs.get("x", {}).get("credits", eco.cfg.initial_credit)
    r = eco.self_report("x", 99.0)
    assert r["event_type"] == "reward-rejected"
    assert "self-report" in r["reason"]
    assert r["credit_before"] == r["credit_after"]


def test_reward_requires_independent_evidence(tmp_path):
    eco = _eco(tmp_path)
    r1 = eco.reward("x", "prediction_correct", evidence_ref="")
    assert r1["event_type"] == "reward-rejected"
    r2 = eco.reward("x", "prediction_correct", evidence_ref="ledger:abc")
    assert r2["event_type"] == "reward-prediction_correct"
    assert r2["credit_after"] > r2["credit_before"]


def test_survival_to_discovery_transfer_forbidden(tmp_path):
    eco = _eco(tmp_path)
    r = eco.transfer("SURVIVAL", "DISCOVERY", 5.0)
    assert r["event_type"] == "transfer-denied"
    assert "forbidden" in r["reason"]


def test_retire_not_delete(tmp_path):
    eco = _eco(tmp_path)
    eco._organ("z")["credits"] = 0.0
    eco._organ("z")["status"] = "SLEEP"
    eco._organ("z")["sleep_cycles"] = 2
    eco.defense("z", "دفاعِ من")
    eco.beat(1, ["z"])
    assert eco.organs["z"]["status"] == "RETIRED"
    assert eco.organs["z"]["retired_at"] is not None
    assert eco.organs["z"]["defense"]  # جنازه/دفاع حفظ میشود
    assert "z" in eco.organs              # delete نیست


def test_replay_reconstructs_balances(tmp_path):
    eco = _eco(tmp_path)
    eco._organ("organism")["credits"] = 20.0
    eco.reward("organism", "prediction_correct", evidence_ref="e1")
    for b in range(1, 5):
        eco.beat(b, ["organism"])
    eco.snapshot()
    rp = eco.replay()
    assert rp["replay_ok"] is True
    assert rp["credits_replayed"]["organism"] == eco.organs["organism"]["credits"]


def test_sim_integrity(tmp_path):
    eco = _eco(tmp_path)
    r = eco.run_sim(beats=12, seed="fixed")
    assert r["events"] >= 12
    assert r["replay"]["replay_ok"] is True
    wp = r["state"]["organs"]["work_pump"]
    assert wp["status"] in ("SLEEP", "RETIRED")   # خواب اتفاق افتاده؛ انتهای ۱۲ ضربان = بازنشستگی
    assert wp["credits"] == 0.0
    assert wp["defense"]                      # دفاع پیش از بازنشستگی ثبت شده
    assert r["state"]["organs"]["organism"]["credits"] == 10.0  # 20+2−12
