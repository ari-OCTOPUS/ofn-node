import hashlib
import json
import os
import sqlite3
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

from ofn.organism.event_kernel.kernel import EventKernel
from ofn.organism.growth.capabilities import atomic_write_registry, load_registry
from ofn.organism.persistence.db import connect
from ofn.organism.runtime.app import serve
from ofn.organism.runtime.lan_auth import TOKEN_HEADER, reset_failures_for_tests
from ofn.organism.runtime.organism_http import organism_request


FAKE_TOKEN = "a" * 32


def cognitive_snapshot(con: sqlite3.Connection, files: dict[str, Path]) -> dict:
    names = {
        row[0]
        for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }

    def count(table: str) -> int:
        if table not in names:
            return 0
        return con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    def head(table: str, column: str):
        if table not in names:
            return None
        row = con.execute(f"SELECT MAX({column}) FROM {table}").fetchone()
        return row[0] if row else None

    hashes = {}
    for key, path in files.items():
        if path.exists():
            hashes[key] = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            hashes[key] = None
    return {
        "events": count("events"),
        "events_head": head("events", "node_seq"),
        "episodes": count("episodes"),
        "outbox": count("outbox"),
        "identity": count("identity_ledger"),
        "identity_head": head("identity_ledger", "sequence"),
        "memory_read_receipts": count("memory_read_receipts"),
        "decision_evidence": count("decision_evidence"),
        "files": hashes,
    }


class GetPurityAndLanTests(unittest.TestCase):
    def setUp(self):
        reset_failures_for_tests()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.db_path = Path(self.temp_dir.name) / "o.db"
        self.public = Path(self.temp_dir.name) / "public.json"
        self.registry = Path(self.temp_dir.name) / "capabilities.json"
        atomic_write_registry(
            load_registry(
                Path(
                    "/opt/octopus/lab/artifacts/capability-awakening/"
                    "02_capability_registry.json"
                )
            ),
            self.registry,
        )
        self.con = connect(self.db_path)
        self.addCleanup(self.con.close)
        self.kernel = EventKernel(self.con)
        env = {
            "OCTOPUS_GET_PURE": "1",
            "OCTOPUS_REQUIRE_LAN_TOKEN": "1",
            "OCTOPUS_LAN_TOKEN": FAKE_TOKEN,
            "OCTOPUS_LEARN_EXTERNAL": "0",
        }
        self.env_patch = patch.dict(os.environ, env, clear=False)
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)
        self.httpd = serve(
            self.con,
            self.kernel,
            port=0,
            public_status_path=self.public,
            capability_registry_path=self.registry,
        )
        self.addCleanup(self.httpd.server_close)
        self.addCleanup(self.httpd.shutdown)
        self.base = f"http://127.0.0.1:{self.httpd.server_port}"

    def _open(self, path, token=FAKE_TOKEN, method="GET", data=None):
        headers = {}
        if token is not None:
            headers[TOKEN_HEADER] = token
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(
            self.base + path,
            data=data,
            headers=headers,
            method=method,
        )
        return urllib.request.urlopen(req, timeout=3)

    def test_get_purity_zero_state_delta(self):
        files = {"public": self.public}
        before = cognitive_snapshot(self.con, files)
        paths = [
            "/api/v1/organism",
            "/api/v1/episodes",
            "/api/v1/utterance",
            "/api/v1/world",
            "/api/v1/self",
            "/api/v1/capabilities",
            "/health",
            "/api/v1/attestation",
        ]
        for path in paths:
            for _ in range(2):
                with self._open(path) as resp:
                    self.assertEqual(resp.status, 200)
        after = cognitive_snapshot(self.con, files)
        self.assertEqual(before, after)

    def test_eval_get_is_not_pure_command(self):
        try:
            self._open("/api/v1/eval")
            self.fail("eval GET should be 405")
        except urllib.error.HTTPError as exc:
            self.assertEqual(exc.code, 405)
            body = json.loads(exc.read())
            self.assertEqual(body["executable"], False)

    def test_loopback_health_without_token(self):
        with urllib.request.urlopen(self.base + "/health", timeout=3) as resp:
            self.assertEqual(resp.status, 200)

    def test_lan_data_without_token_rejected(self):
        try:
            urllib.request.urlopen(self.base + "/api/v1/organism", timeout=3)
            self.fail("expected 401")
        except urllib.error.HTTPError as exc:
            self.assertEqual(exc.code, 401)
            body = json.loads(exc.read())
            self.assertEqual(body, {"error": "unauthorized"})
            self.assertNotIn(FAKE_TOKEN, json.dumps(body))

    def test_invalid_token_rejected(self):
        try:
            self._open("/api/v1/organism", token="b" * 32)
            self.fail("expected 401")
        except urllib.error.HTTPError as exc:
            self.assertEqual(exc.code, 401)

    def test_valid_token_after_unauthorized_probe(self):
        try:
            urllib.request.urlopen(self.base + "/api/v1/organism", timeout=3)
        except urllib.error.HTTPError as exc:
            self.assertEqual(exc.code, 401)
        with self._open("/api/v1/organism") as resp:
            self.assertEqual(resp.status, 200)
        with self._open("/api/v1/organism") as resp:
            body = json.loads(resp.read())
        self.assertEqual(body["organism_id"], "board-life-001")
        self.assertEqual(body["autonomy_state"], "PROPOSE_ONLY")

    def test_client_helper_does_not_retry_401(self):
        first = organism_request(
            self.base + "/api/v1/organism",
            include_token=False,
            retries=5,
        )
        self.assertEqual(first.status, 401)
        self.assertEqual(first.kind, "auth_failure")

    def test_request_size_limit(self):
        try:
            self._open(
                "/api/v1/ask",
                method="POST",
                data=b"x" * (20 * 1024),
            )
            self.fail("expected 413")
        except urllib.error.HTTPError as exc:
            self.assertEqual(exc.code, 413)


if __name__ == "__main__":
    unittest.main()
