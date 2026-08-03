"""Cassette record/replay for LLM traffic — the L2 test backbone.

Format: JSONL, one entry per exchange:
    {"key": <sha256 of task+prompt>, "task": ..., "prompt": ...,
     "response": {"text": ..., "input_tokens": ..., "output_tokens": ...,
                  "orchestration_tokens": ...}}

RecordingLLM wraps a live port (Phase 1) and writes entries as traffic flows.
ReplayLLM answers from the cassette only, and fails closed on a miss: an
unrecorded request in a replay run is a drifted test, not a reason to guess.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ...kernel.errors import FailClosedError
from ...kernel.ports import LLMPort, LLMRequest, LLMResponse


def request_key(request: LLMRequest) -> str:
    return hashlib.sha256(f"{request.task}\x00{request.prompt}".encode("utf-8")).hexdigest()


class CassetteMissError(FailClosedError):
    """Replay requested an exchange the cassette never recorded."""


class RecordingLLM:
    def __init__(self, inner: LLMPort, cassette_path: str | Path) -> None:
        self._inner = inner
        self._path = Path(cassette_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def complete(self, request: LLMRequest) -> LLMResponse:
        response = self._inner.complete(request)
        entry = {
            "key": request_key(request),
            "task": request.task,
            "prompt": request.prompt,
            "response": {
                "text": response.text,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "orchestration_tokens": response.orchestration_tokens,
            },
        }
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return response


class ReplayLLM:
    def __init__(self, cassette_path: str | Path) -> None:
        self._path = Path(cassette_path)
        self._entries: dict[str, dict] = {}
        if not self._path.exists():
            raise CassetteMissError(f"cassette not found: {self._path}")
        with self._path.open(encoding="utf-8") as fh:
            for line_number, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise CassetteMissError(f"corrupt cassette line {line_number}: {exc}") from exc
                self._entries[entry["key"]] = entry

    def complete(self, request: LLMRequest) -> LLMResponse:
        entry = self._entries.get(request_key(request))
        if entry is None:
            raise CassetteMissError(
                f"no cassette entry for task={request.task!r}; re-record or fix the drifted prompt"
            )
        r = entry["response"]
        return LLMResponse(
            text=r["text"],
            input_tokens=int(r.get("input_tokens", 0)),
            output_tokens=int(r.get("output_tokens", 0)),
            orchestration_tokens=int(r.get("orchestration_tokens", 0)),
        )
