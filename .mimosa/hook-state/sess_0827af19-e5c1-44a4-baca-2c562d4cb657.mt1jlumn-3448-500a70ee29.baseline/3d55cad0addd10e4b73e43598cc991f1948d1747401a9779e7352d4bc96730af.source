#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_fugu_proxy.py — WP1 تست‌های Usage Normalizer + proxy structure."""
import json
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))


class TestUsageNormalizer:
    """تست ۱: normalize_usage — فرمتِ واحد."""

    def test_basic_openai_format(self):
        from owner_cockpit.fugu_proxy import normalize_usage
        u = normalize_usage({"prompt_tokens": 100, "completion_tokens": 50})
        assert u["input_tokens"] == 100
        assert u["output_tokens"] == 50
        assert u["total_tokens"] == 150
        assert u["total_cost_usd"] > 0

    def test_cached_tokens(self):
        from owner_cockpit.fugu_proxy import normalize_usage
        u = normalize_usage({
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "prompt_tokens_details": {"cached_tokens": 30},
        })
        assert u["cached_tokens"] == 30
        assert u["input_tokens"] == 100
        # cached باید ارزان‌تر باشد
        assert u["total_cost_usd"] > 0

    def test_orchestration_tokens(self):
        from owner_cockpit.fugu_proxy import normalize_usage
        u = normalize_usage({
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "orchestration_input_tokens": 200,
            "orchestration_output_tokens": 100,
        })
        assert u["orchestration_input_tokens"] == 200
        assert u["orchestration_output_tokens"] == 100
        assert u["total_tokens"] == 450  # 100+50+200+100

    def test_cost_calculation(self):
        from owner_cockpit.fugu_proxy import normalize_usage
        # 1M input + 1M output = $5 + $30 = $35
        u = normalize_usage({"prompt_tokens": 1_000_000, "completion_tokens": 1_000_000})
        assert abs(u["total_cost_usd"] - 35.0) < 0.01

    def test_empty_usage(self):
        from owner_cockpit.fugu_proxy import normalize_usage
        u = normalize_usage({})
        assert u["total_tokens"] == 0
        assert u["total_cost_usd"] == 0.0

    def test_none_usage(self):
        from owner_cockpit.fugu_proxy import normalize_usage
        u = normalize_usage(None)
        assert u["total_tokens"] == 0
        assert u["total_cost_usd"] == 0.0


class TestPricingFile:
    """تست ۲: pricing file structure."""

    def test_default_pricing_has_verified_at(self):
        from owner_cockpit.fugu_proxy import DEFAULT_PRICING
        assert DEFAULT_PRICING["verified_at"]
        assert DEFAULT_PRICING["source"]
        assert "fugu-ultra" in DEFAULT_PRICING
        rates = DEFAULT_PRICING["fugu-ultra"]
        assert rates["input_per_1m"] == 5.0
        assert rates["output_per_1m"] == 30.0
        assert rates["cached_input_per_1m"] == 0.5
