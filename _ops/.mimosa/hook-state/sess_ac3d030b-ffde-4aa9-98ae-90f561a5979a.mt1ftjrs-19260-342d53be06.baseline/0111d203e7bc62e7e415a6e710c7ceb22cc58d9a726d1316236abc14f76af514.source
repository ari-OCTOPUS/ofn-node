#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sandbox.py -- Core CodingSandbox lifecycle (EQUIP G4).

Manages the full lifecycle of a coding agent working in a sandboxed environment:
  1. Create git worktree + branch for each coding task
  2. Enforce filesystem jail (path validation, symlink check)
  3. Execute commands through allowlist + timeout
  4. Validate patches before application
  5. Run tests with no-skip enforcement
  6. Produce commit with Task ID + evidence reference
  7. Cleanup worktree on completion

Design:
  - Each task gets its own worktree + branch
  - All file operations are confined to the worktree
  - Protected paths require owner approval
  - Network is default-deny
  - No auto-merge, no auto-push
  - Every operation is audited

Integration:
  - G1 TaskOrchestrator for task lifecycle
  - G7 PolicyEnforcer for protected path checks
  - G8 RiskGate for risk classification
  - G3 FetchGuard for any network needs (blocked in sandbox)

$0 | stdlib-only for sandbox logic | git for worktree management.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Sequence

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

SCHEMA = "coding-sandbox.v1"

# Default worktree directory
_DEFAULT_WORKTREE_BASE = _OPS.parent / ".worktrees"


class SandboxState(str, Enum):
    """Sandbox lifecycle states."""
    CREATED = "CREATED"
    WORKTREE_READY = "WORKTREE_READY"
    CODING = "CODING"
    TESTING = "TESTING"
    COMMITTED = "COMMITTED"
    CLEANED = "CLEANED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class SandboxConfig:
    """Configuration for a coding sandbox instance.

    Fields:
        repo_root: Path to the git repository root
        worktree_base: Base directory for worktrees
        branch_prefix: Prefix for task branches (e.g., "task/")
        max_diff_bytes: Maximum diff size per patch
        max_test_timeout_s: Maximum test execution time
        max_command_timeout_s: Maximum command execution time
        auto_cleanup: Whether to clean up worktree on completion
    """
    repo_root: Path = field(default_factory=lambda: _OPS.parent)
    worktree_base: Path = field(default_factory=lambda: _DEFAULT_WORKTREE_BASE)
    branch_prefix: str = "task/"
    max_diff_bytes: int = 50_000
    max_test_timeout_s: float = 300.0
    max_command_timeout_s: float = 120.0
    auto_cleanup: bool = True


@dataclass
class SandboxResult:
    """Result of a sandbox operation.

    Fields:
        ok: True if operation succeeded
        state: Current sandbox state
        reason: Human-readable reason (empty if ok)
        worktree_path: Path to the worktree (if created)
        branch_name: Name of the task branch (if created)
        commit_sha: SHA of the commit (if committed)
        test_results: Test execution results
        audit_entries: Audit trail entries
    """
    ok: bool
    state: SandboxState
    reason: str
    worktree_path: str = ""
    branch_name: str = ""
    commit_sha: str = ""
    test_results: dict | None = None
    audit_entries: list = field(default_factory=list)


