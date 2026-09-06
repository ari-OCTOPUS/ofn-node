"""Real HTTP contract for the read-only Cockpit V2 M1 integration."""

from __future__ import annotations

import hashlib
import hmac
import http.client
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path

from ofn.adapters.http_api import ApiApp, HostMap, serve
from ofn.kernel.auth import data_check_string, issue_session
from ofn.kernel.domain import PackSpec, TenantId
from ofn.kernel.tenancy import TenantRegistry
from ofn.run import load_cockpit_v2

NOW = 1_788_000_000
SECRET = "cockpit-v2-http-secret"
OWNER_ID = "5001"
PARTNER_ID = "7001"
OWNER_HOST = "panel.test"
PARTNER_HOST = "studio.test"
OWNER_TOKEN = "333:owner-token"
RESOURCES = ("status", "nodes", "legs", "queue", "audit", "version", "surface")


def _registry() -> TenantRegistry:
    return TenantRegistry({
        "studio": PackSpec(
            tenant=TenantId("studio"),
            capacity_units_per_week=5,
            quota_share=1.0,
        )
    })


def _init_data(token: str, user_id: str) -> str:
    fields = {
        "auth_date": str(NOW),
        "user": json.dumps({"id": int(user_id)}, separators=(",", ":")),
    }
    key = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(
        key, data_check_string(fields).encode(), hashlib.sha256
    ).hexdigest()
    return "&".join(f"{key}={value}" for key, value in fields.items())


class _ReadFixture:
    def __init__(self):
        self.calls: list[tuple[str, object]] = []

    def __call__(self, resource, query):
        self.calls.append((resource, query))
        envelope = {
            "api_version": "v2",
            "resource": resource,
            "data": {"items": []},
            "query": query,
        }
        return envelope, {"validator": f"{resource}-revision-1"}


