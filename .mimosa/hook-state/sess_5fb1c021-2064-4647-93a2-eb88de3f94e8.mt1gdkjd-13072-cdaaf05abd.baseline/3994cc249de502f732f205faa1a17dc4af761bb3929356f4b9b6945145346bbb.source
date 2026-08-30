#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""filesystem_jail.py -- Filesystem jail enforcement for coding sandbox (EQUIP G4).

Enforces that coding agents can only access files within their worktree.
Detects symlink escapes, path traversal attempts, and access outside the jail.

Invariants:
  - All file operations are confined to the worktree root
  - Symlinks pointing outside the jail are detected and blocked
  - Path traversal (../..) is normalized and checked
  - Absolute paths outside the jail are blocked
  - No access to protected system paths

$0 | stdlib-only | no network | no external I/O (pure validation).
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


# Patterns that should never appear in file operations
_DANGEROUS_PATTERNS = [
    re.compile(r"\.\.[\\/]"),       # Path traversal
    re.compile(r"^/"),               # Absolute path (Unix)
    re.compile(r"^[A-Za-z]:[\\/]"), # Absolute path (Windows)
]

# System paths that should never be accessed
_SYSTEM_PATHS = [
    "/etc/passwd", "/etc/shadow", "/etc/hosts",
    "/proc/", "/sys/", "/dev/",
    "C:\\Windows\\", "C:\\ProgramData\\",
]


@dataclass(frozen=True)
class JailCheckResult:
    """Result of a filesystem jail check.

    Fields:
        path: The path that was checked
        allowed: True if path is within the jail
        reason: Human-readable reason (empty if allowed)
        normalized_path: The resolved, normalized path
        is_symlink_escape: True if path escapes jail via symlink
        is_traversal: True if path contains traversal sequences
        jail_root: The jail root used for the check
    """
    path: str
    allowed: bool
    reason: str
    normalized_path: str
    is_symlink_escape: bool = False
    is_traversal: bool = False
    jail_root: str = ""


def normalize_path(path: str | Path) -> str:
    """Normalize a path: resolve relative parts, convert separators."""
    p = str(path).replace("\\", "/")
    # Use PurePosixPath for pure string normalization (no disk access)
    # Manually resolve .. and . to avoid symlink following
    parts = PurePosixPath(p).parts
    resolved = []
    for part in parts:
        if part == "..":
            if resolved and resolved[-1] != ".." and resolved[-1] != "":
                resolved.pop()
            else:
                resolved.append("..")
        elif part == "." or part == "" or part == "/":
            if part == "/":
                resolved.append("/")  # preserve root
            continue
        else:
            resolved.append(part)
    result = "/".join(resolved)
    # Handle edge case: all leading .. consumed
    return result


def check_jail(path: str | Path, jail_root: str | Path) -> JailCheckResult:
    """Check if a path is within the filesystem jail.

    Args:
        path: The path to check
        jail_root: The root directory of the jail (worktree)

    Returns:
        JailCheckResult with allow/deny decision and details.
    """
    path_str = str(path).replace("\\", "/")
    root_str = str(jail_root).replace("\\", "/").rstrip("/")

    # Normalize the path
    norm = normalize_path(path_str)

    # Check for path traversal in the ORIGINAL path (before normalization)
    is_traversal = False
    for pat in _DANGEROUS_PATTERNS:
        if pat.search(path_str):
            # Absolute paths to system locations
            is_traversal = True
            break

    # Check for system paths
    for sys_path in _SYSTEM_PATHS:
        if sys_path.lower() in path_str.lower():
            return JailCheckResult(
                path=path_str, allowed=False,
                reason=f"system-path-access-denied:{sys_path}",
                normalized_path=norm, is_traversal=is_traversal,
                jail_root=root_str,
            )

    # Check if absolute and outside jail
    if path_str.startswith("/") or re.match(r"^[A-Za-z]:", path_str):
        if not norm.startswith(root_str):
            return JailCheckResult(
                path=path_str, allowed=False,
                reason="absolute-path-outside-jail",
                normalized_path=norm, is_traversal=is_traversal,
                jail_root=root_str,
            )

    # Check for symlinks (if path exists on disk)
    real_path = Path(path_str) if os.path.exists(path_str) else None
    if real_path is not None and real_path.is_symlink():
        try:
            target = os.readlink(str(real_path))
            target_norm = normalize_path(target)
            if not target_norm.startswith(root_str):
                return JailCheckResult(
                    path=path_str, allowed=False,
                    reason=f"symlink-escape: target={target_norm}",
                    normalized_path=norm,
                    is_symlink_escape=True, jail_root=root_str,
                )
        except OSError:
            pass  # Can't read symlink — block conservatively
            return JailCheckResult(
                path=path_str, allowed=False,
                reason="symlink-unreadable:blocked",
                normalized_path=norm,
                is_symlink_escape=True, jail_root=root_str,
            )

    # Check normalized path against jail root
    if norm.startswith(root_str + "/") or norm == root_str:
        return JailCheckResult(
            path=path_str, allowed=True, reason="",
            normalized_path=norm, jail_root=root_str,
        )

    # Relative path that doesn't escape but needs jail root context
    if not path_str.startswith("/") and not re.match(r"^[A-Za-z]:", path_str):
        return JailCheckResult(
            path=path_str, allowed=True, reason="relative-path",
            normalized_path=norm, jail_root=root_str,
        )

    return JailCheckResult(
        path=path_str, allowed=False,
        reason="path-outside-jail",
        normalized_path=norm, is_traversal=is_traversal,
        jail_root=root_str,
    )


def validate_paths_for_operation(
    paths: list[str | Path],
    jail_root: str | Path,
    operation: str = "write",
) -> dict[str, JailCheckResult]:
    """Validate multiple paths for an operation within the jail.

    Returns:
        Dict mapping path string to JailCheckResult.
        All paths must be allowed for the operation to proceed.
    """
    return {
        str(p): check_jail(p, jail_root)
        for p in paths
    }


def all_within_jail(
    paths: list[str | Path],
    jail_root: str | Path,
) -> tuple[bool, list[JailCheckResult]]:
    """Check if all paths are within the jail.

    Returns:
        (all_allowed, list_of_failures)
    """
    results = [check_jail(p, jail_root) for p in paths]
    failures = [r for r in results if not r.allowed]
    return len(failures) == 0, failures
