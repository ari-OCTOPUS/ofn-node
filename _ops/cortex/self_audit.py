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


def _item(item, status, evidence, priority, gap_type, section,
         evidence_bound: bool = False):
    out = {"item": item, "status": status, "evidence": evidence,
           "priority": priority, "gap_type": gap_type, "section": section}
    if evidence_bound:
        out["evidence_bound"] = True
    return out


def _grep(path: Path, needle: str) -> bool:
    try:
        return needle in path.read_text("utf-8")
    except OSError:
        return False


def _count_jsonl(path: Path):
    """Line count of a JSONL file; None if missing/unreadable."""
    try:
        if not path.exists():
            return None
        return sum(1 for line in path.read_text("utf-8").splitlines() if line.strip())
    except OSError:
        return None


def _calibration_latest_path() -> Path:
    return STATE / "cortex" / "calibration-latest.json"


def _self_claims_path() -> Path:
    return STATE / "cortex" / "self-claims.jsonl"


def _doctor_vitals_path() -> Path:
    return OPS.parent / "OCTOPUS-DOCTOR" / "90-_meta" / "state" / "doctor-vitals.json"


def _poll_health_path() -> Path:
    return STATE / "telegram" / "poll-health.json"


def _heartstate_path() -> Path:
    return STATE / "pulse" / "heartstate-latest.json"


def _work_health_path() -> Path:
    return STATE / "pulse" / "work-health.json"


def _calibration_py_path() -> Path:
    return OPS / "doctor" / "calibration.py"


def _run_all_py_path() -> Path:
    return OPS / "tests" / "run_all.py"


def _doctor_py_path() -> Path:
    return OPS / "doctor" / "doctor.py"


def _routing_e2e_path() -> Path:
    return OPS / "tests" / "test_telegram_poll_e2e.py"


def _sog_math_path() -> Path:
    return OPS / "heart" / "sog_math.py"


def _parse_run_all_tests(path: Path):
    """Parse TESTS = [...] filenames from run_all.py; None if missing/unreadable."""
    import ast
    try:
        src = path.read_text("utf-8")
    except OSError:
        return None
    import re as _re
    m = _re.search(r"^TESTS\s*=\s*\[", src, _re.M)
    if not m:
        return None
    start = m.end() - 1
    depth = 0
    end = None
    for i, ch in enumerate(src[start:], start):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end is None:
        return None
    try:
        names = ast.literal_eval(src[start:end])
    except (SyntaxError, ValueError):
        return None
    if not isinstance(names, list):
        return None
    return [n for n in names if isinstance(n, str)]


def _read_stop_constants(path: Path):
    """Parse REJECT_FORGET_N / PENDING_* caps from calibration.py source."""
    import re
    try:
        text = path.read_text("utf-8")
    except OSError:
        return None
    out = {}
    for name in ("REJECT_FORGET_N", "PENDING_SOFT_CAP", "PENDING_HARD_CAP"):
        m = re.search(rf"^{name}\s*=\s*(\d+)", text, re.M)
        if not m:
            return None
        out[name] = int(m.group(1))
    out["has_should_skip"] = "def should_skip_bottleneck" in text
    out["has_attention_gate"] = "def attention_gate" in text
    return out


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
    # ۲۰۲۶-۰۸-۰۸ (up-1f41a4499b): consolidate.py حالا poisoning_risk + sources_count
    # می‌سازد و هشدار می‌دهد. گیتِ فعال در کد، نه فقط در قانون.
    guard = _grep(OPS / "cortex" / "consolidate.py", "poisoning_risk")
    if guard:
        return _item("memory poisoning / false-canon guard", "Done",
                     "consolidate._make_note: sources_count + poisoning_risk + alert "
                     "on high-risk agent notes without independent sources (§7)",
                     "P1", "governance", "§6 memory")
    return _item("memory poisoning / false-canon guard", "Missing",
                 "constitution §7: created_by:agent + sources≥2؛ ولی مانیتورِ خودکار نیست",
                 "P1", "governance", "§6 memory")


