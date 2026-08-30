#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""research_contract.py — C6: قراردادِ مأموریتِ پژوهش (immutable، فالسیفای‌پذیر).

هیچ پژوهشی بدونِ این قرارداد اجرا نمی‌شود. قرارداد **پیش از اجرا** falsification_criteria و
stop_condition و budget را تثبیت می‌کند تا حلقه نتواند تا بی‌نهایت بازنویسی کند یا هدف را جابه‌جا
کند (goal-drift). id = hashِ محتوا → immutable و قابلِ‌ردیابی در research ledger.

فیلدهای اجباری (مأموریت C6 step 1): question, hypothesis, budget, tools, stop_condition,
verifier, expected_artifact, falsification_criteria.
"""
from __future__ import annotations

import hashlib
import json
import time

_ALLOWED_TOOLS = frozenset({
    "measure_capabilities", "reproduce_failures", "propose_candidates",
    "test_in_sandbox", "compare_frozen_baselines", "request_owner_review"})  # = SELF_IMPROVEMENT_ALLOWED


class ResearchContractError(ValueError):
    pass


def _canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def validate(spec: dict) -> dict:
    """قراردادِ ورودی را اعتبارسنجی و نرمال کن؛ نقضِ قید → ResearchContractError.
    hard-fail اگر ابزارِ غیرمجاز (خارج از constitutional ALLOWED) بخواهد (fail-closed)."""
    if not isinstance(spec, dict):
        raise ResearchContractError("contract must be a dict")
    req = ("question", "hypothesis", "stop_condition", "verifier",
           "expected_artifact", "falsification_criteria")
    for k in req:
        v = spec.get(k)
        if not (isinstance(v, str) and v.strip()) and not (isinstance(v, (list, dict)) and v):
            raise ResearchContractError(f"missing/empty required field: {k!r}")

    budget = spec.get("budget") or {}
    if not isinstance(budget, dict):
        raise ResearchContractError("budget must be a dict")
    norm_budget = {
        "cost_aud": float(budget.get("cost_aud", 0.0)),
        "time_s": float(budget.get("time_s", 0.0)),
        "tokens": int(budget.get("tokens", 0)),
        "max_experiments": int(budget.get("max_experiments", 20)),
    }
    if norm_budget["max_experiments"] <= 0:
        raise ResearchContractError("budget.max_experiments must be > 0 (bounded)")

    tools = spec.get("tools") or []
    if not isinstance(tools, list) or not tools:
        raise ResearchContractError("tools must be a non-empty list")
    bad = [t for t in tools if t not in _ALLOWED_TOOLS]
    if bad:
        # fail-closed: پژوهش نمی‌تواند ابزارِ خارج از constitutional-allowed بخواهد
        raise ResearchContractError(f"forbidden/unknown tools (fail-closed): {bad}")

    fc = spec.get("falsification_criteria")
    fc = [str(x) for x in fc] if isinstance(fc, list) else [str(fc)]
    if not any(s.strip() for s in fc):
        raise ResearchContractError("falsification_criteria required — a hypothesis that can't be "
                                    "falsified is not research")

    norm = {
        "schema": "research-contract.v1",
        "question": str(spec["question"])[:500],
        "hypothesis": str(spec["hypothesis"])[:500],
        "budget": norm_budget,
        "tools": sorted(set(tools)),
        "stop_condition": str(spec["stop_condition"])[:300],
        "verifier": str(spec["verifier"])[:200],
        "expected_artifact": str(spec["expected_artifact"])[:200],
        "falsification_criteria": fc,
        "created_at_hint": str(spec.get("created_at") or ""),   # ساعت را caller می‌دهد (تعیین‌پذیری)
    }
    return norm


def contract_id(norm: dict) -> str:
    return "rc_" + hashlib.sha256(_canon(
        {k: norm[k] for k in ("question", "hypothesis", "falsification_criteria",
                              "stop_condition", "verifier")}).encode("utf-8")).hexdigest()[:16]


def make_contract(spec: dict) -> dict:
    """قراردادِ نرمال + immutable با id. (caller `created_at` می‌دهد یا زمانِ الان استفاده می‌شود.)"""
    norm = validate(spec)
    if not norm["created_at_hint"]:
        norm["created_at_hint"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    norm["contract_id"] = contract_id(norm)
    return norm
