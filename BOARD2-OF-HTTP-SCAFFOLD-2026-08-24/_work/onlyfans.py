"""OnlyFans adapter — HTTP client scaffold, dry-hold until second owner GO (G1, 2026-08-24).

Board2 / marketing scaffold. Slice G1 adds a thin stdlib-only HTTP client
(``_post_create``) that is UNREACHABLE from ``publish()`` until a second,
explicit owner GO arms it: ``OFN_ONLYFANS_HTTP_ARM=1`` is that second lock
and stays unset here. Until then the deepest ``publish()`` can reach with
``LIVE=1`` + cookie present is the non-sending rule
``onlyfans:http-scaffold-dry-hold`` — no socket is ever opened.

Contract (unchanged defaults + the G1 addition):

- dry_run=True                             -> ok,  adapter:dry-run
- dry_run=False, OFN_ONLYFANS_LIVE unset   -> wire:disabled
- LIVE=1, no cookie                        -> onlyfans:no-credentials
- LIVE=1 + cookie, second lock unset       -> onlyfans:http-scaffold-dry-hold (no network)
- (only after second owner GO) LIVE=1 + cookie + HTTP_ARM=1 -> _post_create attempt

Secrets mirror telegram_channel: read at call time from env
(OFN_ONLYFANS_SESSION_COOKIE / OFN_ONLYFANS_USER_AGENT), never stored on
the class, never logged, never echoed into rule strings. urllib.request
with a short timeout; every failure maps to a ``rule=`` string —
publish() never raises.

The post endpoint is NOT hardcoded: ``_post_create`` reads
``OFN_ONLYFANS_POST_URL`` (owner sets it at GO time, after the endpoint /
payload contract is reviewed as part of G3/G5). Without it the client
refuses with ``onlyfans:endpoint-unconfigured`` rather than guessing.

Do not invent captions. Do not auto-enqueue. telegram_channel remains the
live caption-gated path.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from ofn.adapters.platforms.base import (
    PublishRequest,
    PublishResult,
    RULE_DRY_RUN,
    RULE_WIRE_CLOSED,
)

# Documented env placeholders (names only; values are owner/vault-side):
#   OFN_ONLYFANS_LIVE=1          — only after second owner GO (checklist)
#   OFN_ONLYFANS_HTTP_ARM=1      — the second lock: LIVE+cookie still cannot
#                                  reach HTTP without this arming flag
#   OFN_ONLYFANS_SESSION_COOKIE  — vault/secrets only, never in chat / node.env
#   OFN_ONLYFANS_USER_AGENT      — optional
#   OFN_ONLYFANS_ACCOUNT_ID      — optional account selector
#   OFN_ONLYFANS_POST_URL        — endpoint, set by owner at GO time (never guessed)

RULE_NO_CREDENTIALS = "onlyfans:no-credentials"
RULE_HTTP_HOLD = "onlyfans:http-scaffold-dry-hold"
RULE_ENDPOINT_UNCONFIGURED = "onlyfans:endpoint-unconfigured"
RULE_BAD_RESPONSE = "onlyfans:bad-response"
RULE_NETWORK_ERROR = "onlyfans:network-error"

_HTTP_TIMEOUT_S = 15

__all_platform__ = "onlyfans"


def _env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


class OnlyFansAdapter:
    """Scaffold publisher for OnlyFans. Dry-run by default; HTTP double-locked."""

    platform = "onlyfans"

    def __init__(self, account_id: str = ""):
        self.account_id = account_id or _env("OFN_ONLYFANS_ACCOUNT_ID")

    def publish(self, req: PublishRequest) -> PublishResult:
        if req.dry_run:
            return PublishResult(
                True,
                self.platform,
                req.idempotency_key,
                rule=RULE_DRY_RUN,
            )

        if _env("OFN_ONLYFANS_LIVE") != "1":
            # Closed gate is a feature, not a crash (same shape as bluesky/shopify).
            return PublishResult(
                False,
                self.platform,
                req.idempotency_key,
                rule=RULE_WIRE_CLOSED,
            )

        cookie = _env("OFN_ONLYFANS_SESSION_COOKIE")
        if not cookie:
            return PublishResult(
                False,
                self.platform,
                req.idempotency_key,
                rule=RULE_NO_CREDENTIALS,
            )

        # G1: the HTTP client exists below, but it is unreachable until the
        # second owner GO arms OFN_ONLYFANS_HTTP_ARM=1
        # (see SECOND-GO-CHECKLIST.md in the evidence pack).
        if _env("OFN_ONLYFANS_HTTP_ARM") != "1":
            return PublishResult(
                False,
                self.platform,
                req.idempotency_key,
                rule=RULE_HTTP_HOLD,
            )

        return self._post_create(req, cookie)

    def _post_create(self, req: PublishRequest, cookie: str) -> PublishResult:
        """Thin post-create client (scaffold).

        stdlib only; endpoint comes from env (never hardcoded); timeout short;
        failures map to rule strings; the cookie stays inside this stack frame
        (headers of the request) and never appears in the result. Unit-tested
        with a mocked urlopen — this slice never opens a real socket.
        """
        url = _env("OFN_ONLYFANS_POST_URL")
        if not url:
            return PublishResult(
                False,
                self.platform,
                req.idempotency_key,
                rule=RULE_ENDPOINT_UNCONFIGURED,
            )

        ua = _env("OFN_ONLYFANS_USER_AGENT") or (
            "Mozilla/5.0 (X11; Linux aarch64) ofn-scaffold/1.0"
        )
        payload = json.dumps({"text": req.caption}).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": ua,
                "Cookie": cookie,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=_HTTP_TIMEOUT_S) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            # Status code only — never echo headers/body (may reflect the cookie).
            return PublishResult(
                False,
                self.platform,
                req.idempotency_key,
                rule=f"onlyfans:http-{exc.code}",
            )
        except Exception:
            # URLError / timeout: no exception text (it can carry the URL/UA).
            return PublishResult(
                False,
                self.platform,
                req.idempotency_key,
                rule=RULE_NETWORK_ERROR,
            )
        try:
            body = json.loads(raw.decode("utf-8", "replace") or "{}")
        except ValueError:
            return PublishResult(
                False,
                self.platform,
                req.idempotency_key,
                rule=RULE_BAD_RESPONSE,
            )
        external_id = str(body.get("id") or "")
        return PublishResult(
            True,
            self.platform,
            req.idempotency_key,
            external_id=external_id or None,
            rule="adapter:ok",
        )
