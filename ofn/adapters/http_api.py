"""HTTP surface for the two shells. stdlib `http.server`, zero dependencies.

One structural rule governs this module, and there is a test that enforces it:

    **This file must never import the model router.**

Not "should not call it synchronously" — must not be able to. The hosted
brain has been measured between 7 and 270 seconds. Any code path from an HTTP
request to that brain is a path where a partner taps a button and watches a
white screen. By removing the import entirely, the slow path is not merely
discouraged, it is unreachable. Requests are answered from the ledger and the
fact store, which are local reads in single-digit milliseconds. Thinking
happens elsewhere and its results arrive as a notification.

Tenant routing is by hostname. Each mini-app lives on its own subdomain,
because the messaging platform now restricts its client-side APIs to the exact
origin registered for the app — one origin per app is a platform requirement,
not a preference. An unmapped host resolves to nothing and is refused; there
is no default tenant, because a default is how one partner ends up looking at
another's queue.

Binding is to loopback only. The tunnel daemon is the sole path in from the
world, so the listener never needs a routable address, and not having one
removes a whole category of accident.
"""

from __future__ import annotations

import json
import re
import urllib.parse
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Mapping, Sequence

from ..kernel.auth import (
    AuthError, ReplayGuard, Session, issue_session, parse_and_verify,
    verify_session,
)
from ..kernel.domain import RiskTier, TenantId
from ..kernel.tenancy import TenantRegistry, TenantScope

MAX_BODY_BYTES = 64 * 1024

# How much of the ledger the owner's panel gets in one read. Fixed here rather
# than taken from the query string: a caller-controlled limit on a database
# read is a way to make the node do arbitrary work, and no screen shows more
# than this anyway.
EVENT_TAIL = 40


@dataclass(frozen=True)
class Principal:
    """Who is making this request, after verification."""

    tenant: TenantId
    user_id: str
    is_owner: bool = False

    @property
    def role(self) -> str:
        """`owner` or `partner`. A partner may work on their own business's
        records and nothing else — no settings, no locale, no ledger, no
        allowlist. Those live behind the owner host, which this never is."""
        return "owner" if self.is_owner else "partner"


@dataclass
class Response:
    status: int
    body: object = None
    headers: Mapping[str, str] = field(default_factory=dict)


@dataclass
class HostMap:
    """Hostname to tenant, plus which host is the owner's panel.

    Matching strips the port and lowercases, and nothing else — no wildcards,
    no suffix matching. A host either was configured or it was not.
    """

    tenants: Mapping[str, str]
    owner_host: str = ""

    def resolve(self, host_header: str) -> tuple[str | None, bool]:
        host = (host_header or "").split(":")[0].strip().lower()
        if not host:
            return None, False
        if self.owner_host and host == self.owner_host.lower():
            return None, True
        return self.tenants.get(host), False


