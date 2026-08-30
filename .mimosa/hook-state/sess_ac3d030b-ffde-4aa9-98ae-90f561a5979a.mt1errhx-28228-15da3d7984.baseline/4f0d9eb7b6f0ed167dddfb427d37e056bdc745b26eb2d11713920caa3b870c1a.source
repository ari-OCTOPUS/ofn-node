#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""protected_paths.py -- Protected path definitions for coding sandbox (EQUIP G4).

Deny-by-default: any path not explicitly allowed for writing is blocked.
Protected paths require owner approval before modification.

Categories:
  - ABSOLUTE_PROTECTED: Never writable by agent (safety, credentials, policy)
  - OWNER_APPROVAL_REQUIRED: Writable only after explicit owner approval
  - READ_ONLY_ALWAYS: Agent can read but never write
  - AGENT_WRITABLE: Paths the agent is allowed to modify within worktree

$0 | stdlib-only | no network | no external I/O.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path, PurePath
from typing import Any


class PathPermission(str, Enum):
    """Path permission levels for coding agents."""
    PROTECTED = "protected"             # Never writable (safety critical)
    OWNER_APPROVAL = "owner_approval"  # Requires owner approval
    READ_ONLY = "read_only"             # Can read but never write
    WRITABLE = "writable"              # Agent can modify (within worktree)


# Patterns that match protected paths (deny-by-default)
# Each entry: (compiled_regex, reason, permission_level)
_PROTECTED_PATTERNS: list[tuple[re.Pattern[str], str, PathPermission]] = [
    # Safety & kill switch
    (re.compile(r"(^|[\\/])\.env($|[\\/])", re.I),
     "credential/env-file", PathPermission.PROTECTED),
    (re.compile(r"(^|[\\/])\.env\.", re.I),
     "credential/env-dotfile", PathPermission.PROTECTED),
    (re.compile(r"kill\.switch", re.I),
     "safety-kill-switch", PathPermission.PROTECTED),
    (re.compile(r"STOP-", re.I),
     "safety-stop-flag", PathPermission.PROTECTED),
    (re.compile(r"HALT-ALL", re.I),
     "safety-halt-flag", PathPermission.PROTECTED),

    # Credentials & secrets
    (re.compile(r"(_SECRET|_TOKEN|_API_KEY|id_rsa|\.pem|\.key$)", re.I),
     "credential-secret-file", PathPermission.PROTECTED),
    (re.compile(r"(credential|secret|token)\.", re.I),
     "credential-file", PathPermission.PROTECTED),
    (re.compile(r"trust-boundary\.json", re.I),
     "trust-boundary-config", PathPermission.PROTECTED),

    # Git internals (never modify .git directly)
    (re.compile(r"(^|[\\/])\.git[\\/]"),  # Note: not .gitattributes etc at root
     "git-internal", PathPermission.PROTECTED),

    # Policy & governance
    (re.compile(r"_PROJECT_INSTRUCTIONS\.md", re.I),
     "project-instructions", PathPermission.PROTECTED),
    (re.compile(r"CONSTITUTION\.md", re.I),
     "mcp-constitution", PathPermission.PROTECTED),
    (re.compile(r"NBB-CP", re.I),
     "nbb-core-policy", PathPermission.PROTECTED),

    # Runtime state (never modify live state)
    (re.compile(r"(^|[\\/])_ops[\\/]state([\\/]|$)"),
     "runtime-state", PathPermission.PROTECTED),
    (re.compile(r"ledger\.jsonl", re.I),
     "runtime-ledger", PathPermission.PROTECTED),
    (re.compile(r"nervous-system[\\/].*data\.js", re.I),
     "nervous-system-data", PathPermission.PROTECTED),
    (re.compile(r"_memory[\\/]HEARTBEAT\.md", re.I),
     "memory-heartbeat", PathPermission.PROTECTED),

    # CI/CD & deploy configs
    (re.compile(r"\.github[\\/]workflows[\\/]"),
     "ci-workflows", PathPermission.OWNER_APPROVAL),
    (re.compile(r"deploy[\\/]"),
     "deploy-config", PathPermission.OWNER_APPROVAL),
]

