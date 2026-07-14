"""
llm/glm_client.py — Client for GLM (Z.ai / BigModel) API.

GLM is used for: mathematical analysis, verification, reporting.
Compatible with the OpenAI-style chat completions endpoint.
"""
from __future__ import annotations
import httpx
from .base_client import BaseLLMClient, to_dicts
from config.settings import LLMConfig


class GLMClient(BaseLLMClient):
    name = "GLM"

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig()
        self.base_url = self.config.glm_base_url.rstrip("/")
        self.api_key = self.config.glm_api_key
        self.model = self.config.glm_model

    @property
    def available(self) -> bool:
        return self.config.glm_available

    def chat(self, messages, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        if not self.api_key:
            return self._offline_msg()

        # سقفِ بودجه‌ی روزانه (اجرای ماهانه): وقتی سقفِ ابری پر شد، این کلاینت
        # یک پیامِ «[...]» برمی‌گرداند تا caller (autoloop/router) به Ollama/heuristic
        # سقوط کند — هر مسیرِ ورودی، نه فقط router، مهار می‌شود.
        try:
            from brain import budget
            if not budget.cloud_allowed():
                return "[GLM budget — سقفِ روزانه‌ی تماسِ ابری پر شد؛ محلی/heuristic]"
            budget.record_call("glm")
        except Exception:
            pass  # نبودِ ماژولِ بودجه هرگز مسیرِ اصلی را نمی‌شکند

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": to_dicts(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            from config.settings import GLM_TIMEOUT
            with httpx.Client(timeout=GLM_TIMEOUT) as client:
                resp = client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            return f"[GLM HTTP {e.response.status_code}]: {self._safe_err(e.response.text)}"
        except Exception as e:
            return f"[GLM error]: {type(e).__name__}: {self._safe_err(str(e))}"

    def _safe_err(self, text: str) -> str:
        """پیام خطا بدون نشت کلید API (بدنه‌ی خطای سرور ممکن است کلید را echo کند)."""
        if self.api_key:
            text = text.replace(self.api_key, "***")
        return text[:200]

    def _offline_msg(self) -> str:
        return ("[GLM offline — no API key set. "
                "Set GLM_API_KEY in .env to enable. "
                "Running in mock mode.]")


class GLMClientSync(GLMClient):
    """Alias for clarity — the base client is already synchronous."""
    pass