class TestCockpitV2RealHttp(unittest.TestCase):
    def setUp(self):
        self.read = _ReadFixture()
        self.app = ApiApp(
            _registry(),
            HostMap(
                tenants={PARTNER_HOST: "studio"},
                owner_host=OWNER_HOST,
            ),
            bot_tokens={"studio": "studio-token", "__owner__": OWNER_TOKEN},
            session_secret=SECRET,
            owner_user_ids=(OWNER_ID,),
            partner_user_ids={"studio": (PARTNER_ID,)},
            now=lambda: NOW,
            owner_v2_read=self.read,
        )
        self.legacy = b"<!doctype html><title>legacy panel</title>"
        self.static = {
            "/index.html": self.legacy,
            "/cockpit-v2": b"<!doctype html><title>v2</title>",
            "/cockpit-v2/": b"<!doctype html><title>v2</title>",
            "/cockpit-v2/index.html": b"<!doctype html><title>v2</title>",
            "/cockpit-v2/app.js": b"export {};",
            "/cockpit-v2/module.mjs": b"export {};",
            "/cockpit-v2/app.css": b"body{}",
            "/cockpit-v2/manifest.webmanifest": b"{}",
            "/cockpit-v2/data.json": b"{}",
            "/cockpit-v2/icon.svg": b"<svg/>",
            "/cockpit-v2/icon.png": b"\x89PNG\r\n\x1a\n",
            "/cockpit-v2/font.woff2": b"wOF2",
        }
        self.server = serve(self.app, 0, static=self.static)
        self.thread = threading.Thread(
            target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]
        self.owner_session = issue_session(
            "owner", OWNER_ID, SECRET, now_epoch_s=NOW)
        self.partner_session = issue_session(
            "studio", PARTNER_ID, SECRET, now_epoch_s=NOW)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, method, path, *, host=OWNER_HOST, session=None,
                headers=None, body=b""):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        request_headers = {"Host": host}
        if session:
            request_headers["Authorization"] = "Bearer " + session
        request_headers.update(headers or {})
        connection.request(method, path, body=body, headers=request_headers)
        response = connection.getresponse()
        payload = response.read()
        result = response.status, payload, dict(response.getheaders())
        connection.close()
        return result

    def owner_get(self, path, **kw):
        return self.request(
            "GET", path, session=self.owner_session, **kw)

    def test_exact_seven_authenticated_routes_and_unknown_suffix(self):
        for resource in RESOURCES:
            with self.subTest(resource=resource):
                status, raw, headers = self.owner_get(
                    f"/api/v2/owner/{resource}")
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(raw)["resource"], resource)
                self.assertEqual(headers["Cache-Control"], "private, no-store")
                self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
                self.assertEqual(headers["Referrer-Policy"], "no-referrer")
        before = len(self.read.calls)
        status, _, _ = self.owner_get("/api/v2/owner/not-a-resource")
        self.assertEqual(status, 404)
        self.assertEqual(len(self.read.calls), before)

    def test_auth_matrix_and_auth_failure_never_becomes_304(self):
        path = "/api/v2/owner/status"
        cases = (
            (OWNER_HOST, None, 401),
            (OWNER_HOST, "not-a-session", 401),
            (OWNER_HOST, self.partner_session, 401),
            (PARTNER_HOST, self.partner_session, 404),
        )
        for host, session, expected in cases:
            with self.subTest(host=host, session=bool(session)):
                status, raw, headers = self.request(
                    "GET", path, host=host, session=session,
                    headers={"If-None-Match": 'W/"status-revision-1"'},
                )
                self.assertEqual(status, expected)
                self.assertNotEqual(status, 304)
                self.assertTrue(raw)
                self.assertNotIn("ETag", headers)
        self.assertEqual(self.read.calls, [])

    def test_wrong_methods_are_405_and_do_not_invoke_callback(self):
        for method in ("POST", "DELETE", "PUT", "PATCH"):
            for resource in RESOURCES:
                with self.subTest(method=method, resource=resource):
                    before = len(self.read.calls)
                    status, _, headers = self.request(
                        method, f"/api/v2/owner/{resource}",
                        session=self.owner_session,
                    )
                    self.assertEqual(status, 405)
                    self.assertEqual(headers.get("Allow"), "GET")
                    self.assertEqual(len(self.read.calls), before)

    def test_query_duplicates_blanks_and_decoding_reach_callback(self):
        status, raw, _ = self.owner_get(
            "/api/v2/owner/audit?kind=a&kind=b&empty=&encoded=a%2Fb")
        self.assertEqual(status, 200)
        expected = {
            "kind": ["a", "b"],
            "empty": [""],
            "encoded": ["a/b"],
        }
        self.assertEqual(self.read.calls[-1], ("audit", expected))
        self.assertEqual(json.loads(raw)["query"], expected)

    def test_etag_nonmatch_and_bodyless_matching_304(self):
        status, raw, headers = self.owner_get(
            "/api/v2/owner/queue",
            headers={"If-None-Match": 'W/"other"'},
        )
        self.assertEqual(status, 200)
        self.assertTrue(raw)
        etag = headers["ETag"]
        self.assertEqual(etag, 'W/"queue-revision-1"')

        status, raw, headers = self.owner_get(
            "/api/v2/owner/queue",
            headers={"If-None-Match": f'"unrelated", {etag}'},
        )
        self.assertEqual(status, 304)
        self.assertEqual(raw, b"")
        self.assertEqual(headers["Content-Length"], "0")
        self.assertEqual(headers["ETag"], etag)
        self.assertEqual(headers["Cache-Control"], "private, no-store")
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["Referrer-Policy"], "no-referrer")
        self.assertEqual(
            [resource for resource, _ in self.read.calls].count("queue"), 2)

    def test_static_shell_every_mime_and_legacy_bytes(self):
        expected = {
            "/cockpit-v2": "text/html; charset=utf-8",
            "/cockpit-v2/": "text/html; charset=utf-8",
            "/cockpit-v2/index.html": "text/html; charset=utf-8",
            "/cockpit-v2/app.js": "text/javascript; charset=utf-8",
            "/cockpit-v2/module.mjs": "text/javascript; charset=utf-8",
            "/cockpit-v2/app.css": "text/css; charset=utf-8",
            "/cockpit-v2/manifest.webmanifest":
                "application/manifest+json; charset=utf-8",
            "/cockpit-v2/data.json": "application/json; charset=utf-8",
            "/cockpit-v2/icon.svg": "image/svg+xml",
            "/cockpit-v2/icon.png": "image/png",
            "/cockpit-v2/font.woff2": "font/woff2",
        }
        for path, content_type in expected.items():
            with self.subTest(path=path):
                status, _, headers = self.request("GET", path)
                self.assertEqual(status, 200)
                self.assertEqual(headers["Content-Type"], content_type)
                self.assertEqual(headers["Cache-Control"], "no-store")
                self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
                self.assertEqual(headers["Referrer-Policy"], "no-referrer")
                if content_type.startswith("text/html"):
                    self.assertEqual(headers["X-Frame-Options"], "DENY")
                    self.assertIn("frame-ancestors 'none'",
                                  headers["Content-Security-Policy"])
        for path in ("/", "/index.html"):
            status, raw, _ = self.request("GET", path)
            self.assertEqual(status, 200)
            self.assertEqual(raw, self.legacy)

    def test_static_files_are_public(self):
        status, raw, _ = self.request("GET", "/cockpit-v2/")
        self.assertEqual(status, 200)
        self.assertIn(b"<title>v2</title>", raw)


