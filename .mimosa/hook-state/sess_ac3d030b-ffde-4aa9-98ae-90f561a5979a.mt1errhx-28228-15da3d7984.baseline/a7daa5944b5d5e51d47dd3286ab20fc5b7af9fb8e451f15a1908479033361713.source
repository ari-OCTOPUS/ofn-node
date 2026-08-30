#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""owner_console.discovery_facade — thin adapter to discovery.discover_facade v2.

Keeps conversation/status imports stable while provenance lives in `_ops/discovery/`.
"""
from __future__ import annotations

from typing import Any


def discover_payload(*, max_items: int = 5, query: str = "") -> dict[str, Any]:
    from discovery.sources import default_reply
    reply = default_reply(query or "کشف")
    d = reply.as_dict()
    # trim facts for payload consumers
    d["facts"] = d["facts"][:max_items]
    return d


def discover_reply_text(*, max_items: int = 5, query: str = "") -> str:
    from discovery.sources import default_reply
    reply = default_reply(query or "کشف پنهان")
    return reply.text


def discover_sources_text(*, query: str = "") -> str:
    from discovery.sources import default_reply
    return default_reply(query or "کشف پنهان").sources_text()


def discover_reply(*, query: str = ""):
    from discovery.sources import default_reply
    return default_reply(query or "کشف پنهان")
