"""
llm/langchain_models.py — Adapts GLM and Fugu to LangChain ChatModel interface.

Both GLM and Fugu expose OpenAI-compatible APIs, so we use ChatOpenAI
with custom base_url. This enables:
    - LangGraph tool calling
    - Structured output
    - Native LangChain integration
    - Conversation memory
"""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from config.settings import LLMConfig


def get_glm_chat(config: LLMConfig | None = None, temperature: float = 0.7):
    """
    Get a LangChain ChatModel configured for GLM (Z.ai / BigModel).

    GLM is OpenAI-compatible, so we use ChatOpenAI with a custom base_url.
    """
    from langchain_openai import ChatOpenAI

    cfg = config or LLMConfig()
    if not cfg.glm_api_key:
        raise ValueError(
            "GLM_API_KEY not set. Set it in .env or use mock mode."
        )
    return ChatOpenAI(
        model=cfg.glm_model,
        api_key=cfg.glm_api_key,
        base_url=cfg.glm_base_url,
        temperature=temperature,
        max_tokens=2000,
    )


def get_fugu_chat(config: LLMConfig | None = None, temperature: float = 0.9):
    """
    Get a LangChain ChatModel configured for Sakana Fugu.

    Fugu is also OpenAI-compatible. Higher temperature for creative tasks.
    """
    from langchain_openai import ChatOpenAI

    cfg = config or LLMConfig()
    if not cfg.fugu_api_key:
        raise ValueError(
            "FUGU_API_KEY not set. Set it in .env or use mock mode."
        )
    return ChatOpenAI(
        model=cfg.fugu_model,
        api_key=cfg.fugu_api_key,
        base_url=cfg.fugu_base_url,
        temperature=temperature,
        max_tokens=2000,
    )


def get_chat_model(task: str = "analysis",
                   config: LLMConfig | None = None,
                   temperature: float = 0.7):
    """
    Route to the appropriate ChatModel based on task type.
    Falls back gracefully: preferred → other → raises if no keys.

    task routing matches llm/router.py conventions.
    """
    cfg = config or LLMConfig()

    routing = {
        "analysis": "fugu", "verify": "glm", "math": "glm",
        "report": "fugu", "orchestrate": "fugu",
        "geometry": "fugu", "creative": "fugu", "analogy": "fugu",
        "explore": "fugu", "detect": "fugu",
    }

    preferred = routing.get(task, "glm")

    # Try preferred first
    try:
        if preferred == "glm" and cfg.glm_api_key:
            return get_glm_chat(cfg, temperature)
        if preferred == "fugu" and cfg.fugu_api_key:
            return get_fugu_chat(cfg, temperature)
    except ValueError:
        pass

    # Fallback to the other
    if cfg.glm_api_key:
        return get_glm_chat(cfg, temperature)
    if cfg.fugu_api_key:
        return get_fugu_chat(cfg, temperature)

    raise ValueError(
        "No LLM API key configured. Set GLM_API_KEY or FUGU_API_KEY in .env"
    )


def get_mock_chat():
    """
    Get a lightweight mock ChatModel for offline testing.
    Uses ChatLlamaCpp if a local model exists, else returns a
    simple fake that echoes structured responses.
    """
    from langchain_core.language_models import BaseChatModel
    from langchain_core.messages import AIMessage, BaseMessage
    from langchain_core.outputs import ChatGeneration, ChatResult

    class MockChatModel(BaseChatModel):
        @property
        def _llm_type(self) -> str:
            return "mock"

        def _generate(self, messages: list[BaseMessage], stop=None, **kwargs):
            # Build a contextual mock response
            last_msg = messages[-1].content if messages else ""
            last_lower = last_msg.lower()

            if "shadow" in last_lower or "detect" in last_lower:
                text = ("**[MOCK]** ساختار زمانی قابل‌تشخیص است (λρ≠0). "
                        "E_shadow > 0 نشان می‌دهد بُعد پنهان وجود دارد.")
            elif "verify" in last_lower or "anchor" in last_lower:
                text = ("**[MOCK]** همه‌ی لنگرها PASS شدند. "
                        "Δ_self=0.1225, E_shadow=0.0126.")
            elif "reflect" in last_lower or "quality" in last_lower:
                text = "**[MOCK]** کیفیت: ACCEPT. اعداد سازگار با لنگرها."
            elif "hypoth" in last_lower:
                text = "**[MOCK]** hypotheses: تست داده‌ی Lorenz با σ_ζ=0.02."
            else:
                text = f"**[MOCK MODE]** پیام دریافت شد ({len(last_msg)} کاراکتر)."

            msg = AIMessage(content=text)
            return ChatResult(generations=[ChatGeneration(message=msg)])

    return MockChatModel()


def get_default_chat(task: str = "analysis",
                     config: LLMConfig | None = None,
                     temperature: float = 0.7):
    """
    Get the best available chat model.
    Priority: Fugu → GLM → Mock
    """
    cfg = config or LLMConfig()

    # سقفِ بودجه‌ی روزانه: مسیرِ langchain (گرافِ دستی) هم مثلِ کلاینت‌های httpx
    # زیرِ سقف می‌رود؛ وگرنه یک مسیرِ ابریِ بی‌بودجه بود (یافته‌ی بازبینی).
    try:
        from brain import budget
        if not budget.cloud_allowed():
            return get_mock_chat()
        budget.record_call("langchain")
    except Exception:
        pass

    # Try real APIs
    try:
        return get_chat_model(task, cfg, temperature)
    except ValueError:
        pass

    # Final fallback: mock
    return get_mock_chat()


if __name__ == "__main__":
    from config.settings import get_llm_config

    cfg = get_llm_config()
    print(f"GLM key: {'set' if cfg.glm_api_key else 'NOT set'}")
    print(f"Fugu key: {'set' if cfg.fugu_api_key else 'NOT set'}")

    print("\nTesting mock chat model:")
    mock = get_mock_chat()
    from langchain_core.messages import HumanMessage
    resp = mock.invoke([HumanMessage(content="E_shadow را تحلیل کن")])
    print(f"  Response: {resp.content}")
