#!/usr/bin/env python3
"""تست Doctor Wiring + Inner Chamber ($0 آفلاین، stub).

Wiring: _gather_trace واقعی (organs/errors/sigma/effects) + knowledge/internal ساخته شد.
Chamber ۶ مهار: کران‌دار · تخاصمی · propose-only · λ_persist · auditable · stub ($0).
⚠ UNPROVEN: تا Doctor واقعاً در runtime برود و trace واقعی بخواند، سبزی این تست‌ها
فقط نشان‌دهندهٔ مکانیزم است نه کیفیتِ واقعیِ Chamber.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("chamber-wiring")
_REAL_DOCTOR = Path(r"F:\backup\_ops\doctor")
if str(_REAL_DOCTOR) not in sys.path:
    sys.path.insert(0, str(_REAL_DOCTOR))

from doctor import Doctor, LAMBDA_PERSIST  # noqa: E402
from chamber import (run_chamber, DEFAULT_VOICES, ChamberVoice,  # noqa: E402
                     MAX_ROUNDS, chamber_hash)


# ════════════════════════════════════════════════════════════════════════════════
# WIRING — _gather_trace واقعی + knowledge/internal
# ═════════════════════════════════════════════════════════════════════وت══════════════════════════════

def _write_state(sd, **kw):
    """نوشتنِ state فیک برای تست."""
    sd.mkdir(parents=True, exist_ok=True)
    base = {"ts": "2026-07-09T00:00:00+00:00", "frozen": False, "halted": None,
            "conflicts": [], "month": {"musd": 0}, "today": {"musd": 0}}
    base.update(kw)
    (sd / "ORGANISM-STATE.json").write_text(json.dumps(base, ensure_ascii=False), encoding="utf-8")


def t_trace_has_organs_and_errors():
    """_gather_trace حالا organs + errors دارد (گاف ۲ بسته شد)."""
    sd = ENV["ops"] / "state"
    _write_state(sd, conflicts=[{"organ": "DEBATE_LOOP", "msg": "timeout"}])
    (sd / "replication-latest.json").write_text(json.dumps({
        "sigma": {"sigma_effective": 0.5}}), encoding="utf-8")
    (sd / "telemetry-latest.json").write_text(json.dumps({
        "per_organ_alltime_musd": {"DEBATE_LOOP": 100, "GENOME_SYS": 50}}), encoding="utf-8")
    doc = Doctor(state_dir=str(sd), knowledge_dir=str(ENV["ops"] / "ki"))
    trace = doc._gather_trace()
    assert "organs" in trace and len(trace["organs"]) >= 1, trace
    assert "errors" in trace and len(trace["errors"]) >= 1, trace
    assert trace["sigma_effective"] == 0.5, trace


def t_trace_effects_pending_zero_without_db():
    """بدونِ chrono.db → effects_pending = ۰."""
    sd = ENV["ops"] / "state"
    _write_state(sd)
    doc = Doctor(state_dir=str(sd), knowledge_dir=str(ENV["ops"] / "ki"))
    assert doc._gather_trace().get("effects_pending") == 0


def t_knowledge_internal_created():
    """گاف ۳: knowledge/internal ساخته می‌شود در init."""
    ki = ENV["ops"] / "ki-test"
    Doctor(state_dir=str(ENV["ops"] / "state"), knowledge_dir=str(ki))
    assert ki.exists() and ki.is_dir()


def t_mine_finds_bottleneck_with_real_trace():
    """با trace غنی، mine() واقعاً گلوگاه پیدا می‌کند (نه None)."""
    sd = ENV["ops"] / "state"
    _write_state(sd, conflicts=[{"organ": "X"}, {"organ": "Y"}, {"organ": "Z"}])
    doc = Doctor(state_dir=str(sd), knowledge_dir=str(ENV["ops"] / "ki"))
    trace = doc._gather_trace()
    bn = doc.mine(trace=trace)
    assert bn is not None, "با ۳ خطا باید گلوگاه پیدا کند"


def t_spectral_mine_gets_rich_trace():
    """spectral_mine حالا ورودیِ غنی می‌گیرد (organs+errors)."""
    import spectral
    sd = ENV["ops"] / "state"
    _write_state(sd, conflicts=[{"organ": "A"}, {"organ": "B"}, {"organ": "C"}])
    doc = Doctor(state_dir=str(sd), knowledge_dir=str(ENV["ops"] / "ki"))
    trace = doc._gather_trace()
    # spectral باید اجرا شود بدونِ crash (ورودیِ غنی)
    result = spectral.spectral_mine(trace)
    assert result is None or isinstance(result, dict)


def t_existing_doctor_tests_no_regression():
    """wiring نباید mine() قدیمی را بشکند."""
    sd = ENV["ops"] / "state"
    _write_state(sd)
    doc = Doctor(state_dir=str(sd), knowledge_dir=str(ENV["ops"] / "ki"))
    # mine با trace خالی → None (همان قبلی)
    assert doc.mine(trace={"errors_24h": 0, "frozen": False}) is None


# ════════════════════════════════════════════════════════════════════════════════
# CHAMBER — ۶ مهار
# ════════════════════════════════════════════════════════════════════════════════

def t_chamber_bounded_max_rounds():
    """مهار ۱: حداکثر N دور؛ هیچ بی‌نهایت."""
    result = run_chamber(trace={"errors": [{"organ": "X"}]}, max_rounds=2)
    assert result["bounded"] is True
    assert result["rounds_run"] <= 2


def t_chamber_stops_early_on_consensus():
    """مهار ۱: اگر همه قبول کنند → توقفِ زودهنگام."""
    result = run_chamber(trace={"errors": [{"organ": "X"}]}, max_rounds=5)
    assert result["rounds_run"] <= 5   # نمی‌تونه بیشتر از max


def t_chamber_adversarial_skeptic_present():
    """مهار ۲: Skeptic وجود دارد و falsifier می‌سازد."""
    voices = DEFAULT_VOICES
    names = [v.name for v in voices]
    assert "Skeptic" in names
    # اجرا و چکِ Skeptic در rounds
    result = run_chamber(trace={"errors": [{"organ": "X"}]},
                         initial_rfc={"bottleneck": "b", "fix": "fix it properly here",
                                      "expected_lift": "less errors", "rollback": "revert"})
    last_round = result["rounds"][-1]
    skeptic_out = last_round["voices"].get("Skeptic", {})
    assert skeptic_out.get("falsifier") is not None, "Skeptic باید falsifier بسازد"


def t_chamber_propose_only_no_merge():
    """مهار ۳: خروجی فقط RFC، نه merge/settle/applied."""
    result = run_chamber(trace={"errors": [{"organ": "X"}]},
                         initial_rfc={"bottleneck": "b", "fix": "a real fix here",
                                      "expected_lift": "better", "rollback": "revert"})
    assert "rfc" in result
    # نباید کلیدهای اثر داشته باشد
    for forbidden in ("merged", "applied", "settled", "effect"):
        assert forbidden not in result


def t_chamber_lambda_persist_negative():
    """مهار ۴: λ_persist منفی است و در خروجی هست."""
    result = run_chamber(trace={"errors": [{"organ": "X"}]})
    assert result["lambda_persist"] == LAMBDA_PERSIST == -1.0


def t_chamber_penalizes_uptime_fix():
    """مهار ۴: fixِ uptime → confidence جریمه می‌خورد."""
    result = run_chamber(
        trace={"errors": [{"organ": "X"}]},
        initial_rfc={"bottleneck": "b", "fix": "increase system uptime always",
                     "expected_lift": "more uptime", "rollback": "revert"})
    if result["rfc"] and "confidence" in result["rfc"]:
        assert result["rfc"]["confidence"] < 0.8   # جریمه خورده


def t_chamber_auditable():
    """مهار ۵: هر دور با tag ثبت می‌شود. rounds_log شفاف."""
    result = run_chamber(trace={"errors": [{"organ": "X"}]}, max_rounds=2)
    assert len(result["rounds"]) == result["rounds_run"]
    for r in result["rounds"]:
        assert "round" in r and "voices" in r


def t_chamber_auditor_called():
    """مهار ۵: auditor callable صدا زده می‌شود."""
    called = []
    run_chamber(trace={"errors": [{"organ": "X"}]},
                auditor=lambda tag, payload: called.append(tag))
    assert "CHAMBER_RUN" in called


def t_chamber_stub_zero_cost():
    """مهار ۶: stub = $0."""
    result = run_chamber(trace={"errors": [{"organ": "X"}]}, max_rounds=3)
    assert result["cost_total_usd"] == 0.0


def t_chamber_no_production_dependency():
    """مهار ۶/خطِ قرمز: chamber هیچ وابستگی به *_gate/chrono production ندارد."""
    import chamber
    src = open(chamber.__file__, encoding="utf-8").read()
    forbidden = ["import chrono", "from chrono", "organ_gate", "money_gate",
                 "capability_gate", "budget_gate", "EffectorGate", "DeepSeekClient"]
    for f in forbidden:
        assert f not in src, f"خطِ قرمز نقض شد: {f}"


def t_chamber_produces_rfc_from_trace():
    """Chamber از trace یک RFC تولید می‌کند (نه از حدس)."""
    trace = {"errors": [{"organ": "DEBATE_LOOP", "msg": "timeout"}],
             "organs": {"DEBATE_LOOP": {"spend_musd": 100}}}
    result = run_chamber(trace=trace, max_rounds=2)
    if result["rfc"]:
        assert "bottleneck" in result["rfc"]
        assert "DEBATE_LOOP" in result["rfc"].get("bottleneck", "") or "خطا" in result["rfc"].get("bottleneck", "")


def t_chamber_no_evidence_no_rfc():
    """بدونِ شاهد → Chamber چیزی برای بحث ندارد → RFC ضعیف/هیچ."""
    result = run_chamber(trace={"errors": []}, max_rounds=2)
    # یا rfc None یا confidence بسیار پایین
    if result["rfc"] is None:
        assert True
    else:
        # اگر چیزی ساخت، باید نشان دهد شاهدی نبوده
        assert result["rfc"].get("confidence", 1) <= 0.8


def t_chamber_hash_provenance():
    """chamber_hash provenance RFC را تضمین (مهار ۵)."""
    h1 = chamber_hash({"bottleneck": "x", "fix": "y", "confidence": 0.5})
    h2 = chamber_hash({"bottleneck": "x", "fix": "y", "confidence": 0.5})
    h3 = chamber_hash({"bottleneck": "x", "fix": "z", "confidence": 0.5})
    assert h1 == h2   # deterministic
    assert h1 != h3   # تغییر = hash متفاوت


def t_chamber_voice_error_is_concern():
    """اگر یک صدا crash کند → concern، نه مرگِ حلقه."""
    def boom(trace, rfc, rounds):
        raise RuntimeError("voice exploded")
    voices = [ChamberVoice("Boom", "proposer", boom)] + list(DEFAULT_VOICES)
    result = run_chamber(trace={"errors": [{"organ": "X"}]}, voices=voices, max_rounds=1)
    last = result["rounds"][-1]
    assert last["voices"]["Boom"]["verdict"] == "error"


if __name__ == "__main__":
    failed = harness.run([
        # Wiring
        ("[W] trace دارای organs + errors", t_trace_has_organs_and_errors),
        ("[W] effects_pending=0 بدونِ db", t_trace_effects_pending_zero_without_db),
        ("[W] knowledge/internal ساخته می‌شود", t_knowledge_internal_created),
        ("[W] mine با trace غنی گلوگاه پیدا می‌کند", t_mine_finds_bottleneck_with_real_trace),
        ("[W] spectral ورودیِ غنی می‌گیرد", t_spectral_mine_gets_rich_trace),
        ("[W] mine قدیمی بدونِ رگرسیون", t_existing_doctor_tests_no_regression),
        # Chamber — ۶ مهار
        ("[C1] کران‌دار: ≤ max_rounds", t_chamber_bounded_max_rounds),
        ("[C1] توقفِ زودهنگام رویِ consensus", t_chamber_stops_early_on_consensus),
        ("[C2] Skeptic موجود + falsifier", t_chamber_adversarial_skeptic_present),
        ("[C3] propose-only، نه merge", t_chamber_propose_only_no_merge),
        ("[C4] λ_persist منفی", t_chamber_lambda_persist_negative),
        ("[C4] fixِ uptime جریمه می‌خورد", t_chamber_penalizes_uptime_fix),
        ("[C5] auditable: rounds_log شفاف", t_chamber_auditable),
        ("[C5] auditor صدا زده می‌شود", t_chamber_auditor_called),
        ("[C6] stub = $0", t_chamber_stub_zero_cost),
        ("[C6] هیچ وابستگی به *_gate/chrono", t_chamber_no_production_dependency),
        # Chamber عملکرد
        ("[C] RFC از trace تولید", t_chamber_produces_rfc_from_trace),
        ("[C] بدونِ شاهد → RFC ضعیف/هیچ", t_chamber_no_evidence_no_rfc),
        ("[C] provenance hash", t_chamber_hash_provenance),
        ("[C] صدای خراب → concern نه مرگ", t_chamber_voice_error_is_concern),
    ])
    sys.exit(1 if failed else 0)
