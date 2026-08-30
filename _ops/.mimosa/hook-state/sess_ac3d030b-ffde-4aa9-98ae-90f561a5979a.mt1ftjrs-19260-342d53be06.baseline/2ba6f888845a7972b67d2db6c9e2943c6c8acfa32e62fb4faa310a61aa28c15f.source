"""تست‌های Beat Ownership Lease — تمرکز روی split-brain و fencing.

WORKLOCK: not registered in run_all.py.

Run:
  pytest _ops/tests/test_beat_lease.py -q
"""

from __future__ import annotations

import os
import sys
import threading
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from _ops.runtime.beat_lease import (  # noqa: E402
    BeatLease,
    FileLeaseStore,
    LeaseFrozen,
    LeaseLost,
)


@pytest.fixture
def store(tmp_path):
    return FileLeaseStore(tmp_path / "octopus.lease")


def mk(store, owner, ttl=6.0, margin=1.0, events=None, freeze=None):
    return BeatLease(
        store,
        owner=owner,
        ttl_s=ttl,
        safety_margin_s=margin,
        freeze_file=freeze,
        on_event=(lambda k, d: events.append((k, d))) if events is not None else None,
    )


# ---------------------------------------------------------------- basics


def test_acquire_and_token(store):
    a = mk(store, "laptop")
    assert a.acquire() is True
    assert a.held is True
    assert a.token == 1
    a.release()
    assert a.held is False


def test_second_owner_is_denied_while_first_alive(store):
    a = mk(store, "laptop")
    b = mk(store, "arm1")
    assert a.acquire() is True
    assert b.acquire() is False, "SPLIT-BRAIN: two owners held the beat"
    assert b.held is False


def test_release_lets_the_other_in(store):
    a = mk(store, "laptop")
    b = mk(store, "arm1")
    a.acquire()
    a.release()
    assert b.acquire() is True
    assert b.token >= 1


# ---------------------------------------------------------------- fencing


def test_fencing_token_is_strictly_increasing(store):
    a = mk(store, "laptop")
    a.acquire()
    t1 = a.token
    assert a.renew() is True
    t2 = a.token
    a.release()

    b = mk(store, "arm1")
    b.acquire()
    t3 = b.token
    b.release()

    assert t1 < t2 < t3, (t1, t2, t3)


def test_stale_holder_cannot_renew_after_takeover(store):
    """پروسهٔ pause شده بیدار می‌شود و می‌خواهد ادامه دهد — باید رد شود."""
    a = mk(store, "laptop", ttl=3.0, margin=1.0)
    a.acquire()
    stale_token = a.token

    # a منجمد می‌شود، lease منقضی می‌شود (ttl + margin)، b مالک می‌شود
    time.sleep(4.4)
    b = mk(store, "arm1", ttl=3.0, margin=1.0)
    assert b.acquire() is True
    assert b.token > stale_token

    # حالا a بیدار می‌شود
    assert a.renew() is False, "stale holder renewed over a live owner"
    with pytest.raises(LeaseLost):
        a.assert_valid()
    b.release()


# ---------------------------------------------------------------- expiry


def test_assert_valid_fails_closed_after_expiry(store):
    a = mk(store, "laptop", ttl=2.5, margin=1.0)
    a.acquire()
    a.assert_valid()          # هنوز معتبر
    time.sleep(1.7)           # از valid_until محلی (ttl - margin = 1.5) گذشتیم
    with pytest.raises(LeaseLost):
        a.assert_valid()


def test_local_validity_ends_before_wall_expiry(store):
    """پنجرهٔ ایمنی: مالک قبل از انقضای واقعی خودش را بازنشسته می‌کند."""
    a = mk(store, "laptop", ttl=4.0, margin=1.5)
    a.acquire()
    rec = store.read()
    assert rec is not None
    local_left = a._valid_until_mono - time.monotonic()
    wall_left = rec.expires_wall - time.time()
    assert local_left < wall_left - 1.0


# ---------------------------------------------------------------- renew


def test_renewer_thread_keeps_lease_alive(store):
    a = mk(store, "laptop", ttl=3.0, margin=0.7)
    with a:
        time.sleep(4.5)       # بیش از یک TTL کامل
        a.assert_valid()      # نباید LeaseLost بدهد
        assert a.token >= 3   # حداقل چند بار تمدید شده
    vacated = store.read()
    assert vacated is not None and vacated.vacant, "release must vacate, not delete"


def test_other_cannot_steal_while_renewer_runs(store):
    a = mk(store, "laptop", ttl=3.0, margin=0.7)
    b = mk(store, "arm1", ttl=3.0, margin=0.7)
    with a:
        deadline = time.monotonic() + 4.0
        while time.monotonic() < deadline:
            assert b.acquire() is False, "SPLIT-BRAIN during renewal"
            time.sleep(0.3)


# ---------------------------------------------------------------- freeze


def test_freeze_file_blocks_acquire(store, tmp_path):
    f = tmp_path / "FREEZE"
    f.write_text("owner stop", encoding="utf-8")
    a = mk(store, "laptop", freeze=f)
    with pytest.raises(LeaseFrozen):
        a.acquire()


def test_freeze_file_stops_an_active_holder(store, tmp_path):
    f = tmp_path / "FREEZE"
    a = mk(store, "laptop", freeze=f)
    a.acquire()
    a.assert_valid()
    f.write_text("stop", encoding="utf-8")
    with pytest.raises(LeaseFrozen):
        a.assert_valid()


# ---------------------------------------------------------------- races


def test_concurrent_acquire_exactly_one_winner(store):
    winners = []
    barrier = threading.Barrier(8)

    def worker(i: int) -> None:
        lease = mk(store, f"host{i}", ttl=30.0, margin=5.0)
        barrier.wait()
        if lease.acquire():
            winners.append((i, lease.token))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(winners) == 1, f"SPLIT-BRAIN: {len(winners)} winners → {winners}"


def test_corrupt_lease_file_does_not_grant_silent_ownership(store, tmp_path):
    store.path.write_text("{not json", encoding="utf-8")
    a = mk(store, "laptop")
    assert a.acquire() is True          # می‌تواند از نو بگیرد
    assert a.token == 1
    rec = store.read()
    assert rec is not None and rec.owner == "laptop"


# ---------------------------------------------------------------- events


def test_events_are_emitted_for_the_ledger(store):
    events: list = []
    a = mk(store, "laptop", events=events)
    a.acquire()
    a.renew()
    a.release()
    kinds = [k for k, _ in events]
    assert "lease.acquired" in kinds
    assert "lease.renewed" in kinds
    assert "lease.released" in kinds
    for _, d in events:
        assert "ts" in d and "holder" in d


def test_revision_survives_release_so_tokens_never_repeat(store):
    """پاک‌کردن فایل در release یک باگ امنیتی است — رگرسیون را قفل می‌کنیم."""
    seen: list[int] = []
    for i in range(4):
        lease = mk(store, f"owner{i}")
        assert lease.acquire() is True
        seen.append(lease.token)
        lease.release()
    assert seen == sorted(set(seen)), f"fencing tokens repeated or went backwards: {seen}"


def test_bad_config_is_rejected(store):
    with pytest.raises(ValueError):
        BeatLease(store, owner="x", ttl_s=10.0, safety_margin_s=5.0)


def test_file_store_refuses_unc_path():
    with pytest.raises(RuntimeError, match="UNC/SMB/NFS"):
        FileLeaseStore(r"\\smb\share\octopus.lease")