class TestCockpitStaticLoader(unittest.TestCase):
    def test_loader_maps_only_allowed_regular_files_and_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "assets").mkdir()
            (root / "index.html").write_bytes(b"index")
            (root / "assets" / "app.js").write_bytes(b"js")
            (root / "secret.txt").write_bytes(b"no")
            loaded = load_cockpit_v2(str(root))
        self.assertEqual(loaded["/cockpit-v2"], b"index")
        self.assertEqual(loaded["/cockpit-v2/"], b"index")
        self.assertEqual(loaded["/cockpit-v2/index.html"], b"index")
        self.assertEqual(loaded["/cockpit-v2/assets/app.js"], b"js")
        self.assertNotIn("/cockpit-v2/secret.txt", loaded)

    def test_loader_is_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.html").write_bytes(b"12345")
            (root / "app.js").write_bytes(b"12345")
            loaded = load_cockpit_v2(
                str(root), max_files=1, max_file_bytes=4, max_total_bytes=4)
        self.assertEqual(loaded, {})


if __name__ == "__main__":
    unittest.main()


class TestProductionReaderWiring(unittest.TestCase):
    """The run.py adapter must construct the real model and emit ETags.

    This pins the constructor contract the live service depends on; a
    signature drift here would silently 404 every /api/v2 route in
    production while every unit-level fixture stayed green.
    """

    def test_reader_constructs_real_model_and_returns_etag_metadata(self):
        from types import SimpleNamespace

        from ofn.run import _cockpit_v2_reader

        with tempfile.TemporaryDirectory() as tmp:
            mesh = Path(tmp)
            for name in ("config", "state", "inbox", "audit"):
                (mesh / name).mkdir(parents=True, exist_ok=True)
            previous = os.environ.get("OCTOPUS_MESH_ROOT")
            os.environ["OCTOPUS_MESH_ROOT"] = str(mesh)
            try:
                node = SimpleNamespace(
                    owner_status=lambda: {},
                    owner_observability=lambda: {},
                    owner_metrics=lambda: {},
                    owner_businesses=lambda: {},
                    owner_risks=lambda: {},
                    owner_ledger_summary=lambda: {},
                )
                reader = _cockpit_v2_reader(node)
            finally:
                if previous is None:
                    os.environ.pop("OCTOPUS_MESH_ROOT", None)
                else:
                    os.environ["OCTOPUS_MESH_ROOT"] = previous
        self.assertIsNotNone(reader)
        envelope, metadata = reader("status", {})
        self.assertEqual(envelope["schema_version"], "2.0")
        validator = metadata["validator"]
        self.assertTrue(validator.startswith('W/"'))
        # Deterministic across calls for unchanged sources.
        again = reader("status", {})
        self.assertEqual(again[1]["validator"], validator)
