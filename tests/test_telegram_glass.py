"""telegram_glass — the read-only command surface must never lie.

Three invariants are load-bearing (owner directive 2026-08-22: Telegram is
a read-only command bus, never an actuator):

  1. every answer carries a receipt (run_id, ts, node_id, sources) — a
     "Done" without a receipt cannot be constructed, including on the
     fail-closed path;
  2. an unverifiable claim is answered UNKNOWN, never green, and a
     malformed source fails closed instead of inventing a number;
  3. may_authorize is False always; the module has no send path, no token
     read and no network call — bot wiring stays with the owner's runtime.

No test here opens a socket or touches a token.
"""
from __future__ import annotations

import ast
import json
import os
import tempfile
import unittest
import uuid

from ofn.adapters import telegram_glass as tg
from ofn.kernel.errors import FailClosedError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLASS = os.path.join(ROOT, "ofn", "adapters", "telegram_glass.py")

TS = "2026-09-03T12:00:00Z"
RUN = "00000000-0000-4000-8000-000000000001"


def _rows():
    return [
        {"record_id": "PAY-1", "kind": "payment_claim",
         "verification_status": "VERIFIED", "lead_id": "L1",
         "ts": "2026-09-01T10:00:00Z"},
        {"record_id": "PAY-2", "kind": "payment_claim",
         "verification_status": "UNVERIFIED_NO_RECEIPT",
         "ts": "2026-09-02T10:00:00Z"},
        {"record_id": "Q-1", "kind": "quote", "ts": "2026-09-01T09:00:00Z"},
        {"record_id": "SCORE-1", "kind": "outcome_score", "level": "quote",
         "ts": "2026-09-01T11:00:00Z"},
    ]


def _self_envelope():
    return {"schema": "octopus.self-model.v2", "status": "degraded",
            "generated_at": TS,
            "data": {"sensors": [{"status": "healthy"}, {"status": "stale"}],
                     "processes": [], "capabilities": [], "unknowns": ["u"]},
            "warnings": ["sensors_stale"]}


def _malformed():
    return {
        "/status": {"git_head": 12, "dirty_files": "two",
                    "board_config_hashes": "equal-i-promise"},
        "/self": {"self_model_envelope": {"schema": "nope", "data": {}}},
        "/doctor": {"doctor_snapshot": {"units": "all-fine-trust-me"}},
        "/money": {"ledger_rows": "1 verified payment"},
        "/queue": {"open_prs": {"number": "seven"}},
        "/receipts": {"ledger_rows": [{"kind": 5}]},
    }


def _healthy():
    return {
        "/status": {"git_head": "a" * 40, "dirty_files": 2,
                    "board_config_hashes": {"138": "h1", "180": "h1",
                                            "182": "h1"}},
        "/self": {"self_model_envelope": _self_envelope()},
        "/doctor": {"doctor_snapshot": {"units": [
            {"name": "octopus-router.service", "state": "active"},
            {"name": "octopus-heartbeat.timer", "state": "active"}]}},
        "/money": {"ledger_rows": _rows()},
        "/queue": {"open_prs": [{"number": 7, "title": "feat: x"},
                                {"number": 9, "title": "fix: y"}]},
        "/receipts": {"ledger_rows": _rows()},
    }


def _route_all(snapshot):
    """snapshot maps command → its inputs ({} maps to no inputs at all)."""
    return {c: tg.route(c, snapshot.get(c), run_id=RUN, now_iso=TS)
            for c in tg.COMMANDS}


def _all_responses():
    """Healthy, absent, malformed, unknown-command and both node variants —
    every path the router can take."""
    responses = list(_route_all(_healthy()).values())
    responses += list(_route_all({}).values())
    responses += list(_route_all(_malformed()).values())
    responses.append(tg.route("/nope", {}, run_id=RUN, now_iso=TS))
    responses.append(tg.route("/status", {}, run_id=RUN, now_iso=TS,
                              node_id="SENSORIUM"))
    return responses


