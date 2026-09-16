#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""diagnose.py — استدلالِ دکتر.

دکتر خودش «فکر نمی‌کند» — **context را می‌سازد و Fugu فکر می‌کند.**
چون TRINITY داخلِ Fugu نقش‌های Thinker/Worker/Verifier را خودش پخش می‌کند،
کارِ ما ساختِ یک Context Bundle دقیق است، نه ساختِ ارکستراتورِ دوم.

سه قاعده که در پرامپتِ سیستم قفل شده‌اند و از قوانینِ والت می‌آیند:
  R-01 هیچ سنجهٔ خودارجاعی به‌عنوان شاهد پذیرفته نمی‌شود
  R-02 عددِ منفی منتشر می‌شود، clamp ممنوع
  «نبودِ ❌ یعنی سبز نیست» — بدونِ عدد، ادعا نکن
"""
from __future__ import annotations

import os

from dataclasses import dataclass
from pathlib import Path

from fugu import Fugu, Reply
from vault import Note, Vault

# ۲۹ جولای، از اولین request واقعی: با effort=max، توکن‌های «فکر» هم از سقفِ
# completion می‌خورند؛ ۶۰۰۰ توکن یعنی JSONِ پچ وسطِ راه بریده می‌شود
# (رسید: tokens_out=6000 دقیقاً). سقفِ propose باید جای فکر + کلِ فایل را بدهد.
PROPOSE_MAX_TOKENS = int(os.environ.get("FUGU_PROPOSE_MAX_TOKENS", "16000"))

SYSTEM = """تو «دکترِ اختاپوس» هستی — متخصصِ یک ارگانیسمِ نرم‌افزاریِ مشخص، نه یک دستیارِ عمومی.

قوانینِ تغییرناپذیرِ تو:
۱. **هر سنجه‌ای که وجودِ خودش را می‌سنجد دروغ می‌گوید.** سنجهٔ درون‌زاد (شمارندهٔ ضربان،
   تعدادِ کشف، mtimeِ فایل، پوششِ docstring) هرگز شاهد نیست. فقط سنجهٔ برون‌زاد — چیزی که
   اگر ارگانیسم خاموش شود هم وجود دارد — حق رأی دارد.
۲. **عددِ منفی را منتشر کن.** clamp کردنِ نتیجهٔ بد ممنوع.
۳. **«نبودِ ❌» یعنی سبز نیست.** هر ادعا باید عددِ صریح یا مسیرِ فایل داشته باشد.
   اگر شاهد نداری، بنویس [UNKNOWN] — حدس نزن.
۴. تعارض با قوانینِ والت را **flag کن**، حل نکن. قوانین با هیچ سندِ بیرونی overwrite نمی‌شوند.

