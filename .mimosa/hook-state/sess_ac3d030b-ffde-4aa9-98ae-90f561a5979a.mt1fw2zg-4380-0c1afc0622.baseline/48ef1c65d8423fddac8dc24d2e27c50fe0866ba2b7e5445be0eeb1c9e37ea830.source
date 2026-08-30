"""
llm/ollama_client.py — کلاینتِ مدلِ محلیِ Ollama (لایه‌ی Local-First).

برای کارهای سبک/ارزان/خصوصی: خلاصه‌سازی، دسته‌بندی، بازنویسی، برچسب‌زنی، پیش‌نویس.
سخت‌افزارِ هدف: GTX 1660 Ti → مدلِ کوچکِ quantized (پیش‌فرض qwen2.5:1.5b) و
پاسخ‌های کوتاه (num_predict محدود).

در دسترس‌بودن با یک probe سبک به /api/tags سنجیده و ~۶۰ ثانیه cache می‌شود
تا هر فراخوانی یک HTTP اضافه نخورد.
"""
from __future__ import annotations

import os
import time
import logging

from .base_client import BaseLLMClient, to_dicts

logger = logging.getLogger(__name__)

_avail_cache = {"t": 0.0, "ok": False}
_AVAIL_TTL = 60.0


class OllamaClient(BaseLLMClient):
    name = "Ollama"

    def __init__(self, config=None):
        self.config = config
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
        self.timeout = float(os.getenv("OLLAMA_TIMEOUT", "60"))

    @property
    def available(self) -> bool:
        """probeِ سبک با cacheِ ۶۰ثانیه‌ای — MOCK_MODE آن را خاموش می‌کند."""
        if os.getenv("MOCK_MODE", "").lower() in ("true", "1", "yes"):
            return False
        now = time.time()
        if now - _avail_cache["t"] < _AVAIL_TTL:
            return _avail_cache["ok"]
        ok = False
        try:
            import requests
            r = requests.get(f"{self.base_url}/api/tags", timeout=3)
            ok = r.status_code == 200
        except Exception:
            ok = False
        _avail_cache["t"] = now
        _avail_cache["ok"] = ok
        return ok

    def chat(self, messages, temperature: float = 0.7, max_tokens: int = 400) -> str:
        """گفت‌وگو با مدلِ محلی. خروجیِ کوتاه (سخت‌افزارِ محدود)."""
        try:
            import requests
            r = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": to_dicts(messages),
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        # سقفِ خروجی برای latencyِ قابل‌قبول روی 1660 Ti
                        "num_predict": min(max_tokens, 400),
                    },
                },
                timeout=self.timeout,
            )
            if r.status_code != 200:
                return f"[Ollama HTTP {r.status_code}]"
            return r.json().get("message", {}).get("content", "").strip() \
                or "[Ollama empty response]"
        except Exception as e:
            logger.warning("ollama chat failed: %s", e)
            return f"[Ollama error]: {type(e).__name__}"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    c = OllamaClient()
    print("available:", c.available, "| model:", c.model)
    if c.available:
        print(c.quick("در یک جمله بگو: سایه‌ی اطلاعاتی چیست؟"))
