#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_live4_preflight — پرفلایت غیرزندهٔ LIVE-4 (pytest استاندارد؛ صفر شبکه)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

_H = Path(__file__).resolve().parent
sys.path.insert(0, str(_H))
import live4_harness as H  # noqa: E402


def _fx(**over):
    base = {"fx_source_id": "owner-daily-x", "fx_timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "fx_rate_usd_to_aud": 1.50, "owner_pin_id": "FX-PIN-20260819-01"}
    forced_hash = over.pop("fx_hash", None)
    base.update(over)
    base["fx_hash"] = forced_hash or H.fx_canonical_hash(base)
    return base


def test_fx_valid_passes():
    r = H.validate_fx(_fx())
    assert r["pass"] and r["paid_fallback"] == "ALLOWED" and abs(r["rate"] - 1.5) < 1e-9


def test_fx_expired_blocked():
    old = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat(timespec="seconds")
    r = H.validate_fx(_fx(fx_timestamp_utc=old))
    assert not r["pass"] and "expired" in r["reason"] and r["paid_fallback"] == "BLOCKED"


def test_fx_malformed_or_missing_blocked():
    assert not H.validate_fx({})["pass"]
    assert not H.validate_fx(_fx(fx_rate_usd_to_aud="abc"))["pass"]
    assert not H.validate_fx(_fx(extra=None, fx_hash="deadbeef"))["pass"]


def test_fx_template_absent_blocks():
    r = H.load_fx(_H / "FX-RECORD-ABSENT.json")
    assert not r["pass"] and r["paid_fallback"] == "BLOCKED"


def test_blind_pair_deterministic_and_randomized():
    a = H.blind_pair("base-text", "cond-text", seed=1)
    b = H.blind_pair("base-text", "cond-text", seed=1)
    assert a == b  # قطعی با seed
    pos = {H.blind_pair("x", "y", seed=s)["cond_position"] for s in range(40)}
    assert pos == {"A", "B"}  # تصادفی‌سازی واقعی
    assert a["baseline_sha"] != a["conditioned_sha"]


def test_parse_judge_blind_mapping():
    assert H.parse_judge("A", "A") == "conditioned"
    assert H.parse_judge("B", "A") == "baseline"
    assert H.parse_judge("نمی‌دانم", "A") is None


def test_eligibility_and_system_confidence_exclusion():
    good = {"provenance_json": '{"source":"llm"}', "created_at": "t", "confidence": "0.8", "valid_to": "t"}
    sysrow = {"provenance_json": '{"confidence_source":"SYSTEM_DETERMINISTIC_RULE"}',
              "created_at": "t", "confidence": "0.9", "valid_to": "t"}
    bad = {"provenance_json": "p", "created_at": "t", "confidence": "", "valid_to": "t"}
    rep = H.coverage_report([good, sysrow, bad])
    assert rep["eligible"] == 2 and rep["ineligible"] == 1
    assert rep["llm_confidence_rows"] == 1
    ok, why = H.row_eligible(sysrow)
    assert ok and "excluded-from-llm" in why


def test_synthetic_smoke_receipt_no_network():
    r = H.synthetic_smoke_receipt()
    assert r["kind"] == "SYNTHETIC_PREFLIGHT_SMOKE" and r["fx"]["paid_fallback"] in ("ALLOWED", "BLOCKED")
