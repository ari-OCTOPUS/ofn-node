#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""allowlist_loader.py — Parse observatory-allowlist.yaml into runtime checks.

Deny-by-default: any domain not in the allowlist is rejected.
Domain matching is exact (not suffix-based) per OBS-INV-4.
Path matching supports exact and prefix patterns.

$0 | stdlib-only (no PyYAML required) | no network | read-only on YAML.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


@dataclass(frozen=True)
class AllowlistEntry:
    """A single allowlisted domain+path rule."""
    id: str
    domain: str
    paths: tuple[str, ...]
    leg: str
    rate_limit_rps: float
    daily_request_cap: int
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RejectedEntry:
    """A rejected domain with reasons."""
    domain: str
    reasons: tuple[str, ...]


class ObservatoryAllowlist:
    """Runtime allowlist checker. Deny-by-default.

    Usage:
        al = ObservatoryAllowlist.load(path="architecture/observatory-allowlist.yaml")
        result = al.check("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson")
        # result = {"allowed": True, "entry_id": "F", "domain": "earthquake.usgs.gov", ...}
    """

    SCHEMA_VERSION = "observatory-allowlist.v2"

    def __init__(self) -> None:
        self._entries: dict[str, AllowlistEntry] = {}  # domain -> entry
        self._rejected: list[RejectedEntry] = []
        self._loaded: bool = False

    @classmethod
    def load(cls, path: str | Path | None = None) -> ObservatoryAllowlist:
        """Load allowlist from YAML file. Returns empty (deny-all) if not found."""
        instance = cls()
        if path is None:
            # Default path relative to vault root
            vault = Path(__file__).resolve().parents[2]
            path = vault / "architecture" / "observatory-allowlist.yaml"
        path = Path(path)
        if not path.exists():
            instance._loaded = True
            return instance  # deny-all: empty allowlist

        try:
            data = _parse_yaml(path.read_text(encoding="utf-8"))
        except Exception:
            instance._loaded = True
            return instance

        # Parse allowlist entries
        for entry_data in data.get("allowlist", []):
            domain = str(entry_data.get("domain", "")).strip().lower()
            if not domain:
                continue
            entry = AllowlistEntry(
                id=str(entry_data.get("id", "?")),
                domain=domain,
                paths=tuple(str(p).strip() for p in entry_data.get("paths", [])),
                leg=str(entry_data.get("leg", "")),
                rate_limit_rps=float(entry_data.get("rate_limit_rps", 0.1)),
                daily_request_cap=int(entry_data.get("daily_request_cap", 20)),
                raw=entry_data,
            )
            instance._entries[domain] = entry

        # Parse rejected entries (for informational purposes)
        for rej in data.get("rejected", []):
            instance._rejected.append(RejectedEntry(
                domain=str(rej.get("domain", "")),
                reasons=tuple(str(r) for r in rej.get("reasons_fa", [])),
            ))

        instance._loaded = True
        return instance

    def check(self, url: str) -> dict[str, Any]:
        """Check if a URL is allowed by the allowlist.

        Returns:
            allowed: bool
            entry_id: str or None
            domain: str
            path_matched: str or None
            reason: str
        """
        if not self._loaded:
            return {"allowed": False, "entry_id": None, "domain": "",
                    "path_matched": None, "reason": "allowlist-not-loaded"}

        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception:
            return {"allowed": False, "entry_id": None, "domain": "",
                    "path_matched": None, "reason": "url-parse-failure"}

        if parsed.scheme not in ("https", "http"):
            return {"allowed": False, "entry_id": None,
                    "domain": parsed.hostname or "",
                    "path_matched": None, "reason": "non-http-scheme"}

        domain = (parsed.hostname or "").strip().lower()
        path = parsed.path or "/"
        query = parsed.query or ""

        # SSRF guard: reject private/loopback/reserved IPs
        ip_check = _check_hostname_ssrf(domain)
        if not ip_check["ok"]:
            return {"allowed": False, "entry_id": None, "domain": domain,
                    "path_matched": None, "reason": ip_check["reason"]}

        # Exact domain match (not suffix-based per OBS-INV-4)
        entry = self._entries.get(domain)
        if entry is None:
            return {"allowed": False, "entry_id": None, "domain": domain,
                    "path_matched": None, "reason": "domain-not-in-allowlist"}

        # Check path: must match at least one allowed path
        # If no paths specified, deny (explicit is required)
        if not entry.paths:
            return {"allowed": False, "entry_id": entry.id, "domain": domain,
                    "path_matched": None, "reason": "no-paths-configured"}

        for allowed_path in entry.paths:
            # Handle wildcard patterns (e.g., "/v0/*.json")
            if "*" in allowed_path:
                pattern = re.escape(allowed_path).replace(r"\*", ".*")
                if re.match(f"^{pattern}$", path) or re.match(f"^{pattern}$", path + "?" + query):
                    return {"allowed": True, "entry_id": entry.id, "domain": domain,
                            "path_matched": allowed_path, "reason": "allowed"}
            # Exact or prefix match
            if path == allowed_path or path.startswith(allowed_path.rstrip("/") + "/"):
                return {"allowed": True, "entry_id": entry.id, "domain": domain,
                        "path_matched": allowed_path, "reason": "allowed"}

        return {"allowed": False, "entry_id": entry.id, "domain": domain,
                "path_matched": None, "reason": "path-not-in-allowlist"}

    def domains(self) -> list[str]:
        return list(self._entries.keys())

    def entry(self, domain: str) -> AllowlistEntry | None:
        return self._entries.get(domain.lower())

    def rejected_domains(self) -> list[str]:
        return [r.domain for r in self._rejected]


