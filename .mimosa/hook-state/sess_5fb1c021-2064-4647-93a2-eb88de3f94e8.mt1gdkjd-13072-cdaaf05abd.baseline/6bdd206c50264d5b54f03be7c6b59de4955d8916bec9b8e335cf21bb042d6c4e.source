#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""security-checklist.py — scan codebase for hardcoded secrets and unsafe defaults.

Scans:
  • .py files for token/password/api-key patterns
  • .js files for leaked secrets
  • .md files for accidental token inclusion

Skips:
  • .env files (by name)
  • node_modules, __pycache__, .git, _Archive, _Duplicates, 4d_system outputs
  • Files > 5MB (binary guard)

Emits: nervous-system/security-scan-report.json
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("F:/backup")
NS_DIR = Path("F:/backup/nervous-system")
REPORT_PATH = NS_DIR / "security-scan-report.json"

# Max file size to scan (bytes)
MAX_SIZE = 5 * 1024 * 1024

SKIP_DIRS = frozenset({
    ".git", "__pycache__", ".pytest_cache", "node_modules",
    ".obsidian", ".streamlit", ".venv", "venv",
    "_Archive", "_Duplicates", "broken-dot-git",
})
SKIP_PATH_FRAGMENTS = frozenset({
    "4d_system/outputs", "4d_system/.streamlit", "4d_system/agents",
    "app/node_modules", "app/.git", "app/dist", "app/build",
    "CHRONOS-FABLE-OS/_legacy",
})
SKIP_FILES = frozenset({".env", ".env.local", ".env.production"})

# Patterns: (name, regex, confidence)
PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("telegram_bot_token", re.compile(r'\d{9,10}:[A-Za-z0-9_-]{35}'), "high"),
    ("openai_api_key", re.compile(r'sk-[a-zA-Z0-9]{20,}'), "high"),
    ("github_pat", re.compile(r'ghp_[a-zA-Z0-9]{36}'), "high"),
    ("generic_api_key", re.compile(r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\'][^"\']{16,}["\']'), "medium"),
    ("generic_token", re.compile(r'(?i)(bot[_-]?token|auth[_-]?token|access[_-]?token)\s*[:=]\s*["\'][^"\']{16,}["\']'), "medium"),
    ("password_assignment", re.compile(r'(?i)password\s*[:=]\s*["\'][^"\']{8,}["\']'), "medium"),
    ("secret_assignment", re.compile(r'(?i)secret\s*[:=]\s*["\'][^"\']{8,}["\']'), "medium"),
]

# Unsafe default patterns
UNSAFE_DEFAULTS: list[tuple[str, re.Pattern[str], str]] = [
    ("default_true_gate", re.compile(r'(?i)default\s*=\s*True.*gate'), "medium"),
    ("default_open_approval", re.compile(r'(?i)default.*approve.*=\s*True'), "high"),
    ("batch_approve_unconditional", re.compile(r'(?i)def\s+actAll.*approve'), "medium"),
]


def _should_scan(path: Path) -> bool:
    if path.name.startswith(".") and path.suffix == ".env":
        return False
    if path.name in SKIP_FILES:
        return False
    sp = str(path).replace("\\", "/")
    for frag in SKIP_PATH_FRAGMENTS:
        if frag in sp:
            return False
    for part in path.parts:
        if part in SKIP_DIRS:
            return False
    # Skip generated extractor outputs (false-positive prone)
    if "nervous-system/" in sp and path.name.endswith("-data.js"):
        return False
    try:
        if path.stat().st_size > MAX_SIZE:
            return False
    except OSError:
        return False
    return True


def scan_file(path: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    try:
        text = path.read_text("utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return findings
    lines = text.splitlines()

    for name, pattern, confidence in PATTERNS:
        for lineno, line in enumerate(lines, 1):
            if pattern.search(line):
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith("//"):
                    confidence = "low"
                findings.append({
                    "file": str(path),
                    "line": lineno,
                    "type": name,
                    "confidence": confidence,
                    "context": stripped[:120],
                })

    # Unsafe defaults only in Python code (not JS data files or markdown)
    if path.suffix == ".py":
        for name, pattern, severity in UNSAFE_DEFAULTS:
            for lineno, line in enumerate(lines, 1):
                if pattern.search(line):
                    findings.append({
                        "file": str(path),
                        "line": lineno,
                        "type": name,
                        "confidence": severity,
                        "category": "unsafe_default",
                        "context": line.strip()[:120],
                    })

    return findings


def main() -> int:
    os.makedirs(NS_DIR, exist_ok=True)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    all_findings: list[dict[str, Any]] = []
    files_scanned = 0

    # Targeted scan: only directories likely to contain code
    scan_roots = [
        ROOT / "_ops",
        ROOT / "OCTOPUS",
        ROOT / "nervous-system",
        ROOT / "agent-prompts",
        ROOT / "app" / "src",
        ROOT / "app" / "tests",
    ]
    # Also scan specific file types in root-level folders
    for ext in (".py", ".js", ".md"):
        for scan_root in scan_roots:
            if not scan_root.exists():
                continue
            for path in scan_root.rglob(f"*{ext}"):
                if not _should_scan(path):
                    continue
                files_scanned += 1
                findings = scan_file(path)
                all_findings.extend(findings)

    # Severity summary
    by_confidence: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for f in all_findings:
        c = f.get("confidence", "unknown")
        by_confidence[c] = by_confidence.get(c, 0) + 1
        t = f.get("type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1

    report = {
        "generated": generated,
        "scanner": "security-checklist.py",
        "files_scanned": files_scanned,
        "findings_count": len(all_findings),
        "by_confidence": by_confidence,
        "by_type": by_type,
        "findings": all_findings,
        "safe": len(all_findings) == 0,
    }

    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"security-scan-report.json: {len(all_findings)} findings from {files_scanned} files -> {REPORT_PATH}")
    return 0 if len(all_findings) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
