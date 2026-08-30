#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_runtime.py — unit tests for agi2027_control.runtime.

These test the CONTROL PRIMITIVES in isolation. They do NOT prove the primitives
are wired into live production paths — that is reported separately as
NEEDS_OWNER_HOOK / STAGED (0 production readers verified). A green run here means
the primitives behave correctly; it is not a green light for the organism.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
OPS = HERE.parents[1]  # _ops
if str(OPS) not in sys.path:
    sys.path.insert(0, str(OPS))

from agi2027_control.runtime import (  # noqa: E402
    AdaptiveValueLedger,
    ControlPlane,
    FuguFootprint,
    IdempotencyStore,
    OutboundWriteAheadLedger,
    PolicyGate,
    ProjectFAdapter,
)


class TestG03WriteAhead(unittest.TestCase):
    def test_crash_before_settle_never_auto_resends(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = OutboundWriteAheadLedger(Path(d) / "outbound.sqlite3")
            try:
                payload = {"to": "client@example.invalid", "body": "hello"}

                first = ledger.begin_sending("eff-1", "lead-1", payload)
                self.assertEqual(first["state"], "NEW")
                self.assertTrue(first["allow_send"])

                recovered = ledger.recover_pending(older_than_seconds=0)
                self.assertEqual(len(recovered), 1)
                self.assertEqual(recovered[0]["state"], "needs_owner")
                self.assertFalse(recovered[0]["auto_resend"])

                check = ledger.can_auto_send("eff-1", payload)
                self.assertFalse(check["allow_send"])

                dup = ledger.begin_sending("eff-1", "lead-1", payload)
                self.assertEqual(dup["state"], "DUPLICATE")
                self.assertFalse(dup["allow_send"])
            finally:
                ledger.close()

    def test_payload_conflict_blocks_send(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = OutboundWriteAheadLedger(Path(d) / "outbound.sqlite3")
            try:
                ledger.begin_sending("eff-1", "lead-1", {"a": 1})
                conflict = ledger.begin_sending("eff-1", "lead-1", {"a": 2})
                self.assertEqual(conflict["state"], "CONFLICT")
                self.assertFalse(conflict["allow_send"])
            finally:
                ledger.close()

    def test_owner_retry_requires_new_effect_id(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = OutboundWriteAheadLedger(Path(d) / "outbound.sqlite3")
            try:
                ledger.begin_sending("eff-1", "lead-1", {"a": 1})
                ledger.recover_pending(0)
                res = ledger.owner_resolution("eff-1", "retry_with_new_effect_id")
                self.assertTrue(res["ok"])
                self.assertEqual(res["state"], "needs_new_effect_id")
            finally:
                ledger.close()


class TestIdempotencyAndPolicy(unittest.TestCase):
    def test_duplicate_vs_conflict(self):
        with tempfile.TemporaryDirectory() as d:
            idem = IdempotencyStore(Path(d) / "idem.sqlite3")
            try:
                self.assertEqual(idem.begin("act", {"x": 1})["state"], "NEW")
                self.assertEqual(idem.begin("act", {"x": 1})["state"], "DUPLICATE")
                self.assertEqual(idem.begin("act", {"x": 2})["state"], "CONFLICT")
            finally:
                idem.close()

    def test_policy_fail_closed(self):
        gate = PolicyGate({"repair.x"})
        self.assertFalse(gate.decide({"action_id": "repair.x", "kind": "shell"}, {"is_owner": True})["allow"])
        self.assertFalse(gate.decide({"action_id": "repair.x", "kind": "code_repair"}, {"is_owner": False})["allow"])
        self.assertFalse(gate.decide({"action_id": "repair.x", "kind": "send"}, {"is_owner": True})["allow"])
        self.assertTrue(gate.decide(
            {"action_id": "repair.x", "kind": "send", "owner_approved": True, "safety_gate": True},
            {"is_owner": True},
        )["allow"])


class TestProjectF(unittest.TestCase):
    def test_blocked_without_credentials_no_fake_green(self):
        old_base = os.environ.pop("PROJECTF_API_BASE_URL", None)
        old_token = os.environ.pop("PROJECTF_API_TOKEN", None)
        try:
            adapter = ProjectFAdapter()
            st = adapter.status()
            self.assertEqual(st["status"], "BLOCKED")
            res = adapter.build_module({"name": "demo"})
            self.assertFalse(res["ok"])
            self.assertEqual(res["status"], "BLOCKED")
            self.assertFalse(res["fake_green"])
        finally:
            if old_base is not None:
                os.environ["PROJECTF_API_BASE_URL"] = old_base
            if old_token is not None:
                os.environ["PROJECTF_API_TOKEN"] = old_token

    def test_configured_but_not_approved_does_not_call_network(self):
        os.environ["PROJECTF_API_BASE_URL"] = "https://example.invalid"
        os.environ["PROJECTF_API_TOKEN"] = "dummy"
        try:
            res = ProjectFAdapter().build_module({"name": "demo"})
            self.assertFalse(res["ok"])
            self.assertEqual(res["status"], "READY_NOT_CALLED")
        finally:
            os.environ.pop("PROJECTF_API_BASE_URL", None)
            os.environ.pop("PROJECTF_API_TOKEN", None)


class TestAdaptiveValue(unittest.TestCase):
    def test_low_impact_never_auto_deletes(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = AdaptiveValueLedger(Path(d) / "value.jsonl")
            ledger.record("leg-x", "expensive_no_output", "production",
                          output_score=0, cost_score=2, risk_score=1)
            score = ledger.score("leg-x")
            self.assertTrue(score["low_impact"])
            self.assertFalse(score["auto_delete"])

    def test_no_signal_is_not_low_impact(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = AdaptiveValueLedger(Path(d) / "value.jsonl")
            score = ledger.score("leg-y")
            self.assertEqual(score["verdict"], "INSUFFICIENT_SIGNAL")
            self.assertFalse(score["low_impact"])


class TestControlPlane(unittest.TestCase):
    def test_non_owner_denied(self):
        with tempfile.TemporaryDirectory() as d:
            cp = ControlPlane(Path(d))
            try:
                res = cp.handle("/ops", {"is_owner": False})
                self.assertFalse(res["ok"])
                self.assertEqual(res["status"], "DENIED")
            finally:
                cp.idem.close()

    def test_execute_safe_flag_is_staged_not_wired_and_rollback(self):
        with tempfile.TemporaryDirectory() as d:
            cp = ControlPlane(Path(d))
            try:
                res = cp.handle("/repair execute repair.value.ledger", {"is_owner": True})
                self.assertTrue(res["ok"])
                self.assertEqual(res["status"], "APPLIED")
                self.assertTrue(res["staged_not_wired"])  # honest: not wired into prod
                self.assertEqual(cp.flags.get("OCTOPUS_WIRE_VALUE_LEDGER"), "1")

                rb = cp.handle("/repair rollback repair.value.ledger", {"is_owner": True})
                self.assertTrue(rb["ok"])
                self.assertEqual(rb["status"], "ROLLED_BACK")
                self.assertEqual(cp.flags.get("OCTOPUS_WIRE_VALUE_LEDGER"), "0")
            finally:
                cp.idem.close()

    def test_g03_repair_enables_live_wal_flag_and_rolls_back(self):
        with tempfile.TemporaryDirectory() as d:
            cp = ControlPlane(Path(d))
            try:
                res = cp.handle("/repair execute repair.g03.writeahead_outbound", {"is_owner": True})
                self.assertTrue(res["ok"])
                self.assertEqual(res["status"], "APPLIED")
                self.assertTrue(res["live_wired"])
                self.assertEqual(cp.flags.get("OCTOPUS_WIRE_LEAD_OUTBOUND_WAL"), "1")
                rb = cp.handle("/repair rollback repair.g03.writeahead_outbound", {"is_owner": True})
                self.assertTrue(rb["ok"])
                self.assertEqual(cp.flags.get("OCTOPUS_WIRE_LEAD_OUTBOUND_WAL"), "0")
            finally:
                cp.idem.close()

    def test_unknown_command_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            cp = ControlPlane(Path(d))
            try:
                res = cp.handle("/danger", {"is_owner": True})
                self.assertFalse(res["ok"])
                self.assertEqual(res["status"], "UNKNOWN_COMMAND")
            finally:
                cp.idem.close()

    def test_outbound_status_and_recover_are_owner_visible(self):
        with tempfile.TemporaryDirectory() as d:
            cp = ControlPlane(Path(d))
            try:
                ledger = OutboundWriteAheadLedger(Path(d) / "_ops" / "agi2027_runtime" / "outbound-effects.sqlite3")
                try:
                    ledger.begin_sending("eff-owner", "lead-owner", {"x": 1})
                finally:
                    ledger.close()
                st = cp.handle("/outbound", {"is_owner": True})
                self.assertTrue(st["ok"])
                self.assertIn("sending", st["counts"])
                rec = cp.handle("/outbound recover", {"is_owner": True})
                self.assertTrue(rec["ok"])
                self.assertFalse(rec["auto_resend"])
            finally:
                cp.idem.close()

    def test_projectf_status_visible_without_credentials(self):
        with tempfile.TemporaryDirectory() as d:
            old_base = os.environ.pop("PROJECTF_API_BASE_URL", None)
            old_token = os.environ.pop("PROJECTF_API_TOKEN", None)
            cp = ControlPlane(Path(d))
            try:
                res = cp.handle("/projectf", {"is_owner": True})
                self.assertTrue(res["ok"])
                self.assertEqual(res["projectf"]["status"], "BLOCKED")
            finally:
                cp.idem.close()
                if old_base is not None:
                    os.environ["PROJECTF_API_BASE_URL"] = old_base
                if old_token is not None:
                    os.environ["PROJECTF_API_TOKEN"] = old_token


class TestFuguFootprint(unittest.TestCase):
    def test_footprint_scan_is_scoped_not_full_drive(self):
        # scan a tiny temp dir, not the whole vault — proves the scanner respects a root
        with tempfile.TemporaryDirectory() as d:
            Path(d, "a.py").write_text("import fugu\n", encoding="utf-8")
            fp = FuguFootprint(Path(d)).scan()
            self.assertEqual(fp["scan_root"], str(Path(d)))
            self.assertGreaterEqual(fp["total_lines"], 1)
            self.assertGreaterEqual(fp["files_with_fugu"], 1)



class TestLiveWiringHooks(unittest.TestCase):
    def test_control_result_formatter_is_owner_safe_text(self):
        from agi2027_control.integration import format_control_result
        txt = format_control_result({"ok": True, "status": "OK", "repairs": ["repair.value.ledger"]})
        self.assertIn("Octopus control", txt)
        self.assertIn("repair.value.ledger", txt)

    def test_lead_transport_wal_blocks_duplicate_when_flag_on(self):
        import importlib

        legs = OPS / "legs"
        if str(legs) not in sys.path:
            sys.path.insert(0, str(legs))
        mod = importlib.import_module("lead_outbound_transport")
        saved = {k: os.environ.get(k) for k in [
            "OCTOPUS_WIRE_LEAD_OUTBOUND_WAL", "OCTOPUS_SMTP_HOST", "OCTOPUS_SMTP_PORT",
            "OCTOPUS_SMTP_USER", "OCTOPUS_SMTP_FROM", "OCTOPUS_SMTP_PASS"]}
        try:
            os.environ["OCTOPUS_WIRE_LEAD_OUTBOUND_WAL"] = "1"
            os.environ["OCTOPUS_SMTP_HOST"] = "smtp.example.invalid"
            os.environ["OCTOPUS_SMTP_PORT"] = "587"
            os.environ["OCTOPUS_SMTP_USER"] = "owner@example.invalid"
            os.environ["OCTOPUS_SMTP_FROM"] = "owner@example.invalid"
            os.environ["OCTOPUS_SMTP_PASS"] = "dummy-secret"
            for suffix in ("", "-wal", "-shm"):
                try:
                    (OPS / "agi2027_runtime" / ("outbound-effects.sqlite3" + suffix)).unlink()
                except FileNotFoundError:
                    pass
            candidate = {"lead_id": "L-WAL-1", "contact": {"email": "client@example.invalid"}}
            draft = {"subject": "Quote QT-20260802-001", "body": "hello"}
            calls = []

            def fake_send(*args):
                calls.append(args)

            first = mod.send(candidate, draft, send_impl=fake_send)
            second = mod.send(candidate, draft, send_impl=fake_send)
            self.assertEqual(first["status"], "SENT")
            self.assertTrue(first["sent"])
            self.assertEqual(second["status"], "DUPLICATE")
            self.assertEqual(len(calls), 1)
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


if __name__ == "__main__":
    unittest.main()
