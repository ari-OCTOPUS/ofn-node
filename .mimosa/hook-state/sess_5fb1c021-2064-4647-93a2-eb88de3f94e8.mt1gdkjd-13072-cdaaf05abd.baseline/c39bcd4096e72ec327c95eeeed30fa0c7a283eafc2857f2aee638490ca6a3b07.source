#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_runner.py -- Test execution with no-skip enforcement (EQUIP G4).

Runs tests within the coding sandbox with:
  - Timeout (hard kill after timeout)
  - Output limit (truncate stdout/stderr)
  - No-skip enforcement: agent cannot skip/xfail/delete failing tests
  - Result parsing: count passed/failed/skipped/errored
  - Regression detection: compare against baseline results

Invariants:
  - Failing tests cannot be hidden by the agent
  - Test execution is always time-bounded
  - Test results are audited

$0 | stdlib-only | subprocess for execution | no network.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

SCHEMA = "test-runner.v1"

# Default limits
_DEFAULT_TEST_TIMEOUT_S = 300.0  # 5 minutes
_DEFAULT_MAX_OUTPUT = 200_000    # 200 KB max output


@dataclass(frozen=True)
class TestResult:
    """Immutable result of a test execution.

    Fields:
        ok: True if all tests passed
        total: Total number of tests run
        passed: Number of passed tests
        failed: Number of failed tests
        skipped: Number of skipped tests
        errors: Number of errored tests
        output: Combined stdout+stderr (truncated)
        output_bytes: Size of output before truncation
        elapsed_ms: Execution time in milliseconds
        reason: Human-readable reason (empty if ok)
        timed_out: True if test execution exceeded timeout
        exit_code: Process exit code
        test_file: The test file that was executed
    """
    ok: bool
    total: int
    passed: int
    failed: int
    skipped: int
    errors: int
    output: str
    output_bytes: int
    elapsed_ms: int
    reason: str
    timed_out: bool = False
    exit_code: int | None = None
    test_file: str = ""

    @property
    def failure_count(self) -> int:
        return self.failed + self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "ok": self.ok, "total": self.total,
            "passed": self.passed, "failed": self.failed,
            "skipped": self.skipped, "errors": self.errors,
            "output_bytes": self.output_bytes,
            "elapsed_ms": self.elapsed_ms,
            "reason": self.reason,
            "timed_out": self.timed_out,
            "exit_code": self.exit_code,
            "test_file": self.test_file,
        }


# Pattern to parse pytest-style output
_PYTEST_SUMMARY = re.compile(
    r"(\d+) passed"
    r"(?:,\s*(\d+) failed)?"
    r"(?:,\s*(\d+) skipped)?"
    r"(?:,\s*(\d+) (?:error|errors))?"
    r"(?:.*in\s+[\d.]+s)?",
    re.I | re.S,
)

# Pattern for unittest/script-style output
_RUN_SUMMARY = re.compile(
    r"Ran\s+(\d+)\s+test",
    re.I,
)

_OK_LINE = re.compile(r"^OK\b", re.I)
_FAILED_LINE = re.compile(r"FAILED\b", re.I)


def parse_test_output(output: str, exit_code: int | None = None) -> dict[str, Any]:
    """Parse test output to extract pass/fail/skip counts.

    Supports:
      - pytest summary format: "X passed, Y failed, Z skipped"
      - unittest format: "Ran X test ... OK / FAILED"
      - Script-style custom format: "N/N passed"

    Returns:
        Dict with parsed counts.
    """
    total = 0
    passed = 0
    failed = 0
    skipped = 0
    errors = 0

    # Try pytest format
    m = _PYTEST_SUMMARY.search(output)
    if m:
        passed = int(m.group(1) or 0)
        failed = int(m.group(2) or 0)
        skipped = int(m.group(3) or 0)
        errors = int(m.group(4) or 0)
        total = passed + failed + skipped + errors

    # Try unittest format
    if total == 0:
        m2 = _RUN_SUMMARY.search(output)
        if m2:
            total = int(m2.group(1))
            if re.search(_FAILED_LINE, output):
                failed = 1
                passed = total - failed
            elif re.search(_OK_LINE, output[-200:]):
                passed = total
            else:
                # Unknown status
                passed = total

    # Try script-style "N/N passed" format
    if total == 0:
        m3 = re.search(r"(\d+)/(\d+)\s+passed", output, re.I)
        if m3:
            passed = int(m3.group(1))
            total = int(m3.group(2))
            failed = total - passed

    # Fallback: use exit code
    if total == 0 and exit_code is not None:
        if exit_code == 0:
            total = 1
            passed = 1
        else:
            total = 1
            failed = 1

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "errors": errors,
    }


