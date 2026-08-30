"""
contract.py — قراردادِ انسان‑AI (معامله‌ی دوطرفه، صریح و قابلِ‌بازبینی).

این لایه رابطه را formal می‌کند: AI چه می‌تواند، چه نمی‌تواند، چه زمانی باید بپرسد،
و چه اصولی را همیشه نگه دارد. قرارداد در config (JSON) ذخیره می‌شود و کاربر می‌تواند ببیندش.
خالص است؛ db فقط برای load/save تزریق می‌شود.
"""

from __future__ import annotations

import json

DEFAULT = {
    "ai_may": ["پژوهش", "پیشنهاد", "تحلیل", "یادآوری", "هشدار", "مستندسازیِ تصمیم"],
    "ai_may_not": ["تصمیمِ پزشکی", "اجرای خودکارِ کد", "جابه‌جاییِ پول",
                   "دست‌کاریِ احساسی", "تغییرِ خودکارِ قوانین"],
    "data_allowed": ["log", "insight", "reflection", "daily_state"],
    "data_forbidden": [],
    "ask_before": ["استفاده‌ی بیرونی از سابقه‌ی سلامت", "حذفِ داده", "اعمالِ patch"],
    "principles": [
        "عدم‌قطعیت را توضیح بده",
        "هدفِ بلندمدت را بر هوسِ کوتاه‌مدت ترجیح بده",
        "دست‌کاریِ احساسی ممنوع",
        "تصمیمِ نهایی همیشه با انسان",
        "شفافیت در دلیلِ هر پیشنهاد",
    ],
    "version": "1.0",
}


class Contract:
    def __init__(self, data: dict | None = None):
        self.data = dict(DEFAULT)
        if data:
            self.data.update(data)

    @classmethod
    def load(cls, db) -> "Contract":
        try:
            raw = db.get_config("contract")
            return cls(json.loads(raw)) if raw else cls()
        except Exception:
            return cls()

    def save(self, db) -> None:
        try:
            db.set_config("contract", json.dumps(self.data, ensure_ascii=False))
        except Exception:
            pass

    def allows(self, action: str) -> bool:
        return action not in self.data.get("ai_may_not", [])

    def must_ask(self, action: str) -> bool:
        return action in self.data.get("ask_before", [])

    def render(self) -> str:
        d = self.data
        return (
            f"📜 قراردادِ انسان‑AI (نسخه {d.get('version')})\n\n"
            "AI می‌تواند: " + "، ".join(d["ai_may"]) + "\n"
            "AI نمی‌تواند: " + "، ".join(d["ai_may_not"]) + "\n"
            "قبل از این‌ها می‌پرسد: " + "، ".join(d["ask_before"]) + "\n\n"
            "اصول:\n" + "\n".join(f"• {p}" for p in d["principles"])
        )
