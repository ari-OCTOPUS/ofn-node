"""HTTP surface: host routing, cross-tenant sessions, owner gating, and the
structural rule that keeps a slow model off the request path.
"""

from __future__ import annotations

import ast
import hashlib
import hmac
import json
import os
import unittest

from ofn.adapters.http_api import ApiApp, HostMap, Response
from ofn.kernel.auth import data_check_string
from ofn.kernel.domain import PackSpec, TenantId
from ofn.kernel.tenancy import TenantRegistry

NOW = 1_785_000_000
SECRET = "session-secret"
TOK_Z = "111:token-ziman"
TOK_L = "222:token-lead"
TOK_O = "333:token-owner"
OWNER_ID = "5001"
# Every shell now has a door list. "777" is the partner these tests speak as;
# anyone else is a stranger, which is the behaviour under test.
PARTNERS = {"ziman": ["777"], "lead": ["777"], "studio": ["777"]}

HOSTS = HostMap(
    tenants={"ziman.example.com": "ziman", "lead.example.com": "lead"},
    owner_host="panel.example.com",
)


def registry() -> TenantRegistry:
    return TenantRegistry({
        "ziman": PackSpec(tenant=TenantId("ziman"), capacity_units_per_week=6,
                          quota_share=0.4),
        "lead": PackSpec(tenant=TenantId("lead"), capacity_units_per_week=6,
                         quota_share=0.4),
    })


def init_data(token: str, uid: str, auth_date: int = NOW) -> str:
    fields = {"auth_date": str(auth_date),
              "user": f'{{"id":{uid},"username":"u{uid}"}}'}
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    h = hmac.new(secret, data_check_string(fields).encode(),
                 hashlib.sha256).hexdigest()
    fields["hash"] = h
    return "&".join(f"{k}={v}" for k, v in fields.items())


def app(**kw) -> ApiApp:
    return ApiApp(
        registry(), HOSTS,
        bot_tokens={"ziman": TOK_Z, "lead": TOK_L, "__owner__": TOK_O},
        session_secret=SECRET, owner_user_ids=[OWNER_ID],
        partner_user_ids=PARTNERS,
        now=lambda: NOW, **kw)


def login(a: ApiApp, host: str, token: str, uid: str) -> str:
    r = a.handle("POST", "/api/v1/auth/session", {"host": host},
                 json.dumps({"init_data": init_data(token, uid)}).encode())
    assert r.status == 200, r.body
    return r.body["session"]


def auth_headers(host: str, session: str) -> dict[str, str]:
    return {"host": host, "authorization": f"Bearer {session}"}


