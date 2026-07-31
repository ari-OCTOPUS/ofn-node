#!/usr/bin/env python3
"""
_ops/tests/test_synapse_sense.py — تست‌های اندامِ synapse.

⚠️ وضعیتِ اجرا: این تست‌ها در جلسه‌ی نگارش (۲۰۲۶-۰۷-۲۴، kimi) **اجرا نشده‌اند** —
ابزارِ اجرای pytest در آن جلسه در دسترس نبود. [UNKNOWN] تا اولین اجرای:
    python -m pytest _ops/tests/test_synapse_sense.py -v
self_test() داخلِ خودِ ماژول‌ها نیز همین پوشش را بدونِ pytest می‌دهد:
    python _ops/synapse/sense.py            (flag خاموش → self_test)
    python _ops/synapse/trajectory_monitor.py
    python _ops/synapse/egress_policy.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

OPS = Path(__file__).resolve().parents[1]
if str(OPS) not in sys.path:
    sys.path.insert(0, str(OPS))

from synapse import egress_policy, sense, trajectory_monitor  # noqa: E402


# ── fixtures ─────────────────────────────────────────────────────────────────

def _mk_events(n: int = 1500, start: float = 1_700_000_000.0) -> list[dict]:
    events, t, gap = [], start, 1.0
    for i in range(n):
        gap = 0.8 * gap + 0.2 * (1.0 + ((i * 37) % 7) / 10.0)
        t += max(gap, 0.05)
        events.append({
            "timestamp": "2026-07-24T12:00:00",
            "ts": t,
            "agent_id": f"organ-{i % 5}",
            "event_name": "task.completed" if i % 3 else "heartbeat",
            "status": "ok",
        })
    return events


@pytest.fixture()
def ops_tree(tmp_path: Path) -> Path:
    ops = tmp_path / "ops"
    (ops / "state").mkdir(parents=True)
    with (ops / "state" / "events.jsonl").open("w", encoding="utf-8") as fh:
        for e in _mk_events():
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")
    return ops


@pytest.fixture(autouse=True)
def _clean_env():
    for k in (sense.FLAG, getattr(sense, "FLAG_OCTOPUS", "OCTOPUS_SYNAPSE_ENABLED"),
              sense.DAILY_CAP_ENV, trajectory_monitor.FLAG,
              egress_policy.FLAG_ENFORCE, egress_policy.FLAG_AUDIT):
        os.environ.pop(k, None)
    yield
    for k in (sense.FLAG, getattr(sense, "FLAG_OCTOPUS", "OCTOPUS_SYNAPSE_ENABLED"),
              sense.DAILY_CAP_ENV, trajectory_monitor.FLAG,
              egress_policy.FLAG_ENFORCE, egress_policy.FLAG_AUDIT):
        os.environ.pop(k, None)


# ── sense ────────────────────────────────────────────────────────────────────

class TestSense:
    def test_anchor_hash_format(self):
        h = sense._anchor_hash()
        assert len(h) == 64 and all(c in "0123456789abcdef" for c in h)
        assert h == sense._anchor_hash()

    def test_proposal_schema_exact(self):
        m = sense.compute_sense(_mk_events(200), metrics_mod=None)
        snap = {"source": "t", "content_hash": "0" * 64, "row_count": 200}
        p = sense.build_proposal(metrics=m, snapshot=snap)
        assert p["event"] == "b6.sog.proposal"
        assert p["schema_version"] == 1
        assert p["authority"] == "propose-only"
        assert set(p["proposal"]) <= {"kind", "summary", "evidence", "suggested_next"}
        for ev in p["proposal"]["evidence"]:
            assert set(ev) <= {"metric", "value", "baseline", "note"}
            assert {"metric", "value"} <= set(ev)

    def test_idempotency_deterministic(self):
        m = sense.compute_sense(_mk_events(200), metrics_mod=None)
        snap = {"source": "t", "content_hash": "1" * 64, "row_count": 200}
        assert (sense.build_proposal(metrics=m, snapshot=snap)["idempotency_key"]
                == sense.build_proposal(metrics=m, snapshot=snap)["idempotency_key"])

    def test_flag_off_noop(self, ops_tree):
        assert sense.sense_once(ops_root=ops_tree, fourd_root=ops_tree)["ran"] is False

    def test_sense_once_writes_proposal(self, ops_tree, tmp_path):
        os.environ[sense.FLAG] = "1"
        r = sense.sense_once(ops_root=ops_tree, fourd_root=tmp_path / "no4d",
                             out_dir=tmp_path / "out")
        assert r["ran"] is True
        data = json.loads(Path(r["proposal_path"]).read_text("utf-8"))
        assert data["authority"] == "propose-only"
        assert r["degraded"] is True  # بدونِ 4d → observation-only

    def test_daily_cap(self, ops_tree, tmp_path):
        os.environ[sense.FLAG] = "1"
        os.environ[sense.DAILY_CAP_ENV] = "1"
        out = tmp_path / "out"
        assert sense.sense_once(ops_root=ops_tree, fourd_root=tmp_path, out_dir=out)["ran"] is True
        r2 = sense.sense_once(ops_root=ops_tree, fourd_root=tmp_path, out_dir=out)
        assert r2["ran"] is False and r2["reason"] == "daily-cap"

    def test_self_test_passes(self):
        assert sense.self_test()["ALL"] is True

    # ── ۲۰۲۶-۰۷-۲۸ — سریِ زمانیِ صداقت (C8): شکافِ «حاضر ولی نه سنجش‌پذیر» ──
    # بازسنجیِ ۰۷-۲۵ گفت C8 «حاضر و اجراشونده ولی نه سنجش‌پذیر» است. این تست‌ها
    # اثبات می‌کنند که هر چرخهٔ Sense حالا یک ردیفِ قابل‌رصد با self_referential /
    # gate0 / delta می‌نویسد — یعنی خروجیِ اندام در زمان قابلِ دیدن است.

    def test_trail_appended_with_honesty_fields(self, ops_tree, tmp_path):
        """هر چرخه باید فیلدهای self_referential/gate0/delta را به trail بنویسد."""
        os.environ[sense.FLAG] = "1"
        trail = tmp_path / "trail.jsonl"
        trail.unlink(missing_ok=True)
        sense.sense_once(ops_root=ops_tree, fourd_root=tmp_path / "no4d",
                         out_dir=tmp_path / "out", trail_path=trail)
        sense.sense_once(ops_root=ops_tree, fourd_root=tmp_path / "no4d",
                         out_dir=tmp_path / "out2", trail_path=trail)
        lines = trail.read_text("utf-8").strip().splitlines()
        assert len(lines) >= 2, f"دو چرخه باید دو ردیف بنویسد، {len(lines)} شد"
        for line in lines:
            rec = json.loads(line)
            for fld in ("ts", "cpm", "self_referential", "gate0", "delta", "kind"):
                assert fld in rec, f"فیلدِ {fld} مفقود در trail: {rec}"

    def test_trail_path_configurable(self, tmp_path):
        """_append_trail باید مسیرِ دلخواه را بپذیرد تا تست ایزوله بماند."""
        m = sense.compute_sense(_mk_events(100), metrics_mod=None)
        p = tmp_path / "custom-trail.jsonl"
        sense._append_trail(m, "observation", trail_path=p)
        assert p.exists()
        rec = json.loads(p.read_text("utf-8").strip())
        assert rec["kind"] == "observation"
        assert "cpm" in rec

    def test_trail_failsoft_on_broken_path(self):
        """مسیرِ غیرقابل‌نوشتن نباید Sense را بکشد (fail-closed)."""
        m = sense.compute_sense(_mk_events(50), metrics_mod=None)
        # مسیرِ غیرمعتبر → بی‌صدا برمی‌گردد
        sense._append_trail(m, "observation", trail_path=Path("/nonexistent/x/y/trail.jsonl"))


# ── trajectory_monitor ───────────────────────────────────────────────────────

class TestTrajectory:
    def test_calm_no_burst(self):
        events = [{"ts": 1_700_000_000 + m * 60 + k * 7, "event_name": "heartbeat",
                   "agent_id": "a", "summary": ""} for m in range(120) for k in range(5)]
        assert not any(a["kind"] == "burst" for a in trajectory_monitor.check_once(events))

    def test_burst_detected(self):
        base = [{"ts": 1_700_000_000 + m * 60 + k * 7, "event_name": "heartbeat",
                 "agent_id": "a", "summary": ""} for m in range(120) for k in range(5)]
        burst = [{"ts": 1_700_000_000 + 121 * 60 + i, "event_name": "task.completed",
                  "agent_id": "b", "summary": ""} for i in range(100)]
        kinds = {a["kind"] for a in trajectory_monitor.check_once(base + burst)}
        assert "burst" in kinds

    def test_egress_marker_detected(self):
        base = [{"ts": 1_700_000_000 + m * 60 + k * 7, "event_name": "heartbeat",
                 "agent_id": "a", "summary": ""} for m in range(120) for k in range(5)]
        eg = [{"ts": 1_700_000_000 + 999 * 60 + i, "event_name": "task.completed",
               "agent_id": "c", "summary": "fetch https://example.com"} for i in range(3)]
        kinds = {a["kind"] for a in trajectory_monitor.check_once(base + eg)}
        assert "egress-attempt" in kinds

    def test_run_once_flag_off(self, ops_tree):
        assert trajectory_monitor.run_once(ops_tree / "state" / "events.jsonl")["ran"] is False

    def test_self_test_passes(self):
        assert trajectory_monitor.self_test()["ALL"] is True


# ── egress_policy ────────────────────────────────────────────────────────────

class TestEgress:
    def test_localhost_allowed(self):
        assert egress_policy.is_allowed("http://localhost:11434/api", "ollama") is True

    def test_cloud_denied_by_default(self):
        assert egress_policy.is_allowed("api.deepseek.com", "deepseek") is False
        assert egress_policy.is_allowed("example.com", "unknown") is False

    def test_garbage_denied(self):
        assert egress_policy.is_allowed("", "x") is False
        assert egress_policy.is_allowed(None, "x") is False

    def test_decide_shape(self):
        d = egress_policy.decide("https://example.com/x", "t")
        assert d["allowed"] is False and d["enforced"] is False

    def test_self_test_passes(self):
        assert egress_policy.self_test()["ALL"] is True
