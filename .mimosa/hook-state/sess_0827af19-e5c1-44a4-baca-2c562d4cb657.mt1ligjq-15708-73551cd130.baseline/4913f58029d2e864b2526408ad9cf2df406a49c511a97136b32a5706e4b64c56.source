"""Hunter agent loop — autonomous channel discovery with Claude tool-use."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlmodel import select

from config import settings
from db import Channel, RunLog, get_session, utcnow
from hunter.tools import TOOL_SCHEMA, dispatch_tool

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "hunter.md"
MEMORY_PATH = settings.hunter_memory_path

# Memory file limits — unbounded growth made _load_memory useless because it
# read the FIRST 4000 chars (oldest entries) while new notes append at the end.
MEMORY_MAX_BYTES = 100_000
MEMORY_KEEP_BYTES = 50_000

_client = None


def _get_client():
    """Lazy Anthropic client — importing this module must not need the SDK."""
    global _client
    if _client is None:
        from anthropic import Anthropic

        _client = Anthropic(api_key=settings.anthropic_api_key)
    return _client


def _load_system_prompt() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    # Fallback — short version embedded
    return (
        "You are HUNTER, an autonomous research agent for a Sydney building "
        "painting contractor. Discover NEW lead channels (not in the operator's "
        "known list). For each candidate, verify it exists, find a sample lead, "
        "then call save_channel. Be precise; quality over quantity. Max 5 channels "
        "per run."
    )


def _load_memory() -> str:
    """Return the NEWEST slice of memory (entries append at the end)."""
    if MEMORY_PATH.exists():
        text = MEMORY_PATH.read_text(encoding="utf-8")
        return text[-4000:] if text.strip() else "(no prior runs)"
    return "(no prior runs)"


def _trim_memory(
    text: str, max_bytes: int = MEMORY_MAX_BYTES, keep_bytes: int = MEMORY_KEEP_BYTES
) -> str:
    """Cap memory file size, keeping the newest entries (cut at an entry edge)."""
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    kept = encoded[-keep_bytes:].decode("utf-8", errors="ignore")
    cut = kept.find("\n## ")
    if cut != -1:
        kept = kept[cut:]
    return "(older runs trimmed)\n" + kept


def _append_memory(note: str) -> None:
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = MEMORY_PATH.read_text(encoding="utf-8") if MEMORY_PATH.exists() else ""
    existing += f"\n## {utcnow().isoformat()}\n{note}\n"
    MEMORY_PATH.write_text(_trim_memory(existing), encoding="utf-8")


def _known_channels() -> list[str]:
    with get_session() as s:
        rows = list(s.exec(select(Channel)).all())
        return [f"- {c.name} ({c.url})" for c in rows]


def run_hunter(focus_hint: str | None = None) -> int:
    """One Hunter run. Returns number of new channels saved.

    NOTE: this is a *blocking* sync function (Anthropic client + httpx sync).
    From async code always call it via `await asyncio.to_thread(run_hunter)` —
    calling it directly on the event loop froze the whole bot for minutes.
    """
    log = RunLog(kind="hunter")
    with get_session() as s:
        s.add(log)
        s.commit()
        s.refresh(log)
        log_id = log.id

    system_prompt = _load_system_prompt()
    memory = _load_memory()
    known = "\n".join(_known_channels()) or "(none yet)"

    user_message = (
        "Begin hunt run.\n\n"
        f"## Known channels already in DB (do NOT re-discover):\n{known}\n\n"
        f"## Prior memory (hypotheses tested, dead ends):\n{memory}\n\n"
        f"## Focus this run: {focus_hint or 'choose a rotation (method #6 in your prompt)'}\n\n"
        "Use web_search and fetch_page liberally. When you confirm a channel, "
        "call save_channel. After 5 saves OR when you've exhausted promising "
        "leads, write a brief one-paragraph summary of what you tried and "
        "where to look next time, then end your turn."
    )

    messages: list[dict] = [{"role": "user", "content": user_message}]
    saved = 0
    summary = ""
    tokens_in = 0
    tokens_out = 0
    client = _get_client()

    for _step in range(20):  # hard cap on tool-use rounds
        resp = client.messages.create(
            model=settings.llm_model,
            max_tokens=4000,
            system=system_prompt,
            tools=TOOL_SCHEMA,  # type: ignore[arg-type]
            messages=messages,
        )

        usage = getattr(resp, "usage", None)
        if usage is not None:
            tokens_in += getattr(usage, "input_tokens", 0) or 0
            tokens_out += getattr(usage, "output_tokens", 0) or 0

        # Append assistant turn
        messages.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason == "end_turn":
            for block in resp.content:
                if getattr(block, "type", None) == "text":
                    summary += block.text  # type: ignore[attr-defined]
            break

        if resp.stop_reason != "tool_use":
            logger.warning("Hunter stopped with reason: %s", resp.stop_reason)
            break

        tool_results = []
        for block in resp.content:
            if getattr(block, "type", None) == "tool_use":
                tool_name = block.name  # type: ignore[attr-defined]
                tool_args = block.input  # type: ignore[attr-defined]
                tool_id = block.id  # type: ignore[attr-defined]
                logger.info("Hunter tool: %s args=%s", tool_name, str(tool_args)[:200])
                try:
                    result = dispatch_tool(tool_name, tool_args)  # type: ignore[arg-type]
                    if tool_name == "save_channel":
                        try:
                            parsed = json.loads(result)
                            if parsed.get("saved"):
                                saved += 1
                        except Exception:
                            pass
                except Exception as e:
                    result = json.dumps({"error": str(e)})
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": tool_id, "content": result}
                )

        if not tool_results:
            break

        messages.append({"role": "user", "content": tool_results})

    if summary:
        _append_memory(summary[:2000])

    with get_session() as s:
        row = s.get(RunLog, log_id)
        if row:
            row.finished_at = utcnow()
            row.items_new = saved
            row.tokens_in = tokens_in
            row.tokens_out = tokens_out
            s.add(row)
            s.commit()

    logger.info(
        "Hunter run complete: %d new channels saved (tokens in=%d out=%d)",
        saved, tokens_in, tokens_out,
    )
    return saved
