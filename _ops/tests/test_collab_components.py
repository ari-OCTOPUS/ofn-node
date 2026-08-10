#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_collab_components — تست‌های WP-E: collaborator + memory + digest + sim.

تست می‌کند:
  - collab_memory: default OFF، PII scrub، idempotency، append-only
  - collaborator: default OFF، deterministic stub، contract compliance
  - collab_digest: monitoring digest از snapshot
  - collab_sim: deterministic multi-turn simulation
  - security: no external_effect، no send، no cost
"""
import json
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "owner_console"), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402

ENV = harness.setup("collab-components")

STATE_DIR = ENV["ops"] / "state"


# ─── COLLAB MEMORY TESTS ─────────────────────────────────────────────────────

def t_memory_default_off():
    """collab_memory باید default OFF باشد."""
    import collab_memory as cm
    os.environ.pop("OCTOPUS_WIRE_COLLAB_MEMORY", None)
    assert not cm._is_enabled()


def t_memory_rejects_secrets():
    """PII/secret نباید ذخیره شود."""
    import collab_memory as cm
    os.environ["OCTOPUS_WIRE_COLLAB_MEMORY"] = "1"
    result = cm.append(
        turn_id="t1", role="owner", intent="test",
        summary="my api_key=<REDACTED-OPENAI-KEY>",
        state_dir=STATE_DIR,
    )
    os.environ.pop("OCTOPUS_WIRE_COLLAB_MEMORY", None)
    assert result["status"] == "rejected", f"باید rejected باشد: {result}"


def t_memory_rejects_emails():
    """email نباید ذخیره شود."""
    import collab_memory as cm
    os.environ["OCTOPUS_WIRE_COLLAB_MEMORY"] = "1"
    result = cm.append(
        turn_id="t2", role="owner", intent="test",
        summary="contact me at armin@example.com please",
        state_dir=STATE_DIR,
    )
    os.environ.pop("OCTOPUS_WIRE_COLLAB_MEMORY", None)
    assert result["status"] == "rejected"


def t_memory_idempotent():
    """turn_id تکراری نباید دوباره بنویسد."""
    import collab_memory as cm
    mem_path = STATE_DIR / "collab-memory.jsonl"
    if mem_path.exists():
        mem_path.unlink()
    os.environ["OCTOPUS_WIRE_COLLAB_MEMORY"] = "1"
    r1 = cm.append(turn_id="dup1", role="owner", intent="ask",
                   summary="clean summary", state_dir=STATE_DIR)
    r2 = cm.append(turn_id="dup1", role="owner", intent="ask",
                   summary="clean summary", state_dir=STATE_DIR)
    os.environ.pop("OCTOPUS_WIRE_COLLAB_MEMORY", None)
    assert r1["status"] == "appended"
    assert r2["status"] == "duplicate"


def t_memory_append_only():
    """append باید فقط append کند، نه overwrite."""
    import collab_memory as cm
    mem_path = STATE_DIR / "collab-memory.jsonl"
    if mem_path.exists():
        mem_path.unlink()
    os.environ["OCTOPUS_WIRE_COLLAB_MEMORY"] = "1"
    cm.append(turn_id="a1", role="owner", intent="ask", summary="first", state_dir=STATE_DIR)
    cm.append(turn_id="a2", role="owner", intent="ask", summary="second", state_dir=STATE_DIR)
    os.environ.pop("OCTOPUS_WIRE_COLLAB_MEMORY", None)
    lines = mem_path.read_text("utf-8").strip().splitlines()
    assert len(lines) == 2


def t_memory_disabled_returns_not_ok():
    """وقتی OFF است، append باید ok=False برگرداند."""
    import collab_memory as cm
    os.environ.pop("OCTOPUS_WIRE_COLLAB_MEMORY", None)
    result = cm.append(turn_id="x", role="owner", intent="x", summary="x", state_dir=STATE_DIR)
    assert not result["ok"]


# ─── COLLABORATOR ENGINE TESTS ──────────────────────────────────────────────

def t_collaborator_default_off():
    """collaborator باید default OFF باشد."""
    import collaborator as col
    os.environ.pop("OCTOPUS_WIRE_COLLAB", None)
    r = col.handle("test")
    assert r["kind"] == "disabled"


def t_collaborator_contract_compliance():
    """reply باید owner-console.reply.v1 و external_effect=False."""
    import collaborator as col
    os.environ["OCTOPUS_WIRE_COLLAB"] = "1"
    r = col.handle("هدف فعلی چیه؟")
    os.environ.pop("OCTOPUS_WIRE_COLLAB", None)
    assert r["schema"] == "owner-console.reply.v1"
    assert r["external_effect"] is False
    assert r["estimated_cost"] == 0
    assert r["send_attempted"] is False


def t_collaborator_deterministic_stub():
    """stub باید deterministic باشد — همان ورودی همان rationale."""
    import collaborator as col
    os.environ["OCTOPUS_WIRE_COLLAB"] = "1"
    r1 = col.handle("هدف فعلی چیه؟")
    r2 = col.handle("هدف فعلی چیه؟")
    os.environ.pop("OCTOPUS_WIRE_COLLAB", None)
    assert r1.get("model_source") == "deterministic-stub"
    # rationale should be the same for same kind
    assert (r1.get("data") or {}).get("rationale") == (r2.get("data") or {}).get("rationale")


def t_collaborator_no_model_adapter():
    """OCTOPUS_COLLAB_USE_MODEL=1 ولی adapter نباید وصل شود (fallback to stub)."""
    import collaborator as col
    os.environ["OCTOPUS_WIRE_COLLAB"] = "1"
    os.environ["OCTOPUS_COLLAB_USE_MODEL"] = "1"
    r = col.handle("test")
    os.environ.pop("OCTOPUS_WIRE_COLLAB", None)
    os.environ.pop("OCTOPUS_COLLAB_USE_MODEL", None)
    assert "NOT_CONNECTED" in r.get("model_source", "") or "stub" in r.get("model_source", "")


# ─── DIGEST TESTS ───────────────────────────────────────────────────────────

def t_digest_builds_from_snapshot():
    """digest باید از snapshot بسازد."""
    import collab_digest as cd
    fake = {"organism": {"beat": 42, "halted": False, "frozen": False},
            "health": {}, "flags": {"X": "1"}}
    d = cd.build_digest(snapshot=fake)
    assert d["schema"] == "CollabDigest.v1"
    assert any("beat=42" in v for v in d["verified_changes"])


def t_digest_critical_on_halted():
    """اگر organism halted است، digest باید CRITICAL."""
    import collab_digest as cd
    fake = {"organism": {"halted": True, "frozen": False}, "health": {}, "flags": {}}
    d = cd.build_digest(snapshot=fake)
    assert d["status"] == "CRITICAL"
    assert d["interrupt_affordance"] is True


def t_digest_ok_when_healthy():
    """digest باید OK وقتی همه سالم."""
    import collab_digest as cd
    fake = {"organism": {"halted": False, "frozen": False}, "health": {}, "flags": {}}
    d = cd.build_digest(snapshot=fake)
    assert d["status"] == "OK"
    assert d["interrupt_affordance"] is False


# ─── SIMULATION TESTS ───────────────────────────────────────────────────────

def t_sim_deterministic():
    """sim باید deterministic باشد."""
    import collab_sim as cs
    sd1 = Path(tempfile.mkdtemp(prefix="sim1-"))
    sd2 = Path(tempfile.mkdtemp(prefix="sim2-"))
    r1 = cs.run_simulation(state_dir=sd1)
    r2 = cs.run_simulation(state_dir=sd2)
    # Same scenario → same reply kinds
    kinds1 = [t["reply_kind"] for t in r1["trace"]]
    kinds2 = [t["reply_kind"] for t in r2["trace"]]
    assert kinds1 == kinds2, f"non-deterministic: {kinds1} vs {kinds2}"


def t_sim_no_external_effect():
    """هیچ turn نباید external_effect داشته باشد."""
    import collab_sim as cs
    sd = Path(tempfile.mkdtemp(prefix="sim-eff-"))
    r = cs.run_simulation(state_dir=sd)
    assert r["security_proof"]["all_external_effect_false"] is True
    assert r["security_proof"]["all_cost_zero"] is True
    assert r["security_proof"]["all_send_attempted_false"] is True


def t_sim_produces_memory():
    """sim باید memory records بسازد."""
    import collab_sim as cs
    sd = Path(tempfile.mkdtemp(prefix="sim-mem-"))
    r = cs.run_simulation(state_dir=sd)
    assert r["memory_records"] > 0, "باید memory records داشته باشد"


def t_sim_produces_digest():
    """sim باید digest بسازد."""
    import collab_sim as cs
    sd = Path(tempfile.mkdtemp(prefix="sim-dig-"))
    r = cs.run_simulation(state_dir=sd)
    assert "digest" in r
    assert r["digest"]["schema"] == "CollabDigest.v1"


# ─── RUN ──────────────────────────────────────────────────────────────────────

CHECKS = [
    ("memory-default-off", t_memory_default_off),
    ("memory-rejects-secrets", t_memory_rejects_secrets),
    ("memory-rejects-emails", t_memory_rejects_emails),
    ("memory-idempotent", t_memory_idempotent),
    ("memory-append-only", t_memory_append_only),
    ("memory-disabled-returns-not-ok", t_memory_disabled_returns_not_ok),
    ("collaborator-default-off", t_collaborator_default_off),
    ("collaborator-contract-compliance", t_collaborator_contract_compliance),
    ("collaborator-deterministic-stub", t_collaborator_deterministic_stub),
    ("collaborator-no-model-adapter", t_collaborator_no_model_adapter),
    ("digest-builds-from-snapshot", t_digest_builds_from_snapshot),
    ("digest-critical-on-halted", t_digest_critical_on_halted),
    ("digest-ok-when-healthy", t_digest_ok_when_healthy),
    ("sim-deterministic", t_sim_deterministic),
    ("sim-no-external-effect", t_sim_no_external_effect),
    ("sim-produces-memory", t_sim_produces_memory),
    ("sim-produces-digest", t_sim_produces_digest),
]

failed = harness.run(CHECKS)
sys.exit(1 if failed else 0)
