#!/usr/bin/env python3
"""dm_admin.py — دستورهای /dm_* کاکپیتِ اپراتور روی صفِ DMِ HITL.

langar این را صدا می‌زند. اپراتور draftهای DM را مرور می‌کند، approve/reject می‌کند،
و payload نهایی را **دستی** copy-paste می‌کند. هیچ ارسالِ خودکار وجود ندارد.

دستورها:
  /dm_status                — خلاصهٔ صف
  /dm_queue                 — draftهای منتظرِ review
  /dm_ok <id>               — تأیید → payload آمادهٔ copy-paste
  /dm_no <id> [reason]      — رد
  /dm_sent <id>             — ثبتِ ارسالِ دستی (آمار)
  /dm_ready                 — payloadهای آمادهٔ ارسال
  /dm_new <channel> <kind> <body>  — ساختنِ draftِ دستی (برای تست/وصلِ LLM)

$0 offline · stdlib · fail-soft · content-safe.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_BRAIN = _HERE.parent / "brain"
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

DM_HELP = ("دستورهای DM HITL:\n"
           "/dm_status · /dm_queue · /dm_ok <id> · /dm_no <id> · "
           "/dm_sent <id> · /dm_ready · /dm_new <channel> <kind> <body>")


def _default_pipe():
    from dm_pipeline import DmPipeline
    return DmPipeline()


def handle_dm(cmd: str, arg: str = "", pipe=None) -> str:
    """دیسپچرِ /dm_*. pipe تزریق‌پذیر (تست). هرگز crash؛ هرگز ارسالِ خودکار."""
    cmd = (cmd or "").lower().strip()
    arg = (arg or "").strip()
    try:
        p = pipe if pipe is not None else _default_pipe()
        if cmd == "/dm_status":
            d = p.admin_digest()
            return (f"💬 Project-F · DM HITL\n"
                    f"pending {d['pending_review']} · ready {d['ready_for_manual_send']} · "
                    f"sent {d['sent']} · rejected {d['rejected']} · flagged {d['flagged']}\n"
                    f"auto-send: خاموش (HITL) · {d['next']}")
        if cmd == "/dm_queue":
            pend = p.pending()
            if not pend:
                return "📭 صفِ DM خالی است."
            out = ["📋 DM منتظرِ review (تأیید: /dm_ok <id>):"]
            for it in pend[:10]:
                flag = " ⚠️" if it.get("flagged") else ""
                out.append(f"• <code>{it['id']}</code> [{it['channel']}/{it['kind']}] "
                           f"{(it.get('subject') or it['body'])[:48]}{flag}")
            return "\n".join(out)
        if cmd == "/dm_ready":
            rdy = p.ready()
            if not rdy:
                return "📭 payload آمادهٔ ارسال نیست. /dm_queue + /dm_ok اول."
            out = ["📤 DM آمادهٔ ارسالِ دستی:"]
            for it in rdy[:5]:
                out.append(f"• <code>{it['id']}</code> [{it['channel']}]")
                out.append(f"  {it['body'][:120]}")
                out.append(f"  (ارسال دستی → بعدش /dm_sent {it['id']})")
            return "\n".join(out)
        if cmd == "/dm_ok":
            if not arg:
                return "❌ /dm_ok <id>"
            r = p.approve(arg, actor="operator")
            if not r.get("ok"):
                return f"❌ {r.get('error')}"
            pl = r["payload"]
            return (f"✅ {arg} آمادهٔ ارسالِ <b>دستی</b>:\n"
                    f"[{pl['channel']}] {pl.get('subject','')}\n"
                    f"{pl['body']}\n"
                    f"⚠️ خودکار ارسال نمی‌شود — copy-paste کن، بعدش /dm_sent {arg}")
        if cmd == "/dm_no":
            parts = arg.split(maxsplit=1)
            if not parts:
                return "❌ /dm_no <id> [reason]"
            r = p.reject(parts[0], parts[1] if len(parts) > 1 else "operator")
            return f"🚫 {parts[0]} rejected" if r.get("ok") else f"❌ {r.get('error')}"
        if cmd == "/dm_sent":
            if not arg:
                return "❌ /dm_sent <id>"
            r = p.mark_sent(arg)
            return f"📤 {arg} ارسالی ثبت شد" if r.get("ok") else f"❌ {r.get('error')}"
        if cmd == "/dm_new":
            # /dm_new <channel> <kind> <body...>
            parts = arg.split(maxsplit=2)
            if len(parts) < 3:
                return "❌ /dm_new <channel> <kind> <body>"
            channel, kind, body = parts[0], parts[1], parts[2]
            r = p.draft(channel, kind, body)
            if r.get("flagged"):
                return f"⚠️ {r['id']} ساخته شد ولی <b>flagged</b> — بازنویسی لازم (containment)."
            return f"➕ {r['id']} ساخته شد. /dm_queue برای review."
        return DM_HELP
    except Exception as e:  # noqa: BLE001 — fail-soft
        return f"dm error: {type(e).__name__}"