# ══ the structural rule ═════════════════════════════════════════════════
class TestApiCannotReachTheSlowBrain(unittest.TestCase):
    """The API answers from local storage. It must not be *able* to call a
    hosted model, because that path is 7-270 seconds long."""

    def test_http_api_does_not_import_the_router(self):
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "ofn", "adapters", "http_api.py")
        tree = ast.parse(open(path, encoding="utf-8").read())
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported += [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                imported.append(node.module or "")
                imported += [a.name for a in node.names]
        for name in imported:
            with self.subTest(imported=name):
                low = name.lower()
                self.assertNotIn("router", low)
                self.assertNotIn("brain", low)
                self.assertNotIn("remote", low)


# ══ host routing ════════════════════════════════════════════════════════
class TestHostRouting(unittest.TestCase):
    def test_unknown_host_is_refused(self):
        self.assertEqual(app().handle("GET", "/api/v1/me",
                                      {"host": "evil.example.com"}, b"").status,
                         404)

    def test_no_default_tenant_when_host_missing(self):
        self.assertEqual(app().handle("GET", "/api/v1/me", {}, b"").status, 404)

    def test_port_is_stripped_and_case_ignored(self):
        t, owner = HOSTS.resolve("ZIMAN.example.com:8791")
        self.assertEqual(t, "ziman")
        self.assertFalse(owner)

    def test_owner_host_is_recognised(self):
        t, owner = HOSTS.resolve("panel.example.com")
        self.assertIsNone(t)
        self.assertTrue(owner)

    def test_healthz_needs_no_host_or_auth(self):
        r = app().handle("GET", "/healthz", {}, b"")
        self.assertEqual(r.status, 200)


# ══ auth ════════════════════════════════════════════════════════════════
class TestAuthExchange(unittest.TestCase):
    def test_valid_login_returns_a_session(self):
        a = app()
        r = a.handle("POST", "/api/v1/auth/session", {"host": "ziman.example.com"},
                     json.dumps({"init_data": init_data(TOK_Z, "777")}).encode())
        self.assertEqual(r.status, 200)
        self.assertIn("session", r.body)

    def test_blob_signed_with_another_legs_token_is_refused(self):
        """Ziman's host must not accept a blob signed by the lead bot."""
        a = app()
        r = a.handle("POST", "/api/v1/auth/session", {"host": "ziman.example.com"},
                     json.dumps({"init_data": init_data(TOK_L, "777")}).encode())
        self.assertEqual(r.status, 401)

    def test_replayed_blob_is_refused(self):
        a = app()
        payload = json.dumps({"init_data": init_data(TOK_Z, "777")}).encode()
        h = {"host": "ziman.example.com"}
        self.assertEqual(a.handle("POST", "/api/v1/auth/session", h, payload).status,
                         200)
        self.assertEqual(a.handle("POST", "/api/v1/auth/session", h, payload).status,
                         401)

    def test_empty_or_malformed_body(self):
        a = app()
        h = {"host": "ziman.example.com"}
        self.assertEqual(a.handle("POST", "/api/v1/auth/session", h, b"").status, 400)
        self.assertEqual(a.handle("POST", "/api/v1/auth/session", h,
                                  b"not json").status, 400)

    def test_non_owner_cannot_log_into_the_panel(self):
        a = app()
        r = a.handle("POST", "/api/v1/auth/session", {"host": "panel.example.com"},
                     json.dumps({"init_data": init_data(TOK_O, "999")}).encode())
        self.assertEqual(r.status, 403)

    def test_owner_can(self):
        a = app()
        r = a.handle("POST", "/api/v1/auth/session", {"host": "panel.example.com"},
                     json.dumps({"init_data": init_data(TOK_O, OWNER_ID)}).encode())
        self.assertEqual(r.status, 200)


class TestSessionEnforcement(unittest.TestCase):
    def test_no_session_is_401(self):
        self.assertEqual(app().handle("GET", "/api/v1/me",
                                      {"host": "ziman.example.com"}, b"").status, 401)

    def test_garbage_session_is_401(self):
        h = auth_headers("ziman.example.com", "not-a-token")
        self.assertEqual(app().handle("GET", "/api/v1/me", h, b"").status, 401)

    def test_session_from_one_leg_rejected_on_another(self):
        """The cross-tenant case the token binding exists to stop."""
        a = app()
        s = login(a, "ziman.example.com", TOK_Z, "777")
        r = a.handle("GET", "/api/v1/me", auth_headers("lead.example.com", s), b"")
        self.assertEqual(r.status, 401)

    def test_partner_session_cannot_reach_the_owner_panel(self):
        a = app()
        s = login(a, "ziman.example.com", TOK_Z, "777")
        r = a.handle("GET", "/api/v1/queue",
                     auth_headers("panel.example.com", s), b"")
        self.assertEqual(r.status, 401)

    def test_valid_session_works(self):
        a = app()
        s = login(a, "ziman.example.com", TOK_Z, "777")
        r = a.handle("GET", "/api/v1/me", auth_headers("ziman.example.com", s), b"")
        self.assertEqual(r.status, 200)
        self.assertEqual(r.body["tenant"], "ziman")


# ══ partner surface ═════════════════════════════════════════════════════
class TestPartnerSurface(unittest.TestCase):
    def test_questions_are_scoped_to_the_caller(self):
        seen = {}

        def qs(scope, uid):
            seen["tenant"] = scope.tenant.value
            return [{"id": "q1", "text": "چند تا؟"}]

        a = app(questions_for=qs)
        s = login(a, "ziman.example.com", TOK_Z, "777")
        r = a.handle("GET", "/api/v1/questions",
                     auth_headers("ziman.example.com", s), b"")
        self.assertEqual(r.status, 200)
        self.assertEqual(seen["tenant"], "ziman")
        self.assertEqual(len(r.body["questions"]), 1)

    def test_answer_is_passed_through_with_scope(self):
        got = {}

        def submit(scope, uid, body):
            got.update({"tenant": scope.tenant.value, "uid": uid, "body": body})
            return {"ok": True}

        a = app(submit_answer=submit)
        s = login(a, "ziman.example.com", TOK_Z, "777")
        r = a.handle("POST", "/api/v1/answers",
                     auth_headers("ziman.example.com", s),
                     json.dumps({"question": "q1", "value": 6}).encode())
        self.assertEqual(r.status, 200)
        self.assertEqual(got["tenant"], "ziman")
        self.assertEqual(got["uid"], "777")
        self.assertEqual(got["body"]["value"], 6)

    def test_malformed_answer_body(self):
        a = app()
        s = login(a, "ziman.example.com", TOK_Z, "777")
        h = auth_headers("ziman.example.com", s)
        self.assertEqual(a.handle("POST", "/api/v1/answers", h, b"[]").status, 400)
        self.assertEqual(a.handle("POST", "/api/v1/answers", h, b"{oops").status, 400)

    def test_partner_cannot_reach_owner_routes(self):
        a = app()
        s = login(a, "ziman.example.com", TOK_Z, "777")
        r = a.handle("GET", "/api/v1/queue",
                     auth_headers("ziman.example.com", s), b"")
        self.assertEqual(r.status, 404)

    def test_unknown_path(self):
        a = app()
        s = login(a, "ziman.example.com", TOK_Z, "777")
        r = a.handle("GET", "/api/v1/nope",
                     auth_headers("ziman.example.com", s), b"")
        self.assertEqual(r.status, 404)


# ══ owner surface ═══════════════════════════════════════════════════════
class TestOwnerSurface(unittest.TestCase):
    def _owner_session(self, a: ApiApp) -> str:
        return login(a, "panel.example.com", TOK_O, OWNER_ID)

    def test_queue_is_visible_to_the_owner(self):
        a = app(owner_queue=lambda: [{"id": "d1", "tier": "red"}])
        s = self._owner_session(a)
        r = a.handle("GET", "/api/v1/queue", auth_headers("panel.example.com", s), b"")
        self.assertEqual(r.status, 200)
        self.assertEqual(r.body["queue"][0]["id"], "d1")

    def test_decision_carries_the_second_confirmation_flag(self):
        got = {}

        def decide(item, approve, confirmed):
            got.update({"item": item, "approve": approve, "confirmed": confirmed})
            return {"ok": True}

        a = app(owner_decide=decide)
        s = self._owner_session(a)
        a.handle("POST", "/api/v1/decide", auth_headers("panel.example.com", s),
                 json.dumps({"id": "d1", "approve": True,
                             "confirmed_twice": True}).encode())
        self.assertEqual(got, {"item": "d1", "approve": True, "confirmed": True})

    def test_decision_without_id_is_rejected(self):
        a = app()
        s = self._owner_session(a)
        r = a.handle("POST", "/api/v1/decide", auth_headers("panel.example.com", s),
                     json.dumps({"approve": True}).encode())
        self.assertEqual(r.status, 400)

    def test_confirmation_defaults_to_false(self):
        got = {}
        a = app(owner_decide=lambda i, ap, c: got.update({"c": c}) or {"ok": True})
        s = self._owner_session(a)
        a.handle("POST", "/api/v1/decide", auth_headers("panel.example.com", s),
                 json.dumps({"id": "d1", "approve": True}).encode())
        self.assertFalse(got["c"])


class TestResponseHygiene(unittest.TestCase):
    def test_errors_do_not_describe_the_failure(self):
        a = app()
        bad_session = a.handle("GET", "/api/v1/me",
                               auth_headers("ziman.example.com", "x.y.1.2.z"), b"")
        no_session = a.handle("GET", "/api/v1/me", {"host": "ziman.example.com"}, b"")
        self.assertEqual(bad_session.body, no_session.body)

    def test_response_is_a_plain_object(self):
        r = app().handle("GET", "/healthz", {}, b"")
        self.assertIsInstance(r, Response)
        json.dumps(r.body)      # must be serialisable


if __name__ == "__main__":
    unittest.main()
