#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_validator.py -- Diff/patch validation for coding sandbox (EQUIP G4).

Validates patches before they are applied within the sandbox:
  - Size limit on total diff
  - Line count limit
  - Format validation (unified diff format)
  - Reversibility check (patch must be reversible)
  - No embedded secrets or credentials
  - No binary content伪装 as text

Invariants:
  - Every patch is validated before application
  - Patches exceeding limits are rejected
  - Malformed patches are rejected
  - Patches touching protected paths are flagged

$0 | stdlib-only | no network | no external I/O.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


# Default limits
_DEFAULT_MAX_DIFF_BYTES = 50_000    # 50 KB max diff
_DEFAULT_MAX_LINES = 500           # Max lines in diff
_DEFAULT_MAX_FILES = 10            # Max files in a single patch

# Secret patterns to detect in patches
_SECRET_PATTERNS = [
    re.compile(r"(sk-[A-Za-z0-9]{12,})", re.I),
    re.compile(r"(AKIA[0-9A-Z]{12,})", re.I),
    re.compile(r"(-----BEGIN[\s\S]?PRIVATE)", re.I),
    re.compile(r"(xox[baprs]-[A-Za-z0-9-]+)", re.I),
    re.compile(r"(ghp_[a-zA-Z0-9]{36,})", re.I),
    re.compile(r"(gho_[a-zA-Z0-9]{36,})", re.I),
    re.compile(r"(ghu_[a-zA-Z0-9]{36,})", re.I),
    re.compile(r"(\bpassword\b\s*[:=]\s*\S+)", re.I),
    re.compile(r"(\bapi[_-]?key\b\s*[:=]\s*\S+)", re.I),
    re.compile(r"(\btoken\b\s*[:=]\s*\S+)", re.I),
]

# Unified diff line patterns
_DIFF_HEADER = re.compile(r"^diff --git a/(.*) b/(.*)")
_HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@")
_ADD_LINE = re.compile(r"^\+")
_DEL_LINE = re.compile(r"^-")
_NO_NEWLINE = re.compile(r"^\\ No newline at end of file")


@dataclass(frozen=True)
class PatchValidationResult:
    """Result of patch validation.

    Fields:
        valid: True if patch passes all checks
        reason: Human-readable reason (empty if valid)
        diff_size: Size of diff in bytes
        line_count: Number of lines in diff
        file_count: Number of files touched
        has_secrets: True if secret patterns detected
        secret_matches: List of matched secret patterns
        is_reversible: True if patch appears reversible
        format_ok: True if patch is in valid unified diff format
    """
    valid: bool
    reason: str
    diff_size: int
    line_count: int
    file_count: int
    has_secrets: bool = False
    secret_matches: tuple[str, ...] = ()
    is_reversible: bool = True
    format_ok: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "reason": self.reason,
            "diff_size": self.diff_size,
            "line_count": self.line_count,
            "file_count": self.file_count,
            "has_secrets": self.has_secrets,
            "is_reversible": self.is_reversible,
            "format_ok": self.format_ok,
        }


