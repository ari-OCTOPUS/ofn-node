#!/usr/bin/env python3
"""
client.py — کلاینت LLM حداقلی (stdlib، بدون SDK) برای لوپ مناظره و Governor.

قراردادهای سخت:
  - model و base_url فقط از budgets.yaml (routing.econ / routing.reason) — هرگز هاردکد
    (aliasهای deepseek-chat/reasoner از 2026-07-24 بازنشسته‌اند؛ فایل الان v4-flash دارد).
  - کلید فقط از DEEPSEEK_API_KEY. fallback به ANTHROPIC_API_KEY ممنوع — در استک
    control-brain آن متغیر عمداً حامل کلید DeepSeek برای مسیر anthropic-سازگار است و
    اتکای کور به آن دقیقاً همان تلهٔ نشت است (پک B.1).
  - گارد نشت: base_url باید شامل api.deepseek.com باشد وگرنه RefuseToSend.
  - متر بدون «or 0»: پاسخ بدون usage در مسیر زنده = TelemetryError (نه صفر بی‌صدا).
  - قیمت قفل‌نشده = PriceNotLocked؛ قیمت از کلیدهای price_in/price_out خود budgets.yaml
    (پیشنهاد diff موجود است) — تا مالک بعد از platform.deepseek.com قفل نکند، call زنده نداریم.
  - est همیشه بدترین‌حالت: توکن‌های reasoning هم شارژ می‌شوند (پک B.1).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "budget"))
import opslib  # noqa: E402


class RefuseToSend(RuntimeError):
    """گارد نشت/پیکربندی — عمداً قبل از هر بایت شبکه."""


class PriceNotLocked(RuntimeError):
    """قیمت [EST] هنوز در budgets.yaml قفل نشده (V1) — call زنده ممنوع."""


class TelemetryError(RuntimeError):
    """پاسخ بدون usage — متر کور می‌شود؛ صفرِ بی‌صدا ممنوع."""


def extract_json(text: str) -> dict[str, Any]:
    """JSON را از پاسخ مدل بیرون می‌کشد (حصار ```json / نثر اطراف را تحمل می‌کند)."""
    s = text.strip()
    i, j = s.find("{"), s.rfind("}")
    if i == -1 or j == -1:
        raise ValueError(f"no JSON object in model reply: {s[:120]!r}")
    return json.loads(s[i:j + 1])


class DeepSeekClient:
    """یک client، base_url از فایل. transport تزریقی = تست آفلاین بدون کلید/شبکه ($0)."""

    def __init__(self, role: str = "econ",
                 transport: Callable[[dict], dict] | None = None) -> None:
        routing = opslib.load_budgets().get("routing", {})
        cfg = routing.get(role)
        if not cfg:
            raise RefuseToSend(f"routing.{role} در budgets.yaml نیست")
        self.role = role
        self.model = cfg.get("model")
        self.base_url = str(cfg.get("base_url", "")).rstrip("/")
        self.price_in = cfg.get("price_in")     # USD per 1M — فقط از فایل
        self.price_out = cfg.get("price_out")
        self.transport = transport
        if transport is None:
            if "api.deepseek.com" not in self.base_url:
                raise RefuseToSend(
                    f"leak-guard: base_url «{self.base_url}» deepseek نیست — refusing")
            if not self.model:
                raise RefuseToSend(f"routing.{role}.model خالی است")
            if self.price_in is None or self.price_out is None:
                raise PriceNotLocked(
                    "price_in/price_out در budgets.yaml قفل نشده — اول از platform.deepseek.com "
                    "راستی‌آزمایی و با verdict اضافه کن (پیشنهاد: budgets-proposed-diff.md)")
            self.api_key = os.environ.get("DEEPSEEK_API_KEY")
            if not self.api_key:
                raise RefuseToSend("DEEPSEEK_API_KEY تنظیم نیست (fallback به کلید دیگر ممنوع)")

    def est_worst_case(self, prompt_chars: int, max_tokens: int) -> float:
        """تخمین بدترین‌حالت USD: ورودی ~۳ کاراکتر/توکن + خروجی کامل با سربار reasoning ×۱.۵."""
        pin = float(self.price_in or 0.0)
        pout = float(self.price_out or 0.0)
        return (prompt_chars / 3.0) / 1e6 * pin + (max_tokens * 1.5) / 1e6 * pout

    def complete(self, system: str, user: str, max_tokens: int = 1024,
                 temperature: float = 0.7) -> dict[str, Any]:
        body = {
            "model": self.model or "stub",
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if self.transport is not None:
            raw = self.transport(body)
        else:
            req = urllib.request.Request(
                self.base_url + "/chat/completions",
                data=json.dumps(body).encode("utf-8"),
                headers={"Authorization": f"Bearer {self.api_key}",
                         "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as resp:  # pragma: no cover
                raw = json.loads(resp.read().decode("utf-8"))
        text = (raw.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""
        usage = raw.get("usage")
        if self.transport is None and not usage:
            raise TelemetryError("پاسخ بدون usage — متر کور؛ call را شکست‌خورده حساب کن")
        usage = usage or {}
        tin = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
        tout = usage.get("completion_tokens") or usage.get("output_tokens") or 0
        if self.transport is None and (tin + tout) == 0:
            raise TelemetryError("usage صفر/ناقص — صفر بی‌صدا ممنوع (تلهٔ or 0)")
        cost = (tin / 1e6) * float(self.price_in or 0.0) \
            + (tout / 1e6) * float(self.price_out or 0.0)
        return {"text": text, "model": self.model, "tokens_in": tin, "tokens_out": tout,
                "cost_usd": cost, "stub": self.transport is not None}
