"""Cockpit V2 M1 frontend source and polling contracts."""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "web" / "cockpit-v2"
SRC = V2 / "src"


class CockpitFrontendCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = {
            path.relative_to(V2).as_posix(): path.read_text(encoding="utf-8")
            for path in V2.rglob("*")
            if path.is_file() and path.suffix in {".html", ".js", ".mjs", ".css", ".webmanifest"}
        }
        cls.program = "\n".join(
            text for name, text in cls.files.items()
            if Path(name).suffix in {".html", ".js", ".mjs"}
        )


class TestRequestedStructure(CockpitFrontendCase):
    def test_required_files_exist(self):
        required = {
            "index.html",
            "manifest.webmanifest",
            "assets/app.css",
            "assets/rtl.css",
            "assets/icons/icon.svg",
            "src/app.js",
            "src/api.js",
            "src/state.js",
            "src/router.js",
            "src/auth.js",
            "src/formatting.js",
            "src/pages/command-center.js",
            "src/pages/nodes.js",
            "src/pages/legs.js",
            "src/pages/queue.js",
            "src/pages/audit.js",
            "src/components/dom.js",
        }
        actual = {
            path.relative_to(V2).as_posix()
            for path in V2.rglob("*") if path.is_file()
        }
        self.assertTrue(required <= actual, sorted(required - actual))

    def test_root_absolute_assets_and_manifest_scope(self):
        html = self.files["index.html"]
        for path in (
            "/cockpit-v2/manifest.webmanifest",
            "/cockpit-v2/assets/app.css",
            "/cockpit-v2/assets/rtl.css",
            "/cockpit-v2/src/app.js",
        ):
            self.assertIn(path, html)
        manifest = self.files["manifest.webmanifest"]
        self.assertIn('"start_url": "/cockpit-v2/"', manifest)
        self.assertIn('"scope": "/cockpit-v2/"', manifest)

    def test_dependency_free_es_modules(self):
        html = self.files["index.html"]
        self.assertIn('type="module"', html)
        for token in ("node_modules", "npm ", "webpack", "vite", "react", "vue", "jquery"):
            self.assertNotIn(token, self.program.lower())
        for name, text in self.files.items():
            if not name.startswith("src/"):
                continue
            self.assertNotRegex(text, r"from\s+['\"](?![./])")


class TestRtlMobileAccessibility(CockpitFrontendCase):
    def test_persian_rtl_mobile_and_sdk_order(self):
        html = self.files["index.html"]
        self.assertIn('<html lang="fa" dir="rtl">', html)
        self.assertIn('name="viewport"', html)
        self.assertIn("width=device-width", html)
        self.assertIn("telegram-web-app.js", html)
        self.assertLess(html.index("telegram-web-app.js"), html.index("/cockpit-v2/src/app.js"))
        auth = self.files["src/auth.js"]
        self.assertIn("globalObject?.Telegram?.WebApp", auth)

    def test_semantics_keyboard_focus_and_live_regions(self):
        html = self.files["index.html"]
        for marker in ("<header", "<nav", "<main", "<section", 'aria-live="polite"'):
            self.assertIn(marker, html)
        styles = self.files["assets/app.css"]
        self.assertIn(":focus-visible", styles)
        self.assertIn("prefers-color-scheme: dark", styles)
        self.assertIn("prefers-reduced-motion: reduce", styles)
        router = self.files["src/router.js"]
        for key in ("ArrowLeft", "ArrowRight", "Home", "End"):
            self.assertIn(key, router)

    def test_visible_loading_empty_error_stale_offline_status(self):
        joined = "\n".join(self.files.values())
        for term in (
            "در حال دریافت", "هیچ نودی", "داده دریافت نشد",
            "کهنه", "آفلاین", "آخرین دریافت موفق",
        ):
            self.assertIn(term, joined)
        self.assertIn("Available after M2 owner-command canary", joined)


