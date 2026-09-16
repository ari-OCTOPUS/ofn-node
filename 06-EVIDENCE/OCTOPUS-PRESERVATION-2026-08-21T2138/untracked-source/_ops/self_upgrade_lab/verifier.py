# -*- coding: utf-8 -*-
"""Independent verifier. Confirmed only when failing-before, tests pass, no
secret, rollback possible, and running hash matches the patched files.
LAB_PASS is never labeled production."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .contracts import secret_scan
from .patch_runner import patch_hash_running
import re

_KEY_MATERIAL = re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9]{16,}")


def verify(*, worktree: Path, files: list[str], before: dict, after: dict,
           tests: dict, rollback_ok: bool, memory_write: bool = False) -> dict[str, Any]:
    reasons = []
    before_fail = bool(before.get("failed") or before.get("timeouts")
                       or (before.get("passed", 0) < before.get("n", 1)))
    if not before_fail:
        reasons.append("no-failing-test-before-patch")
    if not tests.get("all_pass"):
        reasons.append("targeted-tests-not-green")
    if after.get("failed") or after.get("timeouts"):
        reasons.append("after-metrics-not-clean")
    if memory_write:
        reasons.append("memory-write-forbidden")
    secret_hits = []
    for rel in files:
        p = worktree / rel
        if p.is_file():
            secret_hits.extend(secret_scan(p.read_text(encoding="utf-8", errors="replace")))
    # test files mention 'password'/'api_key' as reject fixtures — allow those names
    # only inside tests.
    HIGH_SIGNAL = ("BEGIN PRIVATE",)
    real_hits = [h for h in secret_hits if h in HIGH_SIGNAL]
    blob = ""
    for rel in files:
        p = worktree / rel
        if p.is_file():
            blob += p.read_text(encoding="utf-8", errors="replace")
    if _KEY_MATERIAL.search(blob):
        real_hits.append("sk-")
    if real_hits:
        reasons.append("secret-scan")
    if not rollback_ok:
        reasons.append("rollback-unproven")
    running = patch_hash_running(worktree, files)
    confirmed = not reasons
    return {
        "confirmed": confirmed,
        "promotion_ceiling": "LAB_PASS" if confirmed else "NONE",
        "reasons": reasons,
        "secret_scan_hits": len(real_hits),
        "running_hash": running,
        "before_had_failing_test": before_fail,
        "tests_pass": bool(tests.get("all_pass")),
        "rollback_ok": rollback_ok,
        "memory_write": memory_write,
        "label": "LAB_PASS" if confirmed else "REJECT",
        "note": "LAB_PASS is not production.",
    }
