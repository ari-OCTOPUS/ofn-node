"""
agents.py — سه ایجنت با نقش‌های تفکیک‌شده.
چک‌لیست #۵ (تفکیک وظایف / separation of duties) و #۶ (supervisor/worker).

هیچ ایجنتی کنترل کامل ندارد:
  - Researcher فقط جمع‌آوری می‌کند (ابزار: web_search_mock)
  - Analyst فقط تحلیل می‌کند (ابزار: summarize روی متن، بدون دسترسی به جستجو)
  - Supervisor فقط داوری/کنترل می‌کند (approve/reject/halt) و خودش تولید محتوا نمی‌کند
"""
from __future__ import annotations

from src.llm import LLMClient
from src.budget import BudgetLedger
from src.tools import ToolGateway


class Agent:
    name: str = "agent"
    system: str = ""

    def __init__(self, llm: LLMClient, ledger: BudgetLedger, gateway: ToolGateway,
                 audit, ks, prompt_store=None):
        self.llm = llm
        self.ledger = ledger
        self.gateway = gateway
        self.audit = audit
        self.ks = ks
        self.prompt_store = prompt_store   # فاز ۳: پرامپتِ نسخه‌دار/خوداپدیت‌شده

    def system_prompt(self) -> str:
        """پرامپتِ فعال از انبار (اگر باشد)، وگرنه پیش‌فرضِ کلاس."""
        if self.prompt_store is not None:
            p = self.prompt_store.get_active(self.name)
            if p:
                return p
        return self.system

    def _think(self, prompt: str) -> str:
        """یک فراخوانی مدل با اعمال kill-switch + بودجه + ثبت ممیزی."""
        self.ks.check()                      # چک‌لیست #۲
        self.ledger.precheck(self.name)      # چک‌لیست #۱ (قبل)
        res = self.llm.complete(self.system_prompt(), prompt)
        cost = self.ledger.record(           # چک‌لیست #۱ (بعد + قطع خودکار)
            self.name, res.input_tokens, res.output_tokens)
        self.audit.log("agent_call", self.name,
                       tokens=f"{res.input_tokens}+{res.output_tokens}",
                       cost_usd=round(cost, 5), mock=res.mock)
        return res.text


class Researcher(Agent):
    name = "researcher"
    system = ("تو ایجنت Researcher هستی. فقط اطلاعات جمع‌آوری و گزارش می‌کنی. "
              "منابع نامطمئن را صریح پرچم بزن. تحلیل یا نتیجه‌گیری نهایی نکن.")

    def run(self, topic: str) -> str:
        raw = self.gateway.call(self.name, "web_search_mock", query=topic)  # ابزار scoped
        return self._think(f"موضوع: {topic}\nداده‌ی خام جستجو:\n{raw}\n"
                           "این‌ها را در چند بند منظم گزارش کن.")


class Analyst(Agent):
    name = "analyst"
    system = ("تو ایجنت Analyst هستی. فقط بر اساس یافته‌های داده‌شده تحلیل و خلاصه می‌کنی. "
              "حق جستجوی جدید نداری. ادعاهای اثبات‌نشده را به‌عنوان «نیازمند راستی‌آزمایی» علامت بزن.")

    def run(self, findings: str) -> str:
        return self._think(f"یافته‌های Researcher:\n{findings}\n"
                           "یک خلاصه‌ی تحلیلیِ کوتاه و صادقانه بده.")


class Supervisor(Agent):
    name = "supervisor"
    system = ("تو ایجنت Supervisor/ناظر هستی. خروجی Analyst را بررسی می‌کنی. "
              "اگر کیفیت قابل‌قبول است با کلمه‌ی APPROVE شروع کن، وگرنه با REJECT و دلیل کوتاه. "
              "خودت محتوای جدید تولید نکن.")

    def review(self, analysis: str) -> tuple[bool, str]:
        verdict = self._think(f"خروجی تحلیل برای بازبینی:\n{analysis}\n"
                              "آیا تأیید می‌کنی؟ با APPROVE یا REJECT پاسخ بده.")
        approved = verdict.strip().upper().startswith("APPROVE")
        # در حالت MOCK معمولاً APPROVE برنمی‌گردد؛ پیش‌فرض را قابل‌کنترل نگه می‌داریم
        if self.llm.mock:
            approved = "reject" not in analysis.lower()
        self.audit.log("supervisor_verdict", self.name, approved=approved)
        return approved, verdict