def _probe_trace_independent():
    ok = (opslib.ALERTS_MD).exists()
    return _item("trace layer independent of self-report", "Done" if ok else "Partial",
                 "ledger events + governor-alerts + heartbeat (external to agents)",
                 "P1", "none" if ok else "observability", "§8 observability")


def _probe_cost_logging():
    # organ_gate log با هزینه
    ok = (OPS / "budget" / "organ-gate-log.jsonl").exists() or (OPS / "budget" / "organ_gate.py").exists()
    return _item("tool-call cost/latency logging", "Partial" if ok else "Missing",
                 "organ_gate.settle logs est/actual usd؛ latency در local_llm.ms",
                 "P2", "observability", "§8 observability")


def _probe_dashboard():
    """Was file-exists on live/server.py. Now requires live vitals JSON."""
    hs_p = _heartstate_path()
    wh_p = _work_health_path()
    server_ok = (OPS / "live" / "server.py").exists()
    hs = _read(hs_p)
    wh = _read(wh_p)
    if hs is None and wh is None:
        return _item("dashboard for system vitals", "Missing",
                     f"heartstate+work-health unreadable; server.py={server_ok}",
                     "P2", "observability", "§8 observability",
                     evidence_bound=True)
    hs_ok = isinstance(hs, dict) and hs.get("schema") == "heartstate.v1"
    wh_ok = isinstance(wh, dict) and isinstance(wh.get("month_aud"), (int, float))
    if not (hs_ok or wh_ok):
        sch = None if hs is None else (hs.get("schema") if isinstance(hs, dict) else type(hs).__name__)
        wh_keys = list(wh)[:4] if isinstance(wh, dict) else None
        return _item("dashboard for system vitals", "Partial",
                     f"vitals stubbed/wrong schema hs={sch!r} wh_keys={wh_keys}; server.py={server_ok}",
                     "P2", "observability", "§8 observability",
                     evidence_bound=True)
    bits = []
    if hs_ok:
        bits.append(f"heartstate.v1 ts={hs.get('ts')!r}")
    if wh_ok:
        bits.append(f"work-health month_aud={wh.get('month_aud')} gate0={wh.get('gate0')}")
    bits.append(f"server.py={server_ok}")
    st = "Done" if (hs_ok and server_ok) or (hs_ok and wh_ok) else "Partial"
    return _item("dashboard for system vitals", st,
                 "; ".join(bits),
                 "P2", "none" if st == "Done" else "observability", "§8 observability",
                 evidence_bound=True)


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
    """Was always-Done (static claim). Now requires doctor-vitals on disk + gather_trace."""
    vitals_p = _doctor_vitals_path()
    vitals = _read(vitals_p)
    has_gather = _grep(OPS / "doctor" / "doctor.py", "def _gather_trace")
    if not vitals_p.exists() or vitals is None:
        return _item("self-analysis is trace-based not self-talk", "Missing",
                     f"doctor-vitals unreadable: {vitals_p}",
                     "P1", "observability", "§9 self-analysis",
                     evidence_bound=True)
    schema = vitals.get("schema") if isinstance(vitals, dict) else None
    if schema != "doctor-vitals.v1":
        return _item("self-analysis is trace-based not self-talk", "Partial",
                     f"doctor-vitals stubbed/wrong schema={schema!r}",
                     "P1", "observability", "§9 self-analysis",
                     evidence_bound=True)
    exo = 0
    for val in vitals.values():
        if isinstance(val, dict):
            prov = str(val.get("provenance") or "")
            if prov in ("برون‌زاد", "exogenous", "external") or "برون" in prov:
                exo += 1
    if not has_gather:
        return _item("self-analysis is trace-based not self-talk", "Partial",
                     f"vitals ok (exo={exo}) but doctor._gather_trace missing",
                     "P1", "observability", "§9 self-analysis",
                     evidence_bound=True)
    st = "Done" if exo >= 1 else "Partial"
    return _item("self-analysis is trace-based not self-talk", st,
                 f"doctor-vitals.v1 exo_prov={exo} + _gather_trace present ({vitals_p.name})",
                 "P1", "none" if st == "Done" else "observability", "§9 self-analysis",
                 evidence_bound=True)