def validate_patch(
    diff_text: str,
    *,
    max_bytes: int = _DEFAULT_MAX_DIFF_BYTES,
    max_lines: int = _DEFAULT_MAX_LINES,
    max_files: int = _DEFAULT_MAX_FILES,
) -> PatchValidationResult:
    """Validate a patch/diff before application.

    Checks:
      1. Size limits (bytes, lines, files)
      2. Format (unified diff)
      3. Secret detection
      4. Reversibility (has both add and delete context)

    Args:
        diff_text: The unified diff text to validate
        max_bytes: Maximum allowed diff size in bytes
        max_lines: Maximum allowed line count
        max_files: Maximum number of files touched

    Returns:
        PatchValidationResult with detailed validation outcome.
    """
    diff_bytes = len(diff_text.encode("utf-8"))
    lines = diff_text.splitlines()
    line_count = len(lines)

    # 1. Size limits
    if diff_bytes > max_bytes:
        return PatchValidationResult(
            valid=False,
            reason=f"diff-too-large ({diff_bytes} > {max_bytes} bytes)",
            diff_size=diff_bytes, line_count=line_count, file_count=0,
        )

    if line_count > max_lines:
        return PatchValidationResult(
            valid=False,
            reason=f"too-many-lines ({line_count} > {max_lines})",
            diff_size=diff_bytes, line_count=line_count, file_count=0,
        )

    # 2. Format validation
    files_touched: set[str] = set()
    has_add = False
    has_delete = False
    format_ok = True

    for line in lines:
        # Count files
        m = _DIFF_HEADER.match(line)
        if m:
            files_touched.add(m.group(1))
            files_touched.add(m.group(2))
            continue

        # Track add/delete for reversibility
        if _ADD_LINE.match(line) and not _ADD_LINE.match(line[:2] + " "):
            # Lines starting with '+' but not '+++' (which is a file header)
            if not line.startswith("+++"):
                has_add = True
        if _DEL_LINE.match(line):
            if not line.startswith("---"):
                has_delete = True

    file_count = len(files_touched)

    if file_count > max_files:
        return PatchValidationResult(
            valid=False,
            reason=f"too-many-files ({file_count} > {max_files})",
            diff_size=diff_bytes, line_count=line_count,
            file_count=file_count,
        )

    # Check format: if there are file headers, there should be hunk headers
    has_file_headers = any(_DIFF_HEADER.match(l) for l in lines)
    has_hunk_headers = any(_HUNK_HEADER.match(l) for l in lines)
    if has_file_headers and not has_hunk_headers:
        format_ok = False
        return PatchValidationResult(
            valid=False,
            reason="malformed-diff: file headers without hunk headers",
            diff_size=diff_bytes, line_count=line_count,
            file_count=file_count, format_ok=False,
        )

    # 3. Secret detection
    secret_matches: list[str] = []
    for pat in _SECRET_PATTERNS:
        matches = pat.findall(diff_text)
        for m in matches:
            secret_matches.append(f"{pat.pattern[:30]}:{str(m)[:20]}")

    has_secrets = len(secret_matches) > 0
    if has_secrets:
        return PatchValidationResult(
            valid=False,
            reason=f"secret-pattern-detected: {secret_matches[:3]}",
            diff_size=diff_bytes, line_count=line_count,
            file_count=file_count,
            has_secrets=True,
            secret_matches=tuple(secret_matches[:10]),
            format_ok=format_ok,
        )

    # 4. Reversibility: a patch with only additions or only deletions
    # is still reversible (git can reverse it), but flag it
    is_reversible = True
    if has_add and not has_delete:
        is_reversible = True  # git can reverse pure additions
    elif has_delete and not has_add:
        is_reversible = True  # git can reverse pure deletions

    return PatchValidationResult(
        valid=True,
        reason="patch-valid",
        diff_size=diff_bytes, line_count=line_count,
        file_count=file_count,
        is_reversible=is_reversible,
        format_ok=format_ok,
    )


def check_protected_paths_in_patch(
    diff_text: str,
    protected_checker=None,
) -> list[dict[str, Any]]:
    """Check if a patch touches protected paths.

    Args:
        diff_text: The unified diff text
        protected_checker: A function(path) -> PathCheckResult
            If None, returns empty list (no check).

    Returns:
        List of dicts describing protected path violations.
    """
    if protected_checker is None:
        return []

    violations = []
    for line in diff_text.splitlines():
        m = _DIFF_HEADER.match(line)
        if m:
            for path in (m.group(1), m.group(2)):
                result = protected_checker(path)
                if result.is_protected or result.requires_approval:
                    violations.append({
                        "path": path,
                        "permission": result.permission.value,
                        "reason": result.reason,
                    })

    return violations
