#!/usr/bin/env python3
"""test_rfc_sweep.py — تستِ RFC sweep/expire/re-submit در doctor.py.

$0 آفلاین: Doctor بدون DB/Telegram تزریق می‌شود.
"""
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "doctor"))
import harness

from doctor import Doctor, RFC


def _make_doctor(channel=None) -> Doctor:
    """Doctor بدون DB (channel injectable)."""
    return Doctor(state_dir=None, approval_channel=channel, db=None)


def t_rfc_has_created_ts():
    """RFC جدید created_ts > 0 دارد."""
    rfc = RFC(rfc_id="T001", bottleneck="test", fix="fix it",
              expected_lift="better")
    assert rfc.created_ts > 0, f"created_ts should be > 0, got {rfc.created_ts}"


def t_rfc_created_ts_auto_set():
    """اگر created_ts=0 → __post_init__ آن را با time.time() مقداردهی کند."""
    rfc = RFC(rfc_id="T002", bottleneck="test", fix="fix",
              expected_lift="lift", created_ts=0.0)
    assert rfc.created_ts > 0


def t_rfc_created_ts_explicit():
    """اگر created_ts صریح داده شود → تغییر نکند."""
    rfc = RFC(rfc_id="T003", bottleneck="test", fix="fix",
              expected_lift="lift", created_ts=1000.0)
    assert rfc.created_ts == 1000.0


def t_sweep_no_rfcs():
    """sweep بدون RFC → خالی."""
    doc = _make_doctor()
    result = doc._sweep_stale_rfcs(max_age_hours=24)
    assert result["swept"] == 0
    assert result["details"] == []
    assert result["resubmitted"] == []


def t_sweep_off_when_zero():
    """max_age_hours=0 → sweep خاموش."""
    rfc = RFC(rfc_id="T004", bottleneck="test", fix="fix",
              expected_lift="lift", status="submitted-no-channel",
              created_ts=time.time() - 100_000)
    doc = _make_doctor()
    doc._rfcs["T004"] = rfc
    result = doc._sweep_stale_rfcs(max_age_hours=0)
    assert result["swept"] == 0
    assert rfc.status == "submitted-no-channel"  # تغییر نکند


def t_sweep_expires_old_no_channel():
    """RFC با status=submitted-no-channel و age > 24h → expired."""
    rfc = RFC(rfc_id="T005", bottleneck="test", fix="fix",
              expected_lift="lift", status="submitted-no-channel",
              created_ts=time.time() - (25 * 3600))  # 25 ساعت پیش
    doc = _make_doctor()  # channel=None
    doc._rfcs["T005"] = rfc
    result = doc._sweep_stale_rfcs(max_age_hours=24)
    assert result["swept"] == 1
    assert rfc.status == "expired"
    assert len(result["details"]) == 1
    assert result["details"][0]["rfc_id"] == "T005"


def t_sweep_resubmits_when_channel_connected():
    """RFC با no-channel قدیمی ولی channel الان وصل → re-submit."""
    mock_ch = MagicMock()
    mock_ch.rfc_card.return_value = True  # submit موفق
    rfc = RFC(rfc_id="T006", bottleneck="test", fix="fix",
              expected_lift="lift", status="submitted-no-channel",
              created_ts=time.time() - (25 * 3600))
    doc = _make_doctor(channel=mock_ch)
    doc._rfcs["T006"] = rfc
    result = doc._sweep_stale_rfcs(max_age_hours=24)
    assert result["swept"] == 0  # expired نیست، re-submit شد
    assert len(result["resubmitted"]) == 1
    assert result["resubmitted"][0]["rfc_id"] == "T006"
    assert rfc.status == "submitted"  # re-submit موفق → submitted
    mock_ch.rfc_card.assert_called_once()


def t_sweep_keeps_fresh():
    """RFC با age < 24h → تغییر نکند."""
    rfc = RFC(rfc_id="T007", bottleneck="test", fix="fix",
              expected_lift="lift", status="submitted-no-channel",
              created_ts=time.time() - 3600)  # ۱ ساعت پیش
    doc = _make_doctor()
    doc._rfcs["T007"] = rfc
    result = doc._sweep_stale_rfcs(max_age_hours=24)
    assert result["swept"] == 0
    assert rfc.status == "submitted-no-channel"


def t_sweep_expires_submitted_old():
    """RFC با status=submitted و age > 24h → expired (human response timeout)."""
    rfc = RFC(rfc_id="T008", bottleneck="test", fix="fix",
              expected_lift="lift", status="submitted",
              created_ts=time.time() - (30 * 3600))  # 30 ساعت
    doc = _make_doctor()
    doc._rfcs["T008"] = rfc
    result = doc._sweep_stale_rfcs(max_age_hours=24)
    assert result["swept"] == 1
    assert rfc.status == "expired"


if __name__ == "__main__":
    failed = harness.run([
        ("RFC created_ts > 0", t_rfc_has_created_ts),
        ("RFC created_ts auto-set", t_rfc_created_ts_auto_set),
        ("RFC created_ts explicit", t_rfc_created_ts_explicit),
        ("sweep بدون RFC → خالی", t_sweep_no_rfcs),
        ("sweep خاموش (max_age=0)", t_sweep_off_when_zero),
        ("expire old no-channel RFC", t_sweep_expires_old_no_channel),
        ("re-submit وقتی channel وصل", t_sweep_resubmits_when_channel_connected),
        ("fresh RFC بدون تغییر", t_sweep_keeps_fresh),
        ("expire old submitted RFC", t_sweep_expires_submitted_old),
    ])
    sys.exit(1 if failed else 0)