def _probe_stop_condition():
    """Was file-exists on calibration.py. Now reads live constants + defs."""
    cal_py = _calibration_py_path()
    consts = _read_stop_constants(cal_py)
    if consts is None:
        return _item("self-analysis loop has stop-condition", "Missing",
                     f"calibration.py missing/unparseable: {cal_py}",
                     "P1", "governance", "§9 self-analysis",
                     evidence_bound=True)
    expect = {"REJECT_FORGET_N": 3, "PENDING_SOFT_CAP": 3, "PENDING_HARD_CAP": 5}
    if not consts.get("has_should_skip") or not consts.get("has_attention_gate"):
        return _item("self-analysis loop has stop-condition", "Partial",
                     f"defs incomplete should_skip={consts.get('has_should_skip')} "
                     f"attention_gate={consts.get('has_attention_gate')} consts={consts}",
                     "P1", "governance", "§9 self-analysis",
                     evidence_bound=True)
    if any(consts.get(k) != v for k, v in expect.items()):
        return _item("self-analysis loop has stop-condition", "Partial",
                     f"stop caps drifted: " + str({k: consts.get(k) for k in expect}) + f" expected={expect}",
                     "P1", "governance", "§9 self-analysis",
                     evidence_bound=True)
    return _item("self-analysis loop has stop-condition", "Done",
                 f"calibration.py REJECT_FORGET_N={consts['REJECT_FORGET_N']} "
                 f"soft={consts['PENDING_SOFT_CAP']} hard={consts['PENDING_HARD_CAP']} "
                 f"+ should_skip_bottleneck + attention_gate",
                 "P1", "none", "§9 self-analysis",
                 evidence_bound=True)


def _probe_shadow_before_promote():
    """Was file-exists on doctor.py. Now requires run_sandbox + measured_lift + tempfile."""
    doc = _doctor_py_path()
    try:
        src = doc.read_text("utf-8")
    except OSError:
        return _item("improvement proposals shadow-eval before promote", "Missing",
                     f"doctor.py missing/unreadable: {doc}",
                     "P0", "implementation", "A9/A10 self-improve",
                     evidence_bound=True)
    has_sandbox = "def run_sandbox" in src
    has_lift = "measured_lift" in src
    has_tmp = ("tempfile.mkdtemp" in src) or ("tempfile.TemporaryDirectory" in src)
    bits = [f"run_sandbox={has_sandbox}", f"measured_lift={has_lift}", f"tempfile_iso={has_tmp}"]
    if not (has_sandbox or has_lift or has_tmp):
        return _item("improvement proposals shadow-eval before promote", "Partial",
                     "doctor.py present but no sandbox/lift/tempfile markers; " + ", ".join(bits),
                     "P0", "implementation", "A9/A10 self-improve",
                     evidence_bound=True)
    if has_sandbox and has_lift and has_tmp:
        return _item("improvement proposals shadow-eval before promote", "Done",
                     "doctor.run_sandbox + measured_lift + tempfile isolation; " + ", ".join(bits),
                     "P0", "none", "A9/A10 self-improve",
                     evidence_bound=True)
    return _item("improvement proposals shadow-eval before promote", "Partial",
                 "shadow-eval incomplete; " + ", ".join(bits),
                 "P0", "implementation", "A9/A10 self-improve",
                 evidence_bound=True)

