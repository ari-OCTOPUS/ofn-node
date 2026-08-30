"""architecture_explainer.py — فاز Q: پاسخ ساده + فنی دربارهٔ معماری Octopus.

Read-model از فایل‌های واقعی (بدون گراف خیالی). دو حالت:
    ساده:  «Chat Box → Collaborator → حافظه/مغز/معادلات»
    فنی:   data.architecture با call chain و path دقیق.

هیچ authority تولید نمی‌کند؛ advice-only.
"""
from __future__ import annotations

import json
from typing import Any

ARCH_SCHEMA = "architecture-explainer.v1"

# نقشهٔ واقعی اجزا (از call graph discovery — تأییدشده)
COMPONENTS: dict[str, dict[str, Any]] = {
    "miniapp_gateway": {
        "name": "مینی‌اپ گیت‌وی",
        "purpose": "دیوارِ 8774؛ owner-auth + rate-limit + /api/ask و /api/collab",
        "path": "_ops/telegram_center/miniapp_gateway.py",
        "callers": ["Chat Box (Telegram WebApp)"],
        "callees": ["ask_vault", "ask_brain", "collaborator", "mirror_room"],
        "gates": ["owner initData", "rate-limit", "_redact دولایه"],
        "effects_allowed": ["none (خروجی فقط متن/ساختار)"],
        "effects_forbidden": ["external send", "money"],
        "runtime": "LIVE",
    },
    "collaborator": {
        "name": "همکار (مسیر گفت‌وگوی واحد)",
        "purpose": "روتر و assembler مکالمه؛ intent → پاسخ + facts + equation_advice",
        "path": "_ops/owner_console/collaborator.py",
        "callers": ["miniapp_gateway", "Telegram center"],
        "callees": ["conversation", "collab_model_adapter", "owner_recall",
                    "equation_advice", "collab_memory"],
        "gates": ["quarantine/draft (ADR-033)", "OCTOPUS_WIRE_COLLAB"],
        "effects_allowed": ["draft reply (external_effect=false)"],
        "effects_forbidden": ["send", "authorize"],
        "runtime": "LIVE",
    },
    "conversation": {
        "name": "تشخیص نیت",
        "purpose": "۱۷+ regex intent (intro/runtime/blockers/selfmap/...)",
        "path": "_ops/owner_console/conversation.py",
        "callers": ["collaborator"],
        "callees": ["status", "catalog"],
        "gates": ["—"],
        "effects_allowed": ["none"],
        "effects_forbidden": ["authorize"],
        "runtime": "LIVE",
    },
    "collab_model_adapter": {
        "name": "آداپتر مدل همکار",
        "purpose": "model_router.ask با _self_context (دومغز + حافظه cite)",
        "path": "_ops/owner_console/collab_model_adapter.py",
        "callers": ["collaborator"],
        "callees": ["model_router.ask"],
        "gates": ["daily cap 20", "سقف هزینه"],
        "effects_allowed": ["none"],
        "effects_forbidden": ["send"],
        "runtime": "LIVE (OCTOPUS_COLLAB_USE_MODEL=1)",
    },
    "owner_recall": {
        "name": "بازیابی حافظه (cite-only)",
        "purpose": "MemoryGate episodic + self-loop + collab memory → facts",
        "path": "_ops/memory/owner_recall.py",
        "callers": ["collaborator", "unified_context"],
        "callees": ["MemoryStore.search", "JSONL trails"],
        "gates": ["OCTOPUS_WIRE_MEMORY_GATE", "topic_wants_recall"],
        "effects_allowed": ["cite-only"],
        "effects_forbidden": ["authorize (may_authorize=false)"],
        "runtime": "LIVE",
    },
    "equation_advice": {
        "name": "مشاورهٔ معادلات (advice-only)",
        "purpose": "pain/control/σ/phi → advice continue|slow_down",
        "path": "_ops/memory/equation_advice.py",
        "callers": ["collaborator", "unified_context"],
        "callees": ["state JSON", "spectral"],
        "gates": ["برچسب advice_only"],
        "effects_allowed": ["advice"],
        "effects_forbidden": ["decision_effect/apply_effect"],
        "runtime": "LIVE",
    },
    "ask_vault": {
        "name": "پرسش از Vault",
        "purpose": "ripgrep *.md → rank → snippet → پاسخ محلی",
        "path": "_ops/telegram_center/ask_vault.py",
        "callers": ["miniapp_gateway"],
        "callees": ["rg", "local LLM"],
        "gates": ["OCTOPUS_TG_ASK_VAULT"],
        "effects_allowed": ["none"],
        "effects_forbidden": ["authorize"],
        "runtime": "LIVE (flag=1)",
    },
    "ask_brain": {
        "name": "مغز پرسش",
        "purpose": "نردبان محلی→پولی با سهمیه و گپ",
        "path": "_ops/telegram_center/ask_brain.py",
        "callers": ["miniapp_gateway"],
        "callees": ["model_router"],
        "gates": ["OCTOPUS_TG_ASK_BRAIN", "daily cap", "min gap"],
        "effects_allowed": ["none"],
        "effects_forbidden": ["send"],
        "runtime": "LIVE (flag=1)",
    },
    "cortex": {
        "name": "قشر (مغز برنامه‌ریزی)",
        "purpose": "improve/consolidation/planning",
        "path": "_ops/cortex/",
        "callers": ["organism", "collaborator (self_context)"],
        "callees": ["model_router", "memory"],
        "gates": ["OCTOPUS_WIRE_NEURAL"],
        "effects_allowed": ["propose/improve"],
        "effects_forbidden": ["direct apply"],
        "runtime": "LIVE",
    },
    "business_brain": {
        "name": "مغز تجاری",
        "purpose": "فرصت/پیشنهاد تجاری",
        "path": "_ops/cortex/business_brain.py",
        "callers": ["organism"],
        "callees": ["model_router"],
        "gates": ["OCTOPUS_WIRE_NEURAL"],
        "effects_allowed": ["propose"],
        "effects_forbidden": ["send/money"],
        "runtime": "LIVE",
    },
    "pulse_arbiter": {
        "name": "داور نبض (سه قلب، یک ضربان)",
        "purpose": "cardiac + control_law + rhythm → period advisory",
        "path": "_ops/heart/pulse_arbiter.py",
        "callers": ["organism"],
        "callees": ["cardiac", "control_law", "rhythm"],
        "gates": ["OCTOPUS_WIRE_PULSE_ARBITER", "wire_open"],
        "effects_allowed": ["period advisory (spacing دیواری)"],
        "effects_forbidden": ["ledger/age_tick"],
        "runtime": "LIVE",
    },
    "policy_gate": {
        "name": "گیت سیاست (تک‌گلوگاه)",
        "purpose": "تصمیم نهایی برای halt/اثر",
        "path": "_ops/policy/policy_gate.py",
        "callers": ["wiring.request_protective_halt", "limited_effect (مرجع)"],
        "callees": ["policy store"],
        "gates": ["approval", "kill-switch"],
        "effects_allowed": ["allow/deny"],
        "effects_forbidden": ["bypass"],
        "runtime": "LIVE",
    },
}

