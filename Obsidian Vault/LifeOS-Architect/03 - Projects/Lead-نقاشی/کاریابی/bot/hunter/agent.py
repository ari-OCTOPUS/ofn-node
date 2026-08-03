"""Hunter agent loop — autonomous channel discovery with Claude tool-use."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from anthropic import Anthropic
from sqlmodel import select

from config import settings
from db import Channel, RunLog, get_session
from hunter.tools import TOOL_SCHEMA, dispatch_tool

logger = logging.getLogger(__name__)

_client = Anthropic(api_key=settings.anthropic_api_key)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "hunter.md"
MEMORY_PATH = settings.hunter_memory_path


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
    if MEMORY_PATH.exists():
        return MEMORY_PATH.read_text(encoding="utf-8")[:4000]
    return "(no prior runs)"


def _append_memory(note: str) -> None:
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MEMORY_PATH.open("a", encoding="utf-8") as f:
        f.write(f"\n## {datetime.utcnow().isoformat()}\n{note}\n")


def _known_channels() -> list[str]:
    with get_session() as s:
        rows = list(s.exec(select(Channel)).all())
        return [f"- {c.name} ({c.url})" for c in rows]


async def run_hunter(focus_hint: str | None = None) -> int:
    """One Hunter run. Returns number of new channels saved."""
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

    for step in range(20):  # hard cap on tool-use rounds
        resp = _client.messages.create(
            model=settings.llm_model,
            max_tokens=4000,
            system=system_prompt,
            tools=TOOL_SCHEMA,  # type: ignore[arg-type]
            messages=messages,
        )

        # Append assistant turn
        messages.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason == "end_turn":
            # Capture final text as summary
            for block in resp.content:
                if getattr(block, "type", None) == "text":
                    summary += block.text  # type: ignore[attr-defined]
            break

        if resp.stop_reason != "tool_use":
            logger.warning("Hunter stopped with reason: %s", resp.stop_reason)
            break

        # Run each tool use, gather results
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
            row.finished_at = datetime.utcnow()
            row.items_new = saved
            s.add(row)
            s.commit()

    logger.info("Hunter run complete: %d new channels saved", saved)
    return saved
