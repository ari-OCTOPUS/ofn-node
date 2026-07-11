"""test_phase1_envelope.py — Phase-1 (#۱۱–۱۳): EventEnvelope + HeartState + Incident.

پوشش:
  #۱۱ envelope: فیلدهای اختیاریِ schema_version/correlation_id/idempotency_key
      (backward-compatible) + غنی‌سازیِ control_plane از registry (fail-soft، content-free).
  #۱۲ HeartState adapter: build فِیل-سافت، persist فقط با فلگ (سایه، owner-gated).
  #۱۳ Incident record: open/contain، ریسکِ بالا→approval required، scrub containment.

همه additive/read-only/shadow — صفر تغییرِ رفتارِ زنده. env ایزوله از harness.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "heart"))

import harness
ENV = harness.setup("phase1-envelope")

import opslib            # noqa: E402
import events           # noqa: E402
import heartstate       # noqa: E402

STATE = Path(ENV["ops"]) / "state"


def _seed_registry():
    """یک snapshotِ registry ِ کوچک در stateِ تست بنویس (خوراکِ enrichment)."""
    reg = STATE / "registry"
    reg.mkdir(parents=True, exist_ok=True)
    (reg / "registry-latest.json").write_text(json.dumps({
        "schema": "registry.v0",
        "entities": [
            {"logical_id": "urn:octopus:agent:vault-cartographer",
             "entity_type": "Agent", "display_name": "Vault Cartographer",
             "owner": "آری", "risk_tier": "R1", "risk_declared": "low",
             "conformance_score": 0.8},
            {"logical_id": "urn:octopus:project:crypto-etoro",
             "entity_type": "Project", "display_name": "Crypto - etoro",
             "owner": "آری", "risk_tier": "R4-pending", "risk_declared": "critical",
             "conformance_score": 0.83},
        ],
    }, ensure_ascii=False), "utf-8")


# ── #۱۱ EventEnvelope ─────────────────────────────────────────────────────────
def t_a_optional_fields_backcompat():
    """امضای قدیمی همچنان کار می‌کند و فیلدهای نو با پیش‌فرضِ صریح حاضرند (نه null)."""
    e = events.emit("task.completed", "x")                 # سبکِ قدیمی — نباید بشکند
    for k in ("timestamp", "trace_id", "agent_id", "event_name", "approval_state",
              "schema_version", "correlation_id", "idempotency_key"):
        assert k in e, f"فیلدِ گمشده: {k}"
    assert e["schema_version"] == "event.v2"
    assert e["correlation_id"] == "" and e["idempotency_key"] == ""
    e2 = events.emit("task.started", "y", correlation_id="corr-1", idempotency_key="idem-1")
    assert e2["correlation_id"] == "corr-1" and e2["idempotency_key"] == "idem-1"
    # بدونِ enrich، هیچ control_plane چسبانده نمی‌شود (پیش‌فرضِ کم‌هزینه)
    assert "control_plane" not in e


def t_b_enrich_from_registry_failsoft():
    """enrich=True زمینهٔ control-plane را از registry می‌آورد؛ ناشناخته→بدونِ بلوک؛ هرگز crash."""
    # قبل از seed: fail-soft (فایل نیست) — بدونِ کرش، بدونِ control_plane
    pre = events.emit("task.started", "nobody", enrich=True)
    assert "control_plane" not in pre
    _seed_registry()
    ev = events.emit("task.started", "vault-cartographer", enrich=True)
    cp = ev.get("control_plane") or {}
    assert cp.get("owner") == "آری" and cp.get("risk_tier") == "R1"
    assert cp.get("logical_id") == "urn:octopus:agent:vault-cartographer"
    # نگاشت با display-name slug هم کار می‌کند (Crypto - etoro → crypto-etoro)
    ev2 = events.emit("task.completed", "crypto-etoro", enrich=True)
    assert (ev2.get("control_plane") or {}).get("risk_tier") == "R4-pending"
    # agent_idِ ناشناخته: بدونِ control_plane (نه حدس)
    ev3 = events.emit("task.completed", " غریبه", enrich=True)
    assert "control_plane" not in ev3


# ── #۱۳ Incident record ───────────────────────────────────────────────────────
def t_c_incident_names_registered():
    """نام‌های incident در EVENT_NAMES هستند و coerce به task.completed نمی‌شوند."""
    assert "incident.opened" in events.EVENT_NAMES
    assert "incident.contained" in events.EVENT_NAMES
    assert events.emit("incident.opened", "x")["event_name"] == "incident.opened"


def t_d_incident_open_contain_flow():
    """open→ریسکِ بالا approval=required + رکوردِ ساختاریافته؛ contain→بسته؛ recent هر دو را دارد."""
    op = events.open_incident("doctor", what="نقضِ σ", risk="critical", where="heart",
                              path="heart/control_law", policy="restrict",
                              evidence="ledger#123", replay_ref="replay_s#5")
    assert op["event_name"] == "incident.opened" and op["status"] == "alert"
    assert op["approval_state"] == "required"               # critical = منتظرِ مالک
    inc = op.get("incident") or {}
    assert inc.get("what") == "نقضِ σ" and inc.get("outcome") == "open"
    assert inc.get("risk") == "critical" and inc.get("replay_ref") == "replay_s#5"
    # ریسکِ پایین → approval صرفاً unknown (نه required)
    low = events.open_incident("doctor", what="کندیِ لِین", risk="R1")
    assert low["approval_state"] == "unknown"
    co = events.contain_incident("doctor", trace_id=op["trace_id"], outcome="contained",
                                 note="خودترمیم")
    assert co["event_name"] == "incident.contained"
    assert (co.get("incident") or {}).get("outcome") == "contained"
    rec = events.recent_incidents(5)
    names = [r["event_name"] for r in rec]
    assert "incident.opened" in names and "incident.contained" in names
    assert rec[0]["event_name"] == "incident.contained"    # جدیدترین اول


def t_e_incident_scrub_containment():
    """هیچ رشتهٔ ممنوعِ containment از رکوردِ incident بیرون نمی‌رود."""
    ev = events.open_incident("x", what="نشتِ اونلی فنز", where="onlyfans profile",
                              evidence="صبا media")
    blob = json.dumps(ev, ensure_ascii=False)
    for banned in ("اونلی", "onlyfans", "صبا"):
        assert banned not in blob, f"نشت: {banned}"
    inc = ev.get("incident") or {}
    assert inc.get("what") == "(redacted:containment)"
    assert inc.get("where") == "(redacted:containment)"


# ── #۱۲ HeartState adapter ────────────────────────────────────────────────────
def t_f_heartstate_build_failsoft_and_shadow_default():
    """build روی vaultِ خالی نمی‌شکند و ساختارِ کامل می‌دهد؛ بدونِ فلگ persist = no-op."""
    hs = heartstate.build()
    assert hs["schema"] == "heartstate.v1"
    for k in ("shadow", "stress", "innervation", "shadow_only"):
        assert k in hs, k
    assert hs["shadow_only"] is True                        # هیچ wire زنده‌ای نیست
    # بدونِ فلگ: enabled=False و persist چیزی نمی‌نویسد
    os.environ.pop("HEARTSTATE_SHADOW", None)
    assert heartstate.enabled() is False
    out = heartstate.persist()
    assert out["written"] is False
    assert not heartstate.LATEST.exists()                   # صفر side-effect


def t_g_heartstate_flag_gated_write():
    """با فلگِ HEARTSTATE_SHADOW=1: persist می‌نویسد و read_latest همان را برمی‌گرداند."""
    os.environ["HEARTSTATE_SHADOW"] = "1"
    try:
        assert heartstate.enabled() is True
        out = heartstate.persist()
        assert out["written"] is True and heartstate.LATEST.exists()
        rd = heartstate.read_latest()
        assert rd.get("schema") == "heartstate.v1" and "shadow" in rd
    finally:
        os.environ.pop("HEARTSTATE_SHADOW", None)


def t_h_heartstate_real_shadow_extraction():
    """با یک رکوردِ واقعیِ heart-shadow (ساختارِ تودرتو)، build فیلدها را درست استخراج کند —
    این تست دقیقاً باگِ inversion ِ wire_open را که ریویوی خصمانه یافت شکار می‌کند
    (t_f روی vaultِ خالی هرگز این شاخه را اجرا نمی‌کرد → سبزِ دروغین)."""
    pulse = STATE / "pulse"
    pulse.mkdir(parents=True, exist_ok=True)
    (pulse / "heart-shadow-latest.json").write_text(json.dumps({
        "ts": "2026-07-11T15:00:00", "beat": 7,
        "signal": {"schema": "HeartSignal.v1", "beat_seq": 7, "period_s": 300.0,
                   "sigma_now": 0.137, "baro_factor": 1.0},
        "period_s": 300.0,
        "telemetry": {"velocity_per_hr": 12.8},
        "setpoint": {"target_sigma": 1.0, "viable_band_lo": 6.4, "viable_band_hi": 19.2},
        "production_wire": {"open": False, "reasons": ["WIRE_HEART off", "date-gate"]},
        "mode": "shadow",
    }, ensure_ascii=False), "utf-8")
    sh = heartstate.build()["shadow"]
    assert sh["velocity"] == 12.8, sh                       # از telemetry.velocity_per_hr (نه top-level v)
    assert sh["sigma"] == 0.137                             # از signal.sigma_now
    assert sh["period_s"] == 300.0 and sh["mode"] == "shadow"
    assert sh["band"] == [6.4, 19.2]                        # از setpoint.viable_band_* (نه دیکشنریِ خام)
    # حیاتی‌ترین: wire بسته است → wire_open=False و shadow_only=True (نه truthiness ِ دیکشنری)
    assert sh["wire_open"] is False, f"open=False → wire_open باید False باشد: {sh}"
    assert heartstate.build()["shadow_only"] is True
    # برعکس: open=True → shadow_only=False
    (pulse / "heart-shadow-latest.json").write_text(json.dumps(
        {"production_wire": {"open": True, "reasons": []}, "mode": "live"}, ensure_ascii=False), "utf-8")
    hs2 = heartstate.build()
    assert hs2["shadow"]["wire_open"] is True and hs2["shadow_only"] is False


def t_i_heartstate_enabled_rejects_falsy_strings():
    """enabled() فقط truthy ِ صریح را می‌پذیرد — FALSE/off/no تصادفاً فعال نمی‌کنند."""
    for falsy in ("FALSE", "off", "no", "false", "0", ""):
        os.environ["HEARTSTATE_SHADOW"] = falsy
        assert heartstate.enabled() is False, f"{falsy!r} نباید فعال کند"
    for truthy in ("1", "true", "TRUE", "yes", "on"):
        os.environ["HEARTSTATE_SHADOW"] = truthy
        assert heartstate.enabled() is True, f"{truthy!r} باید فعال کند"
    os.environ.pop("HEARTSTATE_SHADOW", None)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_phase1_envelope: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
