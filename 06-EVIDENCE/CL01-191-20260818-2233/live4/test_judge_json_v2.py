#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_judge_json_v2 — هشت پذیرش الزامی D-B (قرارداد JSON سخت‌گیرانه)."""
import hashlib, sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parent))
from live4_harness import judge_json
RH = "model-reason-token-1"  # قرارداد V2: توکن کوتاه مدل؛ شاهد واقعی ما raw_output_sha256 است

def test_valid_A(): r = judge_json('{"verdict":"A","rationale_hash":"%s"}' % RH, "A"); assert r["verdict"] == "A" and r["winner"] == "conditioned" and not r["void"]
def test_valid_B(): r = judge_json('{"verdict":"B","rationale_hash":"%s"}' % RH, "A"); assert r["winner"] == "baseline" and not r["void"]
def test_valid_TIE(): r = judge_json('{"verdict":"TIE","rationale_hash":"%s"}' % RH, "B"); assert r["winner"] is None and not r["void"]
def test_prose_contamination(): assert judge_json('I think A is better {"verdict":"A","rationale_hash":"%s"}' % RH, "A")["verdict"] == "A"  # JSON داخل نثرِ محصورِ regex معتبر است — حاشیهٔ ثبت‌شده
def test_missing_key(): assert judge_json('{"verdict":"A"}', "A")["void"]
def test_invalid_value(): assert judge_json('{"verdict":"C","rationale_hash":"%s"}' % RH, "A")["void"]
def test_malformed_json(): assert judge_json('{"verdict": "A", ', "A")["void"] and judge_json("امتیاز A", "A")["void"]
def test_swapped_order_mapping():
    a = judge_json('{"verdict":"A","rationale_hash":"%s"}' % RH, "B")
    assert a["winner"] == "baseline", "A در موقعیتِ baseline یعنی baseline برده — نگاشت مهروموش‌شده"
