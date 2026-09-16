#!/usr/bin/env python3
"""U1 — صداقت حسگر (lane MP-V41-U1-20260907، سند مأموریت v4.1 §۴/§۵/§۱۶).

دو درزی که این تست‌ها قفل می‌کنند:
  ۱) stress.assess: حسگرِ غایب/خطادار → unknown (stress=null، quality=unknown،
     data_quality=degraded) — نه «۰.۰ آرام» (V4-A01).
  ۲) calibration_probe._binary: «unresolved» → گرید‌نشده (None) — نه شکستِ
     دودویی ۰ در Brier (V4-A02).
مسیرِ خوش‌عاقبت هم رگرسیون می‌شود: کلیدهای قدیمی دست‌نخورده می‌مانند.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
_CORTEX = _OPS / "cortex"
for _p in (str(_CORTEX), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import stress  # noqa: E402
import calibration_probe as cp  # noqa: E402


# ── stress: unknown ≠ calm ────────────────────────────────────────────────────
def test_all_sensors_missing_is_unknown_not_calm(tmp_path, monkeypatch):
    monkeypatch.setattr(stress, "STATE", tmp_path)
    monkeypatch.setattr(stress.opslib, "OPS", tmp_path)
    a = stress.assess()
    assert a["schema"] == "stress.v2"
    assert a["data_quality"] == "degraded"
    assert set(a["unknown"]) == set(stress._SUBSYSTEMS)
    for v in a["subsystems"].values():
        assert v["stress"] is None and v["quality"] == "unknown"
    assert a["organism_stress"] is None          # نه صفرِ آرام


def test_sensor_exception_is_unknown_not_calm(tmp_path, monkeypatch):
    monkeypatch.setattr(stress, "STATE", tmp_path)
    monkeypatch.setattr(stress.opslib, "OPS", tmp_path)

    def boom():
        raise RuntimeError("sensor broken")

    monkeypatch.setattr(stress, "_money_stress", boom)
    a = stress.assess()
    assert a["subsystems"]["money"]["stress"] is None
    assert a["subsystems"]["money"]["quality"] == "unknown"
    assert "money" in a["unknown"]
    assert a["data_quality"] == "degraded"


def test_happy_path_keys_unchanged(tmp_path, monkeypatch):
    (tmp_path / "telemetry-latest.json").write_text(
        json.dumps({"month": {"aud": 15}}), "utf-8")
    (tmp_path / "replication-latest.json").write_text(
        json.dumps({"sigma": {"sigma_effective": 0.5}}), "utf-8")
    (tmp_path / "doctor").mkdir()
    (tmp_path / "doctor" / "rfcs.json").write_text(json.dumps({"rfcs": []}), "utf-8")
    (tmp_path / "selfheal-events.jsonl").write_text("", "utf-8")
    (tmp_path / "governor").mkdir()
    (tmp_path / "governor" / "governor-alerts.md").write_text("", "utf-8")
    monkeypatch.setattr(stress, "STATE", tmp_path)
    monkeypatch.setattr(stress.opslib, "OPS", tmp_path)
    a = stress.assess()
    assert a["data_quality"] == "ok" and a["unknown"] == []
    assert abs(a["subsystems"]["money"]["stress"] - 0.5) < 1e-9
    assert a["subsystems"]["money"]["quality"] == "ok"
    for k in ("organism_stress", "level", "in_fear", "subsystems"):
        assert k in a


def test_organism_in_fear_carries_unknown_note(tmp_path, monkeypatch):
    monkeypatch.setattr(stress, "STATE", tmp_path)
    monkeypatch.setattr(stress.opslib, "OPS", tmp_path)
    feared, why = stress.organism_in_fear()
    assert feared is False
    assert "ناشناخته" in why and "ناقص" in why


# ── calibration_probe: unresolved ≠ failure ───────────────────────────────────
def _w(p: Path, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                 "utf-8")


def _isolate(monkeypatch, tmp_path):
    monkeypatch.setattr(cp, "CLAIMS", tmp_path / "claims.jsonl")
    monkeypatch.setattr(cp, "OUTCOMES", tmp_path / "outcomes.jsonl")
    monkeypatch.setattr(cp, "DISCOVERIES", tmp_path / "disc.jsonl")
    monkeypatch.setattr(cp, "SELF_ACCURACY", tmp_path / "sa.jsonl")


def test_unresolved_truth_is_ungraded_not_failure(tmp_path, monkeypatch):
    _isolate(monkeypatch, tmp_path)
    _w(tmp_path / "claims.jsonl", [{"key": "k1", "confidence": 0.8}])
    _w(tmp_path / "outcomes.jsonl", [{"key": "k1", "label": "unresolved"}])
    r = cp.probe(persist=False)
    assert r["n"] == 0 and r["graded"] == []
    assert r["ungraded"] == 1                       # بی‌جفت = گرید‌نشده
    assert "unresolved" not in cp._FALSY
    assert cp._binary({"key": "k1", "label": "unresolved"}) is None


def test_real_failure_and_success_still_grade(tmp_path, monkeypatch):
    _isolate(monkeypatch, tmp_path)
    _w(tmp_path / "claims.jsonl",
       [{"key": "bad", "confidence": 0.9}, {"key": "good", "confidence": 0.9}])
    _w(tmp_path / "outcomes.jsonl",
       [{"key": "bad", "correct": 0}, {"key": "good", "correct": 1}])
    r = cp.probe(persist=False)
    ys = {g["key"]: g["y"] for g in r["graded"]}
    assert ys == {"bad": 0, "good": 1}              # رگرسیون: ۰/۱ واقعی گرید می‌شوند


def test_probe_carries_truth_semantics_version(tmp_path, monkeypatch):
    _isolate(monkeypatch, tmp_path)
    _w(tmp_path / "claims.jsonl", [])
    _w(tmp_path / "outcomes.jsonl", [])
    r = cp.probe(persist=False)
    assert "binary_truth.v2" in r["truth_semantics"]