class ApiApp:
    """Request routing and handlers. Transport-agnostic and directly testable.

    Handlers are injected rather than imported so this class has no opinion
    about storage, and so tests can drive it without a database. The injected
    callables are all local reads by contract; anything slow belongs in a
    background worker, not behind an HTTP verb.
    """

    def __init__(
        self,
        registry: TenantRegistry,
        hosts: HostMap,
        *,
        bot_tokens: Mapping[str, str],
        session_secret: str,
        owner_user_ids: Sequence[str] = (),
        partner_user_ids: Mapping[str, Sequence[str]] | None = None,
        now: Callable[[], int],
        questions_for: Callable[[TenantScope, str], list] | None = None,
        submit_answer: Callable[[TenantScope, str, dict], dict] | None = None,
        status_for: Callable[[TenantScope], dict] | None = None,
        owner_queue: Callable[[], list] | None = None,
        owner_decide: Callable[[str, bool, bool], dict] | None = None,
        owner_status: Callable[[], dict] | None = None,
        owner_events: Callable[[int], list] | None = None,
    ) -> None:
        self._registry = registry
        self._hosts = hosts
        self._bot_tokens = dict(bot_tokens)
        self._secret = session_secret
        self._owners = set(owner_user_ids)
        # Who may open each partner shell. A verified Telegram signature only
        # proves *a* Telegram account opened the app — the platform signs for
        # every user, not just the one this business belongs to. Without this
        # map, anyone who finds the bot is a partner.
        #
        # An absent or empty entry means nobody, never everybody. That is the
        # whole point: the failure mode of a misconfigured allowlist has to be
        # a locked door, not an open one.
        self._partners = {str(k): set(v)
                          for k, v in (partner_user_ids or {}).items()}
        self._now = now
        self._replay = ReplayGuard()
        self._questions_for = questions_for or (lambda s, u: [])
        self._submit_answer = submit_answer or (lambda s, u, b: {"ok": True})
        self._status_for = status_for or (lambda s: {})
        self._owner_queue = owner_queue or (lambda: [])
        self._owner_decide = owner_decide or (lambda i, a, c: {"ok": True})
        self._owner_status = owner_status or (lambda: {})
        self._owner_events = owner_events or (lambda n: [])

    # ── entry point ───────────────────────────────────────────────────────
    def handle(self, method: str, path: str, headers: Mapping[str, str],
               body: bytes) -> Response:
        if path == "/healthz":
            return Response(200, {"ok": True})

        tenant_name, is_owner_host = self._hosts.resolve(headers.get("host", ""))
        if tenant_name is None and not is_owner_host:
            return Response(404, {"error": "unknown host"})

        if method == "POST" and path == "/api/v1/auth/session":
            return self._auth(tenant_name, is_owner_host, body)

        try:
            principal = self._principal(headers, tenant_name, is_owner_host)
        except AuthError:
            return Response(401, {"error": "unauthorised"})

        if is_owner_host:
            return self._owner_route(method, path, principal, body)
        return self._partner_route(method, path, principal, body)

    # ── auth ──────────────────────────────────────────────────────────────
    def _auth(self, tenant_name: str | None, is_owner_host: bool,
              body: bytes) -> Response:
        """Exchange a signed launch blob for a short-lived session token.

        Done once per app open. Everything afterwards presents the session
        token, so the long-lived launch blob is not replayed on every call.
        """
        try:
            payload = json.loads(body or b"{}")
            raw = str(payload.get("init_data", ""))
        except (json.JSONDecodeError, AttributeError):
            return Response(400, {"error": "bad request"})
        if not raw:
            return Response(400, {"error": "bad request"})

        key = "__owner__" if is_owner_host else (tenant_name or "")
        token = self._bot_tokens.get(key, "")
        now = self._now()
        try:
            user = parse_and_verify(urllib.parse.unquote(raw), token,
                                    now_epoch_s=now)
            self._replay.check_and_remember(
                payload.get("init_data", "")[-64:], now)
        except AuthError:
            return Response(401, {"error": "unauthorised"})

        # Signature first, identity second — always in that order, so an
        # unsigned request is told 401 and never learns whether the id it
        # guessed is on a list.
        if not self._admitted(tenant_name, is_owner_host, user.user_id):
            return Response(403, {"error": "forbidden"})

        subject = "__owner__" if is_owner_host else str(tenant_name)
        session = issue_session(
            "owner" if is_owner_host else subject, user.user_id,
            self._secret, now_epoch_s=now)
        return Response(200, {"session": session, "user_id": user.user_id,
                              "username": user.username})

    def _admitted(self, tenant_name: str | None, is_owner_host: bool,
                  user_id: str) -> bool:
        """Is this verified account allowed on this host at all?"""
        if is_owner_host:
            return user_id in self._owners
        return user_id in self._partners.get(str(tenant_name), set())

    def _principal(self, headers: Mapping[str, str], tenant_name: str | None,
                   is_owner_host: bool) -> Principal:
        raw = headers.get("authorization", "")
        if not raw.lower().startswith("bearer "):
            raise AuthError("missing session")
        sess: Session = verify_session(raw[7:].strip(), self._secret,
                                       now_epoch_s=self._now())
        # Re-checked on every request, not just at the launch exchange.
        # Otherwise removing somebody from the allowlist would leave them
        # working until their session happened to expire, and revocation that
        # takes effect "eventually" is not revocation.
        if not self._admitted(tenant_name, is_owner_host, sess.user_id):
            raise AuthError("no longer admitted")
        if is_owner_host:
            if sess.tenant != "owner" or sess.user_id not in self._owners:
                raise AuthError("not an owner session")
            # The owner's principal is bound to no single leg; handlers that
            # need one take it from the request, and every such handler is
            # owner-gated.
            return Principal(TenantId(next(iter(self._registry)).value),
                             sess.user_id, is_owner=True)
        if sess.tenant != tenant_name:
            # A session minted for one leg presented against another. This is
            # the cross-tenant case the token binding exists to stop.
            raise AuthError("session does not match host")
        return Principal(TenantId(sess.tenant), sess.user_id)

    # ── partner surface ───────────────────────────────────────────────────
    def _partner_route(self, method: str, path: str, p: Principal,
                       body: bytes) -> Response:
        scope = self._registry.scope(p.tenant)
        if method == "GET" and path == "/api/v1/me":
            return Response(200, {"tenant": p.tenant.value, "user_id": p.user_id})
        if method == "GET" and path == "/api/v1/questions":
            return Response(200, {"questions": self._questions_for(scope, p.user_id)})
        if method == "GET" and path == "/api/v1/status":
            return Response(200, self._status_for(scope))
        if method == "POST" and path == "/api/v1/answers":
            try:
                data = json.loads(body or b"{}")
            except json.JSONDecodeError:
                return Response(400, {"error": "bad request"})
            if not isinstance(data, dict):
                return Response(400, {"error": "bad request"})
            return Response(200, self._submit_answer(scope, p.user_id, data))
        return Response(404, {"error": "not found"})

    # ── owner surface ─────────────────────────────────────────────────────
    def _owner_route(self, method: str, path: str, p: Principal,
                     body: bytes) -> Response:
        if not p.is_owner:
            return Response(403, {"error": "forbidden"})
        if method == "GET" and path == "/api/v1/queue":
            return Response(200, {"queue": self._owner_queue()})
        if method == "GET" and path == "/api/v1/owner/status":
            return Response(200, self._owner_status())
        if method == "GET" and path == "/api/v1/owner/events":
            return Response(200, {"events": self._owner_events(EVENT_TAIL)})
        if method == "POST" and path == "/api/v1/decide":
            try:
                data = json.loads(body or b"{}")
            except json.JSONDecodeError:
                return Response(400, {"error": "bad request"})
            item = str(data.get("id", ""))
            if not item:
                return Response(400, {"error": "bad request"})
            approve = bool(data.get("approve", False))
            confirmed = bool(data.get("confirmed_twice", False))
            return Response(200, self._owner_decide(item, approve, confirmed))
        return Response(404, {"error": "not found"})


