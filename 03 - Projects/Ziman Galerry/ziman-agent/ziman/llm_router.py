"""روترِ مدلِ hybrid برای زیمان.

ترتیب: (۱) Ollamaِ محلی — رایگان، دادهٔ محلی می‌ماند.
        (۲) Anthropic API — فقط اگر کلید باشد و budget.can_spend() اجازه دهد.
        (۳) هیچ مسیرِ live نبود → استثنا؛ فراخوان‌کننده به قالبِ offline می‌افتد.

هیچ اکشنِ بیرونیِ دیگری ندارد (نه انتشار، نه ارسال). خرجِ API با Budget گیت می‌شود.
مسیرِ Anthropic از SDK رسمیِ `anthropic` استفاده می‌کند؛ Ollama از httpx (REST محلی).
"""
import os

from .budget import Budget


def _ollama(system, user, model, max_tokens, host):
    import httpx  # local import — تا نبودِ httpx کلِ ایجنت را نشکند
    r = httpx.post(
        f"{host.rstrip('/')}/api/chat",
        json={
            "model": model,
            "stream": False,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "options": {"num_predict": int(max_tokens)},
        },
        timeout=60,
    )
    r.raise_for_status()
    return (r.json().get("message") or {}).get("content", "").strip()


def _anthropic(system, user, model, max_tokens, budget):
    import anthropic  # official SDK — کلید از ANTHROPIC_API_KEY محیط
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=model, max_tokens=int(max_tokens),
        system=system, messages=[{"role": "user", "content": user}],
    )
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    try:
        budget.record(model, resp.usage.input_tokens, resp.usage.output_tokens)
    except Exception:  # noqa: BLE001 — ثبتِ ناموفقِ بودجه نباید خروجی را بشکند
        pass
    return text.strip()


def generate(cfg, system, user, max_tokens, budget=None, base_dir=None):
    """برمی‌گرداند (text, route). اگر هیچ مسیرِ live نبود، RuntimeError می‌دهد.

    route نمونه: "ollama:llama3.1:8b" | "api:claude-haiku-4-5".
    """
    budget = budget or Budget(cfg, base_dir=base_dir)
    gen = cfg.get("generation", {}) or {}
    route_cfg = cfg.get("routing", {}) or {}

    # (۱) Ollamaِ محلی
    if route_cfg.get("ollama_enabled", True):
        host = route_cfg.get("ollama_host", "http://127.0.0.1:11434")
        omodel = route_cfg.get("ollama_model", "llama3.1:8b")
        try:
            text = _ollama(system, user, omodel, max_tokens, host)
            if text:
                return text, f"ollama:{omodel}"
        except Exception:  # noqa: BLE001 — Ollama خاموش/نصب‌نشده → مسیرِ بعدی
            pass

    # (۲) Anthropic API — با کلید و بودجه
    api_model = gen.get("model", "claude-haiku-4-5")
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())
    if has_key and budget.can_spend(api_model):
        text = _anthropic(system, user, api_model, max_tokens, budget)
        if text:
            return text, f"api:{api_model}"

    # (۳) هیچ مسیرِ live‌ای در دسترس نبود
    raise RuntimeError(
        "no live route: ollama unavailable and (api key missing or monthly budget exhausted)")