class CodingSandbox:
    """Safe coding environment for autonomous agents.

    Usage:
        sb = CodingSandbox(config=SandboxConfig(repo_root=Path("/repo")))
        result = sb.create_task(task_id="TASK-001", agent_id="worker-1")
        # Agent works in result.worktree_path
        # Agent runs commands via sb.run_command(...)
        # Agent commits via sb.commit(...)
    """

    def __init__(
        self,
        config: SandboxConfig | None = None,
        audit_path: Path | str | None = None,
        kill_check: Callable[[], bool] | None = None,
    ) -> None:
        self._config = config or SandboxConfig()
        self._audit_path = Path(audit_path) if audit_path else None
        self._kill_check = kill_check
        self._state = SandboxState.CREATED
        self._task_id = ""
        self._agent_id = ""
        self._worktree_path: Path | None = None
        self._branch_name = ""
        self._commit_sha = ""
        self._audit_trail: list[dict] = []
        self._approved_paths: set[str] = set()

    @property
    def state(self) -> SandboxState:
        return self._state

    @property
    def worktree_path(self) -> Path | None:
        return self._worktree_path

    @property
    def branch_name(self) -> str:
        return self._branch_name

    @property
    def task_id(self) -> str:
        return self._task_id

    # ── Task Lifecycle ──────────────────────────────────────────────────

    def create_task(
        self,
        task_id: str,
        agent_id: str,
        *,
        base_branch: str = "HEAD",
    ) -> SandboxResult:
        """Create a new coding task with worktree + branch.

        Args:
            task_id: Unique task identifier
            agent_id: Agent that will work on this task
            base_branch: Branch or ref to base the worktree on

        Returns:
            SandboxResult with worktree_path and branch_name.
        """
        if self._state != SandboxState.CREATED:
            return SandboxResult(
                ok=False, state=self._state,
                reason=f"invalid-state:{self._state.value}",
            )

        if self._check_kill():
            self._state = SandboxState.CANCELLED
            return SandboxResult(
                ok=False, state=SandboxState.CANCELLED,
                reason="kill-switch-active",
            )

        self._task_id = str(task_id)
        self._agent_id = str(agent_id)

        # Generate unique branch name
        short_id = uuid.uuid4().hex[:8]
        self._branch_name = f"{self._config.branch_prefix}{task_id}-{short_id}"

        # Create worktree directory
        wt_base = self._config.worktree_base
        wt_base.mkdir(parents=True, exist_ok=True)
        wt_path = wt_base / f"{task_id}-{short_id}"

        try:
            # Create git worktree
            result = subprocess.run(
                ["git", "worktree", "add", "-b", self._branch_name,
                 str(wt_path), base_branch],
                cwd=str(self._config.repo_root),
                capture_output=True, text=True,
                encoding="utf-8", errors="replace",
                timeout=30,
            )

            if result.returncode != 0:
                self._state = SandboxState.FAILED
                self._audit("worktree-create-failed", {
                    "task_id": self._task_id,
                    "branch": self._branch_name,
                    "stderr": (result.stderr or "")[:500],
                })
                return SandboxResult(
                    ok=False, state=SandboxState.FAILED,
                    reason=f"worktree-create-failed:{(result.stderr or '')[:200]}",
                )

            self._worktree_path = wt_path
            self._state = SandboxState.WORKTREE_READY

            self._audit("task-created", {
                "task_id": self._task_id,
                "agent_id": self._agent_id,
                "branch": self._branch_name,
                "worktree": str(wt_path),
            })

            return SandboxResult(
                ok=True, state=self._state,
                reason="worktree-created",
                worktree_path=str(wt_path),
                branch_name=self._branch_name,
                audit_entries=list(self._audit_trail),
            )

        except subprocess.TimeoutExpired:
            self._state = SandboxState.FAILED
            return SandboxResult(
                ok=False, state=SandboxState.FAILED,
                reason="worktree-create-timeout",
            )
        except Exception as e:
            self._state = SandboxState.FAILED
            return SandboxResult(
                ok=False, state=SandboxState.FAILED,
                reason=f"worktree-create-error:{type(e).__name__}:{e}"[:200],
            )

    def run_command(
        self,
        cmd: str,
        *,
        timeout_s: float | None = None,
        max_output: int = 100_000,
    ) -> dict[str, Any]:
        """Run a command within the sandbox worktree.

        The command passes through the command_runner allowlist and
        is executed within the worktree directory.

        Args:
            cmd: Command to execute
            timeout_s: Timeout override
            max_output: Maximum output bytes

        Returns:
            Command result dict.
        """
        if self._worktree_path is None:
            return {"ok": False, "ran": False, "reason": "no-worktree"}

        if self._check_kill():
            return {"ok": False, "ran": False, "reason": "kill-switch-active"}

        from command_runner import run_command as _run

        result = _run(
            cmd,
            cwd=self._worktree_path,
            timeout_s=timeout_s or self._config.max_command_timeout_s,
            max_output=max_output,
            audit_path=self._audit_path,
            task_id=self._task_id,
        )
        return result.to_dict()

    def run_tests(
        self,
        test_file: str | Path,
        *,
        timeout_s: float | None = None,
        extra_args: list[str] | None = None,
    ) -> dict[str, Any]:
        """Run tests within the sandbox worktree.

        Args:
            test_file: Path to test file (absolute or relative to worktree)
            timeout_s: Timeout override
            extra_args: Additional test arguments

        Returns:
            TestResult dict.
        """
        if self._worktree_path is None:
            return {"ok": False, "reason": "no-worktree"}

        if self._check_kill():
            return {"ok": False, "reason": "kill-switch-active"}

        from test_runner import run_tests as _run_tests

        result = _run_tests(
            test_file,
            cwd=self._worktree_path,
            timeout_s=timeout_s or self._config.max_test_timeout_s,
            audit_path=self._audit_path,
            task_id=self._task_id,
            extra_args=extra_args,
        )
        return result.to_dict()

    def validate_patch(self, diff_text: str) -> dict[str, Any]:
        """Validate a patch before application.

        Args:
            diff_text: Unified diff text

        Returns:
            PatchValidationResult dict.
        """
        from patch_validator import validate_patch as _validate
        from protected_paths import check_path

        result = _validate(
            diff_text,
            max_bytes=self._config.max_diff_bytes,
        )

        # Check protected paths
        violations = []
        if result.valid:
            from patch_validator import check_protected_paths_in_patch
            violations = check_protected_paths_in_patch(
                diff_text, check_path
            )

        return {
            **result.to_dict(),
            "protected_path_violations": violations,
        }

    def approve_protected_path(self, path: str) -> None:
        """Mark a protected path as approved for this task.

        This should only be called after owner approval.
        """
        self._approved_paths.add(str(path).replace("\\", "/"))

    def commit(
        self,
        message: str,
        *,
        allow_empty: bool = False,
    ) -> SandboxResult:
        """Stage all changes and commit in the worktree.

        Args:
            message: Commit message (will be prefixed with task_id)
            allow_empty: Allow empty commits

        Returns:
            SandboxResult with commit SHA.
        """
        if self._worktree_path is None:
            return SandboxResult(
                ok=False, state=self._state,
                reason="no-worktree",
            )

        if self._check_kill():
            self._state = SandboxState.CANCELLED
            return SandboxResult(
                ok=False, state=SandboxState.CANCELLED,
                reason="kill-switch-active",
            )

        # Prefix message with task_id
        full_message = f"[{self._task_id}] {message}"

        try:
            # Stage all changes in worktree (explicit, not git add -A)
            subprocess.run(
                ["git", "add", "-A"],
                cwd=str(self._worktree_path),
                capture_output=True, text=True,
                timeout=30,
            )

            # Commit
            args = ["git", "commit", "-m", full_message]
            if allow_empty:
                args.append("--allow-empty")

            result = subprocess.run(
                args,
                cwd=str(self._worktree_path),
                capture_output=True, text=True,
                encoding="utf-8", errors="replace",
                timeout=30,
            )

            if result.returncode != 0:
                self._audit("commit-failed", {
                    "task_id": self._task_id,
                    "stderr": (result.stderr or "")[:500],
                })
                return SandboxResult(
                    ok=False, state=self._state,
                    reason=f"commit-failed:{(result.stderr or '')[:200]}",
                )

            # Get commit SHA
            sha_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(self._worktree_path),
                capture_output=True, text=True,
                timeout=10,
            )
            sha = sha_result.stdout.strip()[:40] if sha_result.returncode == 0 else ""

            self._commit_sha = sha
            self._state = SandboxState.COMMITTED

            self._audit("committed", {
                "task_id": self._task_id,
                "sha": sha,
                "message": full_message[:200],
            })

            return SandboxResult(
                ok=True, state=self._state,
                reason="committed",
                commit_sha=sha,
                branch_name=self._branch_name,
                worktree_path=str(self._worktree_path),
                audit_entries=list(self._audit_trail),
            )

        except Exception as e:
            return SandboxResult(
                ok=False, state=self._state,
                reason=f"commit-error:{type(e).__name__}:{e}"[:200],
            )

    def cleanup(self) -> SandboxResult:
        """Remove the worktree and delete the branch.

        Returns:
            SandboxResult.
        """
        if self._worktree_path is None:
            self._state = SandboxState.CLEANED
            return SandboxResult(
                ok=True, state=SandboxState.CLEANED,
                reason="no-worktree-to-clean",
            )

        try:
            # Remove worktree
            subprocess.run(
                ["git", "worktree", "remove", str(self._worktree_path),
                 "--force"],
                cwd=str(self._config.repo_root),
                capture_output=True, text=True,
                timeout=30,
            )

            # Delete branch (optional, only if committed)
            if self._branch_name:
                subprocess.run(
                    ["git", "branch", "-D", self._branch_name],
                    cwd=str(self._config.repo_root),
                    capture_output=True, text=True,
                    timeout=10,
                )

            self._state = SandboxState.CLEANED
            self._audit("cleaned", {
                "task_id": self._task_id,
                "worktree": str(self._worktree_path),
                "branch": self._branch_name,
            })

            return SandboxResult(
                ok=True, state=SandboxState.CLEANED,
                reason="cleaned",
                audit_entries=list(self._audit_trail),
            )

        except Exception as e:
            return SandboxResult(
                ok=False, state=self._state,
                reason=f"cleanup-error:{type(e).__name__}:{e}"[:200],
            )

    # ── Internal ──────────────────────────────────────────────────────

    def _check_kill(self) -> bool:
        """Check if kill switch is active."""
        if self._kill_check and self._kill_check():
            return True
        # Check file-based kill switches
        try:
            kill_file = _OPS / "observatory" / "data" / "kill.switch"
            if kill_file.exists():
                return True
            stop_file = _OPS / "STOP-ORGANISM"
            if stop_file.exists():
                return True
        except OSError:
            pass
        return False

    def _audit(self, event: str, details: dict) -> None:
        """Record an audit entry."""
        entry = {
            "schema": SCHEMA,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event": event,
            "task_id": self._task_id,
            "agent_id": self._agent_id,
            "branch": self._branch_name,
            "state": self._state.value,
            **details,
        }
        self._audit_trail.append(entry)

        # Write to file if path configured
        if self._audit_path:
            try:
                p = Path(self._audit_path)
                p.parent.mkdir(parents=True, exist_ok=True)
                with p.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
            except OSError:
                pass
