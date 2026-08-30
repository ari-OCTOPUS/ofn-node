#!/usr/bin/env python3
"""test_synapse_beat.py — سیم‌کشیِ اندامِ SENSE به رانتایم (C8، ۲۰۲۶-۰۷-۲۸).

تا امروز سه ماژولِ synapse کاملاً ساخته بودند ولی **ادغامِ رانتایمِ صفر** داشتند:
هیچ beat/وایرینگ/فلگی آن را صدا نمی‌زد و `out/` هیچ‌وقت فایل نگرفت. این تست اثبات
می‌کند که `synapse_beat` در wiring.py حالا آن وصل‌کردن است — flag-gated، STOP-aware،
non-blocking، offline-safe.

پشتِ OCTOPUS_SYNAPSE_ENABLED (پیش‌فرض خاموش → no-op کامل). $0، propose-only.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

_OPS = Path(__file__).resolve().parents[1]
for p in (str(_OPS), str(_OPS / "synapse"), str(_OPS / "budget")):
    if p not in sys.path:
        sys.path.insert(0, p)

import wiring  # noqa: E402
import sense   # noqa: E402


def _mk_events(n: int = 1500, start: float = 1_700_000_000.0) -> list[dict]:
    events, t, gap = [], start, 1.0
    for i in range(n):
        gap = 0.8 * gap + 0.2 * (1.0 + ((i * 37) % 7) / 10.0)
        t += max(gap, 0.05)
        events.append({"ts": t, "agent_id": f"organ-{i % 5}",
                       "event_name": "task.completed" if i % 3 else "heartbeat"})
    return events


@pytest.fixture()
def ops_tree(tmp_path: Path, monkeypatch) -> Path:
    """یک درختِ ops با events.jsonl واقعی بساز و wiring را به آن redirect کن."""
    ops = tmp_path / "ops"
    (ops / "state").mkdir(parents=True)
    (ops / "synapse" / "out").mkdir(parents=True)
    with (ops / "state" / "events.jsonl").open("w", encoding="utf-8") as fh:
        for e in _mk_events():
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")
    monkeypatch.setattr(wiring.opslib, "STATE_DIR", ops / "state")
    monkeypatch.setattr(wiring.opslib, "STOP_ORGANISM", ops / "STOP-ORGANISM")
    monkeypatch.setattr(sense, "_OPS_ROOT", ops)
    monkeypatch.setattr(sense, "DEFAULT_4D_ROOT", tmp_path / "no4d")
    monkeypatch.setattr(sense, "DEFAULT_OUT_DIR", ops / "synapse" / "out")
    monkeypatch.setattr(sense, "DEFAULT_TRAIL", ops / "state" / "synapse-trail.jsonl")
    return ops


@pytest.fixture(autouse=True)
def _clean_flags(monkeypatch):
    for k in ("OCTOPUS_SYNAPSE_ENABLED", "CHRONO_SYNAPSE_EVERY_N_BEATS",
              sense.FLAG, sense.DAILY_CAP_ENV):
        monkeypatch.delenv(k, raising=False)
    wiring._EPOCH_STATE.pop("synapse_sense", None)


# ── flag / STOP ───────────────────────────────────────────────────────────────

def test_flag_off_is_noop(monkeypatch):
    """فلگ خاموش → None (byte-identical با نبودِ beat)."""
    assert wiring.synapse_beat(beat=100) is None


def test_stop_organism_wins(ops_tree, monkeypatch):
    """STOP مقدم بر هر چیز — حتی با flag روی."""
    monkeypatch.setenv("OCTOPUS_SYNAPSE_ENABLED", "1")
    (ops_tree / "STOP-ORGANISM").write_text("halt", "utf-8")
    assert wiring.synapse_beat(beat=100) is None


def test_halt_wins(ops_tree, monkeypatch):
    monkeypatch.setenv("OCTOPUS_SYNAPSE_ENABLED", "1")
    monkeypatch.setattr(wiring.opslib, "halted", lambda: "STOP(architect)")
    assert wiring.synapse_beat(beat=100) is None


# ── cadence / epoch gate ──────────────────────────────────────────────────────

def test_first_boot_fires(ops_tree, monkeypatch):
    """اولین tick بعد از بوت باید شلیک کند (_EPOCH_STATE در بوت صفر است)."""
    monkeypatch.setenv("OCTOPUS_SYNAPSE_ENABLED", "1")
    monkeypatch.setenv("CHRONO_SYNAPSE_EVERY_N_BEATS", "60")
    out = wiring.synapse_beat(beat=70)   # epoch 1
    assert out is not None and "synapse" in out


def test_same_epoch_skips(ops_tree, monkeypatch):
    """همان epoch نباید دوباره شلیک کند (anti-aliasing cadence)."""
    monkeypatch.setenv("OCTOPUS_SYNAPSE_ENABLED", "1")
    monkeypatch.setenv("CHRONO_SYNAPSE_EVERY_N_BEATS", "60")
    wiring.synapse_beat(beat=70)         # epoch 1 شلیک
    assert wiring.synapse_beat(beat=119) is None   # هنوز epoch 1 → skip


# ── خروجی واقعی ──────────────────────────────────────────────────────────────

def test_beat_writes_proposal_and_trail(ops_tree, monkeypatch):
    """اثباتِ زندهٔ وصل‌کردن: beat باید هم proposal بنویسد هم سریِ زمانیِ صداقت."""
    monkeypatch.setenv("OCTOPUS_SYNAPSE_ENABLED", "1")
    out = wiring.synapse_beat(beat=100)
    assert out is not None, "beat شلیک نکرد"
    # proposal در out/
    proposals = list((ops_tree / "synapse" / "out").glob("proposal-*.json"))
    assert proposals, "هیچ proposal‌ای نوشته نشد"
    # trail در state/
    trail = ops_tree / "state" / "synapse-trail.jsonl"
    assert trail.exists(), "سریِ زمانیِ صداقت نوشته نشد"
    rec = json.loads(trail.read_text("utf-8").strip())
    for fld in ("ts", "cpm", "self_referential", "gate0", "delta", "kind"):
        assert fld in rec, f"فیلدِ {fld} در trail نیست"


def test_beat_non_blocking_on_error(ops_tree, monkeypatch):
    """اگر sense_once خطا دهد، beat نباید tick را بکشد — None برمی‌گرداند + alert."""
    monkeypatch.setenv("OCTOPUS_SYNAPSE_ENABLED", "1")

    def _boom(**kw):
        raise RuntimeError("synapse boom")
    monkeypatch.setattr(sense, "sense_once", _boom)
    alerted = []
    monkeypatch.setattr(wiring.opslib, "alert", lambda items: alerted.append(items))
    out = wiring.synapse_beat(beat=100)
    assert out is None                    # بی‌صدا fail شد
    assert alerted, "هیچ alert‌ای زده نشد — خطای خاموش ممنوع"
    assert "synapse_beat error" in alerted[0][0]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
