"""OpenAI-compatible client for the hosted orchestrator. stdlib only.

Written against `urllib` rather than `requests` so the node keeps its
zero-dependency property. The API surface is OpenAI-compatible, which is the
one real piece of good news about this provider: swapping it out is a base-URL
change, not a rewrite.

Three provider-specific realities are encoded here rather than discovered in
production:

  * **Timeouts are long, and how long depends on which model.** The standard
    model answers in seconds; the deep-reasoning one can run for minutes on a
    hard problem. Published third-party numbers average the two into one wide
    range, which makes the fast model look unusable when it is not. A
    30-second default would turn normal behaviour into a flood of spurious
    failures, so the default is 180 seconds and `timeout_s` is per-instance —
    the deep rung is wired with a much larger one in `run.py`.

  * **Orchestration tokens may be absent.** The provider bills for internal
    fan-out it does not always report. When the field is missing we return 0
    and let the quota layer apply its multiplier — the one thing we must not
    do is report a confident zero.

  * **Failure is fail-closed.** A network error, a bad status, or an
    unparseable body all produce `insufficient=True` with no text, which the
    router treats as "this rung could not answer". It never silently returns
    an empty success, because an empty success looks like a valid answer to
    everything downstream.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Mapping

from .router import BrainReply

DEFAULT_BASE_URL = "https://api.sakana.ai/v1"
DEFAULT_TIMEOUT_S = 180


@dataclass
class RemoteBrain:
    """One rung backed by a hosted OpenAI-compatible endpoint."""

    api_key: str
    model: str
    base_url: str = DEFAULT_BASE_URL
    timeout_s: int = DEFAULT_TIMEOUT_S
    max_output_tokens: int = 2048
    reasoning_effort: str | None = None
    system_prompt: str = ""

    def answer(self, task: str, prompt: str) -> BrainReply:
        if not self.api_key:
            # Missing credential is not an outage — it is a configuration
            # state, and it must not be mistaken for a model that declined.
            return BrainReply("", insufficient=True, model=f"{self.model}:not-armed")

        messages: list[dict[str, str]] = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": prompt})

        body: dict[str, object] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_output_tokens,
        }
        if self.reasoning_effort:
            body["reasoning_effort"] = self.reasoning_effort

        req = urllib.request.Request(
            url=f"{self.base_url.rstrip('/')}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return BrainReply("", insufficient=True,
                              model=f"{self.model}:http-{exc.code}")
        except (urllib.error.URLError, TimeoutError, OSError):
            return BrainReply("", insufficient=True, model=f"{self.model}:unreachable")
        except json.JSONDecodeError:
            return BrainReply("", insufficient=True, model=f"{self.model}:bad-body")

        return self._parse(payload)

    def _parse(self, payload: Mapping[str, object]) -> BrainReply:
        try:
            choices = payload["choices"]            # type: ignore[index]
            text = choices[0]["message"]["content"] or ""   # type: ignore[index]
        except (KeyError, IndexError, TypeError):
            return BrainReply("", insufficient=True, model=f"{self.model}:no-choice")

        usage = payload.get("usage") or {}
        if not isinstance(usage, Mapping):
            usage = {}
        visible = int(usage.get("prompt_tokens", 0) or 0) + \
            int(usage.get("completion_tokens", 0) or 0)
        if visible == 0:
            visible = int(usage.get("total_tokens", 0) or 0)

        # Provider-specific field names for the third bucket, if present at
        # all. Absent means unknown, and unknown is handled by the quota
        # layer's multiplier — never treated as zero here.
        orchestration = 0
        for key in ("orchestration_tokens", "internal_tokens", "routed_tokens"):
            val = usage.get(key)
            if isinstance(val, int) and val > 0:
                orchestration = val
                break

        return BrainReply(
            text=str(text), insufficient=not str(text).strip(),
            visible_tokens=visible, orchestration_tokens=orchestration,
            model=self.model,
        )


@dataclass
class LocalBrain:
    """The small model on this board, behind a command-line runner.

    Kept as a thin shell over a subprocess callable so the concrete runner
    (llama.cpp, llamafile, an HTTP server on loopback) can change without
    touching routing. Tokens are always reported as zero: this rung runs on
    hardware already paid for, and counting its output against a spend budget
    would discourage exactly the behaviour the budget exists to encourage.
    """

    run: object  # Callable[[str, str], str] — injected
    name: str = "local"

    def answer(self, task: str, prompt: str) -> BrainReply:
        try:
            out = self.run(task, prompt)          # type: ignore[operator]
        except Exception:
            return BrainReply("", insufficient=True, model=f"{self.name}:error")
        text = (out or "").strip()
        return BrainReply(text, insufficient=not text, model=self.name)
