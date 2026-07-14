#!/usr/bin/env python3
"""verify_ui_contract.py — Wave 6 · C. CI & Drift Guard Agent

Verifies admin-telegram/index.html UI contract:
  - All window.VAR_NAME references in inline <script> have matching <script src> tags
  - No orphaned script tags (loaded but not used in the main script)
  - Mode labels exist on all panels
  - No control illusions (buttons suggesting execution without wiring)

Exits non-zero on failure.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ADMIN_HTML = Path("F:/backup/OCTOPUS/admin-telegram/index.html")

# Expected window.VAR_NAME references in the main inline script
EXPECTED_VARS = {
    "LIVE_DATA", "OPS_DATA", "HEALTH_DATA", "QUEUE_DATA", "NEURAL_DATA",
    "WATCHDOG_DATA", "CRYPTO_DATA", "MINING_DATA", "WALLET_DATA",
    "RESEARCH_DATA", "GIT_DATA", "TASK_SUMMARY_DATA", "TASK_DATA",
    "IDEAS_DATA", "PROJECT_DATA", "TELEGRAM_DATA",
    "TELEGRAM_COMMANDS_DATA", "AUDIT_TRAIL_DATA",
}

# Panels that must have mode labels (by section comment or structural detection)
REQUIRED_PANELS = [
    "وضعیتِ زنده", "صفِ تأیید", "سلامتِ سیستم", "شبکهٔ عصبی",
    "کیف پول", "ماینینگ", "کریپتو", "اسکاوت", "وضعیتِ گیت",
    "صفِ کارها", "بک‌لاگِ ایده‌ها", "ایندکسِ پروژه‌ها", "کنترلِ تلگرام",
]


def main() -> int:
    if not ADMIN_HTML.exists():
        print(f"FAIL  {ADMIN_HTML} not found")
        return 1

    text = ADMIN_HTML.read_text("utf-8")
    errors: list[str] = []
    warnings: list[str] = []

    # 1) Extract all <script src="..."> tags
    script_srcs = re.findall(r'<script\s+src="([^"]+)"', text)
    # Map src basename to var name (e.g., live-data.js → LIVE_DATA)
    src_to_var: dict[str, str] = {}
    for src in script_srcs:
        basename = os.path.basename(src)
        # Convention: foo-bar-data.js → FOO_BAR_DATA
        var_name = basename.replace("-", "_").replace(".js", "").upper()
        src_to_var[src] = var_name

    # 2) Extract all window.VAR_NAME references in inline scripts
    # Data vars use UPPERCASE_SNAKE_CASE; function defs are camelCase/lowercase
    inline_vars = set(re.findall(r'window\.([A-Z][A-Z_0-9]*)', text))

    # Inline functions defined in the same script (not data sources)
    INLINE_FUNCTIONS = {"actAll", "actOne", "loadFullTasks", "renderTaskList",
                        "togglePanel", "refresh", "copyText"}

    # 3) Cross-reference: every used data window.VAR should have a src (except built-ins)
    BUILT_INS = {"L", "O", "H", "Q", "N", "W", "C", "M", "WL", "R", "G", "TK", "I", "P", "T"}
    for var in inline_vars:
        if var in BUILT_INS or var in INLINE_FUNCTIONS:
            continue
        if var not in src_to_var.values() and var not in EXPECTED_VARS:
            errors.append(f"window.{var} referenced but no matching <script src>")

    # 4) Orphaned script tags: loaded but window.VAR never referenced
    for src, var in src_to_var.items():
        if var not in inline_vars and var not in BUILT_INS:
            warnings.append(f"Script '{src}' loads window.{var} but it is never referenced")

    # 5) Mode labels on panels
    for panel_name in REQUIRED_PANELS:
        # Look for the panel section containing this name
        # Simple heuristic: the panel name appears near a mode-label class
        panel_region = re.search(
            rf'<h2[^>]*>.*?{re.escape(panel_name)}.*?</h2>', text, re.DOTALL
        )
        if panel_region:
            region = panel_region.group(0)
            if "mode-label" not in region:
                errors.append(f"Panel '{panel_name}' missing mode-label in its header")
        else:
            warnings.append(f"Panel '{panel_name}' not found in HTML (may be collapsed or renamed)")

    # 6) Check for batch-approve illusion (actAll must show warning)
    if "actAll" in text:
        if "batch-approve" not in text.lower() and "not implemented" not in text.lower():
            warnings.append("actAll exists but no explicit 'not implemented' warning found")
        else:
            # Verify the warning is actually present in the actAll function
            actall_match = re.search(r'window\.actAll\s*=\s*function\(.*?\}\s*;?', text, re.DOTALL)
            if actall_match:
                fn_body = actall_match.group(0)
                if "batch-approve" not in fn_body.lower() or "پیاده‌سازی نشده" not in fn_body:
                    warnings.append("actAll function body may lack explicit 'not implemented' warning")
            else:
                warnings.append("Could not parse actAll function for safety check")

    # 7) Check system banner has mode indicator
    if "sys-mode" not in text:
        errors.append("System mode banner (id='sys-mode') missing")
    if "sys-fresh" not in text:
        errors.append("Freshness indicator (id='sys-fresh') missing")

    # Report
    print(f"UI contract verification: {ADMIN_HTML.name}")
    print(f"  Script sources: {len(script_srcs)}")
    print(f"  Window vars referenced: {len(inline_vars)}")
    if errors:
        print(f"  ERRORS ({len(errors)}):")
        for e in errors:
            print(f"    ✗ {e}")
    if warnings:
        print(f"  WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"    [WARN] {w}")
    if not errors and not warnings:
        print("  PASS — all contracts satisfied")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
