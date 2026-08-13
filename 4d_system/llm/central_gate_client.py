"""
llm/central_gate_client.py — 4d_system LLM client routed through Octopus's
central paid-LLM gate (_ops/cortex/model_router.py), instead of a direct
httpx call to api.sakana.ai.

۲۰۲۶-۰۸-۱۳ (رأیِ مالک): بازرسیِ ۲۰۲۶-۰۸-۱۳ نشان داد 4d_system مثلِ چند
زیرسیستمِ دیگر کلاینتِ مستقلِ خودش را دارد که هیچ‌وقت در `paid-calls.jsonl`
مرکزی ثبت نمی‌شود. این کلاینت همان قراردادِ BaseLLMClient را پیاده می‌کند
(هر caller موجود — agents/base.py، llm/router.py — بدونِ تغییر کار می‌کند)
ولی درخواست را از دروازهٔ مرکزی رد می‌کند: هر تماس در همان
fugu_quota/paid-calls.jsonl که بقیهٔ ارگانیسم پاسخ‌گویش است ثبت می‌شود.

پیش‌فرض: خاموش. فقط وقتی FUGU_VIA_CENTRAL_GATE=1 باشد در llm/router.py
جایگزینِ FuguClient می‌شود (llm/router.py را ببین). طبقِ DEPRECATED.md
خودِ 4d_system («هیچ import از _ops/ به 4d_system وجود ندارد»)، این
کلاینت فقط وقتی import را واقعاً می‌کوشد که کسی صدایش بزند — نه در
import-time — تا حتی وقتیِ سازمان/_ops قابل‌دسترس نیست، خودِ ماژول
بدون خطا import شود.

محدودیتِ صریح (طبقِ ممیزیِ ۲۰۲۶-۰۸-۱۳): model_router.ask() یک تماسِ
تک‌مرحله‌ای (system+prompt) است — نه توکن‌سازی/ابزار/جریانِ چندنوبتیِ
LangChain. اگر caller ای به قابلیت‌های LangGraph (tool-calling، streaming)
نیاز دارد، این کلاینت مناسب نیست — llm/langchain_models.py عمداً از این
مهاجرت بیرون ماند (تصمیمِ جداگانه لازم دارد).
"""
from __future__ import annotations

from .base_client import BaseLLMClient, to_dicts


class CentralGateClient(BaseLLMClient):
    name = "CentralGate(DeepSeek/Fugu)"

    def __init__(self, tier: str = "primary", task: str = "fourd_llm"):
        # tier="primary" یعنی Fugu (هم‌ارزِ FuguClient که جایگزینش می‌شود)؛
        # caller می‌تواند tier="secondary" (DeepSeek) هم بخواهد.
        self._tier = tier
        self._task = task

    @property
    def available(self) -> bool:
        # فقط قابلِ import بودنِ model_router را چک کن — کلید/سهمیه را
        # خودِ model_router در لحظهٔ تماس تعیین می‌کند (fail-soft آنجا).
        try:
            self._import_router()
            return True
        except Exception:  # noqa: BLE001
            return False

    @staticmethod
    def _import_router():
        import sys
        from pathlib import Path
        root = Path(__file__).resolve().parent.parent.parent  # 4d_system/llm/.. .. = repo root
        cortex_dir = str(root / "_ops" / "cortex")
        if cortex_dir not in sys.path:
            sys.path.insert(0, cortex_dir)
        import model_router  # noqa: WPS433
        return model_router

    def chat(self, messages, temperature: float = 0.9, max_tokens: int = 4000) -> str:
        dicts = to_dicts(messages)
        system_parts = [m["content"] for m in dicts if m.get("role") == "system"]
        transcript_parts = [
            f"{m.get('role', 'user')}: {m.get('content', '')}"
            for m in dicts if m.get("role") != "system"
        ]
        system = "\n".join(system_parts)
        prompt = "\n\n".join(transcript_parts) or "(empty)"

        try:
            model_router = self._import_router()
        except Exception as e:  # noqa: BLE001
            return f"[CentralGate offline — model_router not reachable: {type(e).__name__}]"

        try:
            res = model_router.ask(self._task, prompt, system=system,
                                    max_tokens=max_tokens, tier=self._tier)
        except Exception as e:  # noqa: BLE001
            return f"[CentralGate error]: {type(e).__name__}: {str(e)[:200]}"

        if not isinstance(res, dict) or not res.get("ok"):
            reason = (res or {}).get("reason", "no-answer") if isinstance(res, dict) else "no-answer"
            return f"[CentralGate — {self._task} blocked: {reason}]"
        return str(res.get("text") or "")
