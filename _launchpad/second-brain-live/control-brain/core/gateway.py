# -*- coding: utf-8 -*-
"""API Gateway واحد — تنها راه آداپترها به دنیا (ARCHITECTURE §۴، ADR-004).

- llm(tier="cheap")   → DeepSeek deepseek-v4-flash
- llm(tier="escalate")→ Fugu (پشت دروازه بودجه FUGU_BUDGET_MONTHLY، پیش‌فرض $40)
- search()            → Tavily
- cache ۲۴ساعته در Memory · هر call یک ردیف usage · خطای بودجه = BudgetExceeded
فقط stdlib (urllib) — هیچ وابستگی جدید. هیچ کلیدی لاگ/echo نمی‌شود.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Optional

# قیمت تخمینی هر ۱M توکن (USD) — منبع: pricing رسمی 2026-07
_PRICES = {
    "deepseek": (0.14, 0.28),          # deepseek-v4-flash in/out — [VERIFIED 2026-07-07 api-docs] cache-hit in $0.0028؛ aliasها از 2026-07-24 بازنشسته
    "fugu": (5.00, 30.00),             # fugu-ultra rates (محافظه‌کارانه برای هر دو)
}


class BudgetExceeded(RuntimeError):
    """سقف ماهانه پر شده — caller باید به cheap برگردد یا به ادمین هشدار بدهد."""


class GatewayError(RuntimeError):
    pass


def _post_json(url: str, payload: dict, headers: dict, timeout: int = 90) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read(300).decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            pass
        raise GatewayError(f"HTTP {e.code}: {body[:200]}") from None
    except Exception as e:  # noqa: BLE001
        raise GatewayError(str(e)[:200]) from None


class Gateway:
    def __init__(self, memory, env: Optional[dict] = None):
        self.mem = memory
        e = env or os.environ
        self._ds_key = e.get("DEEPSEEK_API_KEY", "").strip()
        self._fugu_key = e.get("SAKANA_API_KEY", "").strip()
        self._tavily_key = e.get("TAVILY_API_KEY", "").strip()
        self.fugu_budget = float(e.get("FUGU_BUDGET_MONTHLY", "40"))
        self.ds_daily_budget = float(e.get("DEEPSEEK_BUDGET_DAILY", "3"))
        # برای تست: قابل تعویض
        self._post = _post_json

    # ---------------- LLM ----------------
    def llm(self, prompt: str, system: str = "", tier: str = "cheap",
            business: str = "", max_tokens: int = 900, use_cache: bool = True) -> str:
        key = self.mem.cache_key(f"{tier}|{system}|{prompt}"[:4000])
        if use_cache:
            hit = self.mem.cache_get(key)
            if hit:
                return hit
        if tier == "escalate":
            text = self._call_fugu(prompt, system, business, max_tokens)
        else:
            text = self._call_deepseek(prompt, system, business, max_tokens)
        if use_cache and text:
            self.mem.cache_put(key, text)
        return text

    def _messages(self, prompt: str, system: str):
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        return msgs

    def _record(self, provider: str, usage: dict, business: str) -> None:
        tin = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
        tout = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
        # Fugu: توکن‌های orchestration هم واقعی‌اند (pricing رسمی) — جمعشان کن
        det_in = (usage.get("input_tokens_details") or {})
        det_out = (usage.get("output_tokens_details") or {})
        tin += int(det_in.get("orchestration_input_tokens") or 0)
        tout += int(det_out.get("orchestration_output_tokens") or 0)
        pin, pout = _PRICES[provider]
        cost = tin / 1e6 * pin + tout / 1e6 * pout
        self.mem.usage_add(provider, tin, tout, round(cost, 6), business)

    def _call_deepseek(self, prompt, system, business, max_tokens) -> str:
        if not self._ds_key:
            raise GatewayError("DEEPSEEK_API_KEY تنظیم نیست (حالت آفلاین)")
        if self.mem.day_cost("deepseek") >= self.ds_daily_budget:
            raise BudgetExceeded(f"سقف روزانه DeepSeek (${self.ds_daily_budget}) پر شد")
        data = self._post("https://api.deepseek.com/chat/completions",
                          {"model": "deepseek-v4-flash", "max_tokens": max_tokens,
                           "messages": self._messages(prompt, system)},
                          {"Authorization": f"Bearer {self._ds_key}"})
        self._record("deepseek", data.get("usage") or {}, business)
        return (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()

    def _call_fugu(self, prompt, system, business, max_tokens) -> str:
        # قاعدهٔ سخت privacy (کشف pass-2، C17): pool ی Fugu Ultra ثابت است و opt-out ندارد
        # → دیتای Project-F هرگز به Fugu نمی‌رود. escalation آن فقط مسیر عادی/محلی.
        if business == "projectf":
            raise GatewayError("Project-F به Fugu نمی‌رود (قاعدهٔ privacy — pool ثابت Ultra)")
        if not self._fugu_key:
            raise GatewayError("SAKANA_API_KEY تنظیم نیست")
        if self.mem.month_cost("fugu") >= self.fugu_budget:
            raise BudgetExceeded(f"سقف ماهانه Fugu (${self.fugu_budget}) پر شد — escalation قفل")
        data = self._post("https://api.sakana.ai/v1/chat/completions",
                          {"model": os.environ.get("FUGU_MODEL", "fugu"),
                           "max_tokens": max_tokens,
                           "messages": self._messages(prompt, system)},
                          {"Authorization": f"Bearer {self._fugu_key}"})
        self._record("fugu", data.get("usage") or {}, business)
        return (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()

    # ---------------- Web search ----------------
    def search(self, query: str, business: str = "", n: int = 5) -> list:
        """Tavily → [{title,url,content}] — با cache ۲۴ساعته."""
        key = self.mem.cache_key("tavily|" + query)
        hit = self.mem.cache_get(key)
        if hit:
            return json.loads(hit)
        if not self._tavily_key:
            return []
        data = self._post("https://api.tavily.com/search",
                          {"api_key": self._tavily_key, "query": query,
                           "max_results": n, "search_depth": "basic"}, {})
        out = [{"title": r.get("title", ""), "url": r.get("url", ""),
                "content": (r.get("content") or "")[:800]}
               for r in (data.get("results") or [])]
        self.mem.cache_put(key, json.dumps(out, ensure_ascii=False))
        return out

    # ---------------- وضعیت برای /status ----------------
    def budget_line(self) -> str:
        return (f"💰 DeepSeek امروز: ${self.mem.day_cost('deepseek'):.2f}/{self.ds_daily_budget:.0f}"
                f" · Fugu ماه: ${self.mem.month_cost('fugu'):.2f}/{self.fugu_budget:.0f}")
