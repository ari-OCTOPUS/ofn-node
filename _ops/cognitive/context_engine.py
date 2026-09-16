"""context_engine.py — Cognitive Runtime: Context Engine v1 (tiktoken budget).

تصمیم می‌گیرد مدل چه چیزی را ببیند — نه فقط شمارنده.
بخش‌های بودجه‌دار: system → task → working_memory → retrieved_memory → tool_results → recent_chat.

هر بخش truncate می‌شود تا از بودجه نرود.
fail-soft: نبود tiktoken → fallback به طول کاراکتر.
"""
from __future__ import annotations

import time
from typing import Any

# بودجهٔ پیش‌فرض (token)
DEFAULT_BUDGET = {
    "system": 1500,
    "task": 2000,
    "working_memory": 3000,
    "retrieved_memory": 4000,
    "tool_results": 3000,
    "recent_chat": 3000,
}

# سعی در import tiktoken (fail-soft)
_TIKTOKEN = None
try:
    import tiktoken
    _TIKTOKEN = tiktoken.encoding_for_model("gpt-4")
except Exception:  # noqa: BLE001
    pass


def count_tokens(text: str) -> int:
    """شمارش دقیق token با tiktoken؛ fallback به ~۳ کاراکتر/token."""
    if not text:
        return 0
    if _TIKTOKEN is not None:
        try:
            return len(_TIKTOKEN.encode(str(text)))
        except Exception:  # noqa: BLE001
            pass
    return max(1, len(str(text)) // 3)


def _truncate_to_budget(text: str, max_tokens: int) -> str:
    """متن را به بودجهٔ token برش بزن."""
    if not text or max_tokens <= 0:
        return ""
    tokens = count_tokens(text)
    if tokens <= max_tokens:
        return text
    # تقریب: n_char ≈ max_tokens * 3
    ratio = max_tokens / tokens
    cut = int(len(text) * ratio * 0.95)  # کمی محافظه‌کارانه
    return text[:cut].rstrip() + "\n[…truncated]"


def assemble(query: str, *,
             intent: str = "chat",
             session_turns: list[dict] | None = None,
             recall_facts: list[dict] | None = None,
             self_context: str = "",
             tool_results: list[dict] | None = None,
             budget: dict[str, int] | None = None) -> dict[str, Any]:
    """Context را با بودجهٔ جدا برای هر بخش assemble کن.

    ترتیب تزریق (اهمیت نزولی):
        1. system rules
        2. current question
        3. self_context (runtime evidence)
        4. recall_facts (retrieved memory)
        5. tool_results
        6. recent_chat (session turns)

    خروجی:
        {context_text, token_count, budget_used, sections, truncated}
    """
    b = dict(DEFAULT_BUDGET)
    if budget:
        b.update(budget)

    sections: dict[str, dict] = {}
    parts: list[str] = []
    total_tokens = 0
    truncated = []

    # 1. system
    sys_text = (
        "تو اختاپوس هستی — مغزِ کنترل و همکارِ مالک (آرمین). "
        "فارسی، مستقیم، صادق، مکالمه‌ای. "
        "هدف: با هم اختاپوس را کشف و شفاف کنیم. "
        "اثر بیرونی/ارسال/پرداخت انجام نده. "
        "اگر مطمئن نیستی بگو. هویتت را پنهان نکن: ارگانیسم چندلایه با گیت و شواهد."
    )
    sys_trunc = _truncate_to_budget(sys_text, b["system"])
    sections["system"] = {"tokens": count_tokens(sys_trunc), "budget": b["system"]}
    parts.append(sys_trunc)
    total_tokens += sections["system"]["tokens"]
    if len(sys_trunc) < len(sys_text):
        truncated.append("system")

    # 2. current question (task)
    q_trunc = _truncate_to_budget(str(query or ""), b["task"])
    sections["task"] = {"tokens": count_tokens(q_trunc), "budget": b["task"]}
    parts.append(f"پیام مالک:\n{q_trunc}")
    total_tokens += sections["task"]["tokens"]

    # 3. self_context (runtime evidence — working memory)
    sc_trunc = _truncate_to_budget(str(self_context or ""), b["working_memory"])
    if sc_trunc:
        sections["working_memory"] = {"tokens": count_tokens(sc_trunc), "budget": b["working_memory"]}
        parts.append(f"— شواهد زنده —\n{sc_trunc}")
        total_tokens += sections["working_memory"]["tokens"]
        if len(sc_trunc) < len(str(self_context or "")):
            truncated.append("working_memory")

    # 4. recall_facts (retrieved memory)
    facts_text = ""
    if recall_facts:
        fact_lines = []
        for f in recall_facts[:8]:
            preview = str(f.get("content_preview") or f.get("claim") or f.get("title") or "")[:150]
            source = str(f.get("source_path") or f.get("source") or "")[:80]
            fact_lines.append(f"· {preview} [{source}]")
        facts_text = "\n".join(fact_lines)
    facts_trunc = _truncate_to_budget(facts_text, b["retrieved_memory"])
    if facts_trunc:
        sections["retrieved_memory"] = {"tokens": count_tokens(facts_trunc), "budget": b["retrieved_memory"]}
        parts.append(f"— حافظهٔ بازیابی‌شده —\n{facts_trunc}")
        total_tokens += sections["retrieved_memory"]["tokens"]
        if len(facts_trunc) < len(facts_text):
            truncated.append("retrieved_memory")

    # 5. tool_results
    tools_text = ""
    if tool_results:
        tool_lines = []
        for t in tool_results[:5]:
            name = str(t.get("name") or t.get("tool") or "?")[:40]
            result = str(t.get("result") or t.get("summary") or "")[:200]
            tool_lines.append(f"[{name}] {result}")
        tools_text = "\n".join(tool_lines)
    tools_trunc = _truncate_to_budget(tools_text, b["tool_results"])
    if tools_trunc:
        sections["tool_results"] = {"tokens": count_tokens(tools_trunc), "budget": b["tool_results"]}
        parts.append(f"— نتایج ابزار —\n{tools_trunc}")
        total_tokens += sections["tool_results"]["tokens"]

    # 6. recent_chat (session turns)
    chat_text = ""
    if session_turns:
        chat_lines = []
        for turn in session_turns[-6:]:
            who = "مالک" if turn.get("role") == "owner" else "اختاپوس"
            preview = str(turn.get("text_preview") or turn.get("text") or "")[:120]
            chat_lines.append(f"{who}: {preview}")
        chat_text = "\n".join(chat_lines)
    chat_trunc = _truncate_to_budget(chat_text, b["recent_chat"])
    if chat_trunc:
        sections["recent_chat"] = {"tokens": count_tokens(chat_trunc), "budget": b["recent_chat"]}
        parts.append(f"— مکالمهٔ اخیر —\n{chat_trunc}")
        total_tokens += sections["recent_chat"]["tokens"]

    context_text = "\n\n".join(p for p in parts if p and p.strip())
    return {
        "context_text": context_text,
        "token_count": total_tokens,
        "total_budget": sum(b.values()),
        "budget_used": {k: v["tokens"] for k, v in sections.items()},
        "sections": sections,
        "truncated": truncated,
        "tiktoken_available": _TIKTOKEN is not None,
    }