def _probe_change_leveling():
    return _item("change leveled: tune/reconfig/rewrite + contract", "Missing",
                 "none — سطح‌بندیِ صریحِ تغییر و change-contract هنوز نیست (کارِ improve.py)",
                 "P1", "governance", "§10 self-modify")


def _probe_rollback():
    ok = _grep(OPS / "doctor" / "doctor.py", "rollback") or _grep(OPS / "doctor" / "evolution.py", "measured_lift")
    # ۲۰۲۶-۰۸-۰۸ (up-6013ab05d7): git checkpoint tag قبل از merge پیاده شد.
    checkpoint = _grep(OPS / "doctor" / "doctor.py", "OCTOPUS_WIRE_MERGE_CHECKPOINT")
    if ok and checkpoint:
        return _item("rollback path before apply", "Done",
                     "RFC.rollback field + measured_lift drop<0.05 + git tag "
                     "pre-merge (OCTOPUS_WIRE_MERGE_CHECKPOINT)",
                     "P1", "governance", "§10 self-modify")
    return _item("rollback path before apply", "Partial" if ok else "Missing",
                 "RFC.rollback field + measured_lift drop<0.05 + git tags (pre-merge)",
                 "P1", "governance", "§10 self-modify")


def _probe_regression_suite():
    """Was .exists() on marker/run_all. Now parses TESTS and verifies files on disk."""
    run_all = _run_all_py_path()
    names = _parse_run_all_tests(run_all)
    if names is None:
        return _item("regression suite / golden tasks", "Missing",
                     f"run_all.py missing/unparseable TESTS: {run_all}",
                     "P0", "implementation", "A11 validation",
                     evidence_bound=True)
    tests_dir = run_all.parent
    existing = []
    for n in names:
        p = tests_dir / n
        if p.exists():
            existing.append(n)
            continue
        stem = Path(n).stem
        if (tests_dir / stem).is_dir():
            existing.append(n)
    n_list = len(names)
    n_exist = len(existing)
    has_held = any("held_out" in n for n in names)
    has_cap = any("capability_gate" in n for n in names)
    bits = f"TESTS={n_list} exist={n_exist} held_out={has_held} capability_gate={has_cap}"
    if n_list < 20 or n_exist < 15:
        return _item("regression suite / golden tasks", "Partial",
                     f"suite thin/incomplete: {bits}",
                     "P0", "implementation", "A11 validation",
                     evidence_bound=True)
    if not (has_held and has_cap):
        return _item("regression suite / golden tasks", "Partial",
                     f"missing golden/canary markers in TESTS: {bits}",
                     "P0", "implementation", "A11 validation",
                     evidence_bound=True)
    need = max(20, int(0.7 * n_list))
    if n_exist < need:
        return _item("regression suite / golden tasks", "Partial",
                     f"listed tests missing on disk need>={need}: {bits}",
                     "P0", "implementation", "A11 validation",
                     evidence_bound=True)
    return _item("regression suite / golden tasks", "Done",
                 f"run_all TESTS verified on disk; {bits}",
                 "P0", "none", "A11 validation",
                 evidence_bound=True)

def _probe_deterministic_routing_tests():
    """Was file-exists on test_telegram_poll_e2e.py. Now reads dispatch matrix defs."""
    import re as _re
    p = _routing_e2e_path()
    try:
        src = p.read_text("utf-8")
    except OSError:
        return _item("deterministic tests for routing logic", "Missing",
                     f"routing e2e missing/unreadable: {p}",
                     "P1", "implementation", "A11 validation",
                     evidence_bound=True)
    t_defs = _re.findall(r"^def (t_\w+)\(", src, _re.M)
    has_poll = "poll_once" in src
    has_cb = "callback_query" in src or "dispatch" in src.lower()
    has_menu = "menu:" in src
    bits = f"t_defs={len(t_defs)} poll_once={has_poll} callback/dispatch={has_cb} menu={has_menu}"
    if not t_defs:
        return _item("deterministic tests for routing logic", "Partial",
                     f"e2e present but no t_* tests; {bits}",
                     "P1", "implementation", "A11 validation",
                     evidence_bound=True)
    if len(t_defs) >= 4 and has_poll and (has_cb or has_menu):
        return _item("deterministic tests for routing logic", "Done",
                     f"dispatch matrix in {p.name}: {bits}",
                     "P1", "none", "A11 validation",
                     evidence_bound=True)
    return _item("deterministic tests for routing logic", "Partial",
                 f"routing coverage thin; {bits}",
                 "P1", "implementation", "A11 validation",
                 evidence_bound=True)

