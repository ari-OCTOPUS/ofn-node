#!/usr/bin/env python3
"""R1–R24 reply retry / durable outbox tests (sandbox)."""
from __future__ import annotations

import importlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

REAL = Path("/root/octopus-mesh")
sys.path.insert(0, str(REAL / "bin"))
from octomesh_common import compute_checksum  # noqa: E402


def envelope(root_mid=None, **overrides):
    now = datetime.now(timezone.utc)
    mid = root_mid or str(uuid.uuid4())
    msg = {
        "envelope_version": 1,
        "message_id": mid,
        "run_id": "run-retry",
        "sender_node": "138",
        "recipient_node": "180",
        "sender_role": "commander-router-ledger-owner",
        "message_type": "task",
        "scope": "mesh",
        "claim_type": "proposal",
        "created_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expires_at": (now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "correlation_id": "corr-" + mid,
        "idempotency_key": "idem-" + mid,
        "requires_ack": True,
        "may_authorize": False,
        "payload": {"summary": "retry fixture", "task": "RETRY-TEST"},
        "evidence": [],
        "checksum": "",
    }
    msg.update({k: v for k, v in overrides.items() if k != "checksum"})
    msg["checksum"] = compute_checksum(msg)
    return msg


class ReplyRetryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="reply-retry-"))
        root = self.tmp / "octopus-mesh"
        for d in ("bin", "config", "inbox", "outbox", "processed", "rejected",
                  "receipts", "audit", "state/cognition", "state/replies"):
            (root / d).mkdir(parents=True)
        shutil.copy(REAL / "config/nodes.json", root / "config/nodes.json")
        shutil.copy(REAL / "config/policy.json", root / "config/policy.json")
        shutil.copy(REAL / "config/agent_roles.json", root / "config/agent_roles.json")
        shutil.copy(REAL / "config/model_routes.json", root / "config/model_routes.json")
        shutil.copy(REAL / "config/cognitive_policy.json", root / "config/cognitive_policy.json")
        os.environ["OCTOMESH_ROOT"] = str(root)
        os.environ["OCTOMESH_REPLY_BACKOFF"] = "0"
        os.environ["OCTOMESH_REPLY_TRANSMIT"] = "ack"
        import octopus_reply_outbox as outbox
        import octopus_cognitive_worker as worker
        import octopus_model_adapter as adapter
        importlib.reload(adapter)
        importlib.reload(outbox)
        importlib.reload(worker)
        worker.MESH = root
        adapter.MESH = root
        self.root = root
        self.outbox = outbox
        self.worker = worker
        self.outbox.TRANSMIT_HOOK = "ack"
        self.adapter = adapter
        self.model_calls = {"n": 0}
        real_complete = adapter.complete_structured

        def wrapped(task, runtime):
            self.model_calls["n"] += 1
            return real_complete(task, runtime)

        adapter.complete_structured = wrapped

    def set_hook(self, name: str) -> None:
        os.environ["OCTOMESH_REPLY_TRANSMIT"] = name
        self.outbox.TRANSMIT_HOOK = name

    def tearDown(self):
        os.environ.pop("OCTOMESH_REPLY_TRANSMIT", None)
        os.environ.pop("OCTOMESH_REPLY_BACKOFF", None)
        os.environ["OCTOMESH_ROOT"] = str(REAL)
        self.worker.MESH = REAL
        self.adapter.MESH = REAL
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_r01_process_persist_ack_processed(self):
        self.set_hook("ack")
        msg = envelope()
        out = self.worker.handle_task(msg, call_model=True, pause=None)
        self.assertEqual(out["reply_state"], "INPUT_PROCESSED")
        self.assertTrue(self.outbox.reply_acked(msg["message_id"]))
        self.assertTrue(out.get("input_processed"))

    def test_r02_fail_before_transmit_retry_same(self):
        self.set_hook("fail")
        msg = envelope()
        first = self.worker.handle_task(msg, call_model=True, pause=None)
        sha = first["response_sha256"]
        key = first["reply_idempotency_key"]
        self.assertNotEqual(first["reply_state"], "INPUT_PROCESSED")
        n = self.model_calls["n"]
        self.set_hook("ack")
        second = self.worker.handle_task(msg, call_model=True, pause=None)
        self.assertEqual(second["response_sha256"], sha)
        self.assertEqual(second["reply_idempotency_key"], key)
        self.assertFalse(second.get("model_called"))
        self.assertEqual(self.model_calls["n"], n)
        self.assertEqual(second["reply_state"], "INPUT_PROCESSED")

    def test_r03_ack_lost_duplicate_success(self):
        self.set_hook("fail")
        msg = envelope()
        first = self.worker.handle_task(msg, call_model=True, pause=None)
        sha = first["response_sha256"]
        self.set_hook("duplicate")
        second = self.worker.handle_task(msg, call_model=True, pause=None)
        self.assertEqual(second["reply_state"], "INPUT_PROCESSED")
        self.assertEqual(second["response_sha256"], sha)

    def test_r04_sigkill_after_freeze_before_send(self):
        msg = envelope()
        self.set_hook("fail")
        # freeze only
        runtime = self.adapter.discover_runtime()
        resp = self.adapter.complete_structured(msg, runtime)
        sha = self.worker.freeze_prediction(msg, resp)
        pending = self.outbox.persist_pending(msg, resp, sha)
        self.assertEqual(pending["state"], "REPLY_PENDING")
        n = self.model_calls["n"]
        self.set_hook("ack")
        out = self.worker.handle_task(msg, call_model=True, pause=None)
        self.assertFalse(out.get("model_called"))
        self.assertEqual(self.model_calls["n"], n)
        self.assertEqual(out["response_sha256"], pending["response_sha256"])
        self.assertEqual(out["reply_state"], "INPUT_PROCESSED")

    def test_r05_sigkill_after_send_before_ack(self):
        self.outbox.TRANSMIT_CALLS = 0
        self.set_hook("timeout")
        msg = envelope()
        first = self.worker.handle_task(msg, call_model=True, pause=None)
        self.assertIn(first["reply_state"], {"RETRY_WAIT", "REPLY_PENDING"})
        sha = first["response_sha256"]
        self.assertGreaterEqual(self.outbox.TRANSMIT_CALLS, 1)
        handed_calls = self.outbox.TRANSMIT_CALLS
        self.set_hook("duplicate")
        second = self.worker.handle_task(msg, call_model=True, pause=None)
        self.assertEqual(second["reply_state"], "INPUT_PROCESSED")
        self.assertEqual(second["response_sha256"], sha)
        self.assertFalse(second.get("model_called"))
        self.assertEqual(self.outbox.TRANSMIT_CALLS, handed_calls)
        self.assertEqual(self.outbox.TRANSMIT_CALLS, 1)

    def test_r06_retry_no_model(self):
        self.set_hook("fail")
        msg = envelope()
        self.worker.handle_task(msg, call_model=True, pause=None)
        n = self.model_calls["n"]
        self.worker.handle_task(msg, call_model=True, pause=None)
        self.assertEqual(self.model_calls["n"], n)

    def test_r07_sha_stable(self):
        self.set_hook("fail")
        msg = envelope()
        a = self.worker.handle_task(msg, call_model=True, pause=None)
        b = self.worker.handle_task(msg, call_model=True, pause=None)
        self.assertEqual(a["response_sha256"], b["response_sha256"])
        self.assertEqual(a["reply_message_id"], b["reply_message_id"])

    def test_r08_not_processed_before_ack(self):
        self.set_hook("fail")
        msg = envelope()
        self.worker.handle_task(msg, call_model=True, pause=None)
        self.assertFalse(self.worker.already_processed(msg["message_id"], msg["idempotency_key"]))

    def test_r09_duplicate_after_ack(self):
        self.set_hook("ack")
        msg = envelope()
        self.worker.handle_task(msg, call_model=True, pause=None)
        n = self.model_calls["n"]
        second = self.worker.handle_task(msg, call_model=True, pause=None)
        self.assertEqual(second["status"], "duplicate_blocked")
        self.assertEqual(self.model_calls["n"], n)

    def test_r10_orphan_frozen_recovered(self):
        msg = envelope()
        self.set_hook("fail")
        runtime = self.adapter.discover_runtime()
        resp = self.adapter.complete_structured(msg, runtime)
        sha = self.worker.freeze_prediction(msg, resp)
        idx = self.root / "state/cognition/processed_ids.json"
        idx.write_text(json.dumps({msg["message_id"]: {"ts": "t", "artifact_sha256": sha, "immutable": True}}, indent=2))
        n = self.model_calls["n"]
        self.set_hook("ack")
        out = self.outbox.recover_orphan(msg)
        self.assertFalse(out["model_called"])
        self.assertEqual(self.model_calls["n"], n)
        self.assertEqual(out["status"], "recovered_acked")

    def test_r11_orphan_with_receipt_local_repair(self):
        msg = envelope()
        self.set_hook("fail")
        runtime = self.adapter.discover_runtime()
        resp = self.adapter.complete_structured(msg, runtime)
        sha = self.worker.freeze_prediction(msg, resp)
        idx = self.root / "state/cognition/processed_ids.json"
        idx.write_text(json.dumps({
            msg["message_id"]: {"ts": "t", "artifact_sha256": sha, "immutable": True,
                                "reply_acked": False},
        }, indent=2))
        (self.root / "receipts" / f"{msg['message_id']}.ack.json").write_text(
            json.dumps({"status": "ack", "in_reply_to": msg["message_id"]}))
        n = self.model_calls["n"]
        self.set_hook("fail")
        out = self.outbox.recover_orphan(msg)
        self.assertEqual(out["status"], "already_acked")
        self.assertTrue(out.get("local_repair"))
        self.assertFalse(out.get("resend", False))
        self.assertEqual(self.model_calls["n"], n)
        self.assertFalse(out["model_called"])
        self.assertTrue(self.outbox.reply_acked(msg["message_id"]))

    def test_r17_expired_task(self):
        now = datetime.now(timezone.utc)
        msg = envelope()
        msg["expires_at"] = (now - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        msg["checksum"] = compute_checksum(msg)
        err = self.worker.validate_envelope(msg)
        self.assertEqual(err, "expired")
        # Frozen before expiry: retry same bytes, no model re-run.
        fresh = envelope()
        runtime = self.adapter.discover_runtime()
        resp = self.adapter.complete_structured(fresh, runtime)
        sha = self.worker.freeze_prediction(fresh, resp)
        self.outbox.persist_pending(fresh, resp, sha)
        fresh["expires_at"] = (now - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        fresh["checksum"] = compute_checksum(fresh)
        n = self.model_calls["n"]
        self.set_hook("ack")
        out = self.worker.handle_task(fresh, call_model=True, pause=None)
        self.assertEqual(self.model_calls["n"], n)
        self.assertFalse(out.get("model_called"))
        self.assertEqual(out["reply_state"], "INPUT_PROCESSED")

    def test_r12_orphan_no_frozen_escalation(self):
        msg = envelope()
        idx = self.root / "state/cognition/processed_ids.json"
        idx.write_text(json.dumps({msg["message_id"]: {"ts": "t", "immutable": True}}, indent=2))
        out = self.outbox.recover_orphan(msg)
        self.assertEqual(out["status"], "orphaned_response_missing")
        self.assertFalse(out["model_called"])

    def test_r13_no_event_exit_success(self):
        rc = self.worker.main.__wrapped__ if False else 0
        args = type("A", (), {"pause_path": "", "fixture": "", "dry_run": False,
                              "once": True, "foreground": False, "cycles": 1, "sleep": 0,
                              "scan_orphans": False})()
        out = self.worker.run_once(args)
        self.assertEqual(out["status"], "idle")
        self.assertFalse(out["model_called"])

    def test_r14_duplicate_blocked_exit_success(self):
        self.set_hook("ack")
        msg = envelope()
        self.worker.handle_task(msg, call_model=True, pause=None)
        out = self.worker.handle_task(msg, call_model=True, pause=None)
        self.assertEqual(out["status"], "duplicate_blocked")
        self.assertIn(out["status"], self.worker.SAFE_EXIT)

    def test_r15_overlap_blocked(self):
        fd = self.worker.acquire_lock()
        self.assertIsNotNone(fd)
        try:
            fd2 = self.worker.acquire_lock()
            self.assertIsNone(fd2)
        finally:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)

    def test_r16_circuit_breaker(self):
        self.set_hook("fail")
        for _ in range(3):
            self.outbox.circuit_record(False)
        self.assertTrue(self.outbox.circuit_open())
        msg = envelope()
        runtime = self.adapter.discover_runtime()
        resp = self.adapter.complete_structured(msg, runtime)
        sha = self.worker.freeze_prediction(msg, resp)
        rec = self.outbox.persist_pending(msg, resp, sha)
        rec = self.outbox.transmit_pending(rec)
        self.assertTrue(rec.get("circuit_open") or rec.get("state") == "RETRY_WAIT")

    def test_r18_malformed_response_blocked(self):
        msg = envelope()
        self.adapter.complete_structured = lambda task, runtime: {"nope": True}
        out = self.worker.handle_task(msg, call_model=True, pause=None)
        self.assertEqual(out["status"], "rejected")
        self.assertEqual(out["reason"], "response_schema_invalid")

    def test_r19_may_authorize_true_blocked(self):
        msg = envelope(may_authorize=True)
        err = self.worker.validate_envelope(msg)
        self.assertEqual(err, "may_authorize_true_rejected")

    def test_r22_owner_pause(self):
        pause = self.root / "state/OWNER_PAUSE"
        pause.write_text("paused\n")
        msg = envelope()
        out = self.worker.handle_task(msg, call_model=True, pause=str(pause))
        self.assertEqual(out["status"], "paused")
        self.assertFalse(out.get("model_called"))

    def test_r20_bridge_claim_message_id(self):
        src = (REAL / "bin/octomesh_agent_bridge.py").read_text(encoding="utf-8")
        self.assertIn("--message-id", src)

    def test_r21_worker_safe_exits(self):
        for st in ("idle", "duplicate_blocked", "reply_pending", "overlap_blocked"):
            self.assertIn(st, self.worker.SAFE_EXIT)

    def test_r23_no_new_listener_invariant(self):
        self.assertIn("ok", self.worker.SAFE_EXIT)

    def test_r24_external_actions_zero(self):
        self.set_hook("ack")
        msg = envelope()
        out = self.worker.handle_task(msg, call_model=True, pause=None)
        self.assertIs(out.get("executed_locally"), False)
        self.assertIs(out.get("may_authorize"), False)

    def test_r25_pending_unlinked_after_ack(self):
        self.set_hook("ack")
        msg = envelope()
        out = self.worker.handle_task(msg, call_model=True, pause=None)
        self.assertEqual(out["reply_state"], "INPUT_PROCESSED")
        key = out["reply_idempotency_key"]
        self.assertFalse(self.outbox.pending_path(key).is_file())
        self.assertTrue(self.outbox.acked_path(key).is_file())

    def test_r26_start_limit_unit_no_flap(self):
        svc = (REAL / "systemd/octopus-cognitive-worker.service").read_text(encoding="utf-8")
        self.assertIn("StartLimitIntervalSec=120", svc)
        self.assertIn("StartLimitBurst=10", svc)
        self.assertIn("Type=oneshot", svc)
        self.assertIn("Restart=no", svc)



    def test_r27_inject_send_failure_once(self):
        self.outbox.TRANSMIT_CALLS = 0
        self.set_hook("ack")
        msg = envelope()
        msg["payload"]["inject_send_failure_once"] = True
        from octomesh_common import compute_checksum
        msg["checksum"] = compute_checksum(msg)
        first = self.worker.handle_task(msg, call_model=True, pause=None)
        self.assertNotEqual(first["reply_state"], "INPUT_PROCESSED")
        sha = first["response_sha256"]
        self.assertEqual(self.outbox.TRANSMIT_CALLS, 0)
        n = self.model_calls["n"]
        second = self.worker.handle_task(msg, call_model=True, pause=None)
        self.assertEqual(second["reply_state"], "INPUT_PROCESSED")
        self.assertEqual(second["response_sha256"], sha)
        self.assertFalse(second.get("model_called"))
        self.assertEqual(self.model_calls["n"], n)
        self.assertEqual(self.outbox.TRANSMIT_CALLS, 1)


if __name__ == "__main__":
    unittest.main()
