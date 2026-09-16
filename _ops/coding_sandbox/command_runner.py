#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""command_runner.py -- Command execution with limits for coding sandbox (EQUIP G4).

Executes shell commands within the coding sandbox with:
  - Shell allowlist (deny-by-default: unknown commands are blocked)
  - Timeout (hard kill after timeout)
  - Output limit (truncate stdout/stderr)
  - Network default-deny (no curl, wget, ssh, etc.)
  - No privilege escalation (no sudo, runas)
  - Audit trail for every execution

Invariants:
  - Every command is logged before execution
  - No command runs without allowlist check
  - Output is always bounded
  - Network commands are always denied
  - Destructive commands are always denied

$0 | stdlib-only | no network | subprocess only for execution.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

SCHEMA = "command-runner.v1"

# Default limits
_DEFAULT_TIMEOUT_S = 120.0
_DEFAULT_MAX_OUTPUT = 100_000   # 100 KB max output per stream
_DEFAULT_MAX_CMD_LENGTH = 4000

# Shell allowlist: only these command prefixes are allowed
# Format: (regex_pattern, description)
_ALLOWLIST: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^(python[23]?\s|py\s)", re.I), "python-execution"),
    (re.compile(r"^(pytest\s|python\s.*-m\s+pytest)", re.I), "pytest"),
    (re.compile(r"^(git\s)", re.I), "git-command"),
    (re.compile(r"^(cat\s|head\s|tail\s|wc\s|ls\s|dir\s|tree\s)", re.I), "file-inspection"),
    (re.compile(r"^(grep\s|rg\s|find\s)", re.I), "search"),
    (re.compile(r"^(diff\s|patch\s|git\sapply\s)", re.I), "diff-patch"),
    (re.compile(r"^(echo\s|printf\s|type\s)", re.I), "output"),
    (re.compile(r"^(cd\s|pwd|mkdir\s|touch\s)", re.I), "directory-ops"),
    (re.compile(r"^(cp\s|mv\s|rename\s)", re.I), "file-move"),
    (re.compile(r"^(pip\s|pip[23]?\s)", re.I), "package-mgmt"),
    (re.compile(r"^(ruff\s|mypy\s|black\s|isort\s)", re.I), "code-quality"),
    (re.compile(r"^(which\s|where\s|python3?\s--version)", re.I), "system-info"),
]

# Deny-list: these are ALWAYS blocked regardless of allowlist
_DENYLIST: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bcurl\b|\bwget\b|\bnc\b|\bscp\b|\bssh\b|\btelnet\b", re.I),
     "network-command-denied"),
    (re.compile(r"\bsudo\b|\brunas\b|Start-Process.*-Verb\s+RunAs", re.I),
     "privilege-escalation-denied"),
    (re.compile(r"\brm\s+(-\w*\s+)*-\w*[rf]", re.I),
     "destructive-rm-denied"),
    (re.compile(r"\bRemove-Item\b.*-Recurse", re.I),
     "destructive-remove-denied"),
    (re.compile(r"\bgit\s+(push|reset\s+--hard|clean\s+-f|filter-branch)", re.I),
     "dangerous-git-denied"),
    (re.compile(r"(^|\s)git\s+push", re.I),
     "git-push-denied"),
    (re.compile(r"(^|\s)git\s+merge", re.I),
     "git-merge-denied"),
]


@dataclass(frozen=True)
class CommandResult:
    """Immutable result of a command execution.

    Fields:
        ok: True if command succeeded (exit code 0)
        ran: True if command was actually executed
        exit_code: Process exit code (None if not executed)
        stdout: Captured stdout (truncated at MAX_OUTPUT)
        stdout_bytes: Size of stdout before truncation
        stderr: Captured stderr (truncated at MAX_OUTPUT)
        stderr_bytes: Size of stderr before truncation
        elapsed_ms: Execution time in milliseconds
        reason: Human-readable reason (empty if ok)
        blocked: True if command was blocked by runner
        timed_out: True if command exceeded timeout
        cmd_safe: Safe representation of command (truncated)
    """
    ok: bool
    ran: bool
    exit_code: int | None
    stdout: str
    stdout_bytes: int
    stderr: str
    stderr_bytes: int
    elapsed_ms: int
    reason: str
    blocked: bool = False
    timed_out: bool = False
    cmd_safe: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "ok": self.ok, "ran": self.ran,
            "exit_code": self.exit_code,
            "stdout_bytes": self.stdout_bytes,
            "stderr_bytes": self.stderr_bytes,
            "elapsed_ms": self.elapsed_ms,
            "reason": self.reason,
            "blocked": self.blocked,
            "timed_out": self.timed_out,
        }


