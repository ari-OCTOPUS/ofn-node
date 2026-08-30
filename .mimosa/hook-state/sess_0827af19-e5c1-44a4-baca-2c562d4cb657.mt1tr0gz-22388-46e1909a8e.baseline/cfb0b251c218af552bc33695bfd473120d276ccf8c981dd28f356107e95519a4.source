"""LLM client + tier router glue -- the "brain" wiring.

Turns a task kind into the right model (via gates.yaml), calls the Anthropic
Messages API, returns text + token usage + a cost estimate, enforces the
per-run cost guard, and logs cost as a METRIC to the ledger.

Design choices (why this shape):
  * The network call is a pluggable `transport`, so the whole thing is testable
    OFFLINE with a fake -- no API key, no network needed for CI.
  * The real transport uses only the stdlib (urllib): NO required third-party
    dependency, and the API key is read from ANTHROPIC_API_KEY, never hardcoded.
  * `creativity_llm_fn` loads the agent's ROLE PROMPT (agents/creativity-blackbox.md)
    as the system prompt -- the .md "mind" drives the .py "body".
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

_ROOT = Path(__file__).resolve().parents[1]
for _s in ("common", "ledger"):
    sys.path.insert(0, str(_ROOT / _s))

import router  # noqa: E402

# Overridable endpoint: elsewhere in this vault ANTHROPIC_API_KEY deliberately
# carries a DeepSeek key (routed via ANTHROPIC_BASE_URL) -- without this override
# and the guard below, that key would leak to api.anthropic.com.
API_URL = (os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
           .rstrip("/") + "/v1/messages")
ANTHROPIC_VERSION = "2023-06-01"


def _real_transport(model: str, system: str, user: str, max_tokens: int,
                    api_key: str, timeout: int = 60) -> dict[str, Any]:
    # Two-way leak guard on the REAL hostname (substring checks are spoofable):
    #   1) non-Anthropic-looking key must never go to api.anthropic.com;
    #   2) a real Anthropic key (sk-ant-*) must never go anywhere else.
    host = urllib.parse.urlsplit(API_URL).hostname or ""
    is_anthropic = host == "api.anthropic.com" or host.endswith(".anthropic.com")
    if is_anthropic and not api_key.startswith("sk-ant-"):
        raise RuntimeError(
            "leak guard: key does not look like an Anthropic key (sk-ant-*) but "
            "the endpoint is api.anthropic.com -- set ANTHROPIC_BASE_URL to the "
            "provider this key belongs to. (key not shown)")
    if api_key.startswith("sk-ant-") and not is_anthropic:
        raise RuntimeError(
            f"leak guard: an Anthropic key (sk-ant-*) must not be sent to a "
            f"non-Anthropic endpoint ({host or 'unknown host'}) -- unset or fix "
            "ANTHROPIC_BASE_URL. (key not shown)")
    body = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }).encode("utf-8")
    req = urllib.request.Request(API_URL, data=body, headers={
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # pragma: no cover
        return json.loads(resp.read().decode("utf-8"))


class LLMClient:
    """Picks a model by task kind, calls it, meters cost, guards the budget."""

    def __init__(self, genome, api_key: str | None = None,
                 transport: Callable | None = None, ledger=None) -> None:
        self.genome = genome
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.transport = transport            # inject a fake for tests
        self.ledger = ledger

    def complete(self, task_kind: str, system: str, user: str,
                 max_tokens: int = 1024) -> dict[str, Any]:
        choice = router.choose(self.genome, task_kind)
        model = choice["model"]

        if self.transport is not None:
            raw = self.transport(model, system, user, max_tokens)
        else:
            if not self.api_key:
                raise RuntimeError("no ANTHROPIC_API_KEY set and no transport injected")
            raw = _real_transport(model, system, user, max_tokens, self.api_key)

        text = "".join(b.get("text", "") for b in raw.get("content", [])
                       if b.get("type") == "text")
        usage = raw.get("usage", {}) or {}
        tin, tout = usage.get("input_tokens", 0), usage.get("output_tokens", 0)
        cost = (tin / 1e6) * (choice.get("in_price") or 0) \
            + (tout / 1e6) * (choice.get("out_price") or 0)
        cap = self.genome.run_guards.get("max_cost_per_run_usd", 2.0)
        over = cost > cap

        if self.ledger is not None:
            self.ledger.append("METRIC",
                               {"llm_cost_usd": round(cost, 6), "model": model,
                                "task": task_kind, "over_cap": over}, actor="router")
        return {"text": text, "model": model, "tier": choice["tier"],
                "cost_usd": cost, "tokens_in": tin, "tokens_out": tout, "over_cap": over}


def _extract_json(text: str) -> dict[str, Any]:
    """Pull a JSON object out of a model reply (handles ```json fences / prose)."""
    s = text.strip()
    i, j = s.find("{"), s.rfind("}")
    if i == -1 or j == -1:
        raise ValueError(f"no JSON object in model reply: {text[:120]!r}")
    return json.loads(s[i:j + 1])


def creativity_llm_fn(client: LLMClient) -> Callable[[dict], dict]:
    """Build the real llm_fn for the Creativity agent from an LLMClient.

    Uses the agent's role prompt (agents/creativity-blackbox.md) as the system
    prompt and asks for the mandatory JSON schema. The humility contract
    (kill_criteria etc.) is still enforced downstream in Creativity.propose().
    """
    role = (_ROOT / "agents" / "creativity-blackbox.md").read_text(encoding="utf-8")
    system = role + (
        "\n\nOUTPUT: return ONLY a JSON object with exactly these keys: "
        "idea, why_it_might_be_genius, why_it_might_be_insane, "
        "confidence (number 0..1), kill_criteria, smallest_test, reversible (true/false)."
    )

    def fn(context: dict) -> dict:
        user = ("Read-only context from the project:\n"
                + json.dumps(context, ensure_ascii=False)
                + "\n\nPropose ONE bold, madness-or-genius idea as JSON.")
        out = client.complete("creativity", system, user, max_tokens=700)
        return _extract_json(out["text"])

    return fn


def doctor_narrator(client: LLMClient) -> Callable[[str], str]:
    """Optional: an LLM narrative/red-team layer for the Doctor (premium tier).
    The deterministic guardrails in doctor.py stand on their own; this only adds
    prose. Returns a function report_md -> narrative_md."""
    role = (_ROOT / "agents" / "evolutionary-doctor.md").read_text(encoding="utf-8")

    def fn(report_md: str) -> str:
        out = client.complete("doctor", role,
                              "Given this health report, add a 3-bullet red-team "
                              "and a one-line verdict:\n\n" + report_md, max_tokens=500)
        return out["text"]

    return fn
