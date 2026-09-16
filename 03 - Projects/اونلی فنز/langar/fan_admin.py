#!/usr/bin/env python3
"""fan_admin.py — دستورهای /fan_* کاکپیتِ اپراتور روی FanDB (CRM).

langar این را صدا می‌زند. اپراتور می‌تواند fan اضافه کند، خرید ثبت کند،
tag بزند، segment ببیند. صفر PII — فقط alias کوتاه + هش.

دستورها:
  /fan_add <alias> [channel]   — افزودن/refresh یک fan
  /fan_list [segment]          — لیست fans (یا یک segment خاص)
  /fan_buy <alias> <usd> [kind]— ثبت خرید (ppv/sub/tip)
  /fan_tag <alias> <tag>       — افزودن tag
  /fan_stats                   — خلاصهٔ CRM (segments, LTV)

$0 offline · stdlib · fail-soft · صفر PII.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_BRAIN = _HERE.parent / "brain"
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

FAN_HELP = ("دستورهای Fan CRM:\n"
            "/fan_add <alias> [channel] · /fan_list [segment] · "
            "/fan_buy <alias> <usd> [kind] · /fan_tag <alias> <tag> · /fan_stats")


def _db():
    from store import FanDB
    return FanDB()


def handle_fan(cmd: str, arg: str = "", db=None) -> str:
    cmd = (cmd or "").lower().strip()
    arg = (arg or "").strip()
    try:
        d = db if db is not None else _db()
        if cmd == "/fan_stats":
            s = d.summary()
            segs = " · ".join(f"{k}:{v}" for k, v in sorted(s["segments"].items())) or "خالی"
            return (f"👥 Fan CRM\n"
                    f"total: {s['total']} · LTV کل: ${s['total_ltv_usd']:.2f}\n"
                    f"segments: {segs}")
        if cmd == "/fan_add":
            parts = arg.split(maxsplit=1)
            if not parts:
                return "❌ /fan_add <alias> [channel]\nمثال: /fan_add fan-reddit-1 reddit"
            alias = parts[0]
            channel = parts[1].strip() if len(parts) > 1 else "of"
            r = d.add(alias, channel[:16])
            return f"✅ fan ثبت شد: {r['alias']} [{r['segment']}] (id={r['id']})"
        if cmd == "/fan_list":
            seg = arg.lower().strip() if arg else ""
            fans = d.by_segment(seg) if seg else d.all()
            if not fans:
                return f"📭 هیچ fan‌ای" + (f" در segment '{seg}'" if seg else "") + " نیست."
            out = [f"📋 {len(fans)} fan" + (f" [{seg}]" if seg else "") + ":"]
            for f in fans[:15]:
                out.append(f"• {f['alias']} [{f['segment']}] LTV=${f['ltv_usd']:.0f} "
                           f"({f.get('ppv_count', 0)} ppv) · {f.get('channel','?')}")
            if len(fans) > 15:
                out.append(f"... +{len(fans)-15} بیشتر")
            return "\n".join(out)
        if cmd == "/fan_buy":
            parts = arg.split()
            if len(parts) < 2:
                return "❌ /fan_buy <alias> <usd> [kind]\nمثال: /fan_buy fan-1 15 ppv"
            alias = parts[0]
            try:
                amount = float(parts[1])
            except ValueError:
                return "❌ مبلغ باید عدد باشد"
            kind = parts[2] if len(parts) > 2 else "ppv"
            r = d.record_purchase(alias, amount, kind[:16])
            return (f"💰 خرید ثبت شد: {alias} +${amount:.2f} ({kind})\n"
                    f"LTV: ${r['ltv_usd']:.2f} → segment: {r['segment']}")
        if cmd == "/fan_tag":
            parts = arg.split(maxsplit=1)
            if len(parts) < 2:
                return "❌ /fan_tag <alias> <tag>"
            r = d.tag(parts[0], parts[1])
            if not r["ok"]:
                return f"❌ {r['error']}"
            return f"🏷 tag اضافه شد: {parts[0]} → {', '.join(r['tags'])}"
        return FAN_HELP
    except Exception as e:  # noqa: BLE001
        return f"fan error: {type(e).__name__}"