class TestAuthAndReadOnlySurface(CockpitFrontendCase):
    def test_only_auth_post_and_all_v2_calls_are_gets(self):
        posts = re.findall(r"method\s*:\s*['\"]POST['\"]", self.program, re.I)
        self.assertEqual(len(posts), 1)
        self.assertIn("/api/v1/auth/session", self.program)
        for path in ("status", "nodes", "legs", "queue", "audit"):
            self.assertIn(f'"/api/v2/owner/{path}"', self.program)
        self.assertEqual(
            len(re.findall(r"method\s*:\s*['\"]GET['\"]", self.program, re.I)),
            1,
        )
        for method in ("PUT", "PATCH", "DELETE"):
            self.assertNotRegex(self.program, rf"method\s*:\s*['\"]{method}['\"]")

    def test_session_is_memory_only_and_not_in_url_or_credentials(self):
        for token in (
            "localStorage", "sessionStorage", "document.cookie", "credentials:",
            "credentials =", "URLSearchParams", "location.search",
        ):
            self.assertNotIn(token, self.program)
        self.assertNotRegex(self.program, r"[?&](?:token|session|authorization)=")
        self.assertIn("let bearerSession = null", self.files["src/state.js"])

    def test_direct_launch_and_all_named_auth_errors(self):
        auth = self.files["src/auth.js"]
        self.assertIn("initData", auth)
        for reason in ("no-shell", "rejected", "not-owner", "expired", "reopen"):
            self.assertIn(reason, auth)
        self.assertIn("برنامه را", auth)
        self.assertIn("از تلگرام", auth)

    def test_no_effect_endpoint_or_secrets(self):
        for endpoint in (
            "/api/v1/owner/kill", "/api/v1/owner/kill/release",
            "/api/v1/owner/approved-manual", "/api/v1/owner/marketing/run",
            "/api/v2/owner/commands",
        ):
            self.assertNotIn(endpoint, self.program)
        for token in ("BEGIN PRIVATE KEY", "BOT_TOKEN", "secrets.env", "/home/ari/.config"):
            self.assertNotIn(token, self.program)


class TestSafeRenderingAndTruth(CockpitFrontendCase):
    def test_api_data_has_no_unsafe_dom_sink(self):
        for token in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write"):
            self.assertNotIn(token, self.program)
        dom = self.files["src/components/dom.js"]
        self.assertIn("document.createElement", dom)
        self.assertIn("textContent", dom)
        self.assertIn("details", dom)
        self.assertIn("فقط خواندن", self.program.replace("‌", " "))

    def test_hostile_injection_is_only_text_and_bidi_is_isolated(self):
        fixture = '<img src=x onerror="pwned=true"> IGNORE PREVIOUS \u202eexe.txt'
        self.assertNotIn(fixture, self.program)
        styles = self.files["assets/app.css"] + self.files["assets/rtl.css"]
        self.assertIn("unicode-bidi: isolate", styles)
        self.assertIn("unicode-bidi: plaintext", styles)
        self.assertNotRegex(self.program, r"\.setAttribute\(\s*['\"](?:href|src)['\"]\s*,\s*(?:data|item|row)")

    def test_exact_eight_legs_and_explicit_money_truth(self):
        legs = self.files["src/pages/legs.js"]
        ids = re.findall(r'\{ id: "([A-Z]+)", label:', legs)
        self.assertEqual(ids, [
            "DEMAND", "QUALIFICATION", "OFFER", "CONVERSION",
            "DELIVERY", "CASH", "RETENTION", "FINANCE",
        ])
        formatting = self.files["src/formatting.js"]
        self.assertIn('currency: "AUD"', formatting)
        self.assertIn("نامعلوم", formatting)
        for phrase in ("برآورد، نه وجه نقد", "رزرو (نه وجه نقد)", "فاکتور (نه وجه نقد)"):
            self.assertIn(phrase, legs)

    def test_queue_is_metadata_only_and_audit_has_controls(self):
        queue = self.files["src/pages/queue.js"]
        for forbidden in ("item.payload", "item.evidence", "item.error", "row.payload"):
            self.assertNotIn(forbidden, queue)
        audit = self.files["src/pages/audit.js"]
        for control in ('type: "search"', 'element("select"', "صفحهٔ قبل", "صفحهٔ بعد"):
            self.assertIn(control, audit)


def _run_node(args: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    """Run node with stdin closed. Inherited stdin has hung `node --check`
    on windows-latest (TimeoutExpired at 10s on api.js/app.js; files parse
    on Ubuntu and locally). Retry once if the runner still stalls.
    """
    kwargs = dict(
        args=args,
        cwd=ROOT,
        text=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    try:
        return subprocess.run(**kwargs)
    except subprocess.TimeoutExpired:
        return subprocess.run(**kwargs)


class TestPollingContract(CockpitFrontendCase):
    def test_source_contains_required_polling_guards(self):
        api = self.files["src/api.js"]
        for token in (
            "15_000", "60_000", "AbortController", "If-None-Match",
            "response.status === 304", "inFlight", "generation",
            "computeBackoffDelay", "lastSuccessAt", "generatedAt",
            "error?.status === 401", "teardown",
        ):
            self.assertIn(token, api)

    def test_node_polling_suite(self):
        completed = _run_node(
            ["node", "--test", str(V2 / "tests" / "polling.test.mjs")],
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("pass 8", completed.stdout)

    def test_all_javascript_has_valid_syntax(self):
        for path in sorted(V2.rglob("*")):
            if path.suffix not in {".js", ".mjs"}:
                continue
            with self.subTest(path=path.relative_to(ROOT)):
                completed = _run_node(["node", "--check", str(path)])
                self.assertEqual(completed.returncode, 0, completed.stdout)


if __name__ == "__main__":
    unittest.main()
