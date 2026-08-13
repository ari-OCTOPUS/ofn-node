"""
providers.py — روترِ چندprovider برای doctor_lite
هر ۴ سرویس OpenAI-compatible یا REST ساده‌اند. کلیدها فقط از محیط خوانده می‌شوند.

نقش‌ها (verdict آری «هوشمندانه»):
  - Perplexity → جستجوی وب زنده (منبع‌دار)
  - DeepSeek   → فکر/سنتز ارزان در حجم بالا (پیش‌فرض «فکر»)
  - Fugu       → فقط تصمیم‌های سخت/مهم (گران‌تر، فقط با escalation)

هیچ کلیدی در این فایل نیست. اپ کلیدها را از فایل .env (که .agentignore بلاکش می‌کند)
یا از متغیر محیطی می‌خواند.

متغیرهای محیطی مورد نیاز (هرکدام را داری):
  PERPLEXITY_API_KEY
  DEEPSEEK_API_KEY
  FUGU_API_KEY           (Sakana)
  # اختیاری برای وبِ جایگزین:
  TAVILY_API_KEY
"""
from __future__ import annotations
import json, os, urllib.request

# ---------- بارگذاری .env (بدون وابستگی خارجی) ----------
def load_env_file(path: str) -> None:
    """اگر فایل .env کنار اپ باشد، کلیدها را در محیط بار می‌کند. فایل در .agentignore بلاک است."""
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

# ---------- پیکربندی endpointها ----------
ENDPOINTS = {
    "perplexity": {
        "url": "https://api.perplexity.ai/chat/completions",
        "env": "PERPLEXITY_API_KEY",
        "model": "sonar",                 # جستجوی وب زنده
        "kind": "chat",
    },
    "deepseek": {
        "url": "https://api.deepseek.com/chat/completions",
        "env": "DEEPSEEK_API_KEY",
        "model": "deepseek-v4-flash",
        "kind": "chat",
    },
    "fugu": {
        "url": "https://api.sakana.ai/v1/chat/completions",   # OpenAI-compatible (Sakana)
        "env": "FUGU_API_KEY",
        "model": "fugu-ultra-20260615",
        "kind": "chat",
    },
}

class ProviderError(Exception):
    pass

def _post(url: str, key: str, payload: dict, timeout: int = 60) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())

def call_chat(provider: str, system: str, user: str, max_tokens: int = 800) -> dict:
    """یک فراخوانی chat به provider مشخص. خروجی: {text, provider, model, usage}."""
    cfg = ENDPOINTS.get(provider)
    if not cfg:
        raise ProviderError(f"provider ناشناخته: {provider}")
    key = os.environ.get(cfg["env"])
    if not key:
        raise ProviderError(f"کلید {cfg['env']} در محیط نیست")
    payload = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
    }
    data = _post(cfg["url"], key, payload)
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise ProviderError(f"پاسخ نامعتبر از {provider}: {str(data)[:200]}")
    return {
        "text": text,
        "provider": provider,
        "model": cfg["model"],
        "usage": data.get("usage", {}),
        # منابع Perplexity (اگر بود) — داده، نه دستور
        "citations": data.get("citations", []),
    }

def call_chat_via_router(task: str, system: str, user: str, max_tokens: int = 800) -> "dict | None":
    """۲۰۲۶-۰۸-۱۳ (رأیِ مالک): مسیرِ اختیاریِ عبور از دروازهٔ مرکزیِ اختاپوس
    (_ops/cortex/model_router.py) به‌جای تماسِ مستقیمِ این فایل با provider.

    چرا: این اپ (doctor_lite pilot) کلاینتِ مستقلِ خودش را داشت — همان کلاسِ
    شکافی که بازرسیِ ۲۰۲۶-۰۸-۱۳ (713M توکنِ ثبت‌نشده در provider) دنبالش
    می‌گشت. این اپ هرگز واقعاً اجرا نشده (صفر state/log از روزِ ساخت)، پس
    وصل‌کردنش هیچ رفتارِ زنده‌ای را عوض نمی‌کند — فقط از این به بعد اگر
    فعال شود، از همان سهمیه/لاگِ مرکزی رد می‌شود.

    task «think»→tier=secondary (DeepSeek)، «hard»→tier=primary (Fugu) —
    نگاشتِ صریح چون model_router برای taskِ ناشناخته پیش‌فرض به local
    (Ollama) می‌رود، نه به پولی. خروجی None یعنی فراخوان باید به
    call_chat() مستقیم برگردد (fail-soft — این تابع هرگز raise نمی‌کند)."""
    import sys
    try:
        _cortex_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))), "_ops", "cortex")
        if _cortex_dir not in sys.path:
            sys.path.insert(0, _cortex_dir)
        import model_router  # noqa: WPS433
    except Exception:  # noqa: BLE001 — organism نصب نیست/سازگار نیست → fail-soft
        return None
    tier = "primary" if task == "hard" else "secondary"
    try:
        res = model_router.ask(f"doctor_lite_{task}", user, system=system,
                                max_tokens=max_tokens, tier=tier)
    except Exception:  # noqa: BLE001
        return None
    if not isinstance(res, dict) or not res.get("ok"):
        return None
    return {
        "text": res.get("text") or "",
        "provider": f"router:{res.get('tier') or tier}",
        "model": res.get("model") or "",
        "usage": {},
        "citations": [],
    }


def available() -> dict:
    """کدام providerها کلید دارند (بدون فاش‌کردن مقدار)."""
    load_env_file(os.path.join(os.path.dirname(__file__), ".env"))
    out = {p: bool(os.environ.get(c["env"])) for p, c in ENDPOINTS.items()}
    out["tavily"] = bool(os.environ.get("TAVILY_API_KEY"))
    return out

# ---------- روترِ هوشمند (verdict «هوشمندانه») ----------
def route(task: str) -> str:
    """
    task ∈ {search, think, hard}
    - search → perplexity (وب زنده)
    - think  → deepseek (ارزان، حجم بالا)
    - hard   → fugu (فقط تصمیم مهم)
    با fallback: اگر provider اصلی کلید نداشت، به بعدی می‌رود.
    """
    have = available()
    chains = {
        "search": ["perplexity", "deepseek", "fugu"],
        "think":  ["deepseek", "fugu", "perplexity"],
        "hard":   ["fugu", "deepseek", "perplexity"],
    }
    for p in chains.get(task, ["deepseek"]):
        if have.get(p):
            return p
    return ""   # هیچ کلیدی نیست → mock