# ── transport ────────────────────────────────────────────────────────────
def make_handler(app: ApiApp, static: Mapping[str, bytes] | None = None):
    """Build a request handler bound to one `ApiApp`."""
    files = dict(static or {})

    class Handler(BaseHTTPRequestHandler):
        server_version = "ofn"
        sys_version = ""
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *args):  # noqa: A003
            # Silence by default: the ledger is the audit trail, and stdout on
            # a flash-backed board is a wear source, not a feature.
            pass

        def _audit(self, method: str, path: str, status: int) -> None:
            """One line for the events worth diagnosing, and nothing else.

            Narrow on purpose. Three things are worth a line: a shell being
            opened, a launch blob being exchanged, and any API failure. Full
            access logging would be the wear source `log_message` avoids.

            Never a user id, a username, or any part of the launch blob. A
            partner's identity does not belong in the journal, and the leg
            name is enough to tell whose shell it was.
            """
            page = path == "/"
            auth = path.endswith("/auth/session")
            if not (page or auth or (path.startswith("/api/") and status >= 400)):
                return
            leg = (self.headers.get("Host") or "?").split(":")[0].split(".")[0]
            print(f"http {leg} {method} {path} -> {status}", flush=True)

        def _send(self, resp: Response) -> None:
            self._audit(self.command,
                        urllib.parse.urlparse(self.path).path, resp.status)
            payload = (b"" if resp.body is None
                       else json.dumps(resp.body, ensure_ascii=False).encode())
            self.send_response(resp.status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            for k, v in resp.headers.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(payload)

        def _headers(self) -> dict[str, str]:
            return {k.lower(): v for k, v in self.headers.items()}

        def do_GET(self):  # noqa: N802
            path = urllib.parse.urlparse(self.path).path
            if path in files or (path == "/" and "/index.html" in files):
                key = "/index.html" if path == "/" else path
                data = files[key]
                self.send_response(200)
                ctype = ("text/html; charset=utf-8" if key.endswith(".html")
                         else "application/octet-stream")
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                self.wfile.write(data)
                self._audit("GET", path, 200)
                return
            self._send(app.handle("GET", path, self._headers(), b""))

        def do_POST(self):  # noqa: N802
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY_BYTES:
                self._send(Response(413, {"error": "payload too large"}))
                return
            body = self.rfile.read(length) if length else b""
            path = urllib.parse.urlparse(self.path).path
            self._send(app.handle("POST", path, self._headers(), body))

    return Handler


def serve(app: ApiApp, port: int, *, static: Mapping[str, bytes] | None = None,
          host: str = "127.0.0.1") -> ThreadingHTTPServer:
    """Bind a listener. Loopback only — the tunnel is the sole route in."""
    return ThreadingHTTPServer((host, port), make_handler(app, static))
