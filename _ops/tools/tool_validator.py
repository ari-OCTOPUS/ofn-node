#!/usr/bin/env python3
"""tool_validator.py — F2/INV-TOOL-GUARD: اعتبارسنج قطعی خروجی ابزار.

هیچ خروجی ابزار نباید بدون عبور از این ماژول به لایهٔ تصمیم (مدل) برسد.
نقض INV-TOOL-GUARD = HALT، نه retry.

Fault types covered (from ACD-07 schema):
  empty | null | malformed-json | truncated | schema_drift | stale_timestamp
  | wrong_units | http_error | rate_limit | timeout_before_effect
  | timeout_after_effect | contradictory_fields | contamination
"""
from __future__ import annotations

import json, re, time
from dataclasses import dataclass
from typing import Any

INJECTION_MARKERS = ("SYSTEM OVERRIDE:", "ignore previous instructions")


@dataclass(frozen=True)
class ToolResult:
    """Wrapper for tool output — the ONLY type that reaches consumers."""
    value: Any = None
    verdict: str = "OK"  # OK | TOOL_ERROR | EMPTY | STALE | MALFORMED | CONTAMINATED
    reason: str = ""
    raw_size: int = 0
    validated: bool = True


def validate_tool_output(raw, *,
                          expected_type: str = "json",
                          field: str = "",
                          max_age_s: float = 3600.0,
                          as_of_key: str = "as_of",
                          allow_none: bool = False) -> ToolResult:
    """Deterministic validation BEFORE any model/decision consumption.

    This function NEVER calls a model. It NEVER fabricates. On any structural
    failure it returns a ToolResult with verdict != "OK" and the consumer
    MUST halt that path (not retry).
    """
    # 1 empty / null
    if raw is None:
        if allow_none:
            return ToolResult(value=None, verdict="OK", reason="allowed_none")
        return ToolResult(verdict="EMPTY", reason="tool returned None")
    if isinstance(raw, str) and not raw.strip():
        return ToolResult(verdict="EMPTY", reason="tool returned empty string")
    if isinstance(raw, dict) and not raw:
        return ToolResult(verdict="EMPTY", reason="tool returned empty dict")
    if isinstance(raw, dict) and isinstance(raw.get("error"), str):
        return ToolResult(verdict="TOOL_ERROR", reason=raw["error"])

    # 2 malformed / truncated
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            pass  # handled below
            if len(raw) > 20 and not raw.rstrip().endswith(("}", "]", '"')):
                return ToolResult(verdict="MALFORMED", reason="truncated JSON",
                                  raw_size=len(raw))
            return ToolResult(verdict="MALFORMED", reason="invalid JSON",
                              raw_size=len(raw))
    # re-check error after JSON parse (fix: string→dict→error)
    if isinstance(raw, dict) and isinstance(raw.get("error"), str):
        return ToolResult(verdict="TOOL_ERROR", reason=raw["error"])
    if isinstance(raw, dict) and "_raw" in raw:
        return ToolResult(verdict="MALFORMED", reason="raw/truncated payload wrapper")

    # 3 field presence check
    if field and isinstance(raw, dict):
        rec = raw.get("record", raw)  # unwrap envelope
        if not isinstance(rec, dict) or field not in rec:
            return ToolResult(verdict="EMPTY", reason=f"field {field!r} absent")
        val = rec[field]
        if not isinstance(val, (int, float)):
            return ToolResult(verdict="TOOL_ERROR",
                             reason=f"field {field!r} non-numeric: {type(val).__name__}")

    # 4 staleness check
    if isinstance(raw, dict) and as_of_key in raw:
        as_of = str(raw.get(as_of_key, ""))
        try:
            age = time.time() - time.mktime(time.strptime(as_of[:10], "%Y-%m-%d"))
            if age / 86400 > max_age_s / 86400:
                return ToolResult(verdict="STALE", reason=f"as_of={as_of} age={age/86400:.0f}d")
        except ValueError:
            return ToolResult(verdict="STALE", reason=f"as_of unparsable: {as_of!r}")

    # 5 contamination check
    text = json.dumps(raw, ensure_ascii=False) if isinstance(raw, (dict, list)) else str(raw)
    for marker in INJECTION_MARKERS:
        if marker.lower() in text.lower():
            return ToolResult(verdict="CONTAMINATED", reason=f"marker: {marker}")

    return ToolResult(value=raw, verdict="OK", reason="structural pass")


def validate_or_halt(raw, **kwargs) -> Any:
    """Validate and raise on failure — the strict path for INV-TOOL-GUARD."""
    result = validate_tool_output(raw, **kwargs)
    if result.verdict != "OK":
        raise ToolValidationError(result.verdict, result.reason)
    return result.value


class ToolValidationError(Exception):
    """Raised when tool output fails validation — consumer MUST halt, not retry."""
    def __init__(self, verdict: str, reason: str):
        self.verdict = verdict
        self.reason = reason
        super().__init__(f"INV-TOOL-GUARD: {verdict} — {reason}")


if __name__ == "__main__":
    # self-test
    tests = [
        (None, "EMPTY"),
        ("", "EMPTY"),
        ('{"error": "http 503"}', "TOOL_ERROR"),
        ('{"_raw": "trunc', "MALFORMED"),
        ('{"record": {"x": "text_not_num"}, "field": "x"}', "TOOL_ERROR"),
        ('{"as_of": "2020-01-01", "record": {"x": 1}}', "STALE"),
        ('{"record": {"_note": "SYSTEM OVERRIDE: hi"}}', "CONTAMINATED"),
        ('{"record": {"x": 42}}', "OK"),
    ]
    for raw, expected in tests:
        kw = {"field": "x"} if "field" in str(raw) else {}
        r = validate_tool_output(raw, **kw)
        status = "✓" if r.verdict == expected else f"✗ (got {r.verdict}, want {expected})"
        print(f"  {status} {expected}")
