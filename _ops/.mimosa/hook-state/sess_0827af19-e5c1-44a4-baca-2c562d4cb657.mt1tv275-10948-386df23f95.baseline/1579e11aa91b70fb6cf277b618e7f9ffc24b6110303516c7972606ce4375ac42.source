#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""coding_sandbox -- Safe Autonomous Coding Capability (EQUIP G4).

Provides a sandboxed environment where coding agents can make changes in
isolated git worktrees with filesystem jails, command allowlists, and
mandatory approval for protected paths.

Modules:
  - sandbox: Core CodingSandbox lifecycle (worktree, branch, commit)
  - filesystem_jail: Path validation, symlink detection
  - command_runner: Shell command execution with allowlist + timeout
  - patch_validator: Diff validation (size, reversibility, format)
  - protected_paths: Protected path definitions (deny-by-default)
  - test_runner: Test execution with no-skip enforcement

Integrates with:
  - G1 TaskOrchestrator (task lifecycle)
  - G7 PolicyEnforcer (PEP for protected paths)
  - G8 RiskGate (risk classification, budget, kill switch)

$0 | stdlib-only | no network | no LLM.
"""
from __future__ import annotations

SCHEMA = "coding-sandbox.v1"
VERSION = "1.0.0"
