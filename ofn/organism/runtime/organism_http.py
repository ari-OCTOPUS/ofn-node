"""HTTP client for organism 8090. Token is a header, never a query string."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from ofn.organism.runtime.lan_auth import TOKEN_HEADER, load_lan_token, lan_token_required


class OrganismHttpResult:
    def __init__(
        self,
        status: int,
        body: Any = None,
        kind: str = "ok",
        error: str | None = None,
    ):
        self.status = status
        self.body = body
        self.kind = kind
        self.error = error

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "kind": self.kind,
            "error": self.error,
            "has_body": self.body is not None,
        }


def _headers(include_token: bool) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if include_token and lan_token_required():
        token = load_lan_token()
        if token:
            headers[TOKEN_HEADER] = token
    return headers


def organism_request(
    url: str,
    *,
    method: str = "GET",
    data: bytes | None = None,
    timeout: float = 5.0,
    include_token: bool = True,
    retries: int = 1,
) -> OrganismHttpResult:
    """Limited retries. 401 is never retried. Token is not logged."""
    if "X-Octopus-Token=" in url or "lan_token=" in url:
        raise ValueError("token_must_not_be_in_url")
    attempt = 0
    last: OrganismHttpResult | None = None
    max_attempts = max(1, retries)
    while attempt < max_attempts:
        attempt += 1
        req = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers=_headers(include_token),
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                body = None
                if raw:
                    try:
                        body = json.loads(raw.decode("utf-8"))
                    except json.JSONDecodeError:
                        body = None
                return OrganismHttpResult(int(resp.status), body, "ok")
        except urllib.error.HTTPError as exc:
            kind = "auth_failure" if exc.code in {401, 403} else "http_error"
            last = OrganismHttpResult(int(exc.code), None, kind, "http_error")
            if kind == "auth_failure":
                return last
        except TimeoutError:
            last = OrganismHttpResult(0, None, "timeout", "timeout")
        except Exception as exc:
            last = OrganismHttpResult(0, None, "unhealthy", type(exc).__name__)
    return last or OrganismHttpResult(0, None, "unhealthy", "unknown")
