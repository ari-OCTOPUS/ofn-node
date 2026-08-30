"""Deterministic offline replay + shadow ledger. Lab only."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .observation import Observation, Quality
from .pipeline import run_shadow_pipeline

T0 = datetime(2026, 8, 20, 1, 47, 26, tzinfo=timezone.utc)


def _obs(**kw: Any) -> Observation:
    base = dict(
        process_id=7096,
        boot_id="boot-2026-08-20T11:47:04+10",
        source_hash="abc123",
        quality=Quality.VALID.value,
        quality_reasons=[],
        latest_only=False,
        historical_claim=False,
        window_n=None,
        window_ready=2,
    )
    base.update(kw)
    return Observation(**base)  # type: ignore[arg-type]


def fixtures() -> dict[str, list[Observation]]:
    dt = T0
    rec = T0
    healthy = [
        _obs(observation_id="p1", source_id="pulse.arbiter_shadow", metric="arbiter.period_s",
             value=113.61, unit="s", occurred_at=T0, recorded_at=rec, decision_time=dt, beat=42830,
             provenance_path="fixture/healthy"),
        _obs(observation_id="c1", source_id="pulse.arbiter_shadow", metric="arbiter.color",
             value="GREEN", unit="enum", occurred_at=T0, recorded_at=rec, decision_time=dt, beat=42830,
             provenance_path="fixture/healthy"),
        _obs(observation_id="h1", source_id="lab.fixture", metric="rhythm.hrv",
             value=0.26, unit="s", occurred_at=T0, recorded_at=rec, decision_time=dt, beat=42830,
             provenance_path="fixture/healthy", window_n=8),
        _obs(observation_id="w1", source_id="lab.fixture", metric="rhythm.window_n",
             value=8, unit="count", occurred_at=T0, recorded_at=rec, decision_time=dt, beat=42830,
             provenance_path="fixture/healthy", window_n=8),
        _obs(observation_id="i1", source_id="state.identities", metric="identity_health",
             value=0.572, unit="ratio", occurred_at=T0, recorded_at=rec, decision_time=dt, beat=42830,
             provenance_path="fixture/healthy"),
        _obs(observation_id="l1", source_id="pulse.life_currency", metric="life_currency.unit",
             value="life_credit", unit="enum", occurred_at=T0, recorded_at=rec, decision_time=dt, beat=42830,
             provenance_path="fixture/healthy"),
        _obs(observation_id="t1", source_id="pulse.life_currency", metric="life_currency.tokens_min",
             value=0.003, unit="life_credit", occurred_at=T0, recorded_at=rec, decision_time=dt, beat=42830,
             provenance_path="fixture/healthy"),
        _obs(observation_id="d1", source_id="pulse.life_currency", metric="life_currency.daily_cap",
             value=30.0, unit="life_credit", occurred_at=T0, recorded_at=rec, decision_time=dt, beat=42830,
             provenance_path="fixture/healthy"),
        _obs(observation_id="j1", source_id="lab.fixture", metric="judge.rs_ba",
             value=0.55, unit="ratio", occurred_at=T0, recorded_at=rec, decision_time=dt, beat=42830,
             provenance_path="fixture/healthy"),
        _obs(observation_id="r1", source_id="lab.fixture", metric="resource.cpu_pct",
             value=12.0, unit="percent", occurred_at=T0, recorded_at=rec, decision_time=dt, beat=42830,
             provenance_path="fixture/healthy"),
    ]
    restart = [o for o in healthy if o.metric not in ("rhythm.hrv", "rhythm.window_n")]
    restart += [
        _obs(observation_id="h0", source_id="lab.fixture", metric="rhythm.hrv",
             value=0.0, unit="s", occurred_at=T0, recorded_at=rec, decision_time=dt, beat=42780,
             provenance_path="fixture/restart", window_n=1),
        _obs(observation_id="w0", source_id="lab.fixture", metric="rhythm.window_n",
             value=1, unit="count", occurred_at=T0, recorded_at=rec, decision_time=dt, beat=42780,
             provenance_path="fixture/restart", window_n=1),
    ]
    conflict = list(healthy)
    conflict.append(_obs(observation_id="p2", source_id="pulse.arbiter", metric="arbiter.period_s",
                         value=112.76, unit="s", occurred_at=T0, recorded_at=rec, decision_time=dt, beat=42830,
                         provenance_path="fixture/conflict"))
    latest_only = [
        _obs(observation_id="lo1", source_id="pulse.life_currency", metric="life_currency.tokens_min",
             value=0.003, unit="life_credit", occurred_at=T0, recorded_at=rec, decision_time=dt, beat=42784,
             provenance_path="latest.json", latest_only=True, historical_claim=True),
    ]
    future = list(healthy)
    future.append(_obs(observation_id="f1", source_id="lab.fixture", metric="resource.cpu_pct",
                       value=9.0, unit="percent",
                       occurred_at=T0 + timedelta(hours=2), recorded_at=T0 + timedelta(hours=2),
                       decision_time=dt, beat=99999, provenance_path="fixture/future"))
    missing_id = [o for o in healthy if o.metric not in ("identity_health", "identity.learner")]
    c042 = [o for o in healthy if o.metric != "life_currency.tokens_min"]
    c042.append(_obs(observation_id="z0", source_id="pulse.life_currency", metric="life_currency.tokens_min",
                     value=0.0, unit="life_credit", occurred_at=T0, recorded_at=rec, decision_time=dt, beat=1,
                     provenance_path="fixture/c042"))
    empty_reasons_live = list(healthy)  # slice still emits reasons even if live C-044
    return {
        "healthy": healthy,
        "restart_hrv": restart,
        "period_conflict": conflict,
        "latest_only": latest_only,
        "future": future,
        "missing_identity": missing_id,
        "c042": c042,
        "color_empty_reasons": empty_reasons_live,
    }


def run_all(out_dir: Path) -> dict[str, Any]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ledger = out_dir / "shadow-ledger.jsonl"
    results: dict[str, Any] = {"run_id": "replay-2026-08-20-wave0", "seed": "k-shadow-0", "version": "0.1.0", "scenarios": {}}
    for name, obs in fixtures().items():
        pipe = run_shadow_pipeline(obs, decision_time=T0, boot_id="boot-2026-08-20T11:47:04+10")
        results["scenarios"][name] = {
            "global_state": pipe["homeostatic_assessment"]["global_state"],
            "assessment_reasons_n": len(pipe["homeostatic_assessment"]["reasons"]),
            "excluded_n": len(pipe["homeostatic_assessment"]["excluded_evidence"]),
            "world_hypotheses_n": len(pipe["world_state"]["hypotheses"]),
            "gates": [{"domain": g["domain"], "mode": g["mode"], "executable": g["executable"]} for g in pipe["gate_decisions"]],
            "output_hash": pipe["output_hash"],
            "executable": False,
        }
        rec = {
            "schema": "shadow-ledger.v1",
            "run_id": results["run_id"],
            "scenario": name,
            "input_hash": hashlib.sha256(json.dumps([o.to_dict() for o in obs], sort_keys=True, default=str).encode()).hexdigest(),
            "output_hash": pipe["output_hash"],
            "code_version": pipe["code_version"],
            "decision_time": T0.isoformat(),
            "evidence_ids": pipe["homeostatic_assessment"]["evidence_ids"],
            "executable": False,
            "blockers": sorted({b for g in pipe["gate_decisions"] for b in g["blockers"]}),
            "reasons": pipe["homeostatic_assessment"]["reasons"][:8],
        }
        with ledger.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            try:
                os.fsync(fh.fileno())
            except OSError:
                pass
        (out_dir / f"{name}.json").write_text(json.dumps(pipe, ensure_ascii=False, indent=2, default=str), "utf-8")
    blob = json.dumps(results, sort_keys=True).encode()
    results["results_hash"] = hashlib.sha256(blob).hexdigest()
    (out_dir / "REPLAY-SUMMARY.json").write_text(json.dumps(results, indent=2), "utf-8")
    return results