def _probe_blind_informed():
    """Was file-exists on sog_math.py. Now requires blind/informed symbols."""
    p = _sog_math_path()
    try:
        src = p.read_text("utf-8")
    except OSError:
        return _item("blind-vs-informed evaluation harness", "Missing",
                     f"sog_math.py missing/unreadable: {p}",
                     "P1", "theory", "A11 validation",
                     evidence_bound=True)
    need = ("def delta_self", "def e_shadow", "def mc_witness_core")
    present = [n for n in need if n in src]
    has_blind = "blind" in src.lower()
    bits = f"syms={len(present)}/{len(need)} blind_token={has_blind}"
    if len(present) == 0 and not has_blind:
        return _item("blind-vs-informed evaluation harness", "Partial",
                     f"sog_math present but no harness markers; {bits}",
                     "P1", "theory", "A11 validation",
                     evidence_bound=True)
    if len(present) == len(need) and has_blind:
        return _item("blind-vs-informed evaluation harness", "Done",
                     f"sog_math blind/informed harness; {bits} ({', '.join(s.replace('def ','') for s in present)})",
                     "P1", "none", "A11 validation",
                     evidence_bound=True)
    return _item("blind-vs-informed evaluation harness", "Partial",
                 f"harness incomplete; {bits}",
                 "P1", "theory", "A11 validation",
                 evidence_bound=True)

def _probe_single_agent_baseline():
    ok = (OPS / "baseline.py").exists() or (OPS / "doctor" / "box" / "null_dreamer.py").exists()
    return _item("single-agent / null baseline", "Partial" if ok else "Missing",
                 "baseline.py + box/null_dreamer؛ ولی مقایسهٔ سیستمیِ multi-vs-single خودکار نیست",
                 "P2", "theory", "§11/§20 validation")


def _probe_named_owner():
    ok = _grep(OPS.parent / "_PROJECT_INSTRUCTIONS.md", "مالک")
    return _item("named human owner per subsystem", "Partial" if ok else "Missing",
                 "owner=ari (single operator)؛ ولی per-agent owner-mapping صریح نیست",
                 "P2", "governance", "§13 governance")


def _probe_human_append_enforced():
    """P0 رفع‌شده (جلسه ۴۶): configure در بوت + authorize در chrono (پشتِ flag)."""
    wired = _grep(OPS / "organism.py", "configure as _cfg_guard") and \
        _grep(OPS / "chrono.py", "from human_append_guard import default_guard")
    return _item("human-append anti-forgery ENFORCED (is_human unforgeable)",
                 "Done" if wired else "Missing",
                 "organism configure(per-boot secret) + chrono authorize→downgrade؛ "
                 "mint فقط تلگرام؛ جعلِ بی‌توکن→is_human=0 (test_p0_security_fixes)",
                 "P0", "none" if wired else "governance", "§15 human-in-loop")


def _probe_owner_verdict_effect():
    """P0 رفع‌شده (جلسه ۴۶): apply_merge در run_cycle بعد از verdictِ merged."""
    called = _grep(OPS / "doctor" / "doctor.py", "self.apply_merge(self._rfcs[rfc_id])")
    return _item("owner merge verdict has real effect (apply_merge wired)",
                 "Done" if called else "Missing",
                 "run_cycle: merged→apply_merge (lesson+NOTE، پشتِ OCTOPUS_WIRE_APPLY_MERGE) "
                 "+ رفعِ باگِ to_markdown float",
                 "P0", "none" if called else "implementation", "§15 human-in-loop")


