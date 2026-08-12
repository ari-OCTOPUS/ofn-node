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


def t_collaborator_intro_without_model():
    """بدون مدل: معرفی ساختاری (نه clarify)."""
    import collaborator as col
    os.environ["OCTOPUS_WIRE_COLLAB"] = "1"
    os.environ.pop("OCTOPUS_COLLAB_USE_MODEL", None)
    r = col.handle("سلام خودتو به من که مالک هستم معرفی کن")
    os.environ.pop("OCTOPUS_WIRE_COLLAB", None)
    assert r["kind"] == "intro", r
    assert "اختاپوس" in r["text"]
    assert r.get("model_source") == "deterministic-stub"


def t_collaborator_model_adapter_mock():
    """intro عمداً از _LLM_KINDS خارج است (2026-08-12) — حتی با فلگِ مدل، stub می‌ماند.

    دلیلِ تصمیمِ ثبت‌شده در collaborator.py:68: فرستادنِ «سلام» به DeepSeek باعثِ
    client_timeout 60s می‌شد؛ _live_intro_witness شاهدِ زندهٔ فوری (beat/pain/brains)
    دارد. این تست خودِ تصمیم را قفل می‌کند: مدل برای intro صدا زده نمی‌شود.
    """
    import collaborator as col
    import tempfile
    from pathlib import Path

    called = []

    def _fake_ask(*a, **k):
        called.append(1)
        return {"ok": True, "text": "SHOULD-NOT-APPEAR", "tier": "local",
                "model": "mock-llm", "cost_usd": 0.0}

    with tempfile.TemporaryDirectory() as td:
        os.environ["OCTOPUS_COLLAB_MODEL_COUNTER"] = str(Path(td) / "c.json")
        col._model.set_ask_impl(_fake_ask)
        os.environ["OCTOPUS_WIRE_COLLAB"] = "1"
        os.environ["OCTOPUS_COLLAB_USE_MODEL"] = "1"
        try:
            r = col.handle("سلام خودتو معرفی کن")
        finally:
            col._model.set_ask_impl(None)
            os.environ.pop("OCTOPUS_WIRE_COLLAB", None)
            os.environ.pop("OCTOPUS_COLLAB_USE_MODEL", None)
            os.environ.pop("OCTOPUS_COLLAB_MODEL_COUNTER", None)
    assert r["kind"] == "intro", r
    assert r.get("model_source") == "deterministic-stub", r
    assert called == [], "model must NOT be called for intro (intentional 2026-08-12 exclusion)"
    assert "SHOULD-NOT-APPEAR" not in str(r.get("text") or "")


def t_collaborator_model_fallback_on_failure():
    """شکستِ مدل برای kindِ مجاز (chat) → stub با warning صادقانه.

    intro عمداً از _LLM_KINDS خارج است (2026-08-12) پس fallback برایش رخ نمی‌دهد.
    مسیرِ fallback را با kindِ مجاز (chat) مستقیماً از _model_enhance می‌سنجیم.
    """
    import collaborator as col
    import tempfile
    from pathlib import Path

    def _boom(*a, **k):
        return {"ok": False, "reason": "timeout"}

    with tempfile.TemporaryDirectory() as td:
        os.environ["OCTOPUS_COLLAB_MODEL_COUNTER"] = str(Path(td) / "c.json")
        col._model.set_ask_impl(_boom)
        os.environ["OCTOPUS_WIRE_COLLAB"] = "1"
        os.environ["OCTOPUS_COLLAB_USE_MODEL"] = "1"
        try:
            r = col._model_enhance({"kind": "chat", "text": "x", "data": {}}, "owner-text")
        finally:
            col._model.set_ask_impl(None)
            os.environ.pop("OCTOPUS_WIRE_COLLAB", None)
            os.environ.pop("OCTOPUS_COLLAB_USE_MODEL", None)
            os.environ.pop("OCTOPUS_COLLAB_MODEL_COUNTER", None)
    assert r.get("model_source") == "model-fallback-stub", r
    assert "timeout" in str((r.get("data") or {}).get("warning") or ""), r


def t_collaborator_structured_stays_stub_even_with_model_flag():
    """هدف/runtime با فلگ مدل هم ارزان و stub می‌ماند."""
    import collaborator as col
    called = []

    def _track(*a, **k):
        called.append(1)
        return {"ok": True, "text": "should-not-use", "tier": "primary", "model": "x"}

    col._model.set_ask_impl(_track)
    os.environ["OCTOPUS_WIRE_COLLAB"] = "1"
    os.environ["OCTOPUS_COLLAB_USE_MODEL"] = "1"
    try:
        r = col.handle("هدف فعلی چیه؟")
    finally:
        col._model.set_ask_impl(None)
        os.environ.pop("OCTOPUS_WIRE_COLLAB", None)
        os.environ.pop("OCTOPUS_COLLAB_USE_MODEL", None)
    assert not called
    assert r.get("model_source") == "deterministic-stub"
    assert r["kind"] == "goal"

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