# Patterns for agent-writable paths within the worktree
_WRITABLE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\.py$"),       # Python source files
    re.compile(r"\.md$"),       # Markdown documentation
    re.compile(r"\.txt$"),      # Text files
    re.compile(r"\.json$"),     # JSON config (non-protected)
    re.compile(r"\.yaml$"),     # YAML config (non-protected)
    re.compile(r"\.yml$"),       # YAML config (non-protected)
    re.compile(r"\.toml$"),      # TOML config (non-protected)
    re.compile(r"\.cfg$"),       # Config files
    re.compile(r"\.ini$"),       # Ini files
    re.compile(r"\.html$"),      # HTML files
    re.compile(r"\.css$"),       # CSS files
    re.compile(r"\.js$"),        # JavaScript files (non-critical)
    re.compile(r"\.sh$"),        # Shell scripts (non-critical)
    re.compile(r"\.bat$"),       # Batch files (non-critical)
]


@dataclass(frozen=True)
class PathCheckResult:
    """Immutable result of a path permission check.

    Fields:
        path: The path that was checked
        permission: The permission level determined
        reason: Human-readable reason for the decision
        matched_pattern: The pattern that matched (if any)
        is_protected: True if path is protected (never writable)
        requires_approval: True if path requires owner approval
        is_writable: True if agent can write to this path
    """
    path: str
    permission: PathPermission
    reason: str
    matched_pattern: str | None = None
    is_protected: bool = False
    requires_approval: bool = False
    is_writable: bool = False

    def __post_init__(self) -> None:
        # Derive boolean flags from permission
        # (We can't set frozen dataclass fields in __init__,
        #  so we use object.__setattr__ for derived fields)
        object.__setattr__(self, "is_protected",
                           self.permission == PathPermission.PROTECTED)
        object.__setattr__(self, "requires_approval",
                           self.permission == PathPermission.OWNER_APPROVAL)
        object.__setattr__(self, "is_writable",
                           self.permission == PathPermission.WRITABLE)


def check_path(path: str | Path, *,
               worktree_root: Path | str | None = None) -> PathCheckResult:
    """Check if a path is protected, requires approval, or is writable.

    Args:
        path: The path to check (absolute or relative)
        worktree_root: Root of the agent's worktree (for context)

    Returns:
        PathCheckResult with permission level and reason.
    """
    path_str = str(path).replace("\\", "/")

    # Check protected patterns first (deny-by-default)
    for pattern, reason, permission in _PROTECTED_PATTERNS:
        if pattern.search(path_str):
            return PathCheckResult(
                path=path_str,
                permission=permission,
                reason=reason,
                matched_pattern=pattern.pattern,
            )

    # Check if within worktree root (if provided)
    if worktree_root:
        wt = str(worktree_root).replace("\\", "/")
        if path_str.startswith(wt):
            return PathCheckResult(
                path=path_str,
                permission=PathPermission.WRITABLE,
                reason="within-worktree",
            )

    # Default: not writable (fail-closed)
    return PathCheckResult(
        path=path_str,
        permission=PathPermission.READ_ONLY,
        reason="not-in-worktree-and-not-explicitly-writable",
    )


def check_paths(paths: list[str | Path], *,
                worktree_root: Path | str | None = None) -> dict[str, PathCheckResult]:
    """Check multiple paths. Returns dict mapping path string to result."""
    return {str(p): check_path(p, worktree_root=worktree_root) for p in paths}


def is_protected(path: str | Path) -> bool:
    """Quick check: is this path protected?"""
    return check_path(path).is_protected


def requires_owner_approval(path: str | Path) -> bool:
    """Quick check: does this path require owner approval?"""
    return check_path(path).requires_approval


def blocklist_reason(path: str | Path, *,
                    worktree_root: Path | str | None = None) -> str | None:
    """Return block reason if path is blocked, None if writable."""
    result = check_path(path, worktree_root=worktree_root)
    if result.is_writable:
        return None
    return f"{result.permission.value}: {result.reason}"
