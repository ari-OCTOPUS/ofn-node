#!/usr/bin/env python3
"""vault_admin.py — دستورهای /vault_* کاکپیتِ اپراتور روی VaultBank.

langar این را صدا می‌زند. اپراتور می‌تواند asset محتوا اضافه کند، ببیند،
و metric ثبت کند. acquisition_pipeline از این vault draft می‌زند.

دستورها:
  /vault_add <tag> <hook> [channel]   — افزودن asset محتوا
  /vault_list [tag]                   — لیست assets
  /vault_metric <id> <upvotes> [comments] [unlocks] — ثبت metric

$0 offline · stdlib · fail-soft · content-safe (گارد containment دارد).
"""
from __future__ import annotations

import shlex
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_BRAIN = _HERE.parent / "brain"
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

VAULT_HELP = ("دستورهای Vault:\n"
              "/vault_add <tag> <hook> [channel] · /vault_list [tag] · "
              "/vault_metric <id> <up> [comments] [unlocks]")

# پاریته با acquisition_pipeline._BANNED_COPY — گuard containment
# چرا دوزبانه (لِین B · 2026-08-03): اپراتور این دستورها را از تلگرام و به فارسی
# تایپ می‌کند، ولی تطبیق substring روی `.lower()` بود و `str.lower()` روی فارسی
# بی‌اثر است — یعنی «Sydney» رد می‌شد ولی «سیدنی»/«ایرانی» مستقیم داخلِ vault
# می‌نشست و بعداً از همان‌جا draft می‌شد (rule #6).
# «استرالیا/استرالیایی» عمداً اضافه نشده — مثلِ Aussie کشوری و مجاز است.
_BANNED = ("اونلی", "onlyfans", "fansly", "صبا", "saba", "sydney", "سیدنی",
           "persian", "iranian", "harbour", "bondi", "nsw",
           # نامِ پلتفرم و قومیت/زبان به فارسی + فینگلیشِ رایج
           "انلی فنز", "اونلی فنز", "اونلی‌فنز", "فنسلی",
           "ایران", "ایرانی", "پارسی", "پرشین", "فارسی",
           "sidney", "sydeny", "farsi", "irani", "persion")

# نرمال‌سازِ سبکِ فارسی — خالص، stdlib، خودبسنده (عمداً import نمی‌شود: هر گارد
# باید مستقل بایستد؛ importِ fail-soft یعنی گاردی که بی‌صدا بی‌دندان می‌شود).
_FA_TRANS = str.maketrans({"ي": "ی", "ى": "ی", "ك": "ک", "‌": "", "ـ": ""})


def _fa_norm(text: str) -> str:
    """کوچک‌سازی + یکسان‌سازیِ ی/ک عربی + حذفِ نیم‌فاصله/کشیده."""
    return str(text or "").translate(_FA_TRANS).lower()


def _is_clean(*texts) -> bool:
    # نرمال‌سازی قبل از تطبیق: «سيدني» با ی عربی هم باید گرفته شود.
    # نگاشت روی لاتین بی‌اثر ⇒ رفتارِ واژه‌های لاتین دست‌نخورده می‌ماند.
    blob = _fa_norm(" ".join(texts))
    return not any(_fa_norm(b) in blob for b in _BANNED)


def _bank():
    from store import VaultBank
    return VaultBank()


def handle_vault(cmd: str, arg: str = "", bank=None) -> str:
    cmd = (cmd or "").lower().strip()
    arg = (arg or "").strip()
    try:
        b = bank if bank is not None else _bank()
        if cmd == "/vault_list":
            tag = arg.lower().strip() if arg else ""
            assets = b.by_tag(tag) if tag else b.all()
            if not assets:
                return f"📭 vault خالی است." + (f" (tag '{tag}')" if tag else "") + " /vault_add برای افزودن."
            out = [f"📦 {len(assets)} asset" + (f" [{tag}]" if tag else "") + ":"]
            for a in assets[:15]:
                m = a.get("metrics", {})
                metric_str = f" ⬆{m.get('upvotes',0)}" if m else ""
                out.append(f"• <code>{a['id']}</code> [{a.get('channel','?')}] "
                           f"{a.get('tag','?')} · «{a.get('hook','')[:40]}»{metric_str}")
            return "\n".join(out)
        if cmd == "/vault_add":
            try:
                parts = shlex.split(arg)
            except ValueError:
                parts = arg.split()
            if len(parts) < 2:
                return "❌ /vault_add <tag> <hook> [channel]\nمثال: /vault_add pedicure-asmr \"Arch of the Day\" reddit"
            tag = parts[0]
            hook = parts[1]
            channel = parts[2] if len(parts) > 2 else "reddit"
            if not _is_clean(tag, hook, channel):
                return "⚠️ asset flagged — containment/rule#6. بازنویسی لازم."
            r = b.add(tag, hook, caption=hook, channel=channel[:16])
            return f"✅ asset ثبت شد: {r['id']} [{tag}] «{hook[:40]}»"
        if cmd == "/vault_metric":
            parts = arg.split()
            if len(parts) < 2:
                return "❌ /vault_metric <id> <upvotes> [comments] [unlocks]"
            vid = parts[0]
            try:
                up = int(parts[1])
                com = int(parts[2]) if len(parts) > 2 else 0
                unl = int(parts[3]) if len(parts) > 3 else 0
            except ValueError:
                return "❌ اعداد باید integer باشند"
            b.record_metric(vid, up, com, unl)
            return f"📊 metric ثبت شد: {vid} ⬆{up} 💬{com} 🔓{unl}"
        return VAULT_HELP
    except Exception as e:  # noqa: BLE001
        return f"vault error: {type(e).__name__}"