سبک: فارسی، فشرده، بدونِ تعارف. اول حکم، بعد شاهد، بعد نسخه.
هرجا عددی می‌آوری، منبعش را در همان جمله بگو."""


@dataclass
class Diagnosis:
    question: str
    answer: str | None
    used_notes: list[str]
    reply: Reply
    reasons: list[str]

    @property
    def ok(self) -> bool:
        return bool(self.answer)

    def as_markdown(self) -> str:
        head = f"# تشخیص\n\n**پرسش:** {self.question}\n\n"
        if not self.ok:
            return head + f"> [!failure] پاسخی تولید نشد\n> {self.reply.reason}\n"
        src = "\n".join(f"- [[{Path(p).stem}]]" for p in self.used_notes)
        return (head + self.answer.strip() +
                f"\n\n---\n### شاهدهایی که خوانده شد\n{src}\n\n"
                f"*مغز: `{self.reply.model}` · تلاش: `{self.reply.effort}` · "
                f"{self.reply.tokens_out} توکن · {self.reply.ms}ms*\n")


class Doctor:
    def __init__(self, vault_root: Path | str, state_dir: Path | str | None = None):
        self.vault = Vault(vault_root)
        self.brain = Fugu(state_dir or (Path(vault_root) / "90-_meta" / "state"))

    # ---------------------------------------------------------------- context
    def bundle(self, question: str, k: int = 8) -> tuple[str, list[Note]]:
        """Context Bundle — نه dump کلِ والت.

        همیشه قوانین می‌آیند (کوتاه‌اند و مرزِ استدلال را تعیین می‌کنند)،
        بعد نوت‌های مرتبط با پرسش.
        """
        laws = [n for n in self.vault.by_layer("semantic")
                if n.fm.get("type") == "law"]
        hits = [n for n in self.vault.search(question, limit=k)
                if n.fm.get("type") != "law"]
        parts = ["## قوانینِ والت (تغییرناپذیر)"]
        parts += [f"### {n.title}\n{n.excerpt(500)}" for n in laws]
        unc = self._unconscious(question)
        if unc:
            parts.append("\n" + unc)
        parts.append("\n## شاهدهای مرتبط")
        parts += [f"### {n.title}  ({n.rel})\n{n.excerpt()}" for n in hits]
        return "\n\n".join(parts), laws + hits

    def _unconscious(self, question: str) -> str:
        """لایهٔ ۴ فقط **رنگ** می‌دهد. اگر ساکت است، هیچ نمی‌گوید — و این درست است."""
        try:
            from mind import Mind                                # noqa: PLC0415
            return Mind(Path(self.vault.root) / "90-_meta" / "state").context(question)
        except Exception:                                        # noqa: BLE001
            return ""

    # ---------------------------------------------------------------- ask
    def ask(self, question: str, tier: str = "fast", k: int = 8) -> Diagnosis:
        ctx, notes = self.bundle(question, k)
        reasons: list[str] = []
        if not notes:
            reasons.append("هیچ نوتِ مرتبطی در والت پیدا نشد")
        if not self.brain.ready:
            reasons.append("SAKANA_API_KEY تنظیم نیست")

        user = (f"# پرسش\n{question}\n\n# حافظهٔ من دربارهٔ این اختاپوس\n{ctx}\n\n"
                "# کار\nفقط بر پایهٔ شاهدهای بالا جواب بده. اگر شاهد کافی نیست، "
                "صریح بگو چه چیزی را باید اندازه گرفت.")
        rep = self.brain.ask(SYSTEM, user, tier=tier)
        if not rep.usable:
            reasons.append(rep.reason)
        return Diagnosis(question, rep.text, [n.rel for n in notes], rep, reasons)

    # ---------------------------------------------------------------- full
    def full(self, tier: str = "deep") -> Diagnosis:
        """تشخیصِ کامل — همهٔ یافته‌های قرمز + قوانین + معادلات."""
        red = [n for n in self.vault.load() if n.status == "🔴"]
        laws = [n for n in self.vault.load() if n.fm.get("type") == "law"]
        parts = ["## قوانین"] + [f"### {n.title}\n{n.excerpt(400)}" for n in laws]
        parts += ["\n## همهٔ سنجه‌ها و یافته‌های قرمز"]
        parts += [f"### {n.title}  ({n.rel})\n{n.excerpt(900)}" for n in red]
        ctx = "\n\n".join(parts)
        q = ("وضعیتِ کلیِ این ارگانیسم را تشخیص بده. الگوی مشترکِ بینِ خرابی‌ها چیست؟ "
             "به ترتیبِ اهرم نسخه بده — کدام کار بیشترین قفل را باز می‌کند؟ "
             "و بگو کدام عدد هنوز دروغ می‌گوید.")
        rep = self.brain.ask(SYSTEM, f"# پرسش\n{q}\n\n# حافظه\n{ctx}", tier=tier,
                             max_tokens=8000)
        return Diagnosis(q, rep.text, [n.rel for n in red], rep,
                         [] if rep.usable else [rep.reason])

    # ---------------------------------------------------------------- propose
    def propose(self, goal: str, tier: str = "propose", k: int = 10):
        """نثر ⟶ پچِ ساختاریافته. **اعمال نمی‌کند** — فقط پیشنهاد و گیت.

        خروجی یک `PatchSet`ِ گیت‌خورده است. اجرا کارِ `MissionRunner` است و
        merge کارِ رأیِ مالک — نه کارِ این تابع.
        """
        from propose import PROPOSE_SYSTEM, parse_patchset      # noqa: PLC0415

        ctx, notes = self.bundle(goal, k)
        user = (f"# هدف\n{goal}\n\n# حافظهٔ من دربارهٔ این اختاپوس\n{ctx}\n\n"
                "# کار\nیک تغییرِ کوچک، افزایشی و قابلِ‌بازگشت پیشنهاد بده. فقط JSON.")
        rep = self.brain.ask(SYSTEM + "\n\n" + PROPOSE_SYSTEM, user,
                             tier=tier, max_tokens=PROPOSE_MAX_TOKENS)
        if not rep.usable:
            return None, [rep.reason], [n.rel for n in notes]
        try:
            ps = parse_patchset(rep.text)
            if not ps.empty:
                ps.gate()
            return ps, ps.notes, [n.rel for n in notes]
        except Exception as e:                                  # noqa: BLE001
            return None, [f"{type(e).__name__}: {e}"], [n.rel for n in notes]

    # ---------------------------------------------------------------- offline
    def triage(self) -> dict:
        """تشخیصِ آفلاین — بدونِ مغز، فقط از خودِ والت. همیشه کار می‌کند."""
        ns = self.vault.load()
        red = [n for n in ns if n.status == "🔴"]
        endo = [n for n in ns if n.fm.get("provenance") == "درون‌زاد"]
        return {
            "notes": len(ns),
            "red": [n.title for n in red],
            "self_referential_metrics": [n.title for n in endo],
            "verdict": (f"{len(red)} یافتهٔ قرمز · {len(endo)} سنجهٔ درون‌زاد که حق رأی ندارند"
                        if red else "هیچ یافتهٔ قرمزی ثبت نشده"),
            "brain_ready": self.brain.ready,
            "quota_remaining": self.brain.quota.remaining,
        }
