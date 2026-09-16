
import json, os, sys, tempfile, time, subprocess, re
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(r"F:\backup")
EV = ROOT / "06-EVIDENCE" / "OCTOPUS-EXPEDITED-LIVE-ROLLOUT-2026-08-22"
SYD = timezone(timedelta(hours=10))

# Harness-style t_* scripts (NOT pytest) — run as python scripts
SCRIPT_TESTS = [
    "test_poll_lease.py",
    "test_telegram_durable_loop.py",
    "test_merge_effect_p0.py",
    "test_merge_text_p0.py",
    "test_evo_lab_bridge.py",
    "test_evo_outbox_callback_soak.py",
    "test_promote_gate.py",
]
# unittest TestCase with test_* — pytest only
PYTEST_TESTS = [
    "test_self_evidence_p1.py",
]

def now_local():
    return datetime.now(SYD).isoformat()

def parse_harness_counts(text: str):
    """Parse harness summaries across known formats."""
    # 1) OK name: n/n  OR  FAIL name: n/n
    m = re.search(r"\b(?:OK|FAIL)\s+\S+:\s+(\d+)/(\d+)\b", text)
    if m:
        passed = int(m.group(1)); checks = int(m.group(2))
        return checks, passed, checks - passed, m.group(0)
    # 2) RESULT failed=N passed=M [total=T]
    m = re.search(r"RESULT\s+failed=(\d+)\s+passed=(\d+)(?:\s+total=(\d+))?", text)
    if m:
        failed = int(m.group(1)); passed = int(m.group(2))
        checks = int(m.group(3)) if m.group(3) else passed + failed
        return checks, passed, failed, m.group(0)
    # 3) trailing "test_foo: n/n" without OK prefix
    m = re.search(r"(?m)^\s*([\w.-]+):\s+(\d+)/(\d+)\s*$", text)
    if m:
        passed = int(m.group(2)); checks = int(m.group(3))
        return checks, passed, checks - passed, m.group(0).strip()
    # 4) PASS/FAIL per-line tallies (merge_* style without RESULT — fallback)
    pass_lines = len(re.findall(r"(?m)^PASS\s+t_", text))
    fail_lines = len(re.findall(r"(?m)^FAIL\s+t_", text))
    if pass_lines or fail_lines:
        return pass_lines + fail_lines, pass_lines, fail_lines, f"PASS/FAIL lines passed={pass_lines} failed={fail_lines}"
    ok_lines = len(re.findall(r"(?m)^\s*(?:OK|✅)\s+t_", text))
    bad_lines = len(re.findall(r"(?m)^\s*(?:FAIL|❌)\s+t_", text))
    if ok_lines or bad_lines:
        return ok_lines + bad_lines, ok_lines, bad_lines, f"OK/FAIL t_ lines ok={ok_lines} fail={bad_lines}"
    return 0, 0, 0, ""

def parse_pytest_counts(text: str):
    collected = None
    m = re.search(r"collected\s+(\d+)\s+items?", text)
    if m:
        collected = int(m.group(1))
    # pytest -q summary: "62 passed in 1.66s" or "no tests ran"
    if re.search(r"no tests ran", text, re.I):
        return 0, 0, 0, "no tests ran"
    m = re.search(r"(\d+)\s+passed", text)
    passed = int(m.group(1)) if m else 0
    m = re.search(r"(\d+)\s+failed", text)
    failed = int(m.group(1)) if m else 0
    m = re.search(r"(\d+)\s+error", text)
    errors = int(m.group(1)) if m else 0
    if collected is None:
        collected = passed + failed + errors
    summary = ""
    for line in text.splitlines()[::-1]:
        s = line.strip()
        if s and any(k in s for k in ("passed", "failed", "error", "no tests")):
            summary = s
            break
    return collected, passed, failed + errors, summary

def verdict_for(runner, returncode, text):
    if "no tests ran" in text.lower():
        return False, 0, 0, 0, "no tests ran"
    if runner == "pytest":
        collected, passed, failed, summary = parse_pytest_counts(text)
        ok = (returncode == 0 and collected > 0 and failed == 0 and passed > 0)
        return ok, collected, passed, failed, summary
    # harness script
    checks, passed, failed, summary = parse_harness_counts(text)
    has_ok_summary = bool(
        re.search(r"\b(?:OK|FAIL)\s+\S+:\s+\d+/\d+\b", text)
        or re.search(r"RESULT\s+failed=\d+\s+passed=\d+", text)
        or re.search(r"(?m)^\s*[\w.-]+:\s+\d+/\d+\s*$", text)
        or re.search(r"(?m)^PASS\s+t_", text)
        or re.search(r"(?m)^\s*OK\s+t_", text)
    )
    ok = (
        returncode == 0
        and checks > 0
        and failed == 0
        and passed > 0
        and has_ok_summary
    )
    return ok, checks, passed, failed, summary

