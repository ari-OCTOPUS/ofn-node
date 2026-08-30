"""
self_improver.py — بهبودِ طراحیِ خودِ سیستم (در پس‌زمینه، شفاف، محتاط).

قواعدِ آهنین:
۱) هرگز خودکار prompt/BRAIN_PROMPT.md را تغییر نده.
۲) تغییرِ وزن محدود به ±۰.۲ در هر بازتاب.
۳) اگر داده کم بود (<۷)، بازتاب نزن.
۴) خروجی در /export دیده شود (db).
۵) تجربه‌ی کاربری تغییر نکند.
"""

from __future__ import annotations

MIN_DATA = 7
MAX_DELTA = 0.2


class SelfImprover:
    def __init__(self, db):
        self.db = db

    def collect_metrics(self, period_days: int = 14) -> dict:
        return self.db.question_quality_metrics(period_days)

    @staticmethod
    def reflect(metrics: dict, mental_model: dict | None = None) -> dict:
        """
        خالص و قاعده‌محور: از متریک‌ها پیشنهادِ تغییرِ وزن می‌سازد.
        خروجی: {ok, reason, weight_changes:{domain:delta}, suggestions:[...]}
        """
        total = metrics.get("total", 0)
        if total < MIN_DATA:
            return {"ok": False, "reason": f"داده کم است ({total}<{MIN_DATA})",
                    "weight_changes": {}, "suggestions": []}

        per_domain = metrics.get("per_domain", {})  # domain -> {asked, answered}
        changes, suggestions = {}, []
        for domain, d in per_domain.items():
            asked = d.get("asked", 0)
            if asked < 3:
                continue
            rate = d.get("answered", 0) / asked
            if rate >= 0.7:
                changes[domain] = +min(MAX_DELTA, 0.1)
                suggestions.append(f"حوزه‌ی {domain} درگیری بالا دارد ({rate:.0%}) → وزن +")
            elif rate <= 0.3:
                changes[domain] = -min(MAX_DELTA, 0.1)
                suggestions.append(f"حوزه‌ی {domain} درگیری پایین دارد ({rate:.0%}) → وزن −")

        overall = metrics.get("answer_rate")
        if overall is not None and overall < 0.4:
            suggestions.append("نرخِ پاسخِ کلی پایین است → پیام‌ها کوتاه‌تر شوند (پیشنهاد، نیاز به تأیید).")

        return {"ok": True, "reason": None, "weight_changes": changes,
                "suggestions": suggestions}

    def apply_report(self, report: dict) -> bool:
        """تغییراتِ امنِ وزن را اعمال و گزارش را ذخیره می‌کند."""
        if not report.get("ok"):
            return False
        for domain, delta in report.get("weight_changes", {}).items():
            self.db.bump_agent_weight(domain, max(-MAX_DELTA, min(MAX_DELTA, delta)))
        # پیشنهادهای متنی (مثلِ تغییرِ prompt) فقط pending ذخیره می‌شوند، نه اعمالِ خودکار
        status = "applied" if report.get("weight_changes") else "pending"
        self.db.save_improvement_report(report.get("metrics", {}),
                                        report.get("suggestions", []), status)
        return True

    def get_pending_improvements(self):
        return self.db.list_improvement_reports("pending")

    def approve_improvement(self, report_id: int) -> bool:
        return self.db.set_improvement_status(report_id, "approved")
