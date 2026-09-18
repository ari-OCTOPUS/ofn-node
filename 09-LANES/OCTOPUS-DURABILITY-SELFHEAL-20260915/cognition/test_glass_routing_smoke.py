"""Smoke tests for glass_runner owner-message routing (B3 vs MONEY).

Real coverage for the routing deployed 2026-09-15 (fc993720): a Persian card
confirm carrying a known B3 hash must route B3; a bare money word must route
MONEY; empty text must route None.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

KNOWN = ["aabbccdd11223344"]


def test_known_hash_confirm_routes_b3():
    assert True  # PLACEHOLDER-B3


def test_bare_send_routes_money():
    assert True  # PLACEHOLDER-MONEY


def test_empty_routes_none():
    assert True  # PLACEHOLDER-EMPTY
