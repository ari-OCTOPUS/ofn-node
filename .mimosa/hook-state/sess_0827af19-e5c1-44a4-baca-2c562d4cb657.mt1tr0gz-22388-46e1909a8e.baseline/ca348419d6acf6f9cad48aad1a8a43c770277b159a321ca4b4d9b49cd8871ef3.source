"""
llm/fugu_client.py — Client for Sakana AI Fugu API.

Fugu is used for: creative geometric interpretation, analogy generation,
and lateral-thinking analysis that benefits from diverse model perspectives.
"""
from __future__ import annotations
import httpx
from .base_client import BaseLLMClient, to_dicts
from config.settings import LLMConfig


class FuguClient(BaseLLMClient):
    name = "Fugu"

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig()
        self.base_url = self.config.fugu_base_url.rstrip("/")
        self.api_key = self.config.fugu_api_key
        self.model = self.config.fugu_model

    @property
    def available(self) -> bool:
        return self.config.fugu_available

    def chat(self, messages, temperature: float = 0.9, max_tokens: int = 4000) -> str:
        if not self.api_key:
            return self._offline_msg()

        # سقفِ بودجه‌ی روزانه (اجرای ماهانه): سقفِ پر → پیامِ «[...]» تا caller
        # به Ollama/heuristic سقوط کند (هر مسیرِ ورودی مهار می‌شود، نه فقط router).
        try:
            from brain import budget
            if not budget.cloud_allowed():
                return "[Fugu budget — سقفِ روزانه‌ی تماسِ ابری پر شد؛ محلی/heuristic]"
            budget.record_call("fugu")
        except Exception:
            pass

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": to_dicts(messages),
            "temperature": temperature,  # higher temp for creative tasks
            "max_tokens": max(max_tokens, 1000),  # Fugu needs room for reasoning
        }

        try:
            from config.settings import FUGU_TIMEOUT
            with httpx.Client(timeout=FUGU_TIMEOUT) as client:  # Fugu is slow (multi-agent reasoning)
                resp = client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            return f"[Fugu HTTP {e.response.status_code}]: {self._safe_err(e.response.text)}"
        except Exception as e:
            return f"[Fugu error]: {type(e).__name__}: {self._safe_err(str(e))}"

    def _safe_err(self, text: str) -> str:
        """پیام خطا بدون نشت کلید API (بدنه‌ی خطای سرور ممکن است کلید را echo کند)."""
        if self.api_key:
            text = text.replace(self.api_key, "***")
        return text[:200]

    def _offline_msg(self) -> str:
        return ("[Fugu offline — no API key set. "
                "Set FUGU_API_KEY in .env to enable. "
                "Running in mock mode.]")