def check_command(cmd: str) -> tuple[bool, str]:
    """Check if a command is allowed by the allowlist.

    Returns:
        (allowed, reason) — reason is empty if allowed.
    """
    c = str(cmd or "").strip()
    if not c:
        return False, "empty-command"
    if len(c) > _DEFAULT_MAX_CMD_LENGTH:
        return False, f"command-too-long (max={_DEFAULT_MAX_CMD_LENGTH})"

    # Check deny-list first (always blocked)
    for pattern, reason in _DENYLIST:
        if pattern.search(c):
            return False, reason

    # Check allowlist (deny-by-default)
    for pattern, description in _ALLOWLIST:
        if pattern.search(c):
            return True, ""

    return False, "command-not-in-allowlist"


def run_command(
    cmd: str,
    *,
    cwd: str | Path | None = None,
    timeout_s: float = _DEFAULT_TIMEOUT_S,
    max_output: int = _DEFAULT_MAX_OUTPUT,
    env: dict[str, str] | None = None,
    audit_path: Path | str | None = None,
    task_id: str = "",
) -> CommandResult:
    """Execute a command with allowlist check, timeout, and output limits.

    Args:
        cmd: The command to execute
        cwd: Working directory
        timeout_s: Maximum execution time in seconds
        max_output: Maximum bytes captured per output stream
        env: Additional environment variables (merged with os.environ)
        audit_path: Path to append-only audit log
        task_id: Task ID for audit correlation

    Returns:
        CommandResult with execution details.
    """
    # Check allowlist
    ok_cmd, reason_cmd = check_command(cmd)
    if not ok_cmd:
        _audit(audit_path, {
            "ts": _now_iso(), "task_id": task_id,
            "cmd": str(cmd)[:400], "phase": "blocked",
            "reason": reason_cmd, "reason_kind": "allowlist",
        })
        return CommandResult(
            ok=False, ran=False, exit_code=None,
            stdout="", stdout_bytes=0, stderr="", stderr_bytes=0,
            elapsed_ms=0, reason=reason_cmd, blocked=True,
            cmd_safe=str(cmd)[:400],
        )

    # Set up execution
    exec_env = dict(os.environ)
    if env:
        exec_env.update(env)
    # Default-deny network: remove proxy variables as defense-in-depth
    for k in list(exec_env.keys()):
        kl = k.lower()
        if kl.startswith(("http_proxy", "https_proxy", "all_proxy", "ftp_proxy")):
            del exec_env[k]

    work_cwd = str(cwd) if cwd else None
    started = time.time()

    # Audit: start
    _audit(audit_path, {
        "ts": _now_iso(), "task_id": task_id,
        "cmd": str(cmd)[:400], "phase": "start",
        "cwd": str(work_cwd or "")[:400],
    })

    try:
        p = subprocess.run(
            cmd, shell=True, cwd=work_cwd,
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=float(timeout_s),
            env=exec_env,
        )
        out = (p.stdout or "")[:max_output]
        err = (p.stderr or "")[:max_output]
        elapsed = int((time.time() - started) * 1000)

        _audit(audit_path, {
            "ts": _now_iso(), "task_id": task_id,
            "cmd": str(cmd)[:400], "phase": "done",
            "ok": p.returncode == 0, "code": p.returncode,
            "ms": elapsed, "out_bytes": len(p.stdout or ""),
            "err_bytes": len(p.stderr or ""),
        })

        return CommandResult(
            ok=p.returncode == 0, ran=True,
            exit_code=p.returncode,
            stdout=out, stdout_bytes=len(p.stdout or ""),
            stderr=err, stderr_bytes=len(p.stderr or ""),
            elapsed_ms=elapsed, reason="",
            cmd_safe=str(cmd)[:400],
        )

    except subprocess.TimeoutExpired:
        elapsed = int((time.time() - started) * 1000)
        _audit(audit_path, {
            "ts": _now_iso(), "task_id": task_id,
            "cmd": str(cmd)[:400], "phase": "timeout",
            "ms": elapsed, "timeout_s": timeout_s,
        })
        return CommandResult(
            ok=False, ran=True, exit_code=None,
            stdout="", stdout_bytes=0, stderr="", stderr_bytes=0,
            elapsed_ms=elapsed, reason=f"timeout-after-{timeout_s}s",
            timed_out=True, cmd_safe=str(cmd)[:400],
        )

    except Exception as e:
        elapsed = int((time.time() - started) * 1000)
        return CommandResult(
            ok=False, ran=False, exit_code=None,
            stdout="", stdout_bytes=0, stderr="", stderr_bytes=0,
            elapsed_ms=elapsed,
            reason=f"{type(e).__name__}:{e}"[:300],
            cmd_safe=str(cmd)[:400],
        )


def _now_iso() -> str:
    import time as _time
    return _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime())


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
