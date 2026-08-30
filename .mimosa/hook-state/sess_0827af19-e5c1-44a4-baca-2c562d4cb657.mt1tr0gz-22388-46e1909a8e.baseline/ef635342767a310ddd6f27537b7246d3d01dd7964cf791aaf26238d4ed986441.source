"""brain.py — لایه‌ی LLMِ بک‌اند (OpenAI-compatible / Anthropic / Offline)."""

from __future__ import annotations


def _format_user(question, results, target):
    rows = "\n".join(f"[{i+1}] {r.get('title','')}: {r.get('snippet','')}"
                     for i, r in enumerate(results[:5]))
    return f"سؤال: {question}\nهدف: {target}\n\nنتایج:\n{rows or '—'}"


class OfflineBrain:
    name = "offline"

    def is_available(self):
        return True

    def ask(self, system, question, results, target="armin"):
        if not results:
            return "نتیجه‌ای از وب نبود (آفلاین). ادعای آزمون‌پذیر را خودت تعریف کن. [S]"
        lines = [f"[{i+1}] {r.get('title','')} — {r.get('snippet','')[:120]}"
                 for i, r in enumerate(results[:5])]
        return "خلاصه‌ی خام (بدونِ LLM):\n" + "\n".join(lines) + "\n[S] آزموده‌نشده."


class OpenAICompatBrain:
    name = "openai"

    def __init__(self, api_key, base_url=None, model="gpt-4o-mini"):
        self.api_key, self.base_url, self.model = api_key, base_url, model

    def is_available(self):
        return bool(self.api_key)

    def ask(self, system, question, results, target="armin"):
        import openai
        client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
        resp = client.chat.completions.create(
            model=self.model, max_tokens=400,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": _format_user(question, results, target)}])
        return (resp.choices[0].message.content or "").strip()


class AnthropicBrain:
    name = "anthropic"

    def __init__(self, api_key, model="claude-haiku-4-5-20251001"):
        self.api_key, self.model = api_key, model

    def is_available(self):
        return bool(self.api_key)

    def ask(self, system, question, results, target="armin"):
        from anthropic import Anthropic
        client = Anthropic(api_key=self.api_key)
        resp = client.messages.create(
            model=self.model, max_tokens=400, system=system,
            messages=[{"role": "user", "content": _format_user(question, results, target)}])
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()


def get_brain(settings) -> object:
    if getattr(settings, "anthropic_key", None) or getattr(settings, "claude_key", None):
        return AnthropicBrain(settings.claude_key)
    if getattr(settings, "openai_key", None):
        return OpenAICompatBrain(settings.openai_key,
                                 getattr(settings, "openai_base_url", None))
    return OfflineBrain()
