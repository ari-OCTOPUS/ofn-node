#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_prediction_ledger_p4 — تست‌های الزامی P4 (pytest استاندارد).
اجرا: python -X utf8 -m pytest -q 4d_system/tests/test_prediction_ledger_p4.py (از ریشهٔ worktree)"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from memory.prediction_ledger import PredictionLedger  # noqa: E402 (4d_system on path via conftest-less cwd)


def _ledger(tmp_path: Path) -> PredictionLedger:
    return PredictionLedger(tmp_path / "predictions.db")


def _add(led, **over):
    kw = dict(prediction_id="pred-001", content="metric M will exceed 5.0 in window W1",
              trace_id="tr-1", source="cortex", model="deepseek-v4-flash",
              confidence=0.8, eval_window="W1")
    kw.update(over)
    return led.append_prediction(**kw)


def test_append_and_unique_id(tmp_path):
    led = _ledger(tmp_path)
    assert _add(led) == "pred-001"
    with pytest.raises(sqlite3.IntegrityError):
        _add(led)  # duplicate prediction_id


def test_created_at_immutable(tmp_path):
    led = _ledger(tmp_path)
    _add(led)
    with sqlite3.connect(str(led.path)) as raw:
        with pytest.raises(sqlite3.IntegrityError):
            raw.execute("UPDATE predictions SET created_at='2000-01-01T00:00:00+00:00'")


def test_no_delete(tmp_path):
    led = _ledger(tmp_path)
    _add(led)
    with sqlite3.connect(str(led.path)) as raw:
        with pytest.raises(sqlite3.IntegrityError):
            raw.execute("DELETE FROM predictions")


def test_outcome_only_after_prediction(tmp_path):
    led = _ledger(tmp_path)
    with pytest.raises(ValueError):
        led.attach_outcome(prediction_id="ghost", outcome="hit")
    _add(led)
    oid = led.attach_outcome(prediction_id="pred-001", outcome="hit: M=5.3")
    assert oid >= 1 and led.outcomes("pred-001")[0]["outcome"].startswith("hit")


def test_outcome_cannot_backdate_or_rewrite_prediction(tmp_path):
    led = _ledger(tmp_path)
    _add(led)
    pred_before = led.prediction("pred-001")
    with pytest.raises(ValueError):
        led.attach_outcome(prediction_id="pred-001", outcome="late",
                           outcome_at=(datetime.now(timezone.utc) - timedelta(days=30)).isoformat())
    led.attach_outcome(prediction_id="pred-001", outcome="ok")
    assert led.prediction("pred-001") == pred_before  # ردیف پیش‌بینی دست‌نخورده


def test_future_outcome_rejected(tmp_path):
    led = _ledger(tmp_path)
    _add(led)
    with pytest.raises(ValueError):
        led.attach_outcome(prediction_id="pred-001", outcome="future",
                           outcome_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat())


def test_required_fields(tmp_path):
    led = _ledger(tmp_path)
    for missing in ("trace_id", "source", "model", "eval_window"):
        kw = dict(prediction_id="p-x", content="c", trace_id="t", source="s",
                  model="m", confidence=0.5, eval_window="w")
        kw.pop(missing)
        # fail-closed در هر دو لایه: امضا (TypeError) یا بدنه (ValueError)
        with pytest.raises((ValueError, TypeError)):
            led.append_prediction(**kw)
    with pytest.raises(ValueError):
        _add(led, prediction_id="p-bad", confidence=1.7)