def _probe_autonomy_consumed():
    """یافتهٔ workflow: سطحِ autonomy در OWNER-PROFILE ثبت ولی توسطِ هیچ کدِ runtime خوانده نمی‌شود.
    ۲۰۲۶-۰۸-۰۸ (up-863c603099): autonomy_matrix.owner_autonomy_level() حالا OWNER-PROFILE
    را می‌خواند و free_enabled آن را مصرف می‌کند."""
    consumed = _grep(OPS / "cortex" / "autonomy_matrix.py", "owner_autonomy_level")
    if consumed:
        return _item("owner autonomy preference modulates behavior", "Done",
                     "autonomy_matrix.owner_autonomy_level(): OWNER-PROFILE.answers.autonomy "
                     "→ free_enabled() → auto_approve مصرف می‌کند",
                     "P2", "governance", "§1 autonomy")
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
    # ۲۰۲۶-۰۸-۰۸ (up-ae4a7476a9): drift_metric.py ساخته شد — coherence/velocity
    # trend با windowed average و drift detection.
    mod = _grep(OPS / "cortex" / "drift_metric.py", "drifting")
    if mod:
        return _item("drift over time measured", "Done",
                     "drift_metric.compute(): windowed coherence trend + slope + "
                     "drifting flag + alert on persistent decline",
                     "P2", "observability", "§16 time-loops")
    return _item("drift over time measured", "Missing",
                 "none — drift-metric صریح (coherence/velocity trend) هنوز نیست (کاندید improve.py)",
                 "P2", "observability", "§16 time-loops")


def _probe_spec_2027():
    p = OPS.parent / "06 - Architecture Maps" / "SPEC-OCTOPUS-2027-v0.md"
    return _item("SPEC v0 (2027) + autonomy ladder L0-L5 formalized",
                 "Done" if p.exists() else "Missing",
                 "SPEC-OCTOPUS-2027-v0.md §۴ (نگاشتِ L0..L5 به گیت‌های واقعی)",
                 "P1", "none" if p.exists() else "governance", "2027§4 autonomy-ladder")


def _probe_observability_gate():
    ok = _grep(_HERE / "improve.py", "def observability_ok")
    return _item("self-improvement halts when observability dies (GAAT)",
                 "Done" if ok else "Missing",
                 "improve.observability_ok → auto سخت‌قفل + آیتمِ P0 در digest",
                 "P0", "none" if ok else "governance", "2027§21-1 hard-questions")


def _probe_refractory():
    ok = _grep(_HERE / "improve.py", "def refractory_open")
    return _item("refractory period between self-changes",
                 "Done" if ok else "Missing",
                 "improve.refractory_open (۲۴h بینِ دو auto) — pulse→gate→refractory",
                 "P1", "none" if ok else "governance", "2027§14 rhythm-governance")


def _probe_handoff_contract():
    # قراردادِ state-file: هر فایلِ نو schema نسخه‌دار دارد؟ (نمونه‌گیری)
    samples = [STATE / "cortex" / "cortex-state.json",
               STATE / "pulse" / "heart-signals-latest.json",
               STATE / "cortex" / "audit-matrix.json"]
    with_schema = sum(1 for p in samples
                      if (_read(p) or {}).get("schema"))
    st = "Done" if with_schema >= 2 else ("Partial" if with_schema else "Missing")
    return _item("handoff = versioned state-file contract (schema field)", st,
                 f"{with_schema}/{len(samples)} فایلِ نمونه schema-دار (SPEC §۷)",
                 "P2", "none" if st == "Done" else "architecture", "2027§7 handoff")