class TestRouterHealthy(unittest.TestCase):
    """A readable source is answered with numbers, never with vibes."""

    def test_all_six_commands_read_green(self):
        for cmd, resp in _route_all(_healthy()).items():
            self.assertEqual(resp["status"], "ok", cmd)
            self.assertEqual(resp["loop"]["CLAIM_VERIFIED"], "done", cmd)

    def test_status_counts_board_coherence(self):
        data = tg.route("/status", _healthy()["/status"],
                        run_id=RUN, now_iso=TS)["data"]
        self.assertEqual(data["git_head"], "a" * 40)
        self.assertEqual(data["dirty_files"], 2)
        self.assertEqual(data["board_config_coherence"], "coherent")
        self.assertEqual(data["boards_reporting"], 3)

    def test_status_incoherent_boards_are_not_green(self):
        snap = {"git_head": "a" * 40, "dirty_files": 0,
                "board_config_hashes": {"138": "h1", "180": "h2"}}
        resp = tg.route("/status", snap, run_id=RUN, now_iso=TS)
        self.assertEqual(resp["data"]["board_config_coherence"], "incoherent")
        # the fact is verified, but it is an alarm — never ok
        self.assertEqual(resp["status"], "degraded")
        self.assertEqual(resp["loop"]["CLAIM_VERIFIED"], "done")

    def test_money_counts_verified_and_unpriced(self):
        data = tg.route("/money", _healthy()["/money"],
                        run_id=RUN, now_iso=TS)["data"]
        self.assertEqual(data["verified_payment_count"], 1)
        self.assertEqual(data["unverified_payment_count"], 1)
        self.assertEqual(data["unpriced_quote_count"], 1)

    def test_receipts_latest_first_capped(self):
        rows = [{"record_id": f"PAY-{i}", "kind": "payment_claim",
                 "verification_status": "VERIFIED",
                 "ts": f"2026-09-0{i}T00:00:00Z"} for i in range(1, 8)]
        data = tg.route("/receipts", {"ledger_rows": rows},
                        run_id=RUN, now_iso=TS)["data"]
        self.assertEqual(data["payment_rows_total"], 7)
        self.assertEqual(len(data["receipts"]), tg.MAX_RECEIPTS_SHOWN)
        self.assertEqual(data["receipts"][0]["record_id"], "PAY-7")

    def test_doctor_counts_failed_units_only(self):
        units = [{"name": "a.service", "state": "active"},
                 {"name": "b.service", "state": "active"},
                 {"name": "c.service", "state": "failed"}]
        data = tg.route("/doctor", {"doctor_snapshot": {"units": units}},
                        run_id=RUN, now_iso=TS)["data"]
        self.assertEqual(data["doctor_units"], 3)
        self.assertEqual(data["failed_units"], 1)
        self.assertEqual(data["failed_names"], ["c.service"])

    def test_failed_unit_is_degraded_not_green(self):
        """A verified alarm is not 'ok' — the glass must not paint a green
        screen over a failed unit; but the claim IS verified."""
        snap = {"doctor_snapshot": {"units": [
            {"name": "octopus-router.service", "state": "failed"}]}}
        resp = tg.route("/doctor", snap, run_id=RUN, now_iso=TS)
        self.assertEqual(resp["status"], "degraded")
        self.assertEqual(resp["loop"]["CLAIM_VERIFIED"], "done")
        self.assertEqual(resp["data"]["failed_units"], 1)
        self.assertIn("failed_units", resp["warnings"][0])

    def test_self_summarizes_envelope_without_reaching(self):
        data = tg.route("/self", _healthy()["/self"],
                        run_id=RUN, now_iso=TS)["data"]
        self.assertEqual(data["status"], "degraded")
        self.assertEqual(data["readings_total"], 2)
        self.assertEqual(data["readings_healthy"], 1)
        self.assertEqual(data["warnings"], 1)
        self.assertEqual(data["unknowns_declared"], 1)


class TestRouterAbsentSourceAnswersUnknown(unittest.TestCase):
    """No source, no answer: UNKNOWN with the source named — never a guess,
    never a green screen painted over a hole."""

    def test_absent_sources_answer_unknown_not_green(self):
        for cmd, resp in _route_all({}).items():
            self.assertEqual(resp["status"], "unknown", cmd)
            self.assertEqual(resp["loop"]["CLAIM_VERIFIED"], "skipped", cmd)
            self.assertTrue(resp["sources"], cmd)
            self.assertTrue(all(s["state"] == "absent" for s in resp["sources"]),
                            cmd)
            # not a single number was invented for a missing source
            self.assertTrue(all(v == tg.UNKNOWN
                                for v in resp["data"].values()), cmd)

    def test_each_absent_field_is_explicit(self):
        cases = {
            "/money": "money", "/queue": "open_pr_count",
            "/self": "self_model", "/receipts": "receipts",
        }
        for cmd, field in cases.items():
            resp = tg.route(cmd, {}, run_id=RUN, now_iso=TS)
            self.assertEqual(resp["data"][field], tg.UNKNOWN, cmd)
        self.assertEqual(tg.route("/doctor", {}, run_id=RUN, now_iso=TS)
                         ["data"]["failed_units"], tg.UNKNOWN)

    def test_missing_ledger_file_is_named(self):
        resp = tg.route("/money", {"ledger_rows": None,
                                   "ledger_path": "runs/none.jsonl"},
                        run_id=RUN, now_iso=TS)
        self.assertEqual(resp["status"], "unknown")
        self.assertIn("runs/none.jsonl", resp["sources"][0]["source"])

    def test_unknown_command_is_not_green_and_is_receipted(self):
        resp = tg.route("/deploy-everything", {}, run_id=RUN, now_iso=TS)
        self.assertEqual(resp["status"], "unknown_command")
        self.assertEqual(resp["loop"]["INTENT_DETECTED"], "skipped")
        self.assertTrue(resp["sources"])
        self.assertEqual(tg.receipt_of(resp)["run_id"], RUN)
        self.assertIn("known_commands", resp["data"])
        self.assertEqual(resp["data"]["known_commands"], list(tg.COMMANDS))


