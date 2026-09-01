"""Cockpit V2 M1 purity and legacy-preservation contract.

These are source-level invariants that complement the behavioral API and
frontend suites. M1 is a read-only surface beside the existing owner panel;
it must not quietly grow a command path, persist a browser session, or import
an effect executor into the read model.
"""

from __future__ import annotations

import ast
import hashlib
import os
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "web" / "panel.html"
V2_ROOT = ROOT / "web" / "cockpit-v2"
READ_MODEL = ROOT / "ofn" / "adapters" / "cockpit_v2_read_model.py"
HTTP_API = ROOT / "ofn" / "adapters" / "http_api.py"
RUN = ROOT / "ofn" / "run.py"

# Re-pinned by the owner-brain P0 fix (2026-08-31): the legacy panel's ask
# button was updated atomically with the 202/422 + job-polling API contract
# (silent `{"ok": true}` for doomed asks is the bug being repaired). The
# previous pin: 121601 bytes, sha256 735134eb...dda29.
LEGACY_PANEL_BYTES = 123_069
LEGACY_PANEL_SHA256 = (
    "43f5312c121055f41c506317a3001c9f8f0f9b6b0bee28e59bdd08350af47423"
)


class TestLegacyPanelPreserved(unittest.TestCase):
    def test_legacy_panel_exact_bytes_are_unchanged(self):
        # A Windows checkout converts the worktree file to CRLF; the frozen
        # contract is the LF blob, so compare against the LF normalisation.
        raw = PANEL.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(len(raw), LEGACY_PANEL_BYTES)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), LEGACY_PANEL_SHA256)

    def test_v2_is_a_separate_tree(self):
        self.assertTrue(V2_ROOT.is_dir())
        self.assertTrue((V2_ROOT / "index.html").is_file())
        self.assertNotEqual(
            (V2_ROOT / "index.html").resolve(), PANEL.resolve())


class TestReadModelPurity(unittest.TestCase):
    FORBIDDEN_IMPORT_PREFIXES = {
        "subprocess",
        "socket",
        "urllib",
        "requests",
        "httpx",
        "paramiko",
        "ofn.adapters.http_api",
        "ofn.adapters.alert",
        "ofn.adapters.telegram",
        "ofn.model",
        "ofn.router",
        "octopus_common",
    }

    def setUp(self):
        self.src = READ_MODEL.read_text(encoding="utf-8")
        self.tree = ast.parse(self.src, filename=str(READ_MODEL))

    def test_read_model_imports_no_network_process_or_control_module(self):
        imported: set[str] = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        offenders = sorted(
            name for name in imported
            if any(name == prefix or name.startswith(prefix + ".")
                   for prefix in self.FORBIDDEN_IMPORT_PREFIXES)
        )
        self.assertEqual(offenders, [])

    def test_read_model_has_no_process_or_shell_execution(self):
        forbidden_calls = {
            "system", "popen", "run", "call", "check_call", "check_output",
            "exec", "eval",
        }
        offenders: list[str] = []
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.Call):
                continue
            name = None
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            if name in forbidden_calls:
                offenders.append(name)
        self.assertEqual(offenders, [])

    def test_read_model_does_not_open_files_for_write(self):
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.Call):
                continue
            is_open = (
                isinstance(node.func, ast.Name) and node.func.id == "open"
            ) or (
                isinstance(node.func, ast.Attribute) and node.func.attr == "open"
            )
            if not is_open:
                continue
            mode = None
            if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                mode = node.args[1].value
            for keyword in node.keywords:
                if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant):
                    mode = keyword.value.value
            if isinstance(mode, str):
                self.assertFalse(any(flag in mode for flag in "wax+"), mode)

    def test_read_model_uses_no_store_constructor_names(self):
        for token in (
            "Ledger(", "Outbox(", "FactStore(", "LeadStore(",
            "ProductStore(", "MarketingStore(", "ConsentStore(",
            "AudienceStore(",
        ):
            self.assertNotIn(token, self.src)


class TestM1HasNoCommandSurface(unittest.TestCase):
    def test_no_v2_command_endpoint_exists(self):
        source = HTTP_API.read_text(encoding="utf-8")
        self.assertNotIn("/api/v2/owner/commands", source)
        self.assertNotRegex(
            source,
            r'method\s*==\s*"(?:POST|PUT|PATCH|DELETE)"[^\n]*/api/v2/',
        )

    def test_frontend_has_no_effect_api(self):
        joined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(V2_ROOT.rglob("*"))
            if path.is_file() and path.suffix in {".html", ".js", ".mjs"}
        )
        for endpoint in (
            "/api/v1/owner/kill",
            "/api/v1/owner/kill/release",
            "/api/v1/owner/approved-manual",
            "/api/v1/owner/marketing/run",
            "/api/v2/owner/commands",
        ):
            self.assertNotIn(endpoint, joined)
        for method in ("PUT", "PATCH", "DELETE"):
            self.assertNotRegex(
                joined, rf"method\s*:\s*['\"]{method}['\"]")

    def test_frontend_persists_no_session_or_token(self):
        joined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(V2_ROOT.rglob("*"))
            if path.is_file() and path.suffix in {".html", ".js", ".mjs"}
        )
        self.assertNotIn("localStorage", joined)
        self.assertNotIn("sessionStorage", joined)
        self.assertNotRegex(joined, r"document\.cookie\s*=")
        self.assertNotRegex(joined, r"[?&](?:token|session|authorization)=")

    def test_only_authentication_post_is_present_in_frontend(self):
        joined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(V2_ROOT.rglob("*"))
            if path.is_file() and path.suffix in {".html", ".js", ".mjs"}
        )
        posts = re.findall(
            r"(?:method\s*:\s*['\"]POST['\"]|post\s*\()", joined,
            flags=re.IGNORECASE,
        )
        # Source scanners cannot reliably associate a dynamic method with a
        # path, so pin the sole literal POST target as well as the count.
        self.assertLessEqual(len(posts), 1)
        if posts:
            self.assertIn("/api/v1/auth/session", joined)


class TestM1DeploymentPurity(unittest.TestCase):
    def test_code_contains_no_systemd_or_listener_mutation(self):
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (READ_MODEL, HTTP_API, RUN)
        )
        for token in (
            "systemctl restart", "systemctl enable", "systemctl disable",
            "daemon-reload", "firewall", "ufw ", "iptables",
        ):
            self.assertNotIn(token, source)

    def test_v2_uses_no_absolute_secret_path(self):
        joined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in [READ_MODEL, HTTP_API, RUN]
            + [p for p in V2_ROOT.rglob("*") if p.is_file()]
        )
        self.assertNotIn("/home/ari/.config/ofn/secrets.env", joined)
        self.assertNotIn("OCTOPUS_TELEGRAM_BOT_TOKEN", joined)
        self.assertNotRegex(joined, r"-----BEGIN [A-Z ]*PRIVATE KEY-----")


if __name__ == "__main__":
    unittest.main()
