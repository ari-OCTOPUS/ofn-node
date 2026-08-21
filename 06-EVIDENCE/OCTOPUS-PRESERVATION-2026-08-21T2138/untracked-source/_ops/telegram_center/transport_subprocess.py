#!/usr/bin/env python3
"""Terminable Telegram transport — DNS+HTTPS in a killable subprocess.

A daemon thread cannot cancel getaddrinfo; a subprocess CAN be terminated on a
hard deadline, so a stuck resolver cannot leak threads or sockets.

Gated by OCTOPUS_TG_TRANSPORT_SUBPROCESS=1 (default off; the live flags file is
owner-locked). Injected post/get functions and the thread-based bounded pool
remain the fixture path.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

_WORKER = r"""
import json, sys, urllib.request
url, timeout_s, data, headers = json.loads(sys.stdin.read())
req = urllib.request.Request(url, data=(data.encode('utf-8') if data else None),
                             headers=headers or {})
with urllib.request.urlopen(req, timeout=timeout_s) as resp:
    sys.stdout.write(resp.read().decode('utf-8', 'replace'))
"""


def enabled() -> bool:
    return str(os.environ.get("OCTOPUS_TG_TRANSPORT_SUBPROCESS", "0")).strip().lower() \
        in {"1", "true", "yes", "on"}


def call(url: str, timeout_s: float, *, data: bytes | None = None,
         headers: dict | None = None) -> bytes | None:
    """Run one HTTP call in a fresh subprocess with a hard deadline.

    On timeout the child is terminated (killed) by subprocess.run — the stuck
    DNS/socket cannot survive. None means the transport stalled.
    """
    if not enabled():
        raise RuntimeError("subprocess transport is off")
    payload = json.dumps([url, float(timeout_s),
                          data.decode("utf-8", "replace") if data else None,
                          headers or {}])
    try:
        proc = subprocess.run([sys.executable, "-c", _WORKER], input=payload,
                              capture_output=True, text=True,
                              timeout=float(timeout_s) + 5.0)
    except subprocess.TimeoutExpired:
        return None
    if proc.returncode != 0 or not proc.stdout:
        return None
    return proc.stdout.encode("utf-8")
