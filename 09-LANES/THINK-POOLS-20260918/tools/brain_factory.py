#!/usr/bin/env python3
"""Brain factory v2 — the whole provider path, all dialects.

Owner order 2026-09-18: "fix the providers, the whole path". Three defects
stood between six live providers and a callable brain; each is fixed here:

  1. ENV SPLIT — keys live in BOTH secrets.env and external-models.env. A
     caller that loads only one silently loses providers (deepseek/openai keys
     are in the external file). This module loads both itself, so no consumer
     has to know the split. Values are read into os.environ and never printed.
  2. DIALECTS — three providers are not OpenAI-dialect and RemoteBrain cannot
     call them: anthropic (/v1/messages, x-api-key), gemini
     (:generateContent, x-goog-api-key), local llama.cpp (/completion).
     Adapter classes below give each the same answer(task, prompt) surface.
  3. ENDPOINT SOURCE — endpoints come from providers.chat_url() (verified),
     never from base() (which is only an optional override).

Fail-closed throughout: a missing endpoint, key or model raises
BrainBuildError instead of guessing. The OpenAI-dialect path still returns the
original RemoteBrain untouched.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import time
import urllib.request

TOOLS = pathlib.Path("/home/ari/ofn/tools")
STATE_BUDGET = pathlib.Path("/home/ari/ofn/state/api-budget")
for p in (str(TOOLS), str(STATE_BUDGET)):
    if p not in sys.path:
        sys.path.insert(0, p)

import provider_routing as pr  # noqa: E402

sys.path.insert(0, "/home/ari/ofn")
from ofn.adapters.remote_brain import RemoteBrain  # noqa: E402

ENV_FILES = ("/home/ari/.config/ofn/secrets.env",
             "/home/ari/.config/ofn/external-models.env")


class BrainBuildError(RuntimeError):
    """Raised instead of guessing an endpoint, key or model."""


def _load_env_files() -> None:
    """Merge the two credential files into os.environ (names never printed)."""
    for path in ENV_FILES:
        p = pathlib.Path(path)
        if not p.exists():
            continue
        try:
            for line in p.read_text(errors="replace").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
        except OSError:
            continue


_load_env_files()


# ---------------------------------------------------------------------------
# Dialect adapters — same surface as RemoteBrain.answer(task, prompt)
# ---------------------------------------------------------------------------

class _HttpBrain:
    """Shared plumbing: one POST, bounded wait, BrainReply-shaped result."""

    dialect = "abstract"

    def __init__(self, name: str, model: str, url: str, timeout_s: int = 120):
        self.name = name
        self.model = model
        self.url = url
        self.timeout_s = timeout_s

    def _headers(self) -> dict:  # pragma: no cover - overridden
        return {}

    def _body(self, prompt: str, max_tokens: int) -> dict:  # pragma: no cover
        return {}

    def _extract(self, payload: dict) -> str:  # pragma: no cover
        return ""

    def answer(self, task: str, prompt: str):
        from ofn.adapters.router import BrainReply
        body = self._body(prompt, 128)
        req = urllib.request.Request(
            url=self.url, data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", **self._headers()},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as r:
                payload = json.loads(r.read().decode("utf-8", errors="replace"))
        except Exception as exc:  # noqa: BLE001 - network errors are outcomes
            return BrainReply("", insufficient=True,
                              model=f"{self.name}:{type(exc).__name__}")
        text = self._extract(payload)
        return BrainReply(text, insufficient=not text, model=self.model)


class AnthropicBrain(_HttpBrain):
    dialect = "anthropic"

    def __init__(self, api_key, model, url, **kw):
        super().__init__("anthropic", model, url, **kw)
        self.api_key = api_key
        # The key is workspace-unscoped, so the workspace id header is required
        # (HTTP 400 without it, diagnosed 2026-09-18). It is an identifier the
        # owner supplied 2026-09-13, not a credential; only the env NAME is read.
        self.workspace_id = os.environ.get("ANTHROPIC_WORKSPACE_ID", "")

    def _headers(self):
        h = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"}
        if self.workspace_id:
            h["anthropic-workspace-id"] = self.workspace_id
        return h

    def _body(self, prompt, max_tokens):
        return {"model": self.model, "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]}

    def _extract(self, payload):
        return "".join(b.get("text", "") for b in payload.get("content", [])
                       if isinstance(b, dict))


class GeminiBrain(_HttpBrain):
    dialect = "google"

    def __init__(self, api_key, model, url, **kw):
        super().__init__("gemini", model, url, **kw)
        self.api_key = api_key

    def _headers(self):
        return {"x-goog-api-key": self.api_key}

    def _body(self, prompt, max_tokens):
        # Gemini reasoning models consume maxOutputTokens on internal thinking,
        # so a small cap leaves a 5-character answer (measured 2026-09-18).
        return {"contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": max(max_tokens, 1024)}}

    def _extract(self, payload):
        cands = payload.get("candidates") or [{}]
        parts = (cands[0].get("content") or {}).get("parts") or []
        return "".join(p.get("text", "") for p in parts if isinstance(p, dict))


class OpenAICompatBrain(_HttpBrain):
    """OpenAI dialect with the newer parameter names.

    RemoteBrain sends `max_tokens`, which newer OpenAI models reject with
    HTTP 400 (diagnosed 2026-09-18: gpt-5.6-terra -> http-400, empty reply).
    This adapter is used only for the openai provider; every other
    OpenAI-dialect provider keeps the original RemoteBrain untouched.
    """

    dialect = "openai-v2"

    def __init__(self, api_key, model, url, **kw):
        super().__init__("openai", model, url, **kw)
        self.api_key = api_key

    def _headers(self):
        return {"Authorization": f"Bearer {self.api_key}"}

    def _body(self, prompt, max_tokens):
        return {"model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_completion_tokens": max_tokens}

    def _extract(self, payload):
        choices = payload.get("choices") or [{}]
        return ((choices[0].get("message") or {}).get("content") or "")


class LocalLlamaBrain(_HttpBrain):
    dialect = "llamacpp"

    def __init__(self, model, url, **kw):
        super().__init__("local-llamacpp-180", model, url, **kw)

    def _body(self, prompt, max_tokens):
        # llama.cpp native /completion: raw prompt, bounded prediction.
        return {"prompt": prompt, "n_predict": max_tokens, "temperature": 0.2,
                "stop": ["\n\nUser:", "\n\n###"]}

    def _extract(self, payload):
        return payload.get("content", "")


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

OPENAI_SUFFIX = "/chat/completions"
# Below this, a reply is a truncated non-answer rather than an answer.
MIN_USABLE_CHARS = 15


def _registry():
    import providers  # noqa: PLC0415
    return providers


def build(tier: str = "default", pin: str | None = None, states: dict | None = None) -> dict:
    """Build a brain for the current best provider for this tier."""
    decision = pr.decide(pin if pin is not None else pr.env_pin(),
                         states=states, tier=tier)
    provider = decision.get("chosen")
    if not provider:
        raise BrainBuildError(f"no routable provider: {decision.get('reason')} "
                              f"(excluded={decision.get('excluded')})")

    reg = _registry()
    table = getattr(reg, "REGISTRY", {}) or {}
    entry = table.get(provider)
    if not entry:
        raise BrainBuildError(f"provider {provider!r} is not in the provider registry")

    model = ""
    if hasattr(reg, "model"):
        try:
            model = reg.model(provider, tier) or ""
        except Exception:  # noqa: BLE001
            model = ""
    if not model:
        raise BrainBuildError(f"provider {provider!r} has no model mapped for tier {tier!r}")

    try:
        chat = reg.chat_url(provider, model)
    except Exception as exc:  # noqa: BLE001
        raise BrainBuildError(f"provider {provider!r} chat_url failed: {type(exc).__name__}") from exc
    if not chat:
        raise BrainBuildError(f"provider {provider!r} has no resolvable chat endpoint")

    key_var = entry.get("key_var")
    api_key = os.environ.get(key_var, "") if key_var else ""

    dialect = "openai"
    if chat.endswith(OPENAI_SUFFIX):
        if key_var and not api_key:
            raise BrainBuildError(f"provider {provider!r} needs {key_var}, which is not set")
        if provider == "openai":
            brain = OpenAICompatBrain(api_key, model, chat)
        else:
            brain = RemoteBrain(api_key=api_key, model=model, base_url=chat[: -len(OPENAI_SUFFIX)])
    elif entry.get("auth") == "anthropic":
        if not api_key:
            raise BrainBuildError(f"provider {provider!r} needs {key_var}, which is not set")
        brain = AnthropicBrain(api_key, model, chat)
    elif entry.get("auth") == "google":
        if not api_key:
            raise BrainBuildError(f"provider {provider!r} needs {key_var}, which is not set")
        brain = GeminiBrain(api_key, model, chat)
    elif provider.startswith("local-"):
        brain = LocalLlamaBrain(model, chat)
    else:
        raise BrainBuildError(
            f"provider {provider!r} speaks an unsupported dialect at {chat}")

    host = chat.split("//")[-1].split("/")[0]
    pr.record({**decision, "tier": tier, "built_model": model, "base_host": host})
    return {"brain": brain, "decision": decision, "model": model,
            "base_host": host, "dialect": getattr(brain, "dialect", "openai")}


def smoke(provider: str | None = None, tier: str = "standard") -> dict:
    """One tiny real call — the whole-path proof. Local first by default.

    Max 32 output tokens; a handful of these costs cents and stays far inside
    the campaign cap the audit prompt set (<= $2 total).
    """
    t0 = time.time()
    out = build(tier=tier, pin=provider)
    brain, model = out["brain"], out["model"]
    prompt = ("Reply with exactly one word: the capital of France.")
    reply = brain.answer("smoke", prompt)
    text = (getattr(reply, "text", "") or "").strip()[:80]
    return {"provider": out["decision"]["chosen"], "model": model,
            "dialect": out["dialect"], "ok": bool(text),
            "reply_head": text, "latency_s": round(time.time() - t0, 2),
            "insufficient": bool(getattr(reply, "insufficient", False))}


def answer_with_failover(task: str, prompt: str, tier: str = "strong",
                         max_tries: int = 3) -> dict:
    """Ask across live providers until one actually answers.

    Added after a measured failure: at tier=strong the router picked
    gemini/gemini-3.1-pro-preview and the call returned EMPTY in 0.8 s, so a
    customer-facing draft got nothing while deepseek and openai -- both 10/10 in
    the benchmark -- sat unused. An empty reply is a provider failure, not an
    answer, so it now falls through to the next live provider for that tier.

    Returns the first non-empty answer plus the list of what was tried, so a
    caller can see the fallback from evidence rather than trusting it.
    """
    decision = pr.decide(pin=pr.env_pin(), tier=tier)
    tried = []
    for name in decision.get("order", [])[:max_tries]:
        try:
            built = build(tier=tier, pin=name)
        except BrainBuildError as exc:
            tried.append({"provider": name, "blocked": str(exc)[:70]})
            continue
        reply = built["brain"].answer(task, prompt)
        text = (getattr(reply, "text", "") or "").strip()
        tried.append({"provider": name, "model": built["model"], "chars": len(text)})
        # A truncated reply is worse than an empty one: gemini returned
        # "Could" (5 chars) at strong tier, which passed an emptiness check
        # and would have reached a customer. Require a usable length.
        if len(text) >= MIN_USABLE_CHARS:
            return {"provider": name, "model": built["model"], "text": text,
                    "dialect": built["dialect"], "tried": tried,
                    "failures_before_success": len(tried) - 1}
    return {"provider": None, "model": None, "text": "", "tried": tried,
            "failures_before_success": len(tried)}


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--smoke" in args:
        only = args[args.index("--smoke") + 1] if len(args) > args.index("--smoke") + 1 else None
        for pid in ([only] if only else
                    ["local-llamacpp-180", "deepseek", "openai", "anthropic",
                     "gemini", "sakana-fugu"]):
            try:
                r = smoke(pid)
                print(json.dumps(r, ensure_ascii=False))
            except BrainBuildError as exc:
                print(json.dumps({"provider": pid, "ok": False, "blocked": str(exc)[:90]}))
    elif "--tier" in args:
        tier = args[args.index("--tier") + 1]
        out = build(tier=tier)
        print(f"provider={out['decision']['chosen']} model={out['model']} "
              f"host={out['base_host']} dialect={out['dialect']} "
              f"reason={out['decision']['reason']}")
    else:
        print(json.dumps(build()["decision"], indent=1, ensure_ascii=False))
