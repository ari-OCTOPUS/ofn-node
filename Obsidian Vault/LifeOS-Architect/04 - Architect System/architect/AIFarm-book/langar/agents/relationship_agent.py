"""relationship_agent.py — تخصص: رابطه‌ها و ارتباطِ انسانی."""

from __future__ import annotations

from .base_agent import BaseAgent


class RelationshipAgent(BaseAgent):
    name = "relationship"
    domains = ["relationships"]
    system_prompt = (
        "تو ایجنتِ رابطه‌هایِ LANGAR هستی. سؤالت درباره‌ی کیفیتِ ارتباط، صداقت، "
        "مرزها و نزدیکیِ انسانی است. یک سؤالِ مشخص و مهربان بپرس که به یک رابطه‌ی "
        "واقعی وصل باشد، بدونِ قضاوت."
    )
