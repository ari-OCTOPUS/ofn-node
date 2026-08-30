#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_cost_receipt_costobs1 — ۹ پذیرش الزامی COST-OBS-1 (pytest استاندارد، بدون فراخوانی live)."""
import json, sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "cortex"))
from cost_receipt import CostReceiptAdapter, PricingTable

def _fx(tmp_path, with_fx=True):
    d = {"fx_usd_to_aud": 1.52 if with_fx else None,
         "models": {"deepseek-real": {"in_per_1m": 0.27, "out_per_1m": 1.10},
                    "test-model": {"TEST_ONLY": True, "in_per_1m": 1.0, "out_per_1m": 2.0}}}
    p = tmp_path / "pricing.json"; p.write_text(json.dumps(d), encoding="utf-8")
    return PricingTable(p)

def _kw(**over):
    k = dict(trace_id="t-1", provider="deepseek", model="deepseek-real",
             ts_req="2026-08-19T00:00:00Z", ts_resp="2026-08-19T00:00:05Z",
             budget_before_aud=12.0, input_sha256="aa")
    k.update(over); return k

def test_1_reported_complete(tmp_path):
    a = CostReceiptAdapter(_fx(tmp_path))
    r = a.build(**_kw(), usage_payload={"cost_usd": 0.012, "prompt_tokens": 900, "completion_tokens": 100})
    assert r["receipt_status"] == "COMPLETE" and r["cost_method"] == "REPORTED"
    assert abs(r["estimated_or_reported_cost_aud"] - 0.012*1.52) < 1e-9
    assert r["budget_after_aud"] < r["budget_before_aud"]

def test_2_deterministic_estimate(tmp_path):
    a = CostReceiptAdapter(_fx(tmp_path))
    r = a.build(**_kw(), tokens_in=1_000_000, tokens_out=1_000_000)
    assert r["cost_method"] == "DETERMINISTIC_ESTIMATE" and r["receipt_status"] == "COMPLETE"
    assert r["pricing_version"] == a.pricing.sha256[:12]

def test_3_unobservable_blocks_next_paid(tmp_path):
    a = CostReceiptAdapter(_fx(tmp_path))
    r = a.build(**_kw())
    assert r["receipt_status"] == "COST_UNOBSERVABLE" and r["cost_method"] == "UNOBSERVABLE"
    assert a.paid_blocked is True

def test_4_unknown_model_or_unpinned(tmp_path):
    a = CostReceiptAdapter(_fx(tmp_path))
    r1 = a.build(**_kw(model="mystery"), tokens_in=10, tokens_out=10)
    assert r1["receipt_status"] == "COST_UNOBSERVABLE"
    a2 = CostReceiptAdapter(_fx(tmp_path, with_fx=False))
    r2 = a2.build(**_kw(usage_payload={"cost_usd": 0.01}))
    assert r2["receipt_status"] == "COST_UNOBSERVABLE" and "fx" in r2["note"]

def test_5_budget_atomic_caps(tmp_path):
    a = CostReceiptAdapter(_fx(tmp_path), per_call_cap_aud=0.50, hard_stop_aud=12.0)
    r = a.build(**_kw(), tokens_in=100_000_000, tokens_out=100_000_000)  # هزینه >> cap
    assert r.get("cap_violation") == "PER_CALL_CAP_EXCEEDED" and a.paid_blocked
    assert not a.budget_ok(11.9, 0.5) and a.budget_ok(11.4, 0.5)

def test_6_duplicate_trace_idempotent(tmp_path):
    a = CostReceiptAdapter(_fx(tmp_path))
    r1 = a.build(**_kw(), usage_payload={"cost_usd": 0.01})
    r2 = a.build(**_kw(), usage_payload={"cost_usd": 0.01})
    assert r1 == r2 and r2["budget_after_aud"] == r1["budget_after_aud"]  # بدون شارژ دوباره

def test_7_no_secrets_in_serialization(tmp_path):
    a = CostReceiptAdapter(_fx(tmp_path))
    payload = {"cost_usd": 0.01, "api_key": "sk-SECRETSECRETSECRET", "authorization": "Bearer x"}
    r = a.build(**_kw(), usage_payload=payload)
    s = json.dumps(r)
    assert "SECRET" not in s and "Bearer" not in s and r["provider_usage_payload_hash"]

def test_8_fallback_records_both(tmp_path):
    a = CostReceiptAdapter(_fx(tmp_path))
    prim = a.build(**_kw(trace_id="t-0", provider="fugu", free_tier=True))
    r = a.build(**_kw(trace_id="t-1"), fallback_of=prim)
    assert r["fallback"]["primary_provider"] == "fugu" and r["fallback"]["primary_status"] == "COMPLETE"

def test_9_free_tier_marked_unbilled(tmp_path):
    a = CostReceiptAdapter(_fx(tmp_path))
    r = a.build(**_kw(provider="fugu", model="fugu", free_tier=True, tokens_in=100, tokens_out=50))
    assert r["cost_method"] == "FREE_OR_UNBILLED" and r["estimated_or_reported_cost_aud"] is None
    assert a.paid_blocked is False