_ALIASES = {
    "gateway": "miniapp_gateway", "miniapp": "miniapp_gateway", "گیت‌وی": "miniapp_gateway",
    "collaborator": "collaborator", "همکار": "collaborator",
    "conversation": "conversation", "نیت": "conversation",
    "adapter": "collab_model_adapter", "مدل": "collab_model_adapter",
    "recall": "owner_recall", "حافظه": "owner_recall",
    "advice": "equation_advice", "معادله": "equation_advice",
    "vault": "ask_vault", "ask": "ask_vault",
    "brain": "ask_brain", "مغز پرسش": "ask_brain",
    "cortex": "cortex", "قشر": "cortex",
    "business": "business_brain", "تجاری": "business_brain",
    "arbiter": "pulse_arbiter", "نبض": "pulse_arbiter", "heart": "pulse_arbiter",
    "policy": "policy_gate", "سیاست": "policy_gate",
}


def resolve_component(query: str) -> str | None:
    q = str(query or "").lower()
    for key, cid in _ALIASES.items():
        if key in q:
            return cid
    return None


def _simple_text(cid: str | None, q: str) -> str:
    if cid is None:
        return ("سؤال معماری مشخصی پیدا نکردم. می‌توانی بپرسی: "
                "«Pulse Arbiter به چی وصله؟» یا «PolicyGate کجای معماریه؟»")
    c = COMPONENTS[cid]
    return (
        f"{c['name']} — {c['purpose']}. "
        f"فایل: {c['path']}. "
        f"واردشونده از: {', '.join(c['callers'])}؛ خروجی به: {', '.join(c['callees'])}. "
        f"گیت‌ها: {', '.join(c['gates'])}. "
        f"مجاز: {', '.join(c['effects_allowed'])}؛ ممنوع: {', '.join(c['effects_forbidden'])}."
    )


def explain(query: str) -> dict[str, Any]:
    cid = resolve_component(query)
    data: dict[str, Any] = {
        "schema": ARCH_SCHEMA,
        "matched": cid is not None,
        "text": _simple_text(cid, query),
        "architecture": None,
        "may_authorize": False,
    }
    if cid:
        data["architecture"] = {
            "component": cid,
            "detail": COMPONENTS[cid],
            "runtime_verified": COMPONENTS[cid].get("runtime") == "LIVE",
        }
    return data


def full_map() -> dict[str, Any]:
    """نقشهٔ کامل (برای intent خودآگاهی/selfmap)."""
    return {
        "schema": ARCH_SCHEMA,
        "matched": True,
        "text": "نقشهٔ اجزای زنده در بخش data.architecture (فقط اجزای واقعی).",
        "architecture": {
            "components": [
                {"id": cid, "name": c["name"], "purpose": c["purpose"],
                 "path": c["path"], "runtime": c["runtime"]}
                for cid, c in COMPONENTS.items()
            ],
            "edges": [
                "chat_box -> miniapp_gateway -> collaborator",
                "collaborator -> conversation | owner_recall | equation_advice | collab_model_adapter",
                "miniapp_gateway -> ask_vault | ask_brain (ladder)",
                "organism -> pulse_arbiter (three hearts)",
                "limited_effect -> policy_gate (proposal مرجع)",
            ],
            "runtime_verified": True,
            "note": "4d_system/Super-Governor خارج از مسیر (DEPRECATED/SPEC)",
        },
        "may_authorize": False,
    }


if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "Pulse Arbiter به چی وصله؟"
    print(json.dumps(explain(q), ensure_ascii=False, indent=2))
