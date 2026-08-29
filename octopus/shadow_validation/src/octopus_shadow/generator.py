"""Loopback-only synthetic observe poster. Never run against the live Sensorium board."""

from __future__ import annotations

import ipaddress
import json
import socket
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

ALLOWED_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
ALLOWED_PATH = "/v1/observe/synthetic"
ALLOWED_PORT = 8080
MAX_DURATION_S = 15 * 60
MIN_INTERVAL_S = 0.5
MAX_REQUESTS = 2000


class GeneratorError(ValueError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise GeneratorError("redirect_forbidden")


def _loopback_only(hostname: str) -> None:
    host = hostname.strip("[]").lower()
    if host not in ALLOWED_HOSTS:
        raise GeneratorError("lookalike_hostname_rejected")
    infos = socket.getaddrinfo(host, ALLOWED_PORT, type=socket.SOCK_STREAM)
    if not infos:
        raise GeneratorError("hostname_unresolvable")
    for info in infos:
        addr = info[4][0]
        ip = ipaddress.ip_address(addr)
        if not ip.is_loopback:
            raise GeneratorError("resolved_address_not_loopback")


def validate_destination(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "http":
        raise GeneratorError("scheme_must_be_http")
    if parsed.username or parsed.password:
        raise GeneratorError("userinfo_forbidden")
    if parsed.query or parsed.fragment:
        raise GeneratorError("query_or_fragment_forbidden")
    if parsed.path != ALLOWED_PATH:
        raise GeneratorError("path_must_be_observe_synthetic")
    port = parsed.port if parsed.port is not None else 80
    if port != ALLOWED_PORT:
        raise GeneratorError("port_must_be_8080")
    hostname = parsed.hostname or ""
    _loopback_only(hostname)
    return parsed.geturl().split("#")[0]


class ChaosGenerator:
    """Optional tool. POSTs JSON only. Caps duration/rate. Does not execute host actions."""

    def __init__(self, url: str = "http://127.0.0.1:8080/v1/observe/synthetic") -> None:
        self.url = validate_destination(url)
        self.started_at = time.monotonic()
        self.requests = 0
        self._last_at = 0.0

    def _limit(self) -> None:
        elapsed = time.monotonic() - self.started_at
        if elapsed > MAX_DURATION_S:
            raise GeneratorError("duration_cap")
        if self.requests >= MAX_REQUESTS:
            raise GeneratorError("request_cap")
        now = time.monotonic()
        if self._last_at and (now - self._last_at) < MIN_INTERVAL_S:
            raise GeneratorError("rate_cap")

    def post(self, payload: dict, opener: urllib.request.OpenerDirector | None = None) -> dict:
        self._limit()
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(
            self.url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        handler = opener or urllib.request.build_opener(NoRedirect)
        try:
            with handler.open(request, timeout=5) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            raise GeneratorError(f"http_{exc.code}") from exc
        doc = json.loads(raw.decode("utf-8") or "{}")
        if doc.get("executable") is True:
            raise GeneratorError("response_must_not_be_executable")
        if str(doc.get("action") or "NONE") != "NONE":
            raise GeneratorError("response_action_must_be_none")
        self.requests += 1
        self._last_at = time.monotonic()
        return doc
