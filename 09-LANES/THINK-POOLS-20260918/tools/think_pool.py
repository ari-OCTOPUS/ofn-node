#!/usr/bin/env python3
"""THINK-POOLS — provider registry + truthful health classification.

Phase A found the defect this module exists to fix: `sakana-fugu` carried
`status: LIVE` in provider-health.jsonl while its own evidence string said
`HTTP 429 usage_limit_reached`. A router that trusts `status` will keep sending
work to a provider whose credit is gone — which is exactly the "one gets charged,
then runs out" behaviour the owner described.

So classification is derived from *evidence*, not from a declared status:

    LIVE       probe 200 and a model list, no exhaustion signal
    EXHAUSTED  credit/quota signal (429 usage_limit, insufficient_quota, 402)
    AUTH_ERROR credential rejected (401/403) - needs a human, long cooldown
    DOWN       probe failed / never succeeded
    UNKNOWN    no probe, or too old to trust (fail-closed: never routed to)

Routing order is free-first (a local endpoint costs nothing), then LIVE
providers least-used-first so no charged provider sits idle while another
drains. Nothing here prints, stores or returns a credential value.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

REGISTRY_SCHEMA = "think_provider.v1"
HEALTH_SCHEMA = "think_provider_health.v1"

DEFAULT_COOLDOWNS = {
    "EXHAUSTED": 6 * 3600,
    "AUTH_ERROR": 24 * 3600,
    "DOWN": 30 * 60,
}

# Order matters: an exhaustion signal must win over a 200 status.
_EXHAUSTION = re.compile(
    r"(?i)(usage_limit|quota|insufficient|credit|billing|out of budget|429|402)")
_AUTH_FAIL = re.compile(r"(?i)(401|403|unauthor|invalid[_ ]?key|forbidden)")
_STALE_AFTER_S = 24 * 3600


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_registry(raw: dict) -> dict:
    """Normalise a discovered provider set into the registry contract.

    `raw` maps provider name -> {"paid": bool, "key_names": [...], "models": int}.
    Only key NAMES are accepted; a value-looking entry is rejected outright.
    """
    providers = {}
    for name, meta in raw.items():
        key_names = list(meta.get("key_names", []))
        for kn in key_names:
            if not re.fullmatch(r"[A-Z0-9_]+", kn):
                raise ValueError(f"key_names must be env-var NAMES, got {kn!r}")
        providers[name] = {
            "name": name,
            "paid": bool(meta.get("paid", True)),
            "base_url_env": meta.get("base_url_env"),
            "key_names": key_names,
            "models_count": meta.get("models_count"),
            "kind": meta.get("kind", "remote" if meta.get("paid", True) else "local"),
        }
    return {"schema": REGISTRY_SCHEMA, "providers": providers}


def classify(entry: dict | None, *, now: datetime | None = None) -> dict:
    """Derive one provider's true state from its probe evidence."""
    now = now or utc_now()
    if not entry:
        return {"state": "UNKNOWN", "reason": "NO_PROBE", "cooldown_s": None}

    checked = entry.get("checked_at") or entry.get("at")
    age_s = None
    if checked:
        try:
            stamp = datetime.strptime(checked, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            age_s = (now - stamp).total_seconds()
        except ValueError:
            age_s = None

    evidence = " ".join(str(entry.get(k, "")) for k in ("evidence", "error", "status", "detail"))
    http = entry.get("http_status")
    failures = int(entry.get("consecutive_failures") or 0)
    # A /health probe reports its code inside the evidence string rather than in
    # http_status (the local llama.cpp endpoint does), so read it from there too.
    if http is None:
        m = re.search(r"(?:->|HTTP)\s*(\d{3})", evidence)
        if m:
            http = int(m.group(1))
    paid = entry.get("paid", True)

    if _EXHAUSTION.search(evidence) or http in (429, 402):
        return {"state": "EXHAUSTED", "reason": "CREDIT_OR_QUOTA_EXHAUSTED",
                "cooldown_s": DEFAULT_COOLDOWNS["EXHAUSTED"], "evidence": evidence[:160]}
    if _AUTH_FAIL.search(evidence) or http in (401, 403):
        return {"state": "AUTH_ERROR", "reason": "CREDENTIAL_REJECTED",
                "cooldown_s": DEFAULT_COOLDOWNS["AUTH_ERROR"], "evidence": evidence[:160]}
    if age_s is not None and age_s > _STALE_AFTER_S:
        return {"state": "UNKNOWN", "reason": f"PROBE_STALE({int(age_s)}s)",
                "cooldown_s": None, "evidence": evidence[:160]}
    if http == 200 and failures == 0 and ((entry.get("models_count") or 0) > 0 or not paid):
        # A paid/remote provider must show a model list; a local endpoint proves
        # liveness by reachability alone (no discovery list to count).
        return {"state": "LIVE", "reason": "PROBE_OK", "cooldown_s": None,
                "evidence": evidence[:160]}
    if failures > 0 or (http and http != 200):
        return {"state": "DOWN", "reason": f"PROBE_FAILED(http={http},fails={failures})",
                "cooldown_s": DEFAULT_COOLDOWNS["DOWN"], "evidence": evidence[:160]}
    return {"state": "UNKNOWN", "reason": "INSUFFICIENT_EVIDENCE", "cooldown_s": None}


def classify_all(health_record: dict, *, now: datetime | None = None) -> dict:
    """Classify every provider in one health record (providers nest under keys)."""
    out = {}
    for name, val in (health_record or {}).items():
        if name.startswith("_") or not isinstance(val, dict):
            continue
        out[name] = {**classify(val, now=now), "paid": val.get("paid", True)}
    return out


def routing_order(states: dict, usage: dict | None = None) -> list[str]:
    """Free providers first, then LIVE least-used-first.

    EXHAUSTED, AUTH_ERROR, DOWN and UNKNOWN are excluded — a provider whose
    state we cannot trust must not receive work. Least-used-first is what makes
    "no provider sits idle" true in practice rather than by intention.
    """
    usage = usage or {}
    live = [(n, s) for n, s in states.items() if s.get("state") == "LIVE"]
    free = [n for n, s in live if not s.get("paid", True)]
    paid = sorted((n for n, _ in live if (states[n].get("paid", True))),
                  key=lambda n: (usage.get(n, 0), n))
    return free + paid


def usage_share(usage: dict) -> dict:
    """Fraction of calls per provider, so 'none idle' is checkable with numbers."""
    total = sum(usage.values()) or 1
    return {k: round(v / total, 4) for k, v in sorted(usage.items())}


def recharge_detected(previous: dict, current: dict) -> list[str]:
    """Providers that moved from blocked back to LIVE — credit came back."""
    back = []
    for name, now_state in current.items():
        was = (previous or {}).get(name, {}).get("state")
        if was in ("EXHAUSTED", "AUTH_ERROR", "DOWN") and now_state.get("state") == "LIVE":
            back.append(name)
    return sorted(back)


def load_registry(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