# --- SSRF hostname guard ---

_PRIVATE_PATTERNS = re.compile(
    r"^(localhost|127\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|"
    r"0\.|169\.254\.|::1|0:0:0:0:0:0:0:1|fc00:|fe80:|metadata\.google\.internal|"
    r"metadata\.amazon\.com)$",
    re.IGNORECASE | re.ASCII,
)
_NUMERIC_IP = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
_HEX_IP = re.compile(r"^0x[0-9a-f]+$", re.IGNORECASE)


def _check_hostname_ssrf(hostname: str) -> dict[str, Any]:
    """Reject private/loopback/reserved hostnames to prevent SSRF."""
    h = hostname.strip().lower()
    if not h:
        return {"ok": False, "reason": "empty-hostname"}
    # Reject IP-form hostnames
    if _NUMERIC_IP.match(h) or _HEX_IP.match(h):
        return {"ok": False, "reason": "ip-address-hostname-not-allowed"}
    # Reject known private patterns
    if _PRIVATE_PATTERNS.match(h):
        return {"ok": False, "reason": "private-reserved-hostname"}
    # Reject very long hostnames (DNS rebinding indicator)
    if len(h) > 253:
        return {"ok": False, "reason": "hostname-too-long"}
    # Reject hostnames ending with dots that might indicate DNS tricks
    if h.endswith(".local") or h.endswith(".internal") or h.endswith(".localhost"):
        return {"ok": False, "reason": "private-suffix-hostname"}
    return {"ok": True, "reason": "ok"}


# --- Minimal YAML subset parser (reuse pattern from registry.py) ---

def _parse_yaml(text: str) -> dict[str, Any]:
    """Parse a minimal YAML subset used in observatory-allowlist.yaml."""
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text) or {}
    except Exception:
        pass
    # Fallback: JSON-compatible files only
    return json.loads(text) if text.strip().startswith("{") else _hand_yaml(text)


def _hand_yaml(text: str) -> dict[str, Any]:
    """Very small indent YAML reader for allowlist files."""
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    pending_key: str | None = None

    for raw in text.splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if line.startswith("- "):
            item = line[2:].strip()
            if not isinstance(parent, list):
                continue
            parent.append(_scalar_value(item))
            continue

        if ":" in line:
            key, _, rest = line.partition(":")
            key = key.strip()
            rest = rest.strip()
            if rest == "" or rest == "|" or rest.startswith(">"):
                # Lookahead: if next line starts with "- ", make a list
                nxt: Any = []
                parent[key] = nxt
                stack.append((indent, nxt))
            elif rest.startswith("[") and rest.endswith("]"):
                inner = rest[1:-1].strip()
                parent[key] = [
                    _scalar_value(x.strip()) for x in inner.split(",") if x.strip()
                ] if inner else []
            else:
                parent[key] = _scalar_value(rest)
    return root


def _scalar_value(v: str) -> Any:
    if v in ("true", "True"):
        return True
    if v in ("false", "False"):
        return False
    if v in ("null", "None", "~"):
        return None
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    try:
        if "." in v:
            return float(v)
        return int(v)
    except ValueError:
        return v


if __name__ == "__main__":
    import sys

    # Smoke test
    al = ObservatoryAllowlist.load()
    assert al._loaded

    # Check allowed domains from real allowlist
    if "earthquake.usgs.gov" in al.domains():
        r = al.check("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson")
        assert r["allowed"], f"USGS should be allowed: {r}"
        assert r["entry_id"] == "F"

    # Non-allowed domain
    r2 = al.check("https://evil.com/api")
    assert not r2["allowed"]
    assert "not-in-allowlist" in r2["reason"]

    # SSRF tests
    r3 = al.check("http://127.0.0.1/admin")
    assert not r3["allowed"]
    assert "private" in r3["reason"] or "ip-address" in r3["reason"]

    r4 = al.check("http://169.254.169.254/metadata")
    assert not r4["allowed"]

    r5 = al.check("ftp://evil.com/file")
    assert not r5["allowed"]
    assert "non-http" in r5["reason"]

    print("OK allowlist_loader smoke test")
    sys.exit(0)
