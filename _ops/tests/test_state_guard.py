#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_state_guard.py — ۵ تستِ پذیرشِ StateGuard (Seed Agent v1 قدم ۱).

تست‌ها:
  ۱. repair strips null + quarantines invalid
  ۲. scan_all no crash
  ۳. repair idempotent (دومین بار = removed=0)
  ۴. atomic rewrite permission failure preserves original
  ۵. receipt has sha256_before + quarantine + valid preserved
"""
import json
import os
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from state_guard import (  # noqa: E402
    scan_jsonl, repair_jsonl, scan_all, repair_known_targets,
    _atomic_rewrite, _write_receipt, RECEIPTS, REPAIR_TARGETS,
    set_maintenance_lock, release_maintenance_lock, is_maintenance_locked,
    MAINTENANCE_LOCK,
)


@pytest.fixture
def isolated_state(tmp_path, monkeypatch):
    """ STATE_ROOT را به tmp_path منتقل کن تا تست‌ها روی دیتای زنده نباشند."""
    import state_guard
    monkeypatch.setattr(state_guard, "STATE_ROOT", tmp_path)
    monkeypatch.setattr(state_guard, "RECEIPTS", tmp_path / "state_guard-receipts.jsonl")
    monkeypatch.setattr(state_guard, "MAINTENANCE_LOCK", tmp_path / "maintenance-lock.json")
    return tmp_path


class TestRepairStripsNull:
    """تست ۱: repair strips null lines + quarantines invalid JSON."""

    def test_repair_strips_null_and_quarantines(self, isolated_state, monkeypatch):
        # monkeypatch RECEIPTS path for receipt writes
        monkeypatch.setattr("state_guard.RECEIPTS", isolated_state / "receipts.jsonl")
        f = isolated_state / "sample.jsonl"
        f.write_bytes(
            b'{"a":1}\n' + b'\x00\x00\x00\n' + b'{"b":2}\n' + b'{bad json\n'
        )
        s = scan_jsonl(f)
        assert s.total == 4
        assert s.valid == 2
        assert s.null_lines == 1
        assert s.invalid_json == 1

        r = repair_jsonl(f)
        assert r.ok
        assert r.removed_null == 1
        assert r.removed_invalid == 1
        assert r.kept_valid == 2

        lines = f.read_bytes().split(b"\n")
        lines = [ln for ln in lines if ln]  # remove trailing empty
        assert len(lines) == 2
        assert json.loads(lines[0]) == {"a": 1}
        assert json.loads(lines[1]) == {"b": 2}

        assert r.quarantined_to
        assert Path(r.quarantined_to).exists()
        quar_lines = Path(r.quarantined_to).read_bytes().split(b"\n")
        quar_lines = [ln for ln in quar_lines if ln]
        assert len(quar_lines) == 2  # null + invalid


class TestScanAllNoCrash:
    """تست ۲: scan_all no crash on empty/varied dirs."""

    def test_scan_all_no_crash(self, isolated_state, monkeypatch):
        monkeypatch.setattr("state_guard.STATE_ROOT", isolated_state)
        (isolated_state / "x.jsonl").write_text('{"ok":true}\n')
        (isolated_state / "sub").mkdir()
        (isolated_state / "sub" / "y.jsonl").write_bytes(b'{"a":1}\n\x00\n')
        results = scan_all(isolated_state)
        assert len(results) == 2
        valid_map = {Path(r.path).name: r.valid for r in results}
        assert valid_map.get("x.jsonl") == 1
        assert valid_map.get("y.jsonl") == 1


class TestRepairIdempotent:
    """تست ۳: repair idempotent — دومین بار removed=0."""

    def test_repair_idempotent(self, isolated_state, monkeypatch):
        monkeypatch.setattr("state_guard.RECEIPTS", isolated_state / "receipts.jsonl")
        f = isolated_state / "x.jsonl"
        f.write_bytes(b'{"ok":true}\n\x00\x00\n')

        first = repair_jsonl(f)
        assert first.ok
        assert first.removed_null == 1

        second = repair_jsonl(f)
        assert second.ok
        assert second.removed_null == 0
        assert second.removed_invalid == 0


class TestAtomicRewritePermissionFailure:
    """تست ۴: atomic rewrite permission failure preserves original."""

    def test_permission_failure_preserves_original(self, tmp_path, monkeypatch):
        f = tmp_path / "x.jsonl"
        original = b'{"before":true}\n'
        f.write_bytes(original)

        # os.replace را mock کن تا همیشه PermissionError بدهد
        import state_guard
        monkeypatch.setattr("os.replace", lambda *_: (_ for _ in ()).throw(PermissionError("mock")))
        monkeypatch.setattr(state_guard, "RECEIPTS", tmp_path / "receipts.jsonl")

        result = repair_jsonl(f)
        assert not result.ok
        assert f.read_bytes() == original  # فایل اصلی دست‌نخورده


class TestReceiptIntegrity:
    """تست ۵: receipt has sha256_before + quarantine + valid preserved."""

    def test_receipt_has_hashes_and_valid(self, isolated_state, monkeypatch):
        receipts_path = isolated_state / "receipts.jsonl"
        monkeypatch.setattr("state_guard.RECEIPTS", receipts_path)

        f = isolated_state / "test.jsonl"
        f.write_bytes(b'{"valid":1}\n\x00\n{"valid":2}\n{broken\n')

        r = repair_jsonl(f)
        assert r.ok
        assert r.sha256_before  # hash قبل از rewrite
        assert r.sha256_after    # hash بعد
        assert r.sha256_before != r.sha256_after  # تغییر کرده
        assert r.kept_valid == 2  # دو رکورد معتبر حفظ شد

        # receipt را بخوان و verify کن
        receipt_lines = receipts_path.read_text("utf-8").strip().split("\n")
        assert len(receipt_lines) >= 1
        receipt = json.loads(receipt_lines[-1])
        assert receipt["schema"] == "StateGuardReceipt.v1"
        assert receipt["action"] == "repair_jsonl"
        assert receipt["target"] == str(f)
        assert receipt["sha256_before"]
        assert receipt["repair"]["sha256_after"]
        assert receipt["repair"]["quarantined_to"]
        assert receipt["repair"]["kept_valid"] == 2

        # quarantine + meta sidecar
        assert Path(r.quarantined_to).exists()
        meta_path = Path(r.quarantined_to).with_name(
            Path(r.quarantined_to).name + ".meta.json"
        )
        assert meta_path.exists()
        meta = json.loads(meta_path.read_text("utf-8"))
        assert meta["schema"] == "StateGuardQuarantineMeta.v1"
        assert meta["removed_null"] == 1
        assert meta["removed_invalid"] == 1


class TestMaintenanceLock:
    """تست ۶: maintenance lock set/release."""

    def test_lock_set_and_release(self, isolated_state, monkeypatch):
        monkeypatch.setattr("state_guard.MAINTENANCE_LOCK", isolated_state / "lock.json")
        assert not is_maintenance_locked()

        set_maintenance_lock(["test/file.jsonl"], "test")
        assert is_maintenance_locked()

        lock_data = json.loads((isolated_state / "lock.json").read_text("utf-8"))
        assert lock_data["schema"] == "MaintenanceLock.v1"
        assert lock_data["active"] is True
        assert lock_data["owner"] == "state_guard"

        release_maintenance_lock()
        assert not is_maintenance_locked()
        assert not (isolated_state / "lock.json").exists()


class TestRepairKnownTargets:
    """تست ۷: repair_known_targets فقط روی allowlist."""

    def test_repair_targets_is_allowlist(self):
        assert len(REPAIR_TARGETS) == 7  # 6 original + miniapp-hits (2026-08-08)
        for t in REPAIR_TARGETS:
            assert t.endswith(".jsonl")

    def test_missing_target_ok(self, isolated_state, monkeypatch):
        monkeypatch.setattr("state_guard.STATE_ROOT", isolated_state)
        monkeypatch.setattr("state_guard.RECEIPTS", isolated_state / "receipts.jsonl")
        # هیچ فایلی نساخته‌ایم — همه missing
        results = repair_known_targets(isolated_state)
        assert len(results) == 7
        assert all(r.ok for r in results)
        assert all(r.error == "missing-target" for r in results)
