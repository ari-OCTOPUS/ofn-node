#!/usr/bin/env python3
"""test_pf_admin.py — تستِ آداپتورِ /pf_* (propose-only، pipe تزریق‌شده، بدونِ اثرِ بیرونی)."""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (_HERE, _HERE.parent / "brain"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import pf_admin  # noqa: E402
from acquisition_pipeline import AcquisitionPipeline  # noqa: E402


def _pipe(tmp_path):
    return AcquisitionPipeline(store_path=tmp_path / "q.json", brain=None)


def test_status_is_content_free(tmp_path):
    p = _pipe(tmp_path)
    p.auto_plan(2)
    out = pf_admin.handle_pf("/pf_status", "", pipe=p)
    assert "acquisition" in out.lower() and "خاموش" in out
    for banned in ("sydney", "onlyfans", "صبا", "persian"):
        assert banned not in out.lower()


def test_plan_queue_approve_ready_flow(tmp_path):
    p = _pipe(tmp_path)
    assert "ساخته" in pf_admin.handle_pf("/pf_plan", "2", pipe=p)
    q = pf_admin.handle_pf("/pf_queue", "", pipe=p)
    assert "صف" in q
    pid = p.pending()[0]["id"]
    assert "approved" in pf_admin.handle_pf("/pf_ok", pid, pipe=p)
    ready = pf_admin.handle_pf("/pf_ready", pid, pipe=p)
    assert "دستی" in ready          # همیشه پستِ دستیِ انسان — هرگز خودکار
    assert "خودکار پست نمی‌شود" in ready


def test_reject_flow(tmp_path):
    p = _pipe(tmp_path)
    p.auto_plan(1)
    pid = p.pending()[0]["id"]
    assert "rejected" in pf_admin.handle_pf("/pf_no", pid, pipe=p)
    assert p.by_status("rejected")[0]["id"] == pid


def test_ready_requires_approval_fail_closed(tmp_path):
    p = _pipe(tmp_path)
    p.auto_plan(1)
    pid = p.pending()[0]["id"]
    out = pf_admin.handle_pf("/pf_ready", pid, pipe=p)   # بدونِ approve
    assert out.startswith("❌")


def test_unknown_returns_help(tmp_path):
    assert "/pf_status" in pf_admin.handle_pf("/pf_wat", "", pipe=_pipe(tmp_path))


def test_status_exposes_vault_when_wired(tmp_path):
    from store import VaultBank
    vb = VaultBank(path=tmp_path / "v.json")
    vb.add("tag", "hook", channel="reddit")
    p = AcquisitionPipeline(store_path=tmp_path / "q.json", brain=None, vault=vb)
    out = pf_admin.handle_pf("/pf_status", "", pipe=p)
    assert "vault" in out.lower()
    assert "1 asset" in out


def test_fail_soft_never_crashes(tmp_path):
    class _Boom:
        def admin_digest(self):
            raise RuntimeError("boom")
    out = pf_admin.handle_pf("/pf_status", "", pipe=_Boom())
    assert out.startswith("pf error:")   # هرگز کاکپیت را نمی‌شکند


def test_adapter_exposes_no_outward_verb():
    # آداپتور فقط یک تابعِ متنی است — هیچ متدِ post/send/publish/pay
    for verb in ("post", "send", "dm", "publish", "pay", "connect", "login"):
        assert not hasattr(pf_admin, verb)
