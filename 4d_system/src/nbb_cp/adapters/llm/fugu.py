"""FuguLLM — OpenAI-compatible chat-completions adapter (Sakana AI 'fugu').

Lives behind LLMPort so the kernel never sees an HTTP client (CLAUDE.md rule 2).
Stdlib only (urllib) — the project stays dependency-free. Fails closed on ANY API
error: an unreachable or malformed brain is an incident, never a silent mock
fallback (CLAUDE.md rule 4 / INV-12). Untrusted model text is returned verbatim
for the caller to quarantine (INV-9); this adapter never executes it.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from ...kernel.errors import FailClosedError
from ...kernel.ports import LLMRequest, LLMResponse

DEFAULT_HOST = "https://api.sakana.ai/v1"
DEFAULT_PATH = "/chat/completions"
DEFAULT_MODEL = "fugu"          # standard tier, not ultra (spec §11: use_ultra=false)


class FuguError(FailClosedError):
    """The Fugu API was unreachable, returned an error status, or an unusable body."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse to follow redirects. stdlib urllib re-sends the `Authorization: Bearer
    <key>` header to a redirect target WITHOUT a same-host check, so a 3xx from a
    compromised/MITM'd/misconfigured endpoint would exfiltrate the key (in cleartext
    if the target is http://). A legitimate chat/completions endpoint returns 200, so
    a redirect is treated as an error — the key is never re-sent."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        raise FuguError(f"Fugu returned a redirect ({code}) to {newurl!r}; refusing (won't re-send the key)")


# Module-level opener with redirects disabled; used for every call (see complete()).
_OPENER = urllib.request.build_opener(_NoRedirect)


@dataclass(frozen=True)
class FuguLLM:
    """OpenAI-compatible completion port. Inject key/host/model from the app layer;
    the adapter never reads config (dependency direction: app -> adapters)."""

    api_key: str
    host: str = DEFAULT_HOST
    path: str = DEFAULT_PATH
    model: str = DEFAULT_MODEL
    temperature: float = 0.2
    max_tokens: int = 4096
    timeout_s: float = 60.0

    def __post_init__(self) -> None:
        if not self.api_key:
            raise FuguError("Fugu API key missing (set FUGU_API_KEY); refusing to call the live brain")

    def _url(self) -> str:
        return self.host.rstrip("/") + "/" + self.path.lstrip("/")

    def complete(self, request: LLMRequest) -> LLMResponse:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        req = urllib.request.Request(
            self._url(),
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with _OPENER.open(req, timeout=self.timeout_s) as resp:
                raw = resp.read().decode("utf-8", "replace")  # never crash on odd bytes
        except urllib.error.HTTPError as exc:
            body = ""
            try:
                body = exc.read().decode("utf-8", "replace")[:300]
            except Exception:  # noqa: BLE001 - best-effort detail only
                pass
            raise FuguError(f"Fugu HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise FuguError(f"Fugu unreachable: {exc.reason}") from exc
        return self._parse(raw)

    @staticmethod
    def _parse(raw: str) -> LLMResponse:
        # Everything that touches the body — including the usage/token extraction —
        # is inside one guard, so a malformed 200 (non-dict usage, non-numeric tokens,
        # missing content) fails closed as FuguError rather than crashing with a raw
        # AttributeError/ValueError that would bypass the service's incident handler.
        try:
            data = json.loads(raw)
            text = data["choices"][0]["message"]["content"]
            if not isinstance(text, str):
                raise TypeError("response content was not text")
            usage = data.get("usage") or {}
            input_tokens = int(usage.get("prompt_tokens", 0) or 0)
            output_tokens = int(usage.get("completion_tokens", 0) or 0)
        except (json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError, AttributeError) as exc:
            raise FuguError(f"Fugu returned an unusable body: {exc}") from exc
        return LLMResponse(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            orchestration_tokens=0,
        )