def _probe_decision_ledger():
    aq = opslib.AGENT_QUESTIONS.exists()
    return _item("decision ledger (verdicts aggregated)", "Partial" if aq else "Missing",
                 "AGENT_QUESTIONS verdicts + ledger NOTEها + improve-verdicts.jsonl؛ "
                 "تجمیعِ واحدِ query-پذیر نیست",
                 "P2", "governance", "2027§22 artifacts")


def _probe_cost_governance():
    ok = _grep(OPS / "budget" / "budgets.yaml", "cap_monthly")
    return _item("cost governance (multi-model/internet loops)", "Done" if ok else "Partial",
                 "budgets.yaml cap_monthly + organ_gate metering + system_share سهمیهٔ اشتراک",
                 "P1", "none" if ok else "governance", "2027§19 cost")


def _probe_identity_drift():
    # ۲۰۲۶-۰۸-۰۸ (up-ef5929f21b): identity.check_drift() ساخته شد.
    drift_fn = _grep(OPS / "identity.py", "def check_drift")
    if drift_fn:
        return _item("identity drift monitoring in self-modifying agents", "Done",
                     "identity.check_drift(): baseline (name/given_by/given_at) "
                     "مقایسه + alert روی تغییرِ خارجی",
                     "P2", "theory", "2027§11 self-modify")
    return _item("identity drift monitoring in self-modifying agents", "Missing",
                 "none — سنجهٔ driftِ هویتی (پایداریِ رفتار/ارزش بعد از تغییر) هنوز نیست",
                 "P2", "theory", "2027§11 self-modify")


def _probe_change_backlog():
    ok = MATRIX_PATH.exists()
    return _item("prioritized implementation backlog", "Partial" if ok else "Missing",
                 "این audit-matrix + AGENT_QUESTIONS + HANDOFF؛ ولی backlogِ زندهٔ owner-facing = کارِ improve.py",
                 "P1", "implementation", "§19 coding-ready")


def _probe_poll_health():
    """Bind telegram poll-health.json fails/progress counters into audit."""
    ph_p = _poll_health_path()
    ph = _read(ph_p)
    if ph is None:
        return _item("telegram poll-health counters", "Missing",
                     f"poll-health missing/unreadable: {ph_p}",
                     "P1", "observability", "§8 observability",
                     evidence_bound=True)
    if not isinstance(ph, dict):
        return _item("telegram poll-health counters", "Partial",
                     "poll-health not an object",
                     "P1", "observability", "§8 observability",
                     evidence_bound=True)
    fails = ph.get("consecutive_failures")
    counters = ph.get("counters") if isinstance(ph.get("counters"), dict) else {}
    started = counters.get("poll_started_total")
    completed = counters.get("poll_completed_total")
    progress = ph.get("last_progress_at")
    if not isinstance(fails, (int, float)):
        return _item("telegram poll-health counters", "Partial",
                     f"consecutive_failures stubbed/invalid: {fails!r}",
                     "P1", "observability", "§8 observability",
                     evidence_bound=True)
    if not isinstance(started, (int, float)) or not isinstance(completed, (int, float)):
        return _item("telegram poll-health counters", "Partial",
                     f"counters incomplete started={started!r} completed={completed!r}",
                     "P1", "observability", "§8 observability",
                     evidence_bound=True)
    if not isinstance(progress, (int, float)) or float(progress) <= 0:
        return _item("telegram poll-health counters", "Partial",
                     f"last_progress_at stubbed/invalid: {progress!r}",
                     "P1", "observability", "§8 observability",
                     evidence_bound=True)
    return _item("telegram poll-health counters", "Done",
                 f"fails={int(fails)} started={int(started)} completed={int(completed)} "
                 f"progress_at={float(progress):.3f}",
                 "P1", "none", "§8 observability",
                 evidence_bound=True)