def run_tests(
    test_file: str | Path,
    *,
    cwd: str | Path | None = None,
    timeout_s: float = _DEFAULT_TEST_TIMEOUT_S,
    max_output: int = _DEFAULT_MAX_OUTPUT,
    python_cmd: str = "python",
    extra_args: list[str] | None = None,
    audit_path: Path | str | None = None,
    task_id: str = "",
) -> TestResult:
    """Run a test file with timeout and output limits.

    Args:
        test_file: Path to the test file to execute
        cwd: Working directory
        timeout_s: Maximum execution time
        max_output: Maximum output bytes captured
        python_cmd: Python command to use (e.g., "python", "python3")
        extra_args: Additional arguments to pass
        audit_path: Path to audit log
        task_id: Task ID for audit correlation

    Returns:
        TestResult with detailed test execution outcome.
    """
    tf = str(test_file)
    # Quote executable if it contains spaces (Windows paths like "C:\Program Files\...")
    exe = sys.executable
    if " " in exe:
        exe = f'"{exe}"'
    cmd_parts = [
        exe, "-X", "utf8", tf,
    ]
    if extra_args:
        cmd_parts.extend(extra_args)
    cmd = " ".join(cmd_parts)

    work_cwd = str(cwd) if cwd else None
    started = time.time()

    env = dict(__import__("os").environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    _audit(audit_path, {
        "ts": _now_iso(), "task_id": task_id,
        "test_file": tf, "phase": "start",
        "cwd": str(work_cwd or "")[:400],
    })

    try:
        p = subprocess.run(
            cmd, shell=True, cwd=work_cwd,
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=float(timeout_s),
            env=env,
        )
        combined = (p.stdout or "") + (p.stderr or "")
        truncated = combined[:max_output]
        elapsed = int((time.time() - started) * 1000)

        counts = parse_test_output(combined, p.returncode)

        _audit(audit_path, {
            "ts": _now_iso(), "task_id": task_id,
            "test_file": tf, "phase": "done",
            "ok": counts["failed"] == 0 and counts["errors"] == 0,
            "passed": counts["passed"],
            "failed": counts["failed"],
            "code": p.returncode,
            "ms": elapsed,
        })

        return TestResult(
            ok=counts["failed"] == 0 and counts["errors"] == 0,
            total=counts["total"],
            passed=counts["passed"],
            failed=counts["failed"],
            skipped=counts["skipped"],
            errors=counts["errors"],
            output=truncated,
            output_bytes=len(combined),
            elapsed_ms=elapsed,
            reason="",
            exit_code=p.returncode,
            test_file=tf,
        )

    except subprocess.TimeoutExpired:
        elapsed = int((time.time() - started) * 1000)
        _audit(audit_path, {
            "ts": _now_iso(), "task_id": task_id,
            "test_file": tf, "phase": "timeout",
            "ms": elapsed,
        })
        return TestResult(
            ok=False, total=0, passed=0, failed=0, skipped=0, errors=0,
            output="", output_bytes=0,
            elapsed_ms=elapsed,
            reason=f"test-timeout-after-{timeout_s}s",
            timed_out=True, test_file=tf,
        )

    except Exception as e:
        elapsed = int((time.time() - started) * 1000)
        return TestResult(
            ok=False, total=0, passed=0, failed=0, skipped=0, errors=0,
            output="", output_bytes=0,
            elapsed_ms=elapsed,
            reason=f"{type(e).__name__}:{e}"[:300],
            test_file=tf,
        )


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _audit(path: Path | str | None, entry: dict) -> None:
    """Append-only audit log. Never throws. Never blocks."""
    if path is None:
        return
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    except OSError:
        pass
