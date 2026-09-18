#!/usr/bin/env python3
"""Brain factory — turn a registry routing decision into a ready RemoteBrain.

PERFUSION step 2. `RemoteBrain` is a dataclass whose default base URL points at
sakana.ai — the provider whose own probe says the credit is gone. Any caller
that relies on the defaults therefore calls a dead provider. This module builds
the brain from the *decision* instead:

    provider  <- provider_routing.decide()   (credit-aware, free-first)
    base_url  <- providers.py registry       (verified per provider, never guessed)
    api_key   <- the provider's declared env var (value never printed)
    model     <- providers.py tier map

Additive by design: no existing caller is modified, so the live octopus is
untouched. A consumer adopts it with one line. Fail-closed: if the chosen
provider has no verified base URL, no key, or the registry has no entry, it
raises instead of inventing an endpoint.
"""

from __future__ import annotations

import os
import pathlib
import sys

TOOLS = pathlib.Path("/home/ari/ofn/tools")
STATE_BUDGET = pathlib.Path("/home/ari/ofn/state/api-budget")
for p in (str(TOOLS), str(STATE_BUDGET)):
    if p not in sys.path:
        sys.path.insert(0, p)

import provider_routing as pr  # noqa: E402

sys.path.insert(0, "/home/ari/ofn")
from ofn.adapters.remote_brain import RemoteBrain  # noqa: E402


class BrainBuildError(RuntimeError):
    """Raised instead of guessing an endpoint, key or model."""


def _registry():
    """The existing provider registry (verified endpoints live there)."""
    import providers  # noqa: PLC0415 - imported lazily so import cost is opt-in
    return providers


def build(tier: str = "default", pin: str | None = None, states: dict | None = None) -> dict:
    """Build a RemoteBrain for the current best provider.

    Returns {"brain": RemoteBrain, "decision": {...}} so the caller can log why
    this provider was chosen without re-deriving it.
    """
    decision = pr.decide(pin if pin is not None else pr.env_pin(), states=states, tier=tier)
    provider = decision.get("chosen")
    if not provider:
        raise BrainBuildError(f"no routable provider: {decision.get('reason')} "
                              f"(excluded={decision.get('excluded')})")

    reg = _registry()
    table = getattr(reg, "REGISTRY", {}) or {}
    entry = table.get(provider)
    if not entry:
        raise BrainBuildError(f"provider {provider!r} is not in the provider registry")

    # The real vendor endpoint lives in chat_url(); base() only reports an
    # optional reachability override, so using base() produced false "no base
    # URL" blocks for four callable providers. Verified 2026-09-18: chat_url()
    # yields api.deepseek.com / api.openai.com / api.anthropic.com /
    # generativelanguage.googleapis.com / api.sakana.ai / 192.168.0.180:8081.
    model = ""
    if hasattr(reg, "model"):
        try:
            model = reg.model(provider, tier) or ""
        except Exception:  # noqa: BLE001 - tier naming differs per provider
            model = ""
    if not model:
        raise BrainBuildError(f"provider {provider!r} has no model mapped for tier {tier!r}")

    try:
        chat = reg.chat_url(provider, model)
    except Exception as exc:  # noqa: BLE001
        raise BrainBuildError(f"provider {provider!r} chat_url failed: {type(exc).__name__}") from exc
    if not chat:
        raise BrainBuildError(f"provider {provider!r} has no resolvable chat endpoint")

    # RemoteBrain speaks the OpenAI dialect: POST {base}/chat/completions.
    suffix = "/chat/completions"
    if not chat.endswith(suffix):
        raise BrainBuildError(
            f"provider {provider!r} needs a provider-specific adapter "
            f"(endpoint {chat.split('//')[-1].split('/')[0]} is not OpenAI-dialect)")

    key_var = entry.get("key_var")
    api_key = os.environ.get(key_var, "") if key_var else ""
    if key_var and not api_key:
        raise BrainBuildError(f"provider {provider!r} needs {key_var}, which is not set")
    base = chat[: -len(suffix)]

    brain = RemoteBrain(api_key=api_key, model=model, base_url=base)
    pr.record({**decision, "tier": tier, "built_model": model,
               "base_host": base.split("//")[-1].split("/")[0]})
    return {"brain": brain, "decision": decision, "model": model,
            "base_host": base.split("//")[-1].split("/")[0]}


if __name__ == "__main__":
    tier = "default"
    args = sys.argv[1:]
    if "--tier" in args:
        tier = args[args.index("--tier") + 1]
    try:
        out = build(tier=tier)
        print(f"provider={out['decision']['chosen']} model={out['model']} "
              f"base_host={out['base_host']} reason={out['decision']['reason']}")
    except BrainBuildError as exc:
        print(f"BLOCKED: {exc}")
        raise SystemExit(2)