class TestRouterMalformedFailsClosed(unittest.TestCase):
    """A malformed source is refused inside a receipted error — nothing is
    answered in its place, no plausible number is invented."""

    def test_malformed_sources_error_with_receipt(self):
        for cmd, resp in _route_all(_malformed()).items():
            self.assertEqual(resp["status"], "error", cmd)
            self.assertEqual(resp["loop"]["CLAIM_VERIFIED"], "skipped", cmd)
            self.assertIn("fail-closed", resp["warnings"][0], cmd)
            self.assertEqual(tg.receipt_of(resp)["run_id"], RUN)
            self.assertEqual(resp["sources"][0]["state"], "malformed", cmd)

    def test_malformed_answer_invents_no_numbers(self):
        resp = tg.route("/money", {"ledger_rows": "lots"},
                        run_id=RUN, now_iso=TS)
        self.assertEqual(set(resp["data"]), {"error"})

    def test_snapshot_not_a_mapping_fails_closed(self):
        resp = tg.route("/status", "trust me", run_id=RUN, now_iso=TS)
        self.assertEqual(resp["status"], "error")

    def test_unknown_node_tag_raises(self):
        with self.assertRaises(FailClosedError):
            tg.route("/status", {}, run_id=RUN, now_iso=TS, node_id="MARS")


class TestReceiptInvariant(unittest.TestCase):
    """Every answer IS a receipt. 'Done' without one is unexpressible."""

    def test_every_response_on_every_path_carries_a_receipt(self):
        for resp in _all_responses():
            receipt = tg.receipt_of(resp)          # raises if any field missing
            self.assertEqual(receipt["run_id"], RUN)
            self.assertEqual(receipt["ts"], TS)
            self.assertIn(receipt["node_id"], tg.NODE_IDS)
            self.assertIsInstance(receipt["sources"], list)
            self.assertTrue(receipt["sources"])

    def test_run_id_is_a_uuid(self):
        resp = tg.route("/status", {})             # no injected run_id
        self.assertEqual(str(uuid.UUID(resp["run_id"])), resp["run_id"])

    def test_execution_receipt_done_iff_receipt_exists(self):
        for resp in _all_responses():
            has_receipt = all(k in resp for k in
                              ("run_id", "ts", "node_id", "sources"))
            done = resp["loop"]["EXECUTION_RECEIPT"] == "done"
            self.assertEqual(done, has_receipt, resp["command"])

    def test_claim_verified_iff_claims_were_verified(self):
        for resp in _all_responses():
            done = resp["loop"]["CLAIM_VERIFIED"] == "done"
            self.assertEqual(done, resp["status"] in tg._CLAIM_VERIFIED_STATUSES,
                             (resp["command"], resp["status"]))

    def test_done_without_receipt_cannot_be_constructed(self):
        # stripping a receipt field makes the answer unpublishable — the
        # gate refuses it instead of letting "done" pass unreceipted
        resp = tg.route("/money", _healthy()["/money"], run_id=RUN, now_iso=TS)
        for stripped_field in ("run_id", "ts", "node_id", "sources"):
            stripped = {k: v for k, v in resp.items() if k != stripped_field}
            with self.assertRaises(FailClosedError, msg=stripped_field):
                tg.receipt_of(stripped)

    def test_loop_vocabulary_is_the_seven_stage_order(self):
        self.assertEqual(tg.LOOP_STAGES, (
            "USER_MESSAGE_ACCEPTED", "INTENT_DETECTED", "MODEL_STARTED",
            "CLAIM_VERIFIED", "PROPOSAL_CREATED", "EXECUTION_RECEIPT",
            "RUN_COMPLETED"))

    def test_model_and_proposal_stages_never_occur_here(self):
        for resp in _all_responses():
            self.assertEqual(resp["loop"]["MODEL_STARTED"], "skipped")
            self.assertEqual(resp["loop"]["PROPOSAL_CREATED"], "skipped")

    def test_run_completed_on_every_terminating_path(self):
        for resp in _all_responses():
            self.assertEqual(resp["loop"]["RUN_COMPLETED"], "done")


