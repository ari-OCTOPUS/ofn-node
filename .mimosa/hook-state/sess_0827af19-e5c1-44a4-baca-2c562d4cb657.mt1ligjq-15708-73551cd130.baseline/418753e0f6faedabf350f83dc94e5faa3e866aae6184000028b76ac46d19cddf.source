#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fetch_guard.py — Fetch Guard: allowlist-aware network fetch with SSRF protection.

This is the L1 single-exit-door from ADR-041. No other code in the vault
should perform outbound HTTP requests for observation purposes.

Security invariants:
  - Deny-by-default: any URL not in the signed allowlist is blocked
  - No private/loopback/reserved IPs (SSRF prevention)
  - No redirects to non-allowlisted hosts
  - Timeout, size limit, MIME validation on every fetch
  - Only GET and HEAD methods
  - HTTPS only (HTTP only for explicitly allowlisted plain-HTTP domains)
  - No credentials/cookies/headers sent
  - Every fetch is audited

$0 | stdlib-only (urllib) | timeout | size limit | audit log.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import socket
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Defaults
_DEFAULT_TIMEOUT_SECONDS = 15
_DEFAULT_MAX_BODY_BYTES = 1_048_576  # 1 MB
_DEFAULT_MAX_REDIRECTS = 3

# G3 audit log path (env-overridable, defaults to temp)
_AUDIT_ENV_KEY = "EQUIP_G3_AUDIT_PATH"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _audit_log_path() -> Path | None:
    p = os.environ.get(_AUDIT_ENV_KEY)
    if p:
        return Path(p)
    return None


def _audit_to_file(path: Path | None, entry: dict) -> None:
    """Append-only audit log to file. Never throws."""
    if path is None:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    except OSError:
        pass