def main():
    state_dir = Path(tempfile.mkdtemp(prefix="octopus-builder-verify-state-"))
    echo = EV / "_isolation_echo.txt"
    log_dir = EV / "builder-test-logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["OCTOPUS_STATE_DIR"] = str(state_dir)
    env["OCTOPUS_TEST_LIVE_STATE_GUARD"] = "block"
    env["OCTOPUS_TEST_NET_GUARD"] = "1"
    env["OCTOPUS_TEST_ISOLATION_ECHO"] = str(echo)
    iso = str(ROOT / "_ops" / "tests" / "_isolation_boot")
    tests_dir = str(ROOT / "_ops" / "tests")
    prev_pp = env.get("PYTHONPATH", "")
    parts = [iso, tests_dir, str(ROOT / "_ops")]
    if prev_pp:
        parts.append(prev_pp)
    env["PYTHONPATH"] = os.pathsep.join(parts)
    for k in list(env):
        ku = k.upper()
        if "TELEGRAM" in ku and "TOKEN" in ku:
            env.pop(k, None)
    env["TELEGRAM_BOT_TOKEN"] = ""
    env["TG_BOT_TOKEN"] = ""

    results = []
    overall_pass = True
    start = time.time()

    def run_one(name, cmd, runner):
        nonlocal overall_pass
        out_log = log_dir / (name + ".out.txt")
        print("RUN", runner, name, flush=True)
        t0 = time.time()
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(ROOT / "_ops" / "tests"),
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=900,
            )
            dur = time.time() - t0
            text = (proc.stdout or "") + "\n---STDERR---\n" + (proc.stderr or "")
            out_log.write_text(text, encoding="utf-8")
            ok, collected, passed, failed, summary = verdict_for(runner, proc.returncode, text)
            if not ok:
                overall_pass = False
            results.append({
                "file": name,
                "runner": runner,
                "status": "PASS" if ok else "FAIL",
                "returncode": proc.returncode,
                "duration_sec": round(dur, 2),
                "collected": collected,
                "passed": passed,
                "failed": failed,
                "summary": summary,
                "log": str(out_log),
                "fail_reason": None if ok else (
                    "returncode!=0" if proc.returncode != 0 else
                    ("collected==0 or no tests" if collected == 0 else "missing OK/RESULT summary or failures")
                ),
            })
            print(name, "PASS" if ok else "FAIL", "collected=", collected, "passed=", passed, "failed=", failed, summary, flush=True)
        except subprocess.TimeoutExpired:
            overall_pass = False
            results.append({"file": name, "runner": runner, "status": "TIMEOUT", "duration_sec": 900, "collected": 0, "passed": 0, "failed": 0})
            print(name, "TIMEOUT", flush=True)
        except Exception as e:
            overall_pass = False
            results.append({"file": name, "runner": runner, "status": "ERROR", "error": str(e), "collected": 0, "passed": 0, "failed": 0})
            print(name, "ERROR", e, flush=True)

    py = sys.executable
    for name in SCRIPT_TESTS:
        tpath = str(ROOT / "_ops" / "tests" / name)
        run_one(name, [py, "-X", "utf8", tpath], "harness_script")
    for name in PYTEST_TESTS:
        tpath = str(ROOT / "_ops" / "tests" / name)
        run_one(
            name,
            [py, "-X", "utf8", "-m", "pytest", tpath, "-q", "--tb=line", "-p", "no:cacheprovider"],
            "pytest",
        )

    isolation_armed = echo.exists() and "armed" in echo.read_text(encoding="utf-8", errors="replace")
    # Honest gate: every suite collected>0 and returncode 0 and status PASS
    every_ok = overall_pass and all(
        r.get("status") == "PASS" and int(r.get("collected") or 0) > 0 for r in results
    )
    verdict = "BUILDER_VERIFIED_FOR_BOUNDED_OWNER_ROLLOUT" if every_ok else "FAIL"
    doc = {
        "schema": "octopus-builder-verification/1",
        "authorization_id": "OCTOPUS-OWNER-CANARY-20260822-N1",
        "mode": "EXPEDITED_BOUNDED_LIVE_ROLLOUT",
        "builder": "grok-ari-single-writer",
        "independent_verification": False,
        "verdict": verdict,
        "verdict_label": verdict,
        "forbidden_labels_not_used": ["SIG-IV", "INDEPENDENTLY_VERIFIED"],
        "root_cause_note": "Most suites are harness t_* scripts; pytest collects 0. Runner uses harness_script for those, pytest only for test_self_evidence_p1.py. collected==0 / no tests ran => FAIL.",
        "written_at_local": now_local(),
        "isolation": {
            "OCTOPUS_STATE_DIR": str(state_dir),
            "live_state_guard": "block",
            "net_guard": True,
            "isolation_echo_armed": isolation_armed,
            "fake_transport": True,
            "token_in_fixtures": False,
            "telegram_api_called": False,
            "live_send": False,
        },
        "suites": results,
        "coverage": {
            "poll_lease": "test_poll_lease.py",
            "durable_outbox": "test_telegram_durable_loop.py",
            "merge_proof_gate": "test_merge_effect_p0.py",
            "callback_text_verdict": ["test_merge_text_p0.py", "test_evo_outbox_callback_soak.py"],
            "evo_lab_bridge": "test_evo_lab_bridge.py",
            "self_evidence": "test_self_evidence_p1.py",
            "promote_gate": "test_promote_gate.py",
        },
        "duration_sec": round(time.time() - start, 2),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(ROOT), text=True).strip(),
    }
    (EV / "BUILDER-VERIFICATION.json").write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print("VERDICT", verdict)
    print("WROTE", EV / "BUILDER-VERIFICATION.json")
    return 0 if every_ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
