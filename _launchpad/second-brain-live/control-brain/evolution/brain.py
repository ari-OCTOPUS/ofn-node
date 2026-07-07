# -*- coding: utf-8 -*-
"""مغز تکاملی — لایه ۳ (فاز ۴). دیزاین ratified ی vault + الگوهای DEEP-V2.

قوانین سخت (غیرقابل مذاکره):
- هرگز کد اصلی را تغییر نمی‌دهد؛ فقط Proposal (مشکل/راه‌حل/ریسک/اثر/rollback).
- اعمال فقط با تأیید ادمین → ثبت در CHANGELOG.md (append-only) + دستور branch جدا.
- TTL: پیشنهاد بی‌verdict بعد از ۳۰ روز خودکار expired (fail-closed).
- privacy: سیگنال‌های Project-F به تحلیل Fugu داده نمی‌شود (گارد در Gateway هم هست).
- kill سه‌سطحی: STOP-EVO (pause حلقه) · /halt (کل مغز) · git revert (برگشت جهش‌های اعمال‌شده).
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

CB = Path(__file__).resolve().parent.parent
CHANGELOG = CB.parent / "CHANGELOG.md"

_FORMAT = ("خروجی را دقیقاً با این قالب بده (هر بخش یک پاراگرافِ حداکثر ۳ جمله):\n"
           "عنوان: <یک خط>\nمشکل: <چه چیزی در سیستم ضعیف/کند/شکننده است>\n"
           "راه‌حل: <تغییر مشخص و کوچک>\nریسک: <چه چیزی می‌تواند بشکند>\n"
           "اثر: <برآورد فایده، قابل‌اندازه‌گیری>\nبرگشت: <دقیقاً چطور undo می‌شود>")


class EvolutionBrain:
    def __init__(self, memory, gateway):
        self.mem = memory
        self.gw = gateway

    # ---------- ادراک ----------
    def collect_signals(self, include_projectf: bool = False) -> dict:
        st = self.mem.stats()
        sig = {
            "briefs": st["briefs"], "pending_msgs": st["pending"], "sent": st["sent"],
            "knowledge": st["knowledge"],
            "deepseek_month_usd": st["deepseek_month"], "fugu_month_usd": st["fugu_month"],
            "alerts": [],
            "feedback": {},
        }
        for row in self.mem.knowledge_search("BUDGET-STOP", n=5):
            sig["alerts"].append(row[:120])
        for biz in ("ziman", "painting", "accounting") + (("projectf",) if include_projectf else ()):
            fbs = self.mem.feedback_for(biz, n=20)
            if fbs:
                useful = sum(1 for f in fbs if f.useful)
                sig["feedback"][biz] = f"{useful}/{len(fbs)} مفید"
        return sig

    # ---------- پیشنهاد ----------
    def propose(self, tier: str = "cheap") -> int:
        """یک دور فکر → یک Proposal در DB (status=pending). خروجی: id."""
        # privacy: اگر مسیر escalate (Fugu) است، سیگنال Project-F حذف
        signals = self.collect_signals(include_projectf=(tier != "escalate"))
        prompt = (
            "تو مهندس بازمهندسی یک سیستم چندایجنتی کوچک (مغز دوم) هستی. "
            "بر اساس سیگنال‌های زیر، «یک» بهبود کوچک، کم‌ریسک و قابل‌برگشت پیشنهاد بده. "
            "چیزی که همین هفته قابل اعمال باشد. نه بازنویسی بزرگ.\n\n"
            f"سیگنال‌های سیستم:\n{json.dumps(signals, ensure_ascii=False, indent=1)}\n\n"
            f"{_FORMAT}")
        out = self.gw.llm(prompt, system="محافظه‌کار باش؛ ثبات مهم‌تر از هوشمندی است.",
                          tier=tier, business="evolution", use_cache=False, max_tokens=700)
        return self._save(out)

    def _grab(self, label: str, text: str) -> str:
        m = re.search(rf"^{label}\s*[:：]\s*(.+?)(?=\n[^\n]+[:：]|\Z)", text, re.M | re.S)
        return (m.group(1).strip() if m else "—")[:800]

    def _save(self, text: str) -> int:
        title = self._grab("عنوان", text)
        if title == "—":
            title = (text.strip().splitlines() or ["پیشنهاد"])[0][:100]
        return self.mem.add_proposal(
            title=title[:150],
            problem=self._grab("مشکل", text),
            solution=self._grab("راه‌حل", text),
            risk=self._grab("ریسک", text),
            impact=self._grab("اثر", text),
            rollback=self._grab("برگشت", text),
        )

    # ---------- verdict ادمین ----------
    def resolve(self, pid: int, decision: str) -> str:
        """approved → ثبت CHANGELOG (append-only) + دستور branch؛ rejected → بسته.
        هیچ کدی اینجا تغییر نمی‌کند — اعمال واقعی همیشه انسانی/تعاملی است."""
        row = self.mem.get_proposal(pid)
        if row is None or row[7] != "pending":     # status
            return "این پیشنهاد باز نیست."
        if decision != "approved":
            self.mem.set_proposal(pid, "rejected")
            return f"❌ پیشنهاد #{pid} رد شد."
        self.mem.set_proposal(pid, "approved")
        branch = f"evo/{pid}"
        line = (f"\n## [{datetime.now().isoformat(timespec='minutes')}] پیشنهاد #{pid} تأیید شد — {row[1]}\n"
                f"- راه‌حل: {row[3][:300]}\n- ریسک: {row[4][:200]}\n- برگشت: {row[6][:200]}\n"
                f"- branch پیشنهادی: `{branch}` (اعمال فقط روی branch، بعد merge با verdict)\n")
        if not CHANGELOG.exists():
            CHANGELOG.write_text("# CHANGELOG — جهش‌های تأییدشدهٔ مغز تکاملی (append-only)\n",
                                 encoding="utf-8")
        with CHANGELOG.open("a", encoding="utf-8") as f:
            f.write(line)
        self.mem.knowledge_add(f"EVO-APPROVED #{pid}: {row[1]}", tag="evolution")
        return (f"✅ پیشنهاد #{pid} تأیید و در CHANGELOG ثبت شد.\n"
                f"اعمال: در جلسهٔ بعدی Cowork بگو «جهش #{pid} را روی branch {branch} پیاده کن».")