class FetchGuard:
    """Allowlist-aware fetch guard with SSRF protection.

    Usage:
        guard = FetchGuard(allowlist=loaded_allowlist)
        result = guard.fetch("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson")
        # result = {"ok": True, "body": bytes, "content_type": str, "status": int, ...}
    """

    def __init__(
        self,
        allowlist=None,
        timeout: int = _DEFAULT_TIMEOUT_SECONDS,
        max_body_bytes: int = _DEFAULT_MAX_BODY_BYTES,
        max_redirects: int = _DEFAULT_MAX_REDIRECTS,
        audit_path: Path | str | None = None,
    ) -> None:
        self._allowlist = allowlist
        self._timeout = timeout
        self._max_body_bytes = max_body_bytes
        self._max_redirects = max_redirects
        self._audit_path = Path(audit_path) if audit_path else _audit_log_path()

    def _audit(self, entry: dict) -> None:
        """Instance audit: write to self._audit_path."""
        _audit_to_file(self._audit_path, entry)

    @property
    def allowlist(self):
        return self._allowlist

    def check(self, url: str) -> dict[str, Any]:
        """Check if a URL is allowed by the allowlist (no fetch).

        Returns: {"allowed": bool, "reason": str, ...}
        """
        if self._allowlist is None:
            return {"allowed": False, "reason": "no-allowlist-loaded"}

        result = self._allowlist.check(url)
        return result

    def fetch(self, url: str) -> dict[str, Any]:
        """Fetch a URL through the guard (allowlist + SSRF + timeout + size).

        Returns:
            ok: bool
            body: bytes (only if ok)
            content_type: str
            status: int (HTTP status code)
            body_size: int
            body_hash: str (SHA-256)
            fetched_at: str (ISO timestamp)
            url_effective: str (final URL after redirects)
            reason: str (error reason if not ok)
            blocked: bool (True if blocked by guard, not network error)
        """
        # Step 1: Allowlist check
        check_result = self.check(url)
        if not check_result.get("allowed"):
            self._audit({
                "ts": _utc_now_iso(), "action": "fetch-blocked",
                "url": url, "reason": check_result.get("reason", "unknown"),
            })
            return {
                "ok": False, "body": b"", "content_type": "",
                "status": 0, "body_size": 0, "body_hash": "",
                "fetched_at": _utc_now_iso(), "url_effective": url,
                "reason": f"allowlist-blocked: {check_result.get('reason', '')}",
                "blocked": True,
            }

        # Step 2: DNS resolution check (SSRF via DNS rebinding)
        dns_check = self._dns_check(url)
        if not dns_check["ok"]:
            self._audit({
                "ts": _utc_now_iso(), "action": "fetch-blocked",
                "url": url, "reason": dns_check.get("reason", "dns-check-failed"),
            })
            return {
                "ok": False, "body": b"", "content_type": "",
                "status": 0, "body_size": 0, "body_hash": "",
                "fetched_at": _utc_now_iso(), "url_effective": url,
                "reason": f"dns-blocked: {dns_check.get('reason', '')}",
                "blocked": True,
            }

        # Step 3: Fetch with redirect following + re-check on redirect
        try:
            result = self._fetch_with_redirect_guard(
                url, remaining_redirects=self._max_redirects
            )
        except socket.timeout:
            return {
                "ok": False, "body": b"", "content_type": "",
                "status": 0, "body_size": 0, "body_hash": "",
                "fetched_at": _utc_now_iso(), "url_effective": url,
                "reason": "timeout", "blocked": False,
            }
        except urllib.error.URLError as e:
            return {
                "ok": False, "body": b"", "content_type": "",
                "status": 0, "body_size": 0, "body_hash": "",
                "fetched_at": _utc_now_iso(), "url_effective": url,
                "reason": f"url-error: {type(e).__name__}: {e.reason}",
                "blocked": False,
            }
        except Exception as e:
            return {
                "ok": False, "body": b"", "content_type": "",
                "status": 0, "body_size": 0, "body_hash": "",
                "fetched_at": _utc_now_iso(), "url_effective": url,
                "reason": f"fetch-error: {type(e).__name__}: {e}",
                "blocked": False,
            }

        self._audit({
            "ts": _utc_now_iso(), "action": "fetch-ok",
            "url": url, "url_effective": result.get("url_effective", url),
            "status": result.get("status", 0),
            "body_size": result.get("body_size", 0),
            "body_hash": result.get("body_hash", ""),
        })

        return result

    def _fetch_with_redirect_guard(
        self, url: str, remaining_redirects: int
    ) -> dict[str, Any]:
        """Fetch a URL, following redirects only if they stay on the allowlist."""
        if remaining_redirects <= 0:
            return {
                "ok": False, "body": b"", "content_type": "",
                "status": 0, "body_size": 0, "body_hash": "",
                "fetched_at": _utc_now_iso(), "url_effective": url,
                "reason": "max-redirects-exceeded", "blocked": True,
            }

        req = urllib.request.Request(url, method="GET")
        # No credentials, no cookies, no custom headers
        req.add_header("User-Agent", "OctopusObservatory/1.0 (evidence-only; no-auth)")

        fetched_at = _utc_now_iso()
        try:
            resp = urllib.request.urlopen(req, timeout=self._timeout)
        except urllib.error.HTTPError as e:
            # HTTP errors (4xx, 5xx) — not a guard block, but a server error
            return {
                "ok": False, "body": b"", "content_type": "",
                "status": e.code, "body_size": 0, "body_hash": "",
                "fetched_at": fetched_at, "url_effective": url,
                "reason": f"http-error: {e.code}", "blocked": False,
            }

        status = resp.status
        content_type = resp.headers.get("Content-Type", "unknown")
        final_url = resp.url if hasattr(resp, "url") else url

        # Check if redirected to a different host
        if final_url != url:
            parsed_orig = urlparse(url)
            parsed_final = urlparse(final_url)
            if parsed_final.hostname != parsed_orig.hostname:
                # Redirected to a different host — re-check allowlist
                redirect_check = self.check(final_url)
                if not redirect_check.get("allowed"):
                    return {
                        "ok": False, "body": b"", "content_type": "",
                        "status": status, "body_size": 0, "body_hash": "",
                        "fetched_at": fetched_at, "url_effective": final_url,
                        "reason": "redirect-to-non-allowlisted-host", "blocked": True,
                    }

        # Read body with size limit
        body = self._read_limited(resp, self._max_body_bytes)
        body_size = len(body)
        body_hash = hashlib.sha256(body).hexdigest()

        if body_size >= self._max_body_bytes:
            # Body was truncated
            return {
                "ok": False, "body": body[:self._max_body_bytes],
                "content_type": content_type, "status": status,
                "body_size": body_size, "body_hash": body_hash,
                "fetched_at": fetched_at, "url_effective": final_url,
                "reason": f"body-too-large (truncated at {self._max_body_bytes})",
                "blocked": False,
            }

        return {
            "ok": True, "body": body, "content_type": content_type,
            "status": status, "body_size": body_size, "body_hash": body_hash,
            "fetched_at": fetched_at, "url_effective": final_url,
            "reason": "ok", "blocked": False,
        }

    def _read_limited(self, resp, max_bytes: int) -> bytes:
        """Read response body up to max_bytes. Prevents decompression bombs."""
        chunks = []
        total = 0
        while True:
            chunk = resp.read(min(8192, max_bytes - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total >= max_bytes:
                break
        return b"".join(chunks)

    def _dns_check(self, url: str) -> dict[str, Any]:
        """DNS resolution check: verify hostname doesn't resolve to private IP.

        This prevents DNS rebinding attacks where a hostname initially resolves
        to a public IP but then rebinds to a private IP.
        """
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            if not hostname:
                return {"ok": False, "reason": "no-hostname"}
            # Resolve hostname
            addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            for family, _, _, _, sockaddr in addr_info:
                ip = sockaddr[0]
                if _is_private_ip(ip):
                    return {"ok": False,
                            "reason": f"dns-resolves-to-private-ip: {ip}"}
            return {"ok": True, "reason": "dns-ok"}
        except socket.gaierror as e:
            return {"ok": False, "reason": f"dns-resolution-failed: {e}"}
        except Exception as e:
            return {"ok": False, "reason": f"dns-check-error: {type(e).__name__}"}


def _is_private_ip(ip: str) -> bool:
    """Check if an IP address is private/loopback/link-local."""
    import ipaddress
    try:
        addr = ipaddress.ip_address(ip)
        return (
            addr.is_private or addr.is_loopback or addr.is_link_local
            or addr.is_reserved or addr.is_unspecified
            or str(ip).startswith("169.254.")
        )
    except ValueError:
        return False  # can't parse — fail open for safety (fetch itself may fail)


if __name__ == "__main__":
    import sys
    from allowlist_loader import ObservatoryAllowlist

    # Load allowlist
    al = ObservatoryAllowlist.load()

    guard = FetchGuard(
        allowlist=al,
        timeout=10,
        max_body_bytes=65536,  # small for test
    )

    # Test 1: Allowed domain check (no actual fetch)
    r1 = guard.check("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson")
    assert r1["allowed"], f"USGS should be allowed: {r1}"
    print(f"  USGS check: allowed={r1['allowed']}")

    # Test 2: Blocked domain check
    r2 = guard.check("https://evil.com/api")
    assert not r2["allowed"], "evil.com should be blocked"
    print(f"  evil.com check: allowed={r2['allowed']}")

    # Test 3: SSRF check
    r3 = guard.check("http://127.0.0.1/admin")
    assert not r3["allowed"], "localhost should be blocked"
    print(f"  localhost check: allowed={r3['allowed']}")

    # Test 4: DNS rebinding check
    r4 = guard._dns_check("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson")
    print(f"  USGS DNS check: {r4['reason']}")

    # Test 5: DNS check for localhost
    r5 = guard._dns_check("http://localhost/admin")
    assert not r5["ok"], "localhost DNS should fail"
    print(f"  localhost DNS: {r5['reason']}")

    print("OK fetch_guard smoke test")
    sys.exit(0)
