"""
ailab.py — AI-Lab: آزمایشگاهِ مستقلِ پژوهشِ هوش مصنوعی.

تمرکز روی خودِ AI (معماری/حافظه/ارزیابی/امنیت)، نه روانِ کاربر.
داده‌اش در جدول‌های جدا (ailab_*) ذخیره می‌شود و با داده‌ی شخصی قاطی نمی‌شود.
از داده‌ی شخصیِ کاربر در پژوهش استفاده نمی‌کند.

مرزِ ایمنی: AI-Lab می‌تواند برای «خودش» و «سیستمِ انسانی» پیشنهادِ آپدیت بسازد،
ولی فقط به‌صورتِ diffِ سطح ۲ (بدونِ اجرای خودکار). انسان اعمال می‌کند.

با dependency injection ساخته می‌شود تا تست‌پذیر باشد.
"""

from __future__ import annotations

_PERSONA = (
    "تو AI-Labِ LANGAR هستی: مهندس و معمارِ سیستم‌های هوش مصنوعی. تمرکزت روی خودِ AI است "
    "(عامل‌ها، LLM، حافظه، بازیابی، ارزیابی، امنیت، خودبهبودِ کنترل‌شده). سورس‌دار و "
    "تگ‌خورده ([E]/[S]/[P]) پاسخ بده. پیشنهاد می‌دهی، تصمیم/اجرا نه. از داده‌ی شخصیِ "
    "کاربر استفاده نکن."
)

KIND_FOCUS = {
    "research": "یک موضوعِ AI را تحقیق کن: خلاصه، نکاتِ کلیدی، منابع، و کاربردِ احتمالی برای LANGAR.",
    "digest": "خلاصه‌ی کوتاهِ دسته‌بندی‌شده و منبع‌دار از مهم‌ترین پیشرفت‌های اخیرِ AI.",
    "architect": "یک معماریِ پیشنهادی بده: اجزا، ورودی/خروجی، ریسک‌ها، و مراحلِ اجرا (دیاگرامِ متنی).",
    "memory": "تحلیل و پیشنهاد برای حافظه/بازیابی/embedding/خلاصه‌سازی/فراموشیِ کنترل‌شده.",
    "benchmark": "یک تستِ سنجش طراحی کن: دقت، ثبات، کیفیت، hallucination، امنیت، سرعت، UX.",
    "safety": "ریسک‌ها و محدودیت‌ها: privacy، hallucination، خودبهبودِ کنترل‌نشده، دسترسی، وابستگیِ کاربر.",
}


class AILab:
    def __init__(self, brain, search=None, db=None, patch_manager=None, gate=None, budget=None):
        self.brain = brain
        self.search = search
        self.db = db
        self.patch_manager = patch_manager
        self.gate = gate
        self.budget = budget  # BudgetManager اختیاری

    def _gated(self, text: str) -> str:
        if self.gate:
            try:
                if not self.gate(text):
                    return "⚠️ خروجی با قوانین سازگار نبود — حذف شد."
            except Exception:
                pass
        return text

    def query(self, kind: str, topic: str) -> dict:
        focus = KIND_FOCUS.get(kind, KIND_FOCUS["research"])
        results = []
        if self.search is not None:
            try:
                results = self.search.search(topic)
            except Exception:
                results = []
        try:
            from researcher import source_quality
            results = source_quality.rank(results, topic)
        except Exception:
            pass
        data = (f"{topic}\n\nنتایج:\n"
                + "\n".join(f"- {r.get('title','')}: {r.get('snippet','')[:120]}"
                            for r in results[:5]))
        prompt = _PERSONA + "\n" + focus
        # کنترلِ بودجه: اگر بودجه تمام شده، LLM را صدا نزن (حالتِ کم‌هزینه)
        if self.budget is not None and not self.budget.can_spend():
            return {"kind": kind, "topic": topic,
                    "content": "💰 بودجه‌ی AI-Lab تمام شده. نسخه‌ی آفلاین/کم‌هزینه: "
                               f"موضوعِ «{topic}» را با /ai_budget ببین یا فردا دوباره بزن.",
                    "sources": [r.get("url") for r in results if r.get("url")]}
        try:
            content = self.brain.ask(prompt, {"domain": "ailab", "label": kind, "data": data})
            if self.budget is not None:
                model = getattr(self.brain, "model", getattr(self.brain, "name", "?"))
                self.budget.record_text(model, prompt + data, content, f"ai_{kind}")
        except Exception:
            content = f"[S] بدونِ LLM خلاصه‌ی کامل ممکن نیست. موضوع: {topic}"
        content = self._gated(content)
        sources = [r.get("url") for r in results if r.get("url")]
        if self.db is not None:
            try:
                import json
                self.db.save_ailab_entry(kind, topic, content,
                                         json.dumps(sources, ensure_ascii=False))
            except Exception:
                pass
        return {"kind": kind, "topic": topic, "content": content, "sources": sources}

    def add_idea(self, text: str) -> int | None:
        if self.db is None:
            return None
        return self.db.add_ailab_idea(text)

    def list_ideas(self):
        return self.db.list_ailab_ideas() if self.db else []

    def propose_update(self, target: str, issue: str) -> dict:
        """
        target: ailab | human | system  — پیشنهادِ diffِ سطح ۲ (هرگز اجرای خودکار).
        """
        if self.patch_manager is None:
            return {"ok": False, "reason": "patch manager فعال نیست."}
        res = self.patch_manager.generate_patch(f"[AI-Lab → {target}] {issue}")
        if self.db is not None and res.get("ok"):
            try:
                self.db.add_ailab_proposal(target, issue, res.get("path"))
            except Exception:
                pass
        return res
