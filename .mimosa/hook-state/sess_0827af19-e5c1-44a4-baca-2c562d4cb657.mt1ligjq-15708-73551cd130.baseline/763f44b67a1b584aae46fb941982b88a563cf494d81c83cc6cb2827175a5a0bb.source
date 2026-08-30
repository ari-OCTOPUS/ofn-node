#!/usr/bin/env python3
"""verify_schema.py — Wave 6 · C. CI & Drift Guard Agent

CI-grade script that verifies all extractor JS outputs match their schema contracts.
Checks:
  - Each JS file starts with window.VAR_NAME = and ends with ;
  - JSON is parseable
  - Required keys exist per schema contract
  - No NaN, no undefined, no null where numeric expected
  - File sizes within budget

Exits non-zero on failure (for CI integration).
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
from pathlib import Path

NS_DIR = Path("F:/backup/nervous-system")

# Schema contracts: (required_keys_tuple, numeric_paths_set, max_size_bytes)
# Paths use dot notation; * means any key in that dict level
SCHEMAS: dict[str, tuple[tuple, set[str], int]] = {
    "live-data.js": (
        ("generated", "sog", "budget", "daemon", "events"),
        {"sog.identity_now", "sog.drift_now", "budget.cap", "budget.remaining", "events.total_rows", "daemon.total_ticks"},
        2_000_000,  # 2MB
    ),
    "ops-data.js": (
        ("generated",),
        set(),
        500_000,
    ),
    "health-data.js": (
        ("overall", "subscores.system", "subscores.fitness", "subscores.telemetry"),
        {"overall", "subscores.system", "subscores.fitness", "subscores.telemetry"},
        500_000,
    ),
    "queue-data.js": (
        ("queue.items", "queue.counts"),
        {"queue.counts.pending", "queue.counts.approved", "queue.counts.rejected", "queue.counts.high_priority", "queue.counts.money_at_risk"},
        500_000,
    ),
    "crypto-data.js": (
        ("composite.score", "project.security_gate"),
        {"composite.score"},
        1_000_000,
    ),
    "mining-data.js": (
        ("readiness.score", "fleet.nodes_running"),
        {"readiness.score", "fleet.nodes_running", "fleet.nodes_total"},
        1_000_000,
    ),
    "wallet-data.js": (
        ("gate.security_gate", "portfolio.positions"),
        {"portfolio.position_count", "portfolio.approved_count", "budget.remaining", "budget.daily_cap", "budget.spent"},
        500_000,
    ),
    "research-data.js": (
        ("pipeline.total_digests", "fleet.active_scouts"),
        {"pipeline.total_digests", "fleet.active_scouts", "fleet.stale_scouts", "health.score"},
        1_000_000,
    ),
    "git-data.js": (
        ("repos",),
        {"repos[].branch", "repos[].dirty_files"},
        500_000,
    ),
    "task-summary-data.js": (
        ("summary.open_tasks", "summary.by_priority"),
        {"summary.open_tasks", "summary.done_tasks", "summary.total_tasks", "summary.completion_rate"},
        5_000,
    ),
    "task-data.js": (
        ("open_tasks",),
        set(),
        1_000_000,
    ),
    "ideas-data.js": (
        ("summary.total_ideas", "backlog.ready_to_build"),
        {"summary.total_ideas", "summary.ready_to_build_count", "summary.avg_strategic_score"},
        500_000,
    ),
    "project-data.js": (
        ("summary.total_projects", "projects"),
        {"summary.total_projects", "summary.active", "summary.stalled", "summary.average_health"},
        500_000,
    ),
    "telegram-data.js": (
        ("channel.live", "health.score"),
        {"health.score", "poll.last_offset", "poll.poll_batch", "approvals.total"},
        500_000,
    ),
    "telegram-commands-data.js": (
        ("commands",),
        set(),
        100_000,
    ),
    "audit-trail-data.js": (
        ("stats", "stats.total_actions", "recent_actions", "freshness"),
        {"stats.success_rate", "stats.total_actions", "stats.dry_run_ratio", "stats.live_ratio"},
        500_000,
    ),
    "neural-data.js": (
        ("rhythm",),
        {"rhythm.T_beat", "circadian.readiness"},
        500_000,
    ),
    "watchdog-data.js": (
        ("alerts",),
        set(),
        500_000,
    ),
    "graph-data.js": (
        ("nodes", "edges"),
        set(),
        2_000_000,
    ),
}


def _extract_json_from_js(path: Path) -> tuple[dict | None, list[str]]:
    """Parse a JS data file: window.VAR = { ... }; → extract JSON."""
    errors: list[str] = []
    try:
        text = path.read_text("utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return None, [f"Cannot read file: {e}"]

    # Must start with window.VAR_NAME =
    if not re.match(r'^\s*window\.\w+\s*=\s*', text):
        errors.append("Does not start with 'window.VAR_NAME = '")
        return None, errors

    # Must end with semicolon (allowing trailing whitespace)
    if not re.search(r';\s*$', text):
        errors.append("Does not end with ';'")
        return None, errors

    # Extract the JSON payload
    # Find the first '{' or '[' after '='
    m = re.search(r'=\s*([{\[])', text)
    if not m:
        errors.append("No JSON object/array found after '='")
        return None, errors

    start_char = m.group(1)
    start_idx = m.start(1)

    # Simple brace counting to find the matching end
    brace = 1 if start_char == '{' else 1  # same logic for [] really, but we track both
    stack = [start_char]
    i = start_idx + 1
    in_string = False
    escape = False

    while i < len(text) and stack:
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == '{':
                stack.append('{')
            elif ch == '[':
                stack.append('[')
            elif ch == '}':
                if stack and stack[-1] == '{':
                    stack.pop()
                else:
                    errors.append("Mismatched brace '}'")
                    return None, errors
            elif ch == ']':
                if stack and stack[-1] == '[':
                    stack.pop()
                else:
                    errors.append("Mismatched bracket ']'")
                    return None, errors
        i += 1

    if stack:
        errors.append("Unclosed braces/brackets")
        return None, errors

    json_str = text[start_idx:i]
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        errors.append(f"JSON parse error: {e}")
        return None, errors

    return data, errors


def _get_path(data, path: str):
    """Navigate dot-path in nested dicts/lists. Returns (value, ok)."""
    parts = path.split(".")
    current = data
    for p in parts:
        if p.endswith("[]"):
            # Wildcard: check all items in list
            key = p[:-2]
            if isinstance(current, dict):
                current = current.get(key)
            if not isinstance(current, list):
                return None, False
            # For wildcard, we just check the first element exists
            if not current:
                return None, False
            current = current[0]
        else:
            if isinstance(current, dict):
                if p not in current:
                    return None, False
                current = current[p]
            else:
                return None, False
    return current, True


def _check_numeric_clean(data, numeric_paths: set[str]) -> list[str]:
    """Ensure numeric paths have no NaN, undefined, null."""
    errors: list[str] = []
    for path in numeric_paths:
        val, ok = _get_path(data, path)
        if not ok:
            continue  # missing key caught elsewhere
        if val is None:
            errors.append(f"Path '{path}' is null")
        elif isinstance(val, float) and math.isnan(val):
            errors.append(f"Path '{path}' is NaN")
        elif isinstance(val, float) and math.isinf(val):
            errors.append(f"Path '{path}' is Inf")
        elif isinstance(val, str) and val.lower() in ("nan", "undefined", "null", "inf", "infinity"):
            errors.append(f"Path '{path}' has string sentinel '{val}'")
    return errors


def verify_file(name: str) -> list[str]:
    errors: list[str] = []
    path = NS_DIR / name
    if not path.exists():
        errors.append(f"File does not exist")
        return errors

    contract = SCHEMAS.get(name)
    if not contract:
        errors.append("No schema contract defined")
        return errors

    required_keys, numeric_paths, max_size = contract

    # Size check
    size = path.stat().st_size
    if size > max_size:
        errors.append(f"Size {size} bytes exceeds budget {max_size}")

    # Parse
    data, parse_errors = _extract_json_from_js(path)
    errors.extend(parse_errors)
    if data is None:
        return errors

    # Required keys
    for key_path in required_keys:
        _, ok = _get_path(data, key_path)
        if not ok:
            errors.append(f"Missing required key '{key_path}'")

    # Numeric cleanliness
    errors.extend(_check_numeric_clean(data, numeric_paths))

    return errors


def main() -> int:
    os.makedirs(NS_DIR, exist_ok=True)
    all_ok = True
    results: dict[str, list[str]] = {}

    for name in sorted(SCHEMAS.keys()):
        errs = verify_file(name)
        results[name] = errs
        if errs:
            all_ok = False
            print(f"FAIL  {name}: {len(errs)} issue(s)")
            for e in errs[:3]:
                print(f"       -> {e}")
            if len(errs) > 3:
                print(f"       ... and {len(errs)-3} more")
        else:
            size = (NS_DIR / name).stat().st_size
            print(f"PASS  {name} ({size} bytes)")

    summary = {
        "overall": "PASS" if all_ok else "FAIL",
        "files_checked": len(SCHEMAS),
        "files_passed": sum(1 for v in results.values() if not v),
        "files_failed": sum(1 for v in results.values() if v),
    }
    print(f"\nSchema verification: {summary['files_passed']}/{summary['files_checked']} passed")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
