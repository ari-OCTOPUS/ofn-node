"""telegram.py — render برای تاپیکِ ⛏ Mining (Topic 24). صفر شبکه، صفر توکن.

منوی ۶-گزینه‌ای با namespaceِ اختصاصیِ ``mo:`` (رفعِ تصادمِ callback).
هر verdict-card دکمهٔ واقعیِ ✅/❌ دارد که در mergeِ واقعی به VERDICT_QUEUE می‌نویسد (نه no-op).
"""
from __future__ import annotations

TOPIC = "⛏ Mining"

MENU = [
    {"label": "🛠 ناوگان", "cb": "mo:fleet"},
    {"label": "⛏ کوین‌ها", "cb": "mo:coins"},
    {"label": "🔋 برق", "cb": "mo:power"},
    {"label": "🧠 تصمیم‌ها", "cb": "mo:dec"},
    {"label": "⚠️ ریسک", "cb": "mo:risk"},
    {"label": "📊 گزارش", "cb": "mo:report"},
]


def render_pinned(beat: dict) -> str:
    """متنِ کارتِ پینِ زنده — در هر mining_beat و /mining now تازه می‌شود."""
    f = beat.get("fleet", {})
    r = beat.get("readiness", {})
    halt = "⛔HALT" if beat.get("halt_proposal") else "OK"
    return (
        f"{TOPIC} · فاز {beat.get('phase', '?')} · "
        f"نود {f.get('running', 0)}/{f.get('nodes_total', 0)} · "
        f"برق {halt} · آمادگی {r.get('score', 0)}٪ · "
        f"live={beat.get('live')} ({beat.get('signal')})"
    )


def render_topic(beat: dict) -> dict:
    """کارتِ کاملِ تاپیک: پین + منوی ۶-گزینه‌ای + verdict-cards + هشدارِ HALT."""
    return {
        "topic": TOPIC,
        "pinned": render_pinned(beat),
        "menu": list(MENU),
        "verdict_cards": [
            {"id": vid, "cb_yes": f"mo:vok:{vid}", "cb_no": f"mo:vno:{vid}"}
            for vid in beat.get("open_verdict_ids", []) if vid
        ],
        "halt_alert": bool(beat.get("halt_proposal", False)),
    }
