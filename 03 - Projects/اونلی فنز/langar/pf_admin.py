#!/usr/bin/env python3
"""pf_admin.py — دستورهای /pf_* کاکپیتِ اپراتور روی خطِ لولهٔ اکتساب (propose-only).

langar (کاکپیتِ اپراتورِ Project-F، بات جدا/ایزوله، owner-allowlist) این را صدا می‌زند.
اپراتور مجاز است درفت‌ها را ببیند (in-folder، isolated) — ولی هیچ اکشنِ بیرونی: فقط
draft/queue/approve/reject روی AcquisitionPipeline. انتشارِ واقعی = دستیِ انسان پس از GATE 0.
$0 offline · stdlib · fail-soft · content-safe (کپیِ گاردشده؛ هرگز هویت/شهر/پلتفرم).
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_BRAIN = _HERE.parent / "brain"
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

PF_HELP = ("دستورهای Project-F acquisition:\n"
           "/pf_status · /pf_plan [n] · /pf_queue · /pf_ok <id> · /pf_no <id> · /pf_ready <id>")


def _default_pipe():
    from acquisition_pipeline import AcquisitionPipeline
    brain = None
    try:
        from acquisition import AcquisitionBrain
        brain = AcquisitionBrain()
    except Exception:  # noqa: BLE001 — brain اختیاری؛ fallback به هوکِ امن
        brain = None
    return AcquisitionPipeline(brain=brain)


def handle_pf(cmd: str, arg: str = "", pipe=None) -> str:
    """دیسپچرِ /pf_*. pipe تزریق‌پذیر (تست). هرگز crash؛ هرگز اکشنِ بیرونی."""
    cmd = (cmd or "").lower().strip()
    arg = (arg or "").strip()
    try:
        p = pipe if pipe is not None else _default_pipe()
        if cmd == "/pf_status":
            d = p.admin_digest()
            return (f"🎛 Project-F · acquisition\n"
                    f"drafted {d['drafted']} · approved {d['approved']} · "
                    f"ready {d['ready']} · rejected {d['rejected']} · flagged {d['flagged']}\n"
                    f"outward: خاموش (GATE 0) · {d['next']}")
        if cmd == "/pf_plan":
            n = int(arg) if arg.isdigit() else 3
            items = p.auto_plan(n)
            return f"➕ {len(items)} درفت ساخته و صف شد. /pf_queue برای دیدن، /pf_ok <id> برای تأیید."
        if cmd == "/pf_queue":
            pend = p.pending()
            if not pend:
                return "📭 صفِ درفت خالی است. /pf_plan برای ساخت."
            out = ["📋 صفِ درفت (تأیید: /pf_ok <id> · رد: /pf_no <id>):"]
            for it in pend[:10]:
                out.append(f"• <code>{it['id']}</code> [{it['channel']}] {it['hook'][:48]}")
            return "\n".join(out)
        if cmd in ("/pf_ok", "/pf_approve"):
            r = p.approve(arg, actor="operator")
            return f"✅ {arg} approved — /pf_ready {arg} برای payloadِ پستِ دستی" if r.get("ok") \
                else f"❌ {r.get('error')}"
        if cmd in ("/pf_no", "/pf_reject"):
            r = p.reject(arg, "operator")
            return f"🚫 {arg} rejected" if r.get("ok") else f"❌ {r.get('error')}"
        if cmd == "/pf_ready":
            r = p.finalize(arg)
            if not r.get("ok"):
                return f"❌ {r.get('error')}"
            pl = r["payload"]
            return (f"📤 آمادهٔ پستِ <b>دستی</b> ({r['mode']}):\n"
                    f"[{pl['channel']}] {pl['caption']}\n"
                    f"⚠️ خودکار پست نمی‌شود — خودت دستی پست کن (اکانت/GATE 0 لازم).")
        return PF_HELP
    except Exception as e:  # noqa: BLE001 — fail-soft، هرگز کاکپیت را نمی‌شکند
        return f"pf error: {type(e).__name__}"
