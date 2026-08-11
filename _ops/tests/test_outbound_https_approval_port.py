#!/usr/bin/env python3
"""test_outbound_https_approval_port.py — Phase 2b behavioral test.

Verifies that _LocalApprovalStore has been deleted from outbound_https.py
and replaced with an injectable _approval_port. Without injection, submit()
and execute_if_approved() return NOT_WIRED (fail-closed). With a mock port,
calls are correctly delegated.

2026-08-11: Architectural repair — commit 0c40fef created a second
disconnected queue (_LocalApprovalStore). This test proves the fix:
no second queue, only injectable port."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # _ops/tests
_OPS = _HERE.parent                                # _ops
sys.path.insert(0, str(_OPS / "budget"))
sys.path.insert(0, str(_OPS / "integrations"))

passed = 0


def _assert(condition: bool, label: str):
    global passed
    assert condition, f"FAIL: {label}"
    passed += 1
    print(f"  ✅ {label}")


# Build a synthetic vault so opslib can resolve
_tmpdir = Path(tempfile.mkdtemp())
try:
    state_dir = _tmpdir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    # Create a domain allowlist so we get past the allowlist gate
    allow_dir = state_dir / "outbound_https"
    allow_dir.mkdir(parents=True, exist_ok=True)
    (allow_dir / "domain-allowlist.json").write_text(
        json.dumps({"domains": {"example.com": {"methods": ["GET", "POST"]}}}),
        "utf-8")

    # Patch opslib.STATE_DIR BEFORE importing outbound_https
    import opslib
    _orig_state_dir = opslib.STATE_DIR
    opslib.STATE_DIR = state_dir

    # Force reimport of outbound_https with patched STATE_DIR
    if "outbound_https" in sys.modules:
        del sys.modules["outbound_https"]
    import importlib
    import outbound_https as OB
    importlib.reload(OB)

    # ─── t_a: _LocalApprovalStore deleted ───
    _assert(not hasattr(OB, "_LocalApprovalStore"),
            "t_a_LocalApprovalStore_deleted")

    # ─── t_b: _get_store deleted ───
    _assert(not hasattr(OB, "_get_store"),
            "t_b_get_store_deleted")

    # ─── t_c: _approval_port defaults to None ───
    _assert(OB._approval_port is None,
            "t_c_approval_port_default_none")

    # ─── t_d: _set_approval_port exists ───
    _assert(callable(getattr(OB, "_set_approval_port", None)),
            "t_d_set_approval_port_exists")

    # ─── t_e: submit returns NOT_WIRED when no port ───
    os.environ["OCTOPUS_WIRE_OUTBOUND_HTTPS"] = "1"
    r = OB.submit("GET", "https://example.com/api")
    _assert(r.get("status") == "NOT_WIRED",
            "t_e_submit_not_wired_no_port")
    _assert(r.get("reason") == "no_approval_port",
            "t_e_submit_not_wired_reason")

    # ─── t_f: execute_if_approved returns NOT_WIRED when no port ───
    r2 = OB.execute_if_approved("fake-id")
    _assert(r2.get("status") == "NOT_WIRED",
            "t_f_execute_not_wired_no_port")
    _assert(r2.get("reason") == "no_approval_port",
            "t_f_execute_not_wired_reason")

    # ─── t_g: injected port receives add_pending call ───
    _calls = []

    def _mock_add(spec):
        _calls.append(("add", spec))
        return "mock-job-42"

    def _mock_get(jid):
        _calls.append(("get", jid))
        return None

    def _mock_done(jid):
        _calls.append(("done", jid))

    OB._set_approval_port({
        "add_pending": _mock_add,
        "get": _mock_get,
        "mark_done": _mock_done,
    })
    _assert(OB._approval_port is not None,
            "t_g_port_wired")

    # ─── t_h: submit delegates to injected port ───
    r3 = OB.submit("POST", "https://example.com/api/test", body="hello")
    _assert(r3.get("ok") is True,
            "t_h_submit_ok_with_port")
    _assert(r3.get("status") == "PENDING_APPROVAL",
            "t_h_submit_status_pending")
    _assert(r3.get("job_id") == "mock-job-42",
            "t_h_submit_job_id_from_port")
    add_calls = [c for c in _calls if c[0] == "add"]
    _assert(len(add_calls) == 1,
            "t_h_add_pending_called_once")
    _assert(len(add_calls[0][1].get("action_sha256", "")) == 64,
            "t_h_approval_binds_action_hash")

    # ─── t_i: execute delegates get to injected port ───
    r4 = OB.execute_if_approved("some-id")
    _assert(r4.get("status") == "NOT_FOUND",
            "t_i_execute_delegates_get")
    get_calls = [c for c in _calls if c[0] == "get"]
    _assert(len(get_calls) == 1,
            "t_i_get_called_once")

    # ─── t_j: port returns approved status correctly ───
    def _mock_get_approved(jid):
        import time
        return {"job_id": jid, "status": "approved", "expires_epoch": time.time() + 60}

    OB._set_approval_port({
        "add_pending": _mock_add,
        "get": _mock_get_approved,
        "mark_done": _mock_done,
    })
    # execute will fail because spec file doesn't exist, but the
    # port.get() should be called and return "approved" → goes to
    # job_spec_missing (not NOT_WIRED)
    r5 = OB.execute_if_approved("some-id")
    _assert(r5.get("status") != "NOT_WIRED",
            "t_j_execute_with_approved_not_wired")
    # job spec file doesn't exist, so it should be FAILED with job_spec_missing
    _assert(r5.get("status") == "FAILED",
            "t_j_execute_approved_missing_spec")

    # Restore
    opslib.STATE_DIR = _orig_state_dir

finally:
    shutil.rmtree(_tmpdir, ignore_errors=True)

print(f"\n✅ test_outbound_https_approval_port: {passed}/{passed}")