class TestMayAuthorizeInvariant(unittest.TestCase):
    """Read-only command bus: no authorize, no send, no token, no network."""

    def test_may_authorize_is_false_on_every_path(self):
        for resp in _all_responses():
            self.assertIs(resp["may_authorize"], False)
            self.assertIs(resp["read_only"], True)

    def test_node_tags_are_the_three_named_nodes(self):
        for node in tg.NODE_IDS:
            resp = tg.route("/status", {}, run_id=RUN, now_iso=TS, node_id=node)
            self.assertEqual(resp["node_id"], node)

    def test_source_has_no_send_path_or_token_or_network(self):
        with open(GLASS, encoding="utf-8") as fh:
            src = fh.read()
        for absent in ("sendMessage", "getUpdates", "sendPhoto",
                       "answerCallbackQuery", "TELEGRAM_BOT_TOKEN",
                       "api.telegram.org", "requests.", "urllib", "aiohttp",
                       "socket", "http.client", "send_authorized",
                       "quote_sent"):
            self.assertNotIn(absent, src)
        # the only subprocess use is local, read-only git
        self.assertEqual(src.count("subprocess.run"), 2)
        self.assertIn('["git", "-C", str(root), "rev-parse", "HEAD"]', src)
        self.assertIn('["git", "-C", str(root), "status", "--porcelain"]', src)

    def test_imports_are_stdlib_plus_kernel_only(self):
        with open(GLASS, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        allowed_roots = {"datetime", "json", "subprocess", "uuid", "pathlib",
                         "typing", "ofn", "__future__"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertIn(alias.name.split(".")[0], allowed_roots)
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                self.assertIn((node.module or "").split(".")[0], allowed_roots)


class TestBuilders(unittest.TestCase):
    """Builders read local files only; a missing source is named, a broken
    ledger line fails closed (the ledger is tamper-evident — guessing
    defeats the tamper-evidence)."""

    def test_learning_snapshot_missing_file_named_not_invented(self):
        snap = tg.build_learning_snapshot("runs/does-not-exist.jsonl")
        self.assertIsNone(snap["ledger_rows"])
        self.assertEqual(snap["ledger_path"], "runs/does-not-exist.jsonl")
        self.assertEqual(snap["ledger_error"], "file-absent")

    def test_learning_snapshot_parses_jsonl_readonly(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ledger.jsonl")
            with open(path, "w", encoding="utf-8") as fh:
                for row in _rows():
                    fh.write(json.dumps(row) + "\n")
            snap = tg.build_learning_snapshot(path)
            self.assertEqual(len(snap["ledger_rows"]), 4)
            resp = tg.route("/money", snap, run_id=RUN, now_iso=TS)
            self.assertEqual(resp["data"]["verified_payment_count"], 1)
            self.assertEqual(resp["status"], "ok")

    def test_learning_snapshot_malformed_line_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ledger.jsonl")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(_rows()[0]) + "\n")
                fh.write("{not json}\n")
            with self.assertRaises(FailClosedError):
                tg.build_learning_snapshot(path)

    def test_status_snapshot_reads_local_git(self):
        snap = tg.build_status_snapshot(ROOT)
        self.assertIsNotNone(snap["git_head"])
        self.assertEqual(len(snap["git_head"]), 40)
        self.assertIsInstance(snap["dirty_files"], int)

    def test_self_snapshot_absent_and_injected(self):
        self.assertIsNone(tg.build_self_snapshot(None)["self_model_envelope"])
        snap = tg.build_self_snapshot(lambda: _self_envelope())
        self.assertEqual(snap["self_model_envelope"]["schema"],
                         "octopus.self-model.v2")

    def test_self_snapshot_rejects_non_mapping_envelope(self):
        with self.assertRaises(FailClosedError):
            tg.build_self_snapshot(lambda: "healthy-trust-me")

    def test_board_coherence_with_one_reporter_is_unknown(self):
        resp = tg.route("/status", {"git_head": "a" * 40, "dirty_files": 0,
                                    "board_config_hashes": {"138": "h1"}},
                        run_id=RUN, now_iso=TS)
        self.assertEqual(resp["data"]["board_config_coherence"], tg.UNKNOWN)
        self.assertEqual(resp["status"], "unknown")


class TestRenderText(unittest.TestCase):
    """The rendered glass answer stays honest in Persian too."""

    def test_unknown_renders_as_namaaloom_not_a_number(self):
        text = tg.render_text(tg.route("/money", {}, run_id=RUN, now_iso=TS))
        self.assertIn("نامعلوم", text)
        self.assertIn("may_authorize=false", text)
        self.assertIn("LAPTOP", text)

    def test_healthy_renders_receipt_head_and_counts(self):
        text = tg.render_text(tg.route("/money", _healthy()["/money"],
                                       run_id=RUN, now_iso=TS))
        self.assertIn(RUN[:8], text)
        self.assertIn("verified_payment_count: 1", text)
        self.assertIn("فقط‌خواندنی", text)


if __name__ == "__main__":
    unittest.main()
