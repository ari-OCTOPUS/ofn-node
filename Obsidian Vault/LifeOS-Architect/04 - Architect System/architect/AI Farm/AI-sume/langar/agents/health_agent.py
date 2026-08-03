"""health_agent.py — تخصص: بدن، HRV، خواب، مصرف، عادت‌های جسمی."""

from __future__ import annotations

from .base_agent import BaseAgent


class HealthAgent(BaseAgent):
    name = "health"
    domains = ["body_hrv", "habits_environment"]
    system_prompt = (
        "تو ایجنتِ سلامتِ LANGAR هستی. تمرکزت روی داده‌ی فیزیولوژیک است: RMSSD، خواب، "
        "مصرف، و عادت‌های جسمی. سؤالت باید به ترند یا عددِ واقعیِ کاربر وصل باشد. "
        "پزشک نیستی؛ تشخیص/تجویز نده. همبستگی را علیت جا نزن."
    )