# ─── MEMORY HARDENING TESTS (Phase 3) ────────────────────────────────────────

def t_memory_rejects_empty_turn_id():
    """turn_id خالی باید رد شود."""
    import collab_memory as cm
    os.environ["OCTOPUS_WIRE_COLLAB_MEMORY"] = "1"
    result = cm.append(turn_id="", role="owner", intent="ask",
                       summary="clean summary", state_dir=STATE_DIR)
    os.environ.pop("OCTOPUS_WIRE_COLLAB_MEMORY", None)
    assert result["status"] == "rejected", f"empty turn_id should be rejected: {result}"
    assert "invalid turn_id" in result.get("reason", "")


def t_memory_rejects_oversized_turn_id():
    """turn_id بیش از 128 کاراکتر باید رد شود."""
    import collab_memory as cm
    os.environ["OCTOPUS_WIRE_COLLAB_MEMORY"] = "1"
    result = cm.append(turn_id="x" * 200, role="owner", intent="ask",
                       summary="clean summary", state_dir=STATE_DIR)
    os.environ.pop("OCTOPUS_WIRE_COLLAB_MEMORY", None)
    assert result["status"] == "rejected"
    assert "invalid turn_id" in result.get("reason", "")


def t_memory_rejects_invalid_role():
    """role غیرمجاز باید رد شود."""
    import collab_memory as cm
    os.environ["OCTOPUS_WIRE_COLLAB_MEMORY"] = "1"
    result = cm.append(turn_id="hr1", role="hacker", intent="ask",
                       summary="clean summary", state_dir=STATE_DIR)
    os.environ.pop("OCTOPUS_WIRE_COLLAB_MEMORY", None)
    assert result["status"] == "rejected"
    assert "invalid role" in result.get("reason", "")


def t_memory_rejects_empty_intent():
    """intent خالی باید رد شود."""
    import collab_memory as cm
    os.environ["OCTOPUS_WIRE_COLLAB_MEMORY"] = "1"
    result = cm.append(turn_id="hi1", role="owner", intent="",
                       summary="clean summary", state_dir=STATE_DIR)
    os.environ.pop("OCTOPUS_WIRE_COLLAB_MEMORY", None)
    assert result["status"] == "rejected"
    assert "invalid intent" in result.get("reason", "")


def t_memory_rejects_oversized_summary():
    """summary بیش از 2000 کاراکتر باید رد شود."""
    import collab_memory as cm
    os.environ["OCTOPUS_WIRE_COLLAB_MEMORY"] = "1"
    result = cm.append(turn_id="hs1", role="owner", intent="ask",
                       summary="x" * 3000, state_dir=STATE_DIR)
    os.environ.pop("OCTOPUS_WIRE_COLLAB_MEMORY", None)
    assert result["status"] == "rejected"
    assert "invalid summary" in result.get("reason", "")


def t_memory_rejects_state_dir_escape():
    """state_dir resolved بیرون از state root باید fail-closed رد شود."""
    import collab_memory as cm
    os.environ["OCTOPUS_WIRE_COLLAB_MEMORY"] = "1"
    escaped = Path(ENV["root"]) / "outside-memory"
    result = cm.append(turn_id="rs1", role="owner", intent="ask",
                       summary="clean summary", state_dir=escaped)
    os.environ.pop("OCTOPUS_WIRE_COLLAB_MEMORY", None)
    assert result == {"ok": False, "status": "rejected", "reason": "invalid state_dir"}
    assert not (escaped / "collab-memory.jsonl").exists()


# ─── RUN ──────────────────────────────────────────────────────────────────────

CHECKS = [
    ("memory-default-off", t_memory_default_off),
    ("memory-rejects-secrets", t_memory_rejects_secrets),
    ("memory-rejects-emails", t_memory_rejects_emails),
    ("memory-idempotent", t_memory_idempotent),
    ("memory-append-only", t_memory_append_only),
    ("memory-disabled-returns-not-ok", t_memory_disabled_returns_not_ok),
    ("memory-rejects-empty-turn-id", t_memory_rejects_empty_turn_id),
    ("memory-rejects-oversized-turn-id", t_memory_rejects_oversized_turn_id),
    ("memory-rejects-invalid-role", t_memory_rejects_invalid_role),
    ("memory-rejects-empty-intent", t_memory_rejects_empty_intent),
    ("memory-rejects-oversized-summary", t_memory_rejects_oversized_summary),
    ("memory-rejects-state-dir-escape", t_memory_rejects_state_dir_escape),
    ("collaborator-default-off", t_collaborator_default_off),
    ("collaborator-contract-compliance", t_collaborator_contract_compliance),
    ("collaborator-deterministic-stub", t_collaborator_deterministic_stub),
    ("collaborator-intro-without-model", t_collaborator_intro_without_model),
    ("collaborator-intro-excluded-from-model", t_collaborator_model_adapter_mock),
    ("collaborator-chat-model-fallback", t_collaborator_model_fallback_on_failure),
    ("collaborator-structured-stays-stub", t_collaborator_structured_stays_stub_even_with_model_flag),
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
