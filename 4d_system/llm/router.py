"""
llm/router.py — Routes requests to the right LLM based on task type.

    Analysis / verification / math  →  GLM
    Creative / geometric / analogy   →  Fugu
    (fallback if offline)            →  Mock

The router also provides a unified `ask()` that picks the best available model.
"""
from __future__ import annotations

from .base_client import BaseLLMClient
from .glm_client import GLMClient
from .fugu_client import FuguClient
from config.settings import LLMConfig


class MockClient(BaseLLMClient):
    """Produces canned but structured responses for UI testing without API keys."""
    name = "Mock"

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig()

    @property
    def available(self) -> bool:
        return True

    def chat(self, messages, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        # Build a contextual mock response based on the last user message
        user_msg = ""
        for m in reversed(messages):
            if isinstance(m, dict):
                role = m.get("role", "")
                content = m.get("content", "")
            else:
                role = m.role
                content = m.content
            if role == "user":
                user_msg = content.lower()
                break

        if "verify" in user_msg or "anchor" in user_msg:
            return self._mock_verify()
        if "shadow" in user_msg or "detect" in user_msg:
            return self._mock_detect()
        if "geometry" in user_msg or "tesseract" in user_msg or "dimension" in user_msg:
            return self._mock_geometry()
        if "report" in user_msg or "summary" in user_msg:
            return self._mock_report()
        return self._mock_generic()

    def _mock_verify(self) -> str:
        return (
            "**[MOCK MODE — Verifier]**\n\n"
            "Anchor verification (simulated):\n"
            "- P = 0.00325184 ✓ PASS\n"
            "- S = 0.01081296 ✓ PASS\n"
            "- Δ_self = 0.122520 ✓ PASS\n"
            "- E_shadow = 0.012553 ✓ PASS\n"
            "- identity 0.135073 = E_shadow + Δ_self ✓ PASS\n\n"
            "All anchors reproduced. Set GLM_API_KEY for real analysis."
        )

    def _mock_detect(self) -> str:
        return (
            "**[MOCK MODE — Detector]**\n\n"
            "Shadow analysis of input series:\n"
            "- temporal MI ≈ 0.0094 nat/step\n"
            "- lag-1 autocorrelation = 0.136\n"
            "- verdict: **hidden dimension DETECTED** (λρ≠0 equivalent)\n\n"
            "The series shows non-trivial temporal structure consistent "
            "with an underlying hidden state. Set GLM_API_KEY for real analysis."
        )

    def _mock_geometry(self) -> str:
        return (
            "**[MOCK MODE — Analyst]**\n\n"
            "Geometric interpretation:\n"
            "The detected temporal redundancy is analogous to seeing the "
            "3D shadow of a 4D tesseract. Just as a Flatlander sees a "
            "changing 2D shape when a 3D object rotates, we see temporal "
            "correlations as the 'shadow' of a hidden state dimension.\n\n"
            "Key connection: E_shadow > 0 ⟺ λρ ≠ 0 mirrors Takens' theorem "
            "(deterministic structure is recoverable from a scalar time series)."
        )

    def _mock_report(self) -> str:
        return (
            "**[MOCK MODE — Reporter]**\n\n"
            "## Experiment Report Card\n\n"
            "| Quantity | Value |\n|---|---|\n"
            "| E_shadow | 0.012553 nat/step |\n"
            "| Δ_self | 0.122520 nat/step |\n"
            "| I_pred | 0.0144179 nat |\n"
            "| Verdict | hidden structure detected |\n\n"
            "Set GLM_API_KEY + FUGU_API_KEY for real multi-agent analysis."
        )

    def _mock_generic(self) -> str:
        return (
            "[MOCK MODE] I'm running without API keys. "
            "Your question was received. Set GLM_API_KEY and/or FUGU_API_KEY "
            "in .env for real LLM-powered analysis."
        )


class LLMRouter:
    """
    Central router. Holds one client per model and picks the right one.

    Usage:
        router = LLMRouter()
        response = router.ask("What is E_shadow?", task="analysis")
    """

    # task → preferred model — دکترینِ Local-First:
    #   کارهای سبک/ارزان/خصوصی → Ollama (رایگان، محلی)
    #   کارهای سختِ مهندسی/خلاقانه → Fugu (گران، عمیق)
    #   راستی‌آزمایی/ریاضیِ دقیق → GLM
    TASK_ROUTING = {
        # ── CLOUD: مهندسیِ عمیق (ارزشِ هزینه دارد) ──
        "analysis":    "fugu",   # مغز اصلی: تحلیل
        "detect":      "fugu",   # تشخیص
        "report":      "fugu",   # گزارش‌نویسی
        "orchestrate": "fugu",   # رهبری
        "explore":     "fugu",   # کاوش
        "geometry":    "fugu",   # هندسه
        "creative":    "fugu",   # خلاقیت
        "analogy":     "fugu",   # تمثیل
        "verify":      "glm",    # کمکی: راستی‌آزمایی عددی
        "math":        "glm",    # کمکی: ریاضی دقیق
        # ── LOCAL: سبک/روتین/خصوصی (رایگان با Ollama) ──
        "summarize":   "ollama",
        "classify":    "ollama",
        "rewrite":     "ollama",
        "translate":   "ollama",
        "extract":     "ollama",
        "tag":         "ollama",
        "draft":       "ollama",
        "microcopy":   "ollama",
        "insight":     "ollama",  # بینشِ کوتاهِ لوپ — کیفیتِ «خوبِ کافی»
    }

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig()
        self.glm  = GLMClient(self.config)
        # 2026-08-13 (رأی مالک): با FUGU_VIA_CENTRAL_GATE=1، self.fugu به‌جای
        # تماسِ مستقیمِ httpx به api.sakana.ai از دروازهٔ مرکزیِ اختاپوس رد
        # می‌شود (paid-calls.jsonl مشترک، fugu_quota مشترک). پیش‌فرض خاموش —
        # رفتارِ همیشگی دست‌نخورده می‌ماند مگر صریحاً روشن شود.
        import os
        if str(os.environ.get("FUGU_VIA_CENTRAL_GATE", "")).strip() == "1":
            from .central_gate_client import CentralGateClient
            self.fugu = CentralGateClient(tier="primary", task="fourd_llm")
        else:
            self.fugu = FuguClient(self.config)
        from .ollama_client import OllamaClient
        self.ollama = OllamaClient(self.config)
        self.mock = MockClient(self.config)

    def route_explain(self, task: str = "analysis") -> tuple[BaseLLMClient, str]:
        """انتخابِ کلاینت + دلیلِ شفافِ تصمیم (explainable routing)."""
        preferred = self.TASK_ROUTING.get(task, "fugu")

        # سقفِ بودجه‌ی روزانه: اگر انتخابِ ترجیحی ابری است ولی سقفِ ابری پر شده،
        # پیش از هر چیز به محلیِ رایگان (Ollama) سقوط کن — اجرای ماهانه ارزان می‌ماند.
        if preferred in ("fugu", "glm"):
            try:
                from brain import budget
                if not budget.cloud_allowed():
                    if self.ollama.available:
                        return self.ollama, (f"BUDGET: سقفِ روزانه‌ی ابری پر شد؛ "
                                             f"«{task}» → {self.ollama.model} (محلیِ رایگان)")
                    return self.mock, "BUDGET: سقفِ ابری پر و Ollama خاموش → mock"
            except Exception:
                pass

        if preferred == "ollama":
            if self.ollama.available:
                return self.ollama, f"LOCAL: taskِ سبک «{task}» → {self.ollama.model} (رایگان)"
            # fallbackِ ابریِ ارزان‌تر اول
            if self.glm.available:
                return self.glm, f"CLOUD-fallback: Ollama خاموش؛ «{task}» → GLM"
            if self.fugu.available:
                return self.fugu, f"CLOUD-fallback: Ollama/GLM خاموش؛ «{task}» → Fugu"
            return self.mock, "MOCK: هیچ مدلی در دسترس نیست"

        if preferred == "fugu" and self.fugu.available:
            return self.fugu, f"CLOUD: taskِ سختِ «{task}» → Fugu (عمقِ مهندسی)"
        if preferred == "glm" and self.glm.available:
            return self.glm, f"CLOUD: «{task}» → GLM (دقتِ عددی)"

        # fallback chain
        if self.fugu.available:
            return self.fugu, f"CLOUD-fallback: «{task}» → Fugu"
        if self.glm.available:
            return self.glm, f"CLOUD-fallback: «{task}» → GLM"
        if self.ollama.available:
            return self.ollama, f"LOCAL-fallback: cloud خاموش؛ «{task}» → {self.ollama.model}"
        return self.mock, "MOCK: هیچ مدلی در دسترس نیست"

    def get_client(self, task: str = "analysis") -> BaseLLMClient:
        """Pick the best available client for a task (Local-First doctrine)."""
        client, reason = self.route_explain(task)
        import logging
        logging.getLogger(__name__).info("route: %s", reason)
        return client

    def ask(self, prompt: str, system: str = "", task: str = "analysis",
            temperature: float = 0.7) -> str:
        """One-shot ask with automatic routing."""
        client = self.get_client(task)
        return client.quick(prompt, system=system, temperature=temperature)

    @property
    def status(self) -> dict:
        """Status report for the UI."""
        ollama_ok = self.ollama.available
        any_live = self.glm.available or self.fugu.available or ollama_ok
        return {
            "fugu": "online" if self.fugu.available else "offline",
            "glm":  "online" if self.glm.available else "offline",
            "ollama": f"online ({self.ollama.model})" if ollama_ok else "offline",
            "mode": "live" if any_live else "mock",
        }


_router_singleton: LLMRouter | None = None


def get_router(fresh: bool = False) -> LLMRouter:
    """Factory for convenience — برمی‌گرداند singleton مشترک.

    fresh=True یک instance جدید می‌سازد (برای تست/mock کردن).
    """
    global _router_singleton
    if fresh:
        return LLMRouter()
    if _router_singleton is None:
        _router_singleton = LLMRouter()
    return _router_singleton


if __name__ == "__main__":
    router = get_router()
    print("=== Router status ===")
    for k, v in router.status.items():
        print(f"  {k}: {v}")

    print("\n=== Mock test ===")
    print(router.ask("verify the anchors", task="verify"))
