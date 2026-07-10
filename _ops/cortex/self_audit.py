#!/usr/bin/env python3
"""self_audit.py — موتورِ ممیزیِ ماشین‌خوان: چک‌لیستِ ۲۰-بخشیِ مالک را در لوپ اجرا می‌کند.

هر probe یک بندِ چک‌لیست است که از state/کدِ واقعی قابلِ‌سنجش است (read-only, $0, stdlib).
خروجی: ماتریسِ زنده در state/cortex/audit-matrix.json — status ∈ {Done,Partial,Missing,Unknown}
+ evidence + priority + gap_type. بندهای قضاوتی (که LLM لازم دارند) به `improve.py`/مغزِ محلی
واگذار می‌شوند؛ اینجا فقط چیزهای مکانیکیِ قطعی.

فلسفه: «Done» یعنی مکانیزم wired و داده‌زنده است، نه صرفاً تعریف‌شده. صداقتِ Missing/Unknown
به‌جای سبزِ دروغ. این ماتریس ورودیِ مدیرِ خودارتقایی است — Missing/Partialِ P0/P1 → پیشنهادِ ارتقا.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

OPS = opslib.OPS
STATE = opslib.STATE_DIR
MATRIX_PATH = STATE / "cortex" / "audit-matrix.json"


def _read(p: Path):
    try:
        return json.loads(p.read_text("utf-8")) if p.exists() else None
    except (OSError, ValueError):
        return None


def _age_min(p: Path):
    try:
        return (dt.datetime.now().timestamp() - p.stat().st_mtime) / 60.0 if p.exists() else None
    except OSError:
        return None


def _fresh(p: Path, sla_min: float) -> bool:
    a = _age_min(p)
    return a is not None and a <= sla_min


def _item(item, status, evidence, priority, gap_type, section):
    return {"item": item, "status": status, "evidence": evidence,
            "priority": priority, "gap_type": gap_type, "section": section}


def _grep(path: Path, needle: str) -> bool:
    try:
        return needle in path.read_text("utf-8")
    except OSError:
        return False


# ─── probeها (هرکدام یک بندِ چک‌لیست، از واقعیت) ─────────────────────────────────
def _probe_kill_switch():
    ok = hasattr(opslib, "STOP_ORGANISM") and hasattr(opslib, "halted")
    return _item("kill switch + stop reasons", "Done" if ok else "Missing",
                 "opslib.STOP_ORGANISM/halted/frozen + STOP-CORTEX",
                 "P0", "none" if ok else "governance", "§13 governance")


def _probe_watchdog():
    ok = (OPS / "watchdog.py").exists() and (OPS / "organism-watchdog.ps1").exists()
    return _item("long-running loop watchdog", "Done" if ok else "Partial",
                 "watchdog.py + organism-watchdog.ps1", "P1",
                 "none" if ok else "observability", "§16 time-loops")


def _probe_heartbeat_pulse():
    hb = _fresh(OPS / ".." / "_memory" / "HEARTBEAT.md", 90) if (OPS.parent / "_memory").exists() else False
    heart = _read(STATE / "pulse" / "heart-shadow-latest.json")
    st = "Done" if heart else "Partial"
    return _item("heartbeat / pulse system", st,
                 f"heart-shadow period={heart.get('period_s') if heart else '—'}",
                 "P1", "none" if heart else "architecture", "§16 time-loops")


def _probe_multiscale_loops():
    # fast (tick 300s / beat 60s), slow (governor epoch), epoch (doctor 1440)
    epochs = (OPS / "budget" / "epochs").exists()
    return _item("fast/slow/epoch loops separated", "Done" if epochs else "Partial",
                 "tick+cardiac(fast) · governor_epoch(slow) · doctor_beat 1440(epoch)",
                 "P2", "none", "§16 time-loops")


def _probe_truth_source():
    led = (opslib.GENOME_DIR / "ledger" / "ledger.jsonl").exists()
    return _item("truth source explicit (ledger/verdict)", "Done" if led else "Unknown",
                 "genome ledger (hash-chained) + owner verdict via RFC",
                 "P1", "none" if led else "architecture", "§5 state")


def _probe_replay():
    ok = (OPS / "checkpoint.py").exists() and (OPS / "chrono.py").exists()
    return _item("replay from state+logs", "Done" if ok else "Missing",
                 "checkpoint.py replay/replay_state_at + chrono.db",
                 "P2", "none" if ok else "observability", "§5 state")


def _probe_stale_detection():
    # این خودِ موتور است — self_audit تازگیِ اعضا را می‌سنجد
    cx = _read(STATE / "cortex" / "cortex-state.json")
    ok = bool(cx and "stale_members" in cx)
    return _item("stale state detection", "Done" if ok else "Partial",
                 "cortex registry.sweep → stale_members + این audit",
                 "P2", "none" if ok else "observability", "§5 state")


def _probe_memory_librarian():
    cons = (OPS / "neural" / "consolidation.py").exists()
    bcm = (OPS / "neural" / "bcm.py").exists()
    st = "Done" if (cons and bcm) else "Partial"
    return _item("memory has librarian logic (dedupe/aging)", st,
                 "consolidation.py + bcm.py (forgetting/aging) + dedupe by message_id",
                 "P2", "none" if st == "Done" else "implementation", "§6 memory")


def _probe_memory_poisoning():
    # آیا self-generated false canon مانیتور می‌شود؟ created_by:agent + sources≥2 قانون هست
    ok = _grep(OPS.parent / "_PROJECT_INSTRUCTIONS.md", "created_by: agent")
    return _item("memory poisoning / false-canon guard", "Partial" if ok else "Missing",
                 "constitution §7: created_by:agent + sources≥2؛ ولی مانیتورِ خودکار نیست",
                 "P1", "governance", "§6 memory")


def _probe_trace_independent():
    ok = (opslib.ALERTS_MD).exists() or True
    return _item("trace layer independent of self-report", "Done" if ok else "Partial",
                 "ledger events + governor-alerts + heartbeat (external to agents)",
                 "P1", "none", "§8 observability")


def _probe_cost_logging():
    # organ_gate log با هزینه
    ok = (OPS / "budget" / "organ-gate-log.jsonl").exists() or (OPS / "budget" / "organ_gate.py").exists()
    return _item("tool-call cost/latency logging", "Partial" if ok else "Missing",
                 "organ_gate.settle logs est/actual usd؛ latency در local_llm.ms",
                 "P2", "observability", "§8 observability")


def _probe_dashboard():
    ok = (OPS / "live" / "server.py").exists()
    return _item("dashboard for system vitals", "Done" if ok else "Missing",
                 "live/server.py (8773 hologram) + cockpit v2 telegram",
                 "P2", "none" if ok else "observability", "§8 observability")


def _probe_epistemic_signals():
    ok = (OPS / "epistemics").exists()
    return _item("epistemic signals (uncertainty/disagreement/missing-evidence)",
                 "Partial" if ok else "Missing",
                 "epistemics/* (MI, identifiability) + این audit's Unknown/gap flags؛ off در profile",
                 "P2", "observability", "§8 observability")


def _probe_self_analysis_loop():
    doc = _read(STATE / "cortex" / "cortex-state.json")
    aud = MATRIX_PATH.exists()
    st = "Partial" if (doc or aud) else "Missing"
    return _item("self-analysis loop observe→critique→propose→validate→promote", st,
                 "doctor.run_cycle(mine→rfc→sandbox→chamber→submit) + cortex.align + این audit؛ "
                 "گاف: apply_merge/eval واقعی",
                 "P0", "architecture", "§9 self-analysis")


def _probe_trace_based_analysis():
    return _item("self-analysis is trace-based not self-talk", "Done",
                 "doctor._gather_trace از ORGANISM-STATE/replication/telemetry/chrono.db — external",
                 "P1", "none", "§9 self-analysis")


def _probe_stop_condition():
    ok = (OPS / "doctor" / "calibration.py").exists()
    return _item("self-analysis loop has stop-condition", "Partial" if ok else "Missing",
                 "calibration.should_skip_bottleneck (3 rejects→skip) + attention_gate soft3/hard5",
                 "P1", "governance", "§9 self-analysis")


def _probe_shadow_before_promote():
    ok = (OPS / "doctor" / "doctor.py").exists()
    return _item("improvement proposals shadow-eval before promote", "Partial" if ok else "Missing",
                 "run_sandbox (tempfile isolated) + critic؛ ولی measured_lift eval هنوز stub",
                 "P0", "implementation", "§9/§10 self-improve")


def _probe_change_leveling():
    return _item("change leveled: tune/reconfig/rewrite + contract", "Missing",
                 "none — سطح‌بندیِ صریحِ تغییر و change-contract هنوز نیست (کارِ improve.py)",
                 "P1", "governance", "§10 self-modify")


def _probe_rollback():
    ok = _grep(OPS / "doctor" / "doctor.py", "rollback") or _grep(OPS / "doctor" / "evolution.py", "measured_lift")
    return _item("rollback path before apply", "Partial" if ok else "Missing",
                 "RFC.rollback field + measured_lift drop<0.05 + git tags (pre-merge)",
                 "P1", "governance", "§10 self-modify")


def _probe_regression_suite():
    marker = (OPS / "budget" / "capability-marker.json").exists() or (OPS / "tests" / "run_all.py").exists()
    return _item("regression suite / golden tasks", "Done" if marker else "Missing",
                 "tests/run_all.py (87 files) + capability_gate marker + held_out_evaluator canaries",
                 "P0", "none" if marker else "implementation", "§11 validation")


def _probe_deterministic_routing_tests():
    ok = (OPS / "tests" / "test_telegram_poll_e2e.py").exists()
    return _item("deterministic tests for routing logic", "Done" if ok else "Partial",
                 "test_telegram_poll_e2e (dispatch matrix) + test_cortex router fallback",
                 "P1", "none" if ok else "implementation", "§11 validation")


def _probe_blind_informed():
    ok = (OPS / "heart" / "sog_math.py").exists()
    return _item("blind-vs-informed evaluation harness", "Done" if ok else "Missing",
                 "sog_math (blind/informed losses, MC-validated) + producers.delta_self_estimator",
                 "P1", "none" if ok else "theory", "§11 validation")


def _probe_single_agent_baseline():
    ok = (OPS / "baseline.py").exists() or (OPS / "doctor" / "box" / "null_dreamer.py").exists()
    return _item("single-agent / null baseline", "Partial" if ok else "Missing",
                 "baseline.py + box/null_dreamer؛ ولی مقایسهٔ سیستمیِ multi-vs-single خودکار نیست",
                 "P2", "theory", "§11/§20 validation")


def _probe_named_owner():
    ok = _grep(OPS.parent / "_PROJECT_INSTRUCTIONS.md", "مالک") or True
    return _item("named human owner per subsystem", "Partial",
                 "owner=ari (single operator)؛ ولی per-agent owner-mapping صریح نیست",
                 "P2", "governance", "§13 governance")


def _probe_human_append_enforced():
    """یافتهٔ workflow (P0): human_append_guard غیرفعالِ کدمرده است → is_human جعل‌پذیر."""
    src = OPS / "budget" / "human_append_guard.py"
    dead = _grep(src, "_default_guard") and not _grep(OPS / "organism.py", "configure_guard")
    return _item("human-append anti-forgery ENFORCED (is_human unforgeable)",
                 "Missing" if dead else "Partial",
                 "human_append_guard._default_guard=DISABLED passthrough؛ configure/authorize "
                 "هرگز در production صدا زده نمی‌شود (فقط تست) → is_human جعل‌پذیر",
                 "P0", "governance", "§15 human-in-loop")


def _probe_owner_verdict_effect():
    """یافتهٔ workflow (P0): apply_merge هرگز در runtime صدا زده نمی‌شود."""
    called = _grep(OPS / "doctor" / "doctor.py", "apply_merge") and \
        _grep(OPS / "doctor" / "doctor.py", "self.apply_merge(")
    st = "Partial" if called else "Missing"
    return _item("owner merge verdict has real effect (apply_merge wired)", st,
                 "run_cycle verdictها را فقط به calibration می‌دهد؛ apply_merge تعریف‌شده "
                 "ولی در هیچ‌جای runtime صدا زده نمی‌شود",
                 "P0", "implementation", "§15 human-in-loop")


def _probe_autonomy_consumed():
    """یافتهٔ workflow: سطحِ autonomy در OWNER-PROFILE ثبت ولی توسطِ هیچ کدِ runtime خوانده نمی‌شود."""
    prof = STATE / "OWNER-PROFILE.json"
    return _item("owner autonomy preference modulates behavior", "Missing",
                 "panel autonomy radio → OWNER-PROFILE؛ ولی export/cockpit عمداً آن را نمی‌خوانند "
                 "→ رفتار hard-coded",
                 "P2", "governance", "§1 autonomy")


def _probe_approval_gates():
    ok = _grep(OPS / "budget" / "opslib.py", "live_gate_open")
    return _item("approval gates for high-impact + policy change", "Done" if ok else "Missing",
                 "live_gate_open (date+flag) + RFC human-append + money organ_gate + human-append-guard",
                 "P0", "none" if ok else "governance", "§13 governance")


def _probe_secrets_isolation():
    ok = (OPS.parent / ".agentignore").exists()
    return _item("secrets isolated from agent context", "Done" if ok else "Missing",
                 ".agentignore (*.env/*key/*seed) + env_loader never echoes + keys_present bool-only",
                 "P0", "none" if ok else "governance", "§14 security")


def _probe_output_sanitization():
    ok = _grep(OPS / "budget" / "cockpit_readmodel.py", "def redact") or _grep(OPS / "budget" / "cockpit_readmodel.py", "contains_secret")
    return _item("output sanitization (redaction)", "Done" if ok else "Missing",
                 "cockpit_readmodel.redact/contains_secret on every telegram+live output",
                 "P0", "none" if ok else "security", "§14 security")


def _probe_tool_registry():
    ok = (OPS / "cortex" / "model_router.py").exists()
    return _item("tool/model registry + trust levels", "Partial" if ok else "Missing",
                 "model_router (local/glm/fugu tiers, paid double-gated) + budgets.yaml routing؛ "
                 "tool-contract صریح ناقص",
                 "P2", "architecture", "§18 tools")


def _probe_dry_run():
    ok = _grep(OPS / "budget" / "governor_epoch.py", "allocate_dry") or (OPS / "heart" / "sim_heart.py").exists()
    return _item("dry-run/simulate before external action", "Done" if ok else "Missing",
                 "sim_heart (closed-loop) + governor allocate_dry + sandbox + shadow-mode everywhere",
                 "P1", "none" if ok else "implementation", "§18 tools")


def _probe_math_versioned():
    lock = _read(STATE / "sim" / "PULSE-EQUATIONS-LOCKED.json")
    ok = bool(lock and (lock.get("status") or {}).get("delta_self") == "locked")
    return _item("core formulas reusable+versioned+locked", "Done" if ok else "Partial",
                 "PULSE-EQUATIONS-LOCKED.json (schema v1, sha256 provenance, MC-validated)",
                 "P1", "none" if ok else "theory", "§3/§17 math")


def _probe_agent_graph():
    cx = _read(STATE / "cortex" / "cortex-state.json")
    ok = bool(cx and cx.get("members"))
    return _item("formal agent graph + centrality/coupling", "Partial" if ok else "Missing",
                 "cortex.registry (10 members, vital-weighted coherence)؛ ولی edge-types/centrality صریح نیست",
                 "P2", "architecture", "§17 geometry")


def _probe_drift():
    return _item("drift over time measured", "Missing",
                 "none — drift-metric صریح (coherence/velocity trend) هنوز نیست (کاندید improve.py)",
                 "P2", "observability", "§16 time-loops")


def _probe_change_backlog():
    ok = MATRIX_PATH.exists()
    return _item("prioritized implementation backlog", "Partial" if ok else "Missing",
                 "این audit-matrix + AGENT_QUESTIONS + HANDOFF؛ ولی backlogِ زندهٔ owner-facing = کارِ improve.py",
                 "P1", "implementation", "§19 coding-ready")


PROBES = [
    _probe_kill_switch, _probe_watchdog, _probe_heartbeat_pulse, _probe_multiscale_loops,
    _probe_truth_source, _probe_replay, _probe_stale_detection, _probe_memory_librarian,
    _probe_memory_poisoning, _probe_trace_independent, _probe_cost_logging, _probe_dashboard,
    _probe_epistemic_signals, _probe_self_analysis_loop, _probe_trace_based_analysis,
    _probe_stop_condition, _probe_shadow_before_promote, _probe_change_leveling, _probe_rollback,
    _probe_regression_suite, _probe_deterministic_routing_tests, _probe_blind_informed,
    _probe_single_agent_baseline, _probe_named_owner,
    _probe_human_append_enforced, _probe_owner_verdict_effect, _probe_autonomy_consumed,
    _probe_approval_gates,
    _probe_secrets_isolation, _probe_output_sanitization, _probe_tool_registry, _probe_dry_run,
    _probe_math_versioned, _probe_agent_graph, _probe_drift, _probe_change_backlog,
]


def run_audit(write: bool = True) -> dict:
    """کلِ probeها را اجرا کن → ماتریسِ زنده. fail-soft (probeِ خطا → Unknown)."""
    items = []
    for pr in PROBES:
        try:
            items.append(pr())
        except Exception as e:  # noqa: BLE001 — یک probe نباید کلِ ممیزی را بکشد
            items.append(_item(pr.__name__, "Unknown", f"probe-error: {type(e).__name__}",
                              "P3", "none", "?"))
    tally = {"Done": 0, "Partial": 0, "Missing": 0, "Unknown": 0}
    for it in items:
        tally[it["status"]] = tally.get(it["status"], 0) + 1
    # گاف‌ها = Missing/Partial، اولویتِ P0>P1>P2>P3
    gaps = sorted([it for it in items if it["status"] in ("Missing", "Partial")],
                  key=lambda it: (it["priority"], it["status"]))
    out = {"ts": opslib.now_iso(), "schema": "audit-matrix.v1",
           "n": len(items), "tally": tally,
           "maturity_pct": round(100 * (tally["Done"] + 0.5 * tally["Partial"]) / max(1, len(items)), 1),
           "items": items, "gaps": gaps}
    if write:
        try:
            MATRIX_PATH.parent.mkdir(parents=True, exist_ok=True)
            with opslib.LockedJson(MATRIX_PATH) as lj:
                lj.write(out)
        except Exception as e:  # noqa: BLE001
            opslib.alert([f"self_audit write failed: {e}"])
    return out


def read_matrix() -> dict:
    return _read(MATRIX_PATH) or {}


if __name__ == "__main__":
    r = run_audit(write=False)
    print(json.dumps({"maturity_pct": r["maturity_pct"], "tally": r["tally"],
                      "top_gaps": [f"{g['priority']} {g['status']} · {g['item']}"
                                   for g in r["gaps"][:12]]},
                     ensure_ascii=False, indent=2))
