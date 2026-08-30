#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""context_assembler.py — slot-based prompt assembler برای Seed Agent v1.

قرارداد (Seed Agent v1 — قدمِ ۵، ۲۰۲۶-۰۸-۰۸):
  · ۷ slot با اولویت — RULES/USER هرگز trim نمی‌شوند.
  · هر slot از منبعِ موجودش می‌خواند (octopus_reader → live_snapshot/retrieval/semantic).
  · assembly_trace: هر run لاگ می‌کند چه retrieve شد، چه trim شد.
  · پشت فلگ OCTOPUS_WIRE_SEED_ASSEMBLER (default OFF = no-op کامل).
  · fail-soft: شکست هر slot = slot خالی، نه crash نوبت.

الگوی trim: اول EPISODES، بعد TRACE، بعد FACTS (k کم).
هرگز RULES و USER.

منبع طراحی: Kimi K3 seed pack (2026-08-08) + behavioral model §۴.
"""
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from octopus_reader import (  # noqa: E402
    read_snapshot, read_semantic, read_trace, read_retrieval,
)
import octopus_reader as _reader  # noqa: E402 — برای monkeypatch در تست

FLAG = "OCTOPUS_WIRE_SEED_ASSEMBLER"


def _flag_on() -> bool:
    return str(os.environ.get(FLAG, "0")).strip().lower() in ("1", "true", "yes", "on")


# ─── مدل ────────────────────────────────────────────────────────────────────

@dataclass
class Slot:
    name: str
    priority: int          # کمتر = مهم‌تر، در trim آخر می‌ماند
    budget: int            # سقف کاراکتر تقریبی
    pinned: bool = False   # pinned = هرگز trim
    content: str = ""


@dataclass
class AssembleInput:
    user_msg: str
    mission: dict = field(default_factory=dict)  # {goal, acceptance, risk_level}
    query: str | None = None  # اگه None، از user_msg استفاده می‌شود


@dataclass
class AssemblyTrace:
    ts: float = field(default_factory=time.time)
    flag_on: bool = False
    slots: list[dict] = field(default_factory=list)
    trimmed: list[str] = field(default_factory=list)
    query: str = ""
    total_chars: int = 0
    error: str = ""


# ─── رندررهای معنایی (درس heart-dict: هرگز خام dump نکن) ──────────────────

def _render_state(snap: dict) -> str:
    """STATE slot: snapshot را به متنِ معنایی رندر کن، نه dict خام.
    درسِ bug قلب: 'قلب: {schema:...}' ممنوع؛ 'ریتم=325s' مجاز."""
    if not snap or snap.get("status") in ("error", "disabled"):
        reason = snap.get("reason", "unavailable") if snap else "unavailable"
        return f"state: {reason}"
    parts: list[str] = []
    org = snap.get("organism", {})
    if isinstance(org, dict):
        if org.get("beat") is not None:
            parts.append(f"beat={org['beat']}")
        if org.get("halted"):
            parts.append("HALTED")
        if org.get("frozen"):
            parts.append("FROZEN")
    budget = snap.get("budget", {})
    if isinstance(budget, dict) and budget.get("fugu_quota"):
        spent = budget.get("spent_today_usd", 0)
        if isinstance(spent, (int, float)):
            parts.append(f"fugu={spent:.2f}/{budget['fugu_quota']}")
    flags = snap.get("flags", {})
    if isinstance(flags, dict) and flags.get("n_armed") is not None:
        parts.append(f"flags={flags['n_armed']}/{flags.get('n_total', '?')}")
    health = snap.get("health", {})
    if isinstance(health, dict) and health.get("n_dark_gates") is not None:
        parts.append(f"dark_gates={health['n_dark_gates']}")
    return " | ".join(parts) if parts else "state: no signals"


def _render_facts(facts: list[dict]) -> str:
    """FACTS slot: هر fact با citation.
    درس: بدون source = «نامعلوم» (معیار #۳)."""
    if not facts:
        return "(no facts retrieved)"
    out: list[str] = []
    for i, f in enumerate(facts[:8], 1):
        src = f.get("source", "?")[:60]
        rel = f.get("relevance", 0)
        snippet = f.get("snippet", f.get("title", ""))[:120]
        out.append(f"[{i}] {snippet}\n    source={src} rel={rel:.2f}")
    return "\n".join(out)


def _render_episodes(records: list[dict]) -> str:
    """EPISODES slot: خلاصه‌ی آخرین semantic memory."""
    if not records:
        return "(no recent episodes)"
    out: list[str] = []
    for r in records[:5]:
        gist = str(r.get("gist", ""))[:100]
        sal = r.get("salience", 0)
        agent = r.get("source_agent", "?")[:20]
        out.append(f"• ({sal:.2f}) [{agent}] {gist}")
    return "\n".join(out)


def _render_trace(records: list[dict]) -> str:
    """TRACE slot: آخرین اعمالِ applied."""
    if not records:
        return "(no recent applied effects)"
    out: list[str] = []
    for r in records[:5]:
        beat = r.get("beat", "?")
        signals = r.get("signals", [])
        adj = r.get("confidence_adjustment", 0)
        adj_str = f"{adj:+.2f}" if isinstance(adj, (int, float)) else "?"
        out.append(f"• beat={beat} adj={adj_str} signals={signals}")
    return "\n".join(out)


def _rules_text() -> str:
    """RULES slot: قوانین سخت از seed pack."""
    return (
        "تو Seed Agent Octopus هستی. قوانین:\n"
        "۱) propose-only تا approval انسانی.\n"
        "۲) هر claim بدون source = «نامعلوم».\n"
        "۳) applied فقط با verify_effect.\n"
        "۴) روی دیتای corrupt/stale استدلال نکن.\n"
        "۵) هر fact باید as_of داشته باشد.\n"
        "۶) secrets هرگز در پاسخ/trace.\n"
        "خروجی: JSON با answer/evidence/memory_writes/proposals."
    )


def _output_spec() -> str:
    """output spec در USER slot — قرارداد خروجی."""
    return (
        "\n\n---\n"
        "خروجی: JSON با:\n"
        '  "answer": پاسخ کوتاه فارسی\n'
        '  "evidence": [{"claim","source","as_of"}]\n'
        '  "memory_writes": [{"type","content","provenance","confidence","as_of"}]\n'
        '  "proposals": [{"action","risk","requires_approval":true}]'
    )


# ─── موتور اصلی ─────────────────────────────────────────────────────────────

class ContextAssembler:
    """ساختِ پرامپت ۷-slot با بودجهٔ توکن و trim هوشمند."""

    def __init__(self, total_budget: int = 4000):
        self.total_budget = total_budget

    def build(self, inp: AssembleInput) -> tuple[str, AssemblyTrace]:
        trace = AssemblyTrace(flag_on=_flag_on(), query=inp.query or inp.user_msg[:80])
        if not _flag_on():
            trace.error = f"{FLAG}=0 — assembler is no-op"
            return "", trace

        try:
            slots = self._fill_slots(inp)
            final, trimmed = self._trim(slots)
            trace.trimmed = trimmed
            trace.slots = [{"name": s.name, "chars": len(s.content)} for s in final if s.content]
            trace.total_chars = sum(len(s.content) for s in final)
            prompt = "\n\n".join(
                f"### {s.name}\n{s.content}" for s in final if s.content
            )
            return prompt, trace
        except Exception as e:  # noqa: BLE001
            trace.error = f"{type(e).__name__}: {e!s:.200}"
            # fail-soft: حداقل RULES + USER را برگردان
            fallback = f"### RULES\n{_rules_text()}\n\n### USER\n{inp.user_msg}{_output_spec()}"
            return fallback, trace

    def _fill_slots(self, inp: AssembleInput) -> list[Slot]:
        query = inp.query or inp.user_msg

        # STATE — fail-soft (از طریق _reader برای monkeypatch)
        try:
            snap = _reader.read_snapshot()
        except Exception:  # noqa: BLE001
            snap = {"status": "error", "reason": "snapshot unavailable"}
        state_text = _render_state(snap)

        # FACTS — fail-soft
        try:
            facts = _reader.read_retrieval(query, k=6)
        except Exception:  # noqa: BLE001
            facts = []
        facts_text = _render_facts(facts)

        # EPISODES — fail-soft
        try:
            episodes = _reader.read_semantic(n=5)
        except Exception:  # noqa: BLE001
            episodes = []
        episodes_text = _render_episodes(episodes)

        # TRACE — fail-soft
        try:
            trace_records = _reader.read_trace(n=10)
        except Exception:  # noqa: BLE001
            trace_records = []
        trace_text = _render_trace(trace_records)

        # MISSION
        mission_text = json.dumps(inp.mission, ensure_ascii=False) if inp.mission else "(no mission set)"

        return [
            Slot("RULES", 0, 400, pinned=True, content=_rules_text()),
            Slot("MISSION", 1, 300, content=mission_text),
            Slot("STATE", 2, 200, content=state_text),
            Slot("FACTS", 3, 1200, content=facts_text),
            Slot("EPISODES", 4, 400, content=episodes_text),
            Slot("TRACE", 5, 300, content=trace_text),
            Slot("USER", 6, 9999, pinned=True, content=inp.user_msg + _output_spec()),
        ]

    def _trim(self, slots: list[Slot]) -> tuple[list[Slot], list[str]]:
        """Trim از کم‌اهمیت‌ترین (بیشترین priority) به مهم‌ترین.
        ترتیب قربانی: EPISODES → TRACE → FACTS → MISSION → STATE.
        هرگز RULES و USER (pinned).
        اگر pinned slots خودشان از budget بیشتر باشند، trim متوقف می‌شود
        (USER بزرگ‌تر از budget مجاز است — آن را قطع نمی‌کنیم).
        پیاده‌سازی: هر slot غیرِpinned را حداکثر یک‌بار به ۸۰٪ سقف می‌رسانیم،
        نه کاراکتربه‌کاراکتر (مانند نسخهٔ کیمی، اما با گاردِ توقف)."""
        trimmed: list[str] = []
        total = sum(len(s.content) for s in slots)
        if total <= self.total_budget:
            return sorted(slots, key=lambda x: x.priority), trimmed

        for s in sorted(slots, key=lambda x: -x.priority):
            if s.pinned or not s.content or total <= self.total_budget:
                continue
            # یک برشِ بزرگ: slot را به ~۶۰٪ کاهش بده
            target_len = int(len(s.content) * 0.6)
            if target_len < 10:
                target_len = 0   # slot خیلی کوچک است — کاملاً خالی کن
            if target_len > 0:
                s.content = s.content[:target_len] + "…"
            else:
                s.content = ""
            trimmed.append(s.name)
            total = sum(len(x.content) for x in slots)

        # اگر هنوز بالایِ budget هست (pinned slots بزرگ)، یک دورِ دوم
        for s in sorted(slots, key=lambda x: -x.priority):
            if s.pinned or not s.content or total <= self.total_budget:
                continue
            s.content = ""   # slot غیرِpinned را کاملاً خالی کن
            trimmed.append(s.name)
            total = sum(len(x.content) for x in slots)

        return sorted(slots, key=lambda x: x.priority), trimmed