def _probe_calibration_evidence():
    """Live Brier/n from calibration-latest.json + self-claims.jsonl counts.

    Cannot be Done without reading those on-disk files. Stubbed/missing → not Done.
    """
    cal_p = _calibration_latest_path()
    claims_p = _self_claims_path()
    cal = _read(cal_p)
    n_claims = _count_jsonl(claims_p)
    if cal is None:
        return _item("live calibration evidence (Brier/n + self-claims)", "Missing",
                     f"calibration-latest missing/unreadable: {cal_p}",
                     "P1", "observability", "§9 self-analysis",
                     evidence_bound=True)
    n = cal.get("n")
    brier = cal.get("brier")
    schema = cal.get("schema")
    if schema != "calibration.v1":
        return _item("live calibration evidence (Brier/n + self-claims)", "Partial",
                     f"calibration stubbed/wrong schema={schema!r}",
                     "P1", "observability", "§9 self-analysis",
                     evidence_bound=True)
    if not isinstance(n, (int, float)) or int(n) <= 0:
        return _item("live calibration evidence (Brier/n + self-claims)", "Partial",
                     f"calibration n stubbed/invalid: {n!r}",
                     "P1", "observability", "§9 self-analysis",
                     evidence_bound=True)
    if not isinstance(brier, (int, float)):
        return _item("live calibration evidence (Brier/n + self-claims)", "Partial",
                     f"calibration brier stubbed/invalid: {brier!r}",
                     "P1", "observability", "§9 self-analysis",
                     evidence_bound=True)
    if n_claims is None or n_claims <= 0:
        return _item("live calibration evidence (Brier/n + self-claims)", "Partial",
                     f"brier={brier} n={int(n)} but self-claims.jsonl empty/missing",
                     "P1", "observability", "§9 self-analysis",
                     evidence_bound=True)
    return _item("live calibration evidence (Brier/n + self-claims)", "Done",
                 f"calibration-latest n={int(n)} brier={float(brier):.6f}; "
                 f"self-claims.jsonl lines={n_claims}",
                 "P1", "none", "§9 self-analysis",
                 evidence_bound=True)



PROBES = [
    _probe_kill_switch, _probe_watchdog, _probe_heartbeat_pulse, _probe_multiscale_loops,
    _probe_truth_source, _probe_replay, _probe_stale_detection, _probe_memory_librarian,
    _probe_memory_poisoning, _probe_trace_independent, _probe_cost_logging, _probe_dashboard,
    _probe_epistemic_signals, _probe_self_analysis_loop, _probe_trace_based_analysis,
    _probe_calibration_evidence,
    _probe_poll_health,
    _probe_stop_condition, _probe_shadow_before_promote, _probe_change_leveling, _probe_rollback,
    _probe_regression_suite, _probe_deterministic_routing_tests, _probe_blind_informed,
    _probe_single_agent_baseline, _probe_named_owner,
    _probe_human_append_enforced, _probe_owner_verdict_effect, _probe_autonomy_consumed,
    _probe_approval_gates,
    _probe_secrets_isolation, _probe_output_sanitization, _probe_tool_registry, _probe_dry_run,
    _probe_math_versioned, _probe_agent_graph, _probe_drift,
    _probe_spec_2027, _probe_observability_gate, _probe_refractory,
    _probe_handoff_contract, _probe_decision_ledger, _probe_cost_governance,
    _probe_identity_drift, _probe_change_backlog,
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
    eb_n = sum(1 for it in items if it.get("evidence_bound"))
    eb_done = sum(1 for it in items if it.get("evidence_bound") and it["status"] == "Done")
    out = {"ts": opslib.now_iso(), "schema": "audit-matrix.v1",
           "n": len(items), "tally": tally,
           # W2: maturity_pct still mostly static checklist coverage.
           # evidence_bound_* count probes that read live on-disk files.
           "maturity_pct": round(100 * (tally["Done"] + 0.5 * tally["Partial"]) / max(1, len(items)), 1),
           "static_by_construction": eb_n == 0,
           "evidence_bound_n": eb_n,
           "evidence_bound_done": eb_done,
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
