#!/usr/bin/env python3
"""Owner-gated compatibility wrapper for the canonical subprocess transport.

The implementation lives in ``transport_pool.subprocess_transport`` so the
runtime and tests cannot drift between two independent DNS/HTTP workers.
"""
from __future__ import annotations

import os


def enabled() -> bool:
    return str(os.environ.get("OCTOPUS_TG_TRANSPORT_SUBPROCESS", "0")).strip().lower() \
        in {"1", "true", "yes", "on"}


def call(url: str, timeout_s: float, *, data: bytes | None = None,
         headers: dict | None = None) -> bytes | None:
    if not enabled():
        raise RuntimeError("subprocess transport is off")
    from transport_pool import subprocess_transport
    return subprocess_transport(url, timeout_s, data=data, headers=headers)
