# -*- coding: utf-8 -*-
"""T43 (دستور مالک #۷): تست‌های lease نویسنده — acquire/renew/expire/
steal-prevention/concurrent-write-rejection + ادغام دو نویسنده.

همه روی tmp_path (قفل واقعی `_ops/state/locks/octopus-writer.lock` لمس نمی‌شود
— lease هنوز فعال نیست)."""
from pathlib import Path
import sys
import time

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS))

import writer_lease as wl  # noqa: E402

import pytest  # noqa: E402


@pytest.fixture()
def lease_path(tmp_path, monkeypatch):
    p = tmp_path / "octopus-writer.lock"
    monkeypatch.setattr(wl, "LOCK_PATH", p)
    return p


def test_acquire_and_inspect(lease_path, capsys):
    assert wl.acquire("B", "s1", 900, "ledger,evidence") == 0
    out = capsys.readouterr().out
    assert "ACQUIRED" in out
    assert wl.inspect() == 0
    rec = wl._read()
    assert rec["agent_id"] == "B" and rec["session_id"] == "s1"
    for f in ("agent_id", "session_id", "acquired_at", "ttl_seconds", "scope"):
        assert f in rec  # قرارداد فیلدهای دستور #۶ §۴


def test_renew_by_holder_only(lease_path, capsys):
    wl.acquire("B", "s1", 1, "ledger")
    assert wl.renew("B", "s1", 900) == 0            # دارنده
    capsys.readouterr()
    assert wl.renew("A", "sX", 900) == 4            # غیردارنده → DENIED
    assert "not-holder" in capsys.readouterr().out


def test_concurrent_write_rejection_hold(lease_path, capsys):
    assert wl.acquire("A", "sA", 900, "git") == 0
    capsys.readouterr()
    rc = wl.acquire("B", "sB", 900, "git")
    assert rc == 3                                     # HOLD — ایجنت دوم read-only
    out = capsys.readouterr().out
    assert "HOLD" in out and "A" in out


def test_expired_lease_archived_not_deleted(lease_path, capsys, monkeypatch):
    wl.acquire("A", "sA", ttl_short := 0, "ledger")   # ttl صفر → فوری منقضی
    capsys.readouterr()
    monkeypatch.setattr(wl, "_now", lambda: time.time() + 10)
    assert wl.acquire("B", "sB", 900, "ledger") == 0  # takeover صریح
    out = capsys.readouterr().out
    assert "STALE_ARCHIVED" in out
    stale = list(lease_path.parent.glob("octopus-writer.lock.stale.*"))
    assert stale, "lease منقضی باید بایگانی شود، نه پاک"
    assert wl._read()["agent_id"] == "B"


def test_steal_prevention_live_lease(lease_path, capsys):
    wl.acquire("A", "sA", 900, "ledger")
    capsys.readouterr()
    # تلاش برای ربایش با session جعلیِ همان ایجنت → renew ضمنی فقط با جفت یکسان
    assert wl.acquire("A", "s-other", 900, "ledger") == 3
    # release توسط غیردارنده ممنوع
    assert wl.release("B", "sB", force=False) == 4
    # release توسط دارنده → بایگانی released
    assert wl.release("A", "sA", force=False) == 0
    assert list(lease_path.parent.glob("*.released.*"))
    assert wl._read() is None


def test_integration_two_writers_one_holds(lease_path, capsys):
    """دستور #۷ §۴: دو نویسندهٔ شبیه‌سازی‌شدهٔ هم‌زمان → یکی HOLD."""
    results = []
    for agent, session in (("A", "sA"), ("B", "sB")):
        results.append(wl.acquire(agent, session, 900, "ledger,evidence,git"))
    assert results == [0, 3]
