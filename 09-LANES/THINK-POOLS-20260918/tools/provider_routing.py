#!/usr/bin/env python3
"""Registry-aware brain routing (PERFUSION P1).

Problem this fixes, measured 2026-09-18: `BRAIN_PROVIDER=fugu` pointed at
sakana-fugu, whose own probe evidence says `HTTP 429 usage_limit_reached` — the
brain was calling a provider with no credit while three live providers and a
free local model sat unused.

Rules:
  * A manual pin is still honoured when it is routable (reproducibility).
  * When the pin is NOT routable, routing falls back to the registry order:
    free providers first, then least-used live providers.
  * Never choose a provider whose state we cannot trust (EXHAUSTED / AUTH_ERROR
    / DOWN / UNKNOWN are excluded).
  * `brainport` can only name models for the providers it already knows, so
    `decide_brainport()` restricts itself to those tokens; the wider
    `decide()` is for consumers that carry a model map.

Every decision is appended to a routing ledger so "which provider did the brain
actually use" is answerable from evidence, not from configuration.

Read-only with respect to providers; writes only its own ledger.
"""

from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone

TOOLS = pathlib.Path("/home/ari/ofn/tools")
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
import think_pool as tp  # noqa: E402

BASE = pathlib.Path("/home/ari/ofn/state/api-budget")
HEALTH = BASE / "config" / "provider-health.jsonl"
LEDGER = BASE / "config" / "brain-routing.jsonl"

# Registry name -> the token brainport uses in its own model map.
BRAINPORT_TOKENS = {"sakana-fugu": "fugu", "deepseek": "deepseek"}

# How much thinking a provider is fit for. Found by executing: routing "free
# first" sent the STRONG tier to a 0.6B local model, which would trade the
# owner's strong pool for zero cost. Free-first is correct for bulk work and
# wrong for reasoning, so the tier now gates the candidate set.
TIER_RANK = {"default": 0, "standard": 0, "cheap": 0,
             "strong": 1, "hard": 1, "reasoning": 1,
             "frontier": 2}
PROVIDER_MAX_RANK = {
    "local-llamacpp-180": 0,   # qwen3-0.6b: adequate for bulk, not for reasoning
    "sakana-fugu": 2,
    "deepseek": 2,
    "openai": 2,
    "anthropic": 2,
    "gemini": 2,
}


def min_rank_for(tier: str | None) -> int:
    return TIER_RANK.get((tier or "default").strip().lower(), 1)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def latest_states() -> tuple[dict, str | None]:
    """Classified state of every provider from the newest health record."""
    if not HEALTH.exists():
        return {}, None
    rows = []
    for line in HEALTH.read_text(errors="replace").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    if not rows:
        return {}, None
    newest = rows[-1]
    states = tp.classify_all(newest.get("record") or {})
    for name, s in states.items():
        s["paid"] = (newest.get("record") or {}).get(name, {}).get("paid", s.get("paid", True))
    return states, newest.get("at")


def usage_counts() -> dict:
    """Call counts per provider from the budget ledger (least-used-first input)."""
    usage: dict[str, int] = {}
    led = BASE / "budget-ledger.jsonl"
    if not led.exists():
        return usage
    for line in led.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        name = str(r.get("provider") or "unknown")
        usage[name] = usage.get(name, 0) + 1
    return usage


def decide(pin: str | None = None, states: dict | None = None, tier: str | None = None) -> dict:
    """Full routing decision over the whole registry.

    `tier` gates the candidate set: a tier that needs real reasoning excludes
    providers not fit for it (the free 0.6B local model), even though they are
    first in the general order.
    """
    if states is None:
        states, probed_at = latest_states()
    else:
        probed_at = None
    usage = usage_counts()
    order = tp.routing_order(states, usage=usage)
    min_rank = min_rank_for(tier)
    if min_rank > 0:
        order = [n for n in order if PROVIDER_MAX_RANK.get(n, 2) >= min_rank]

    pin_state = (states.get(pin) or {}).get("state") if pin else None
    pin_fit = pin is None or PROVIDER_MAX_RANK.get(pin, 2) >= min_rank
    if pin and pin_state == "LIVE" and pin_fit:
        chosen, reason = pin, "PIN_ROUTABLE"
    elif pin and pin_state == "LIVE" and not pin_fit:
        chosen = order[0] if order else None
        reason = f"PIN_UNDERPOWERED_FOR_TIER({tier})_FALLBACK"
    elif pin and pin_state:
        chosen = order[0] if order else None
        reason = f"PIN_BLOCKED({pin}={pin_state})_FALLBACK"
    elif pin:
        chosen = order[0] if order else None
        reason = "PIN_UNKNOWN_FALLBACK"
    else:
        chosen, reason = (order[0] if order else None), "REGISTRY_ORDER"

    return {
        "schema": "brain_routing.v1",
        "at_utc": _utc(),
        "tier": tier,
        "min_rank": min_rank,
        "pin": pin,
        "pin_state": pin_state,
        "chosen": chosen,
        "reason": reason,
        "order": order,
        "excluded": sorted(n for n in states if n not in order),
        "states": {n: s.get("state") for n, s in sorted(states.items())},
        "health_probed_at": probed_at,
    }


def decide_brainport(pin: str | None = None, states: dict | None = None) -> dict:
    """Restricted decision: only providers brainport can name a model for.

    `states` is injectable so the fallback logic is testable without touching
    the live health record.
    """
    full = decide(pin, states=states)
    if pin in BRAINPORT_TOKENS and full["reason"] == "PIN_ROUTABLE":
        full["token"] = BRAINPORT_TOKENS[pin]
        return full
    for name in full["order"]:
        if name in BRAINPORT_TOKENS:
            full["chosen"] = name
            full["token"] = BRAINPORT_TOKENS[name]
            full["reason"] = full["reason"] + "->BRAINPORT_OK"
            return full
    full["token"] = None
    full["reason"] = full["reason"] + "->NO_BRAINPORT_PROVIDER"
    return full


def env_pin() -> str | None:
    """The configured pin, translated to registry spelling.

    brainport spells the provider "fugu"; the registry calls it "sakana-fugu".
    """
    import os
    raw = (os.environ.get("BRAIN_PROVIDER") or "").strip().lower()
    if not raw:
        return None
    return {"fugu": "sakana-fugu"}.get(raw, raw)


def record(decision: dict) -> None:
    """Append the decision so usage is answerable from evidence."""
    try:
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        with LEDGER.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({k: decision[k] for k in
                                 ("at_utc", "pin", "pin_state", "chosen", "reason", "token")
                                 if k in decision}, sort_keys=True) + "\n")
    except OSError:
        pass


if __name__ == "__main__":
    args = sys.argv[1:]
    pin = None
    if "--pin" in args:
        pin = args[args.index("--pin") + 1]
    else:
        pin = env_pin()
    if "--brainport" in args:
        d = decide_brainport(pin)
        record(d)
        print(d.get("token") or "")
    elif "--pick" in args:
        d = decide(pin)
        record(d)
        print(d.get("chosen") or "")
    else:
        print(json.dumps(decide(pin), indent=1, ensure_ascii=False))
