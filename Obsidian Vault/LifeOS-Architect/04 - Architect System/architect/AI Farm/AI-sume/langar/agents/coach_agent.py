"""
coach_agent.py — ایجنتِ پیش‌فعال (proactive).

برخلافِ بقیه که «سؤال» می‌پرسند، این یکی وقتی الگوی نگران‌کننده‌ای ببیند
(مثلِ افتِ خواب + استرسِ بالا) یک «پیشنهادِ آرام» می‌دهد. داده‌محور، بدونِ
ادعای پزشکی، با احترام به قانونِ «همبستگی ≠ علیت».

در این نسخه به‌صورتِ مستقل قابلِ‌استفاده است؛ در گامِ بعدی به WorldModel وصل می‌شود.
"""

from __future__ import annotations

from .base_agent import BaseAgent


class CoachAgent(BaseAgent):
    name = "coach"
    domains = []  # توسطِ router انتخاب نمی‌شود؛ proactive فراخوانی می‌شود
    system_prompt = (
        "تو کوچِ آرامِ LANGAR هستی. بر پایه‌ی داده، یک پیشنهادِ کوچک و عملی بده "
        "(نه سؤال). آرام، بدونِ فشار، بدونِ ادعای پزشکی. تأکید کن که این یک سیگنالِ "
        "شخصی است، نه تشخیص."
    )

    def should_intervene(self, world_state: dict) -> bool:
        """قاعده‌ی ساده: افتِ خواب + استرسِ بالا → مداخله."""
        sleep = world_state.get("sleep")
        stress = world_state.get("stress")
        low_sleep = sleep is not None and sleep <= 2
        high_stress = stress is not None and stress >= 4
        return bool(low_sleep and high_stress)

    def propose(self, world_state: dict) -> str:
        ctx = {"domain": "coach", "label": "کوچ", "data": str(world_state)}
        try:
            return self.brain.ask(self._full_prompt(), ctx)
        except Exception:
            return ("سیگنال: خواب پایین و استرس بالا کنارِ هم دیده می‌شوند. "
                    "این تشخیص نیست؛ امروز را ساده بگیر و خواب را در اولویت بگذار.")
