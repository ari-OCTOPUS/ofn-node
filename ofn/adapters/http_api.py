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
import traceback
import urllib.parse
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Mapping, Sequence

from ..kernel.auth import (
    AuthError, ReplayGuard, Session, hmac_variants, issue_session,
    parse_and_verify, verify_session,
)
from ..kernel.domain import RiskTier, TenantId
from ..kernel.tenancy import TenantRegistry, TenantScope

# Paths that serve a shell under a name other than "/".
_SHELL_ALIASES = ("/sabaapp",)

MAX_MEDIA_BODY_BYTES = 24 * 1024 * 1024
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
    # Raw bytes instead of JSON. Only for her own photos and her own export
    # — everything else on this API is JSON, and a second body type is a
    # second thing that can leak, so it is opt-in and named.
    raw: bytes | None = None
    content_type: str = ""


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


def _first_tenant(registry):
    """A tenant to bill the owner's own thinking against.

    The owner is not a tenant and the quota is per-tenant, so one has to be
    chosen. Sorted rather than "whichever came first", because a spend that
    lands on a different leg depending on dict ordering is a spend nobody can
    account for later.
    """
    return sorted(registry, key=lambda t: t.value)[0]


def _json_object(body: bytes) -> dict | None:
    """Parse a JSON object, or None. Anything that is not an object — a list,
    a bare number — is treated as malformed rather than coerced."""
    try:
        data = json.loads(body or b"{}")
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


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
        products_for: Callable[[TenantScope], dict] | None = None,
        create_product: Callable[[TenantScope, str, dict], dict] | None = None,
        update_product: Callable[[TenantScope, str, str, dict], dict] | None = None,
        attach_photo: Callable[[TenantScope, str, str, dict], dict] | None = None,
        studio_board: Callable[[TenantScope], dict] | None = None,
        studio_marketing: Callable[[TenantScope], dict] | None = None,
        run_marketing_cycle: Callable | None = None,
        route_preview: Callable | None = None,
        send_to_outbox: Callable | None = None,
        studio_reading: Callable[[TenantScope], dict] | None = None,
        studio_media: Callable | None = None,
        export_album: Callable | None = None,
        studio_gallery: Callable[[TenantScope], dict] | None = None,
        studio_overview: Callable[[TenantScope], dict] | None = None,
        studio_guidance: Callable[[TenantScope], dict] | None = None,
        set_labels: Callable[[TenantScope, str, str, dict], dict] | None = None,
        set_media_labels: Callable | None = None,
        describe_media: Callable | None = None,
        add_media: Callable | None = None,
        create_album: Callable | None = None,
        file_media: Callable | None = None,
        request_reading: Callable[[TenantScope], dict] | None = None,
        judge_reading: Callable[[TenantScope, str, str], dict] | None = None,
        create_draft: Callable[[TenantScope, str, dict], dict] | None = None,
        attach_media: Callable[[TenantScope, str, str, dict], dict] | None = None,
        publish_draft: Callable[[TenantScope, str, str, dict], dict] | None = None,
        record_felt: Callable[[TenantScope, str, str, dict], dict] | None = None,
        owner_queue: Callable[[], list] | None = None,
        owner_decide: Callable[[str, bool, bool], dict] | None = None,
        owner_status: Callable[[], dict] | None = None,
        owner_events: Callable[[int], list] | None = None,
        brain_status: Callable[[], dict] | None = None,
        brain_probe: Callable[[TenantScope], dict] | None = None,
        owner_ask: Callable[[TenantScope, str], dict] | None = None,
    ) -> None:
        self._registry = registry
        self._hosts = hosts
        self._attach_photo = attach_photo
        self._brain_status = brain_status
        self._brain_probe = brain_probe
        self._owner_ask = owner_ask
        self._studio_board = studio_board
        self._studio_marketing = studio_marketing
        self._run_marketing_cycle = run_marketing_cycle
        self._route_preview = route_preview
        self._send_to_outbox = send_to_outbox
        self._studio_reading = studio_reading
        self._studio_media = studio_media
        self._export_album = export_album
        self._studio_gallery = studio_gallery
        self._studio_overview = studio_overview
        self._studio_guidance = studio_guidance
        self._set_labels = set_labels
        self._set_media_labels = set_media_labels
        self._describe_media = describe_media
        self._add_media = add_media
        self._create_album = create_album
        self._file_media = file_media
        self._request_reading = request_reading
        self._judge_reading = judge_reading
        self._create_draft = create_draft
        self._attach_media = attach_media
        self._publish_draft = publish_draft
        self._record_felt = record_felt
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
        self._products_for = products_for or (lambda s: {"products": []})
        self._create_product = create_product or (
            lambda s, u, b: {"ok": False, "error": "products are not wired"})
        self._update_product = update_product or (
            lambda s, u, k, b: {"ok": False, "error": "products are not wired"})
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

        if method == "POST" and path == "/api/v1/shell/boot":
            return self._shell_boot(body)

        try:
            principal = self._principal(headers, tenant_name, is_owner_host)
        except AuthError:
            return Response(401, {"error": "unauthorised"})

        if is_owner_host:
            return self._owner_route(method, path, principal, body)
        return self._partner_route(method, path, principal, body)

    # ── boot report ───────────────────────────────────────────────────────
    # Every way a shell can fail to come up. Closed on purpose: this route is
    # unauthenticated — it has to be, since the failure it exists to report is
    # "could not authenticate" — so nothing the page sends may reach the
    # journal as free text.
    # `no-shell` used to be both of the two below at once. They have opposite
    # causes and opposite fixes, so one name for them meant the journal could
    # never answer the only question worth asking. Kept as an accepted stage
    # because journal history contains it and the other three shells still
    # send it; new reports from the studio shell use the split pair.
    _BOOT_STAGES = frozenset({
        "opened",       # script ran at all
        "no-shell",     # legacy: either of the two below, indistinguishable
        "no-sdk",       # telegram-web-app.js never ran — a LOADING failure
        "no-initdata",  # SDK present, nothing signed — wrong way in
        "rejected", "not-allowed", "unreachable", "error",
        "threw",        # an exception during boot
        "live",         # session established, screen drawn
    })

    # JavaScript error messages are ASCII and short. Anything else is either
    # not an error message or not one worth a journal line.
    _BOOT_DETAIL = re.compile(r"[^A-Za-z0-9 ._:'()\[\]/-]")

    def _shell_boot(self, body: bytes) -> Response:
        """Record why a shell did or did not come up.

        A partner reporting "it opens and there is nothing there" is the
        hardest thing to diagnose on this node, because the failure is on a
        phone, in a client that has no console, over a tunnel. Without this
        route the only evidence is the absence of later requests, and absence
        cannot distinguish "opened outside the client" from "threw on line
        four" — which have opposite fixes.

        Deliberately not authenticated, deliberately not stored, and it
        answers 200 to anything well-formed: a diagnostic that can itself
        fail loudly would be one more thing to diagnose.
        """
        try:
            sent = json.loads(body or b"{}")
        except ValueError:
            return Response(400, {"error": "bad json"})
        if not isinstance(sent, dict):
            return Response(400, {"error": "bad body"})
        stage = sent.get("stage")
        if stage not in self._BOOT_STAGES:
            return Response(400, {"error": "unknown stage"})
        detail = self._BOOT_DETAIL.sub("", str(sent.get("detail", ""))[:120])
        # Through the reason header, which `_send` strips before the response
        # leaves and appends to the journal line — the same path auth
        # failures already take, so there is one format to read, not two.
        return Response(200, {"ok": True}, headers={
            "X-OFN-Auth-Reason": f"boot {stage}"
                                 + (f" · {detail}" if detail else "")})

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
            # Raw, not pre-decoded: `_parse_qs` splits first and decodes each
            # value, which is the order the platform signed.
            user = parse_and_verify(raw, token, now_epoch_s=now)
            self._replay.check_and_remember(
                payload.get("init_data", "")[-64:], now)
        except AuthError as exc:
            reason = getattr(exc, "reason", "")
            if reason == "signature_mismatch":
                # Say which combination the platform actually signed, so the
                # answer costs one tap rather than another round of theory.
                probe = hmac_variants(raw, token)
                hit = [k for k, ok in probe.items() if ok]
                reason += f" probe={','.join(hit) if hit else 'none'}"
            # Same body to the caller, a named reason in the journal.
            return Response(401, {"error": "unauthorised"},
                            {"X-OFN-Auth-Reason": reason})

        # Signature first, identity second — always in that order, so an
        # unsigned request is told 401 and never learns whether the id it
        # guessed is on a list.
        if not self._admitted(tenant_name, is_owner_host, user.user_id):
            return Response(403, {"error": "forbidden"})

        subject = "__owner__" if is_owner_host else str(tenant_name)
        session = issue_session(
            "owner" if is_owner_host else subject, user.user_id,
            self._secret, now_epoch_s=now)
        # `first_name` travels only on this response, only after the signature
        # and the allowlist have both passed. It is what the shell greets with;
        # before this point the shell knows no name to show.
        return Response(200, {"session": session, "user_id": user.user_id,
                              "username": user.username,
                              "first_name": user.first_name})

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

        # ── pieces ───────────────────────────────────────────────────────
        if method == "GET" and path == "/api/v1/products":
            return Response(200, self._products_for(scope))
        if method == "POST" and path == "/api/v1/products":
            data = _json_object(body)
            if data is None:
                return Response(400, {"error": "bad request"})
            out = self._create_product(scope, p.user_id, data)
            return Response(200 if out.get("ok") else 400, out)
        if method == "POST" and path.startswith("/api/v1/products/") \
                and path.endswith("/photos"):
            sku = path[len("/api/v1/products/"):-len("/photos")]
            if not sku or "/" in sku or self._attach_photo is None:
                return Response(404, {"error": "not found"})
            data = _json_object(body)
            if data is None:
                return Response(400, {"error": "bad request"})
            out = self._attach_photo(scope, p.user_id, sku, data)
            return Response(200 if out.get("ok") else 400, out)
        if method == "POST" and path.startswith("/api/v1/products/"):
            sku = path[len("/api/v1/products/"):]
            # One path segment only. Without this, a crafted sku turns a
            # product edit into a route nobody wrote.
            if not sku or "/" in sku:
                return Response(404, {"error": "not found"})
            data = _json_object(body)
            if data is None:
                return Response(400, {"error": "bad request"})
            out = self._update_product(scope, p.user_id, sku, data)
            return Response(200 if out.get("ok") else 400, out)

        # ── studio ───────────────────────────────────────────────────────
        if method == "GET" and path == "/api/v1/studio/gallery":
            if self._studio_gallery is None:
                return Response(404, {"error": "not found"})
            return Response(200, self._studio_gallery(scope))
        if method == "GET" and path == "/api/v1/studio/overview":
            if self._studio_overview is None:
                return Response(404, {"error": "not found"})
            return Response(200, self._studio_overview(scope))
        if method == "GET" and path == "/api/v1/studio/guidance":
            if self._studio_guidance is None:
                return Response(404, {"error": "not found"})
            return Response(200, self._studio_guidance(scope))
        if method == "GET" and path == "/api/v1/studio/reading":
            if self._studio_reading is None:
                return Response(404, {"error": "not found"})
            return Response(200, self._studio_reading(scope))
        if method == "POST" and path == "/api/v1/studio/reading":
            # Asking costs money; reading is free. Two verbs on one path so a
            # screen that merely opens cannot spend.
            if self._request_reading is None:
                return Response(404, {"error": "not found"})
            out = self._request_reading(scope)
            return Response(200 if out.get("ok") else 400, out)
        if method == "POST" and path == "/api/v1/studio/reading/judge":
            data = _json_object(body)
            if data is None or self._judge_reading is None:
                return Response(400, {"error": "bad request"})
            out = self._judge_reading(scope, str(data.get("key", "")),
                                      str(data.get("disposition", "")))
            return Response(200 if out.get("ok") else 400, out)
        if method == "POST" and path == "/api/v1/studio/media":
            data = _json_object(body)
            if data is None or self._add_media is None:
                return Response(400, {"error": "bad request"})
            out = self._add_media(scope, p.user_id, data)
            return Response(200 if out.get("ok") else 400, out)
        if method == "POST" and path == "/api/v1/studio/albums":
            data = _json_object(body)
            if data is None or self._create_album is None:
                return Response(400, {"error": "bad request"})
            out = self._create_album(scope, p.user_id, data)
            return Response(200 if out.get("ok") else 400, out)
        if method == "POST" and path.startswith("/api/v1/studio/media/") \
                and path.endswith("/album"):
            mid = path[len("/api/v1/studio/media/"):-len("/album")]
            if not mid or "/" in mid or self._file_media is None:
                return Response(404, {"error": "not found"})
            data = _json_object(body)
            if data is None:
                return Response(400, {"error": "bad request"})
            out = self._file_media(scope, mid, data)
            return Response(200 if out.get("ok") else 400, out)
        if method == "POST" and path.startswith("/api/v1/studio/media/") \
                and path.endswith("/labels"):
            mid = path[len("/api/v1/studio/media/"):-len("/labels")]
            if not mid or "/" in mid or self._set_media_labels is None:
                return Response(404, {"error": "not found"})
            data = _json_object(body)
            if data is None:
                return Response(400, {"error": "bad request"})
            out = self._set_media_labels(scope, mid, data)
            return Response(200 if out.get("ok") else 400, out)
        if method == "POST" and path.startswith("/api/v1/studio/media/") \
                and path.endswith("/describe"):
            mid = path[len("/api/v1/studio/media/"):-len("/describe")]
            if not mid or "/" in mid or self._describe_media is None:
                return Response(404, {"error": "not found"})
            data = _json_object(body)
            if data is None:
                return Response(400, {"error": "bad request"})
            out = self._describe_media(scope, mid, data)
            return Response(200 if out.get("ok") else 400, out)
        if method == "GET" and path.startswith("/api/v1/studio/media/"):
            rest = path[len("/api/v1/studio/media/"):]
            parts = rest.split("/")
            if len(parts) != 2 or self._studio_media is None:
                return Response(404, {"error": "not found"})
            return self._studio_media(scope, parts[0], parts[1])
        if method == "GET" and path.startswith("/api/v1/studio/album/") \
                and path.endswith("/export"):
            album = path[len("/api/v1/studio/album/"):-len("/export")]
            if not album or "/" in album or self._export_album is None:
                return Response(404, {"error": "not found"})
            return self._export_album(scope, album)
        if method == "GET" and path == "/api/v1/studio/board":
            if self._studio_board is None:
                return Response(404, {"error": "not found"})
            return Response(200, self._studio_board(scope))
        if method == "GET" and path == "/api/v1/studio/marketing":
            if self._studio_marketing is None:
                return Response(404, {"error": "not found"})
            return Response(200, self._studio_marketing(scope))
        if method == "POST" and path.startswith("/api/v1/studio/drafts/") \
                and path.endswith("/route-preview"):
            if self._route_preview is None:
                return Response(404, {"error": "not found"})
            did = path[len("/api/v1/studio/drafts/"):-len("/route-preview")]
            data = _json_object(body) or {}
            platforms = tuple(str(x) for x in (data.get("platforms") or ()))
            out = self._route_preview(
                scope, did, platforms,
                framing=str(data.get("framing", "beauty")),
                adult_label=bool(data.get("adult_label", False)))
            return Response(200, out)
        if method == "POST" and path.startswith("/api/v1/studio/drafts/") \
                and path.endswith("/send-to-outbox"):
            if self._send_to_outbox is None:
                return Response(404, {"error": "not found"})
            did = path[len("/api/v1/studio/drafts/"):-len("/send-to-outbox")]
            data = _json_object(body) or {}
            platforms = tuple(str(x) for x in (data.get("platforms") or ()))
            out = self._send_to_outbox(
                scope, p.user_id, did, platforms,
                framing=str(data.get("framing", "beauty")),
                adult_label=bool(data.get("adult_label", False)))
            return Response(200 if out.get("ok") else 400, out)
        if method == "POST" and path == "/api/v1/studio/drafts":
            data = _json_object(body)
            if data is None or self._create_draft is None:
                return Response(400, {"error": "bad request"})
            out = self._create_draft(scope, p.user_id, data)
            return Response(200 if out.get("ok") else 400, out)
        if method == "POST" and path.startswith("/api/v1/studio/drafts/"):
            rest = path[len("/api/v1/studio/drafts/"):]
            # Exactly `<id>/<verb>`. Anything else is a route nobody wrote,
            # and a crafted id must not be able to reach one.
            parts = rest.split("/")
            if len(parts) != 2 or not parts[0] or not parts[1]:
                return Response(404, {"error": "not found"})
            draft_id, verb = parts
            data = _json_object(body)
            if data is None:
                return Response(400, {"error": "bad request"})
            handler = {"media": self._attach_media,
                       "publish": self._publish_draft,
                       "felt": self._record_felt}.get(verb)
            if handler is None:
                return Response(404, {"error": "not found"})
            out = handler(scope, p.user_id, draft_id, data)
            return Response(200 if out.get("ok") else 400, out)
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
        # ── brain, owner-only (phase A) ──────────────────────────────────
        if method == "GET" and path == "/api/v1/owner/brain":
            if self._brain_status is None:
                return Response(200, {"wired": False, "why": "not attached"})
            return Response(200, self._brain_status())
        if method == "POST" and path == "/api/v1/owner/brain/probe":
            if self._brain_probe is None:
                return Response(404, {"error": "not found"})
            scope = self._registry.scope(_first_tenant(self._registry))
            out = self._brain_probe(scope)
            return Response(200 if out.get("ok") else 400, out)
        if method == "POST" and path == "/api/v1/owner/ask":
            if self._owner_ask is None:
                return Response(404, {"error": "not found"})
            data = _json_object(body)
            if data is None:
                return Response(400, {"error": "bad request"})
            scope = self._registry.scope(_first_tenant(self._registry))
            out = self._owner_ask(scope, str(data.get("prompt", "")))
            return Response(200 if out.get("ok") else 400, out)
        # ── weekly marketing cycle, owner-only ─────────────────────────
        # Owner-only because it spends brain budget. The partner sees the
        # result via the read-only /api/v1/studio/marketing snapshot; she
        # does not trigger a run. The cron/timer also calls this path.
        if method == "POST" and path == "/api/v1/owner/marketing/run":
            if self._run_marketing_cycle is None:
                return Response(404, {"error": "not found"})
            data = _json_object(body) or {}
            scope = self._registry.scope(_first_tenant(self._registry))
            now = self._now()
            out = self._run_marketing_cycle(
                scope,
                week_id=str(data.get("week_id", "")),
                starts_at=int(data.get("starts_at", now) or now),
                style_id=str(data.get("style_id", "educational")),
                terms=tuple(data.get("terms", ()) or ()),
                now_epoch_s=now)
            return Response(200 if out.get("ok") else 400, out)

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

        def _audit(self, method: str, path: str, status: int,
                   extra: str = "") -> None:
            """One line for the events worth diagnosing, and nothing else.

            Narrow on purpose. Three things are worth a line: a shell being
            opened, a launch blob being exchanged, and any API failure. Full
            access logging would be the wear source `log_message` avoids.

            Never a user id, a username, or any part of the launch blob. A
            partner's identity does not belong in the journal, and the leg
            name is enough to tell whose shell it was.
            """
            # A shell is also served at an alias path (`/sabaapp`), and
            # `path == "/"` did not know that — so the one event worth seeing
            # when a partner reports a blank screen was the one not recorded.
            page = path == "/" or path.rstrip("/") in _SHELL_ALIASES
            auth = path.endswith("/auth/session")
            # A boot report is only ever sent when something is worth
            # knowing, so it is always worth a line — including at 200,
            # which is the whole point of it.
            boot = path.endswith("/shell/boot")
            if not (page or auth or boot
                    or (path.startswith("/api/") and status >= 400)):
                return
            leg = (self.headers.get("Host") or "?").split(":")[0].split(".")[0]
            print(f"http {leg} {method} {path} -> {status}{extra}", flush=True)

        def _send(self, resp: Response) -> None:
            # The reason header is for the journal only and is stripped
            # before the response goes out.
            reason = resp.headers.get("X-OFN-Auth-Reason", "")
            if reason:
                resp.headers = {k: v for k, v in resp.headers.items()
                                if k != "X-OFN-Auth-Reason"}
            self._audit(self.command,
                        urllib.parse.urlparse(self.path).path, resp.status,
                        f"  ({reason})" if reason else "")
            binary = resp.raw is not None
            payload = resp.raw if binary else (
                b"" if resp.body is None
                else json.dumps(resp.body, ensure_ascii=False).encode())
            self.send_response(resp.status)
            self.send_header(
                "Content-Type",
                resp.content_type or ("application/octet-stream" if binary
                                      else "application/json; charset=utf-8"))
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            if binary:
                # Her own photos, over an authenticated request. Never cached
                # by anything in between: `private` keeps them out of a proxy,
                # `no-store` keeps them off disk in the browser. The tunnel is
                # a proxy she does not control.
                self.send_header("Cache-Control", "private, no-store")
            for k, v in resp.headers.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(payload)

        def _headers(self) -> dict[str, str]:
            return {k.lower(): v for k, v in self.headers.items()}

        def _dispatch(self, method: str, path: str, body: bytes) -> None:
            """Run a handler so that no outcome closes the socket silently.

            Without this, an exception inside a handler propagates up to
            `socketserver`, which logs a traceback and drops the connection
            with no response written. The caller sees a network failure, so
            the shell reports "unreachable" — the node looks *down* rather
            than *broken*, and the two get diagnosed very differently.

            The body says nothing beyond 500 on purpose: the traceback goes
            to the journal, where the operator is, and never to the browser,
            where it would name paths and columns to whoever is holding the
            phone.
            """
            try:
                self._send(app.handle(method, path, self._headers(), body))
            except Exception:                      # noqa: BLE001 — last resort
                traceback.print_exc()
                self._send(Response(500, {"error": "internal error"}))

        def do_GET(self):  # noqa: N802
            path = urllib.parse.urlparse(self.path).path
            if path in files or (path == "/" and "/index.html" in files):
                key = "/index.html" if path == "/" else path
                data = files[key]
                self.send_response(200)
                # Decided from the bytes, not the name: the studio shell is
                # also served at `/sabaapp`, which has no extension, and
                # handing a partner `application/octet-stream` makes the
                # phone offer to download the page instead of open it.
                if key.endswith(".woff2"):
                    ctype = "font/woff2"
                elif (key.endswith(".html")
                      or data[:15].lstrip().lower().startswith(b"<!doctype")):
                    # Decided from the bytes, not the name: the studio shell
                    # is also served at `/sabaapp`, which has no extension.
                    ctype = "text/html; charset=utf-8"
                else:
                    ctype = "application/octet-stream"
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("X-Content-Type-Options", "nosniff")
                if key.endswith(".woff2"):
                    # The font changes when the file changes, which is never
                    # during a run. A year is what a fingerprinted asset gets;
                    # this one is not fingerprinted, so a day — long enough to
                    # stop refetching it on every open, short enough that
                    # replacing it does not need a cache-busting name.
                    self.send_header("Cache-Control", "public, max-age=86400")
                elif ctype.startswith("text/html"):
                    # No validator was sent with these — no ETag, no
                    # Last-Modified — so a client caching them heuristically
                    # has no way to find out they changed, and the shell is
                    # not fingerprinted either. The visible symptom is a
                    # partner reporting "I restarted it and saw no change"
                    # while the node serves the new file to every other
                    # caller, which is a very expensive thing to debug.
                    self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)
                self._audit("GET", path, 200)
                return
            self._dispatch("GET", path, b"")

        def do_POST(self):  # noqa: N802
            length = int(self.headers.get("Content-Length") or 0)
            path_now = urllib.parse.urlparse(self.path).path
            # The photo route carries base64, which is one third larger than
            # the image. Raised here and only here: lifting the global limit
            # to fit a photo would lift it for every other endpoint too.
            cap = (MAX_MEDIA_BODY_BYTES
                   if path_now.endswith(("/media", "/photos"))
                   else MAX_BODY_BYTES)
            if length > cap:
                self._send(Response(413, {"error": "payload too large"}))
                return
            body = self.rfile.read(length) if length else b""
            path = urllib.parse.urlparse(self.path).path
            self._dispatch("POST", path, body)

    return Handler


def serve(app: ApiApp, port: int, *, static: Mapping[str, bytes] | None = None,
          host: str = "127.0.0.1") -> ThreadingHTTPServer:
    """Bind a listener. Loopback only — the tunnel is the sole route in."""
    return ThreadingHTTPServer((host, port), make_handler(app, static))
