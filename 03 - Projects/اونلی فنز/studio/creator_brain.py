#!/usr/bin/env python3
"""creator_brain.py — 🧠 لایهٔ هوشِ مکالمه‌ایِ استودیوی Creator (LLM-backed).
[C1 opsec rename 2026-07-20: صفر نامِ شخصی در filename/کلاس/env — DL-2026-07-20-PII-INCIDENT]

هدف: تعاملی و هوشمند — بر اساسِ حرف‌های واقعیِ C، پاسخِ گرم می‌دهد و سوالِ درست
می‌پرسد (ظرفیت، ایدهٔ محتوا، حال‌وهوا). با حافظهٔ تعاملی (JSONL) و guard layerِ PII.

سیم‌کشی (blueprint §۳ · BRAIN-SPEC §۱):
  creator_studio.py ──(text)──▶ CreatorBrain.respond_to_creator(text)
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
              GuardLayer     MemoryStore     LLMClient
           (redact PII)   (creator_memory.jsonl) (Ollama first,
                                                 cloud fallback)

قرارداد سازگاری با creator_studio.py:
  - brain=None پذیرفته می‌شود (fail-soft).
  - respond_to_creator(text) -> str | None   ←  اصلی (alias قدیمی: respond_to_saba)
  - think_and_communicate(...) -> dict     ←  برای brief_page compat

قواعد (PROJECT-F-CONTROL-MANIFEST):
  - صفر PII/هویت/شهر در ورودی و خروجیِ LLM
  - فقط پا (feet-only)، بدون چهره/explicit
  - پرداخت فقط درون‌پلتفرم (هرگز paypal/crypto/p2p)
  - propose-only — هیچ‌چیز خودکار منتشر نمی‌شود
  - محدودهٔ خالق مقدمِ مطلق
  - لحن گرم، فارسی، حداکثر ۳ جمله

$0 آفلاین (Ollama localhost) · stdlib-only · fail-soft · rollback-able.
حذف این فایل = برگشت به DualBrainV3 (همان الگوی brain= قبلی).
"""
from __future__ import annotations

import html
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
MEMORY_FILE = HERE / "creator_memory.jsonl"
LANGAR_CONFIG = HERE.parent / "langar" / "langar_config.json"

# Ollama local (پیش‌فرض، $0، localhost)
OLLAMA_URL = os.environ.get("STUDIO_OLLAMA_URL",
                            os.environ.get("SABA_OLLAMA_URL", "http://127.0.0.1:11434"))
OLLAMA_MODEL = os.environ.get("STUDIO_OLLAMA_MODEL",
                              os.environ.get("SABA_OLLAMA_MODEL",
                                             os.environ.get("OLLAMA_MODEL", "qwen2.5:latest")))
OLLAMA_TIMEOUT = int(os.environ.get("STUDIO_OLLAMA_TIMEOUT_S",
                                    os.environ.get("SABA_OLLAMA_TIMEOUT_S", "60")))
MIN_INTERVAL_S = float(os.environ.get("STUDIO_MIN_INTERVAL_S",
                                      os.environ.get("SABA_MIN_INTERVAL_S", "3")))

# Sakana Fugu (fallback اختیاری، فقط با STUDIO_LLM_CLOUD=1 [یا نام قدیمی SABA_LLM_CLOUD] + FUGU_API_KEY)
FUGU_URL = "https://api.sakana.ai/v1/chat/completions"
FUGU_MODEL = "fugu-ultra-20260615"
FUGU_TIMEOUT = 45

# ─── FORBIDDEN_TERMS (هم‌خوان با brain/dual_brain_v3.py:33-37) ──────────────
FORBIDDEN_TERMS = [
    "persian", "sydney", "iran", "tehran", "middle east",
    "real name", "address", "phone", "email",
    "paypal", "crypto", "bank transfer", "p2p",
    "onlyfans",  # containment: هرگز در پاسخ نباشد
]

# ─── intent classification (بدون LLM — keyword matching) ──────────────────
_INTENT_KEYWORDS = {
    "halt":      ["وایسا", "بایست", "تمومش", "تمامش", "دیگه نه", "نمی‌خوام", "استاپ", "stop", "متوقف"],
    "capacity":  ["ساعت", "ظرفیت", "وقت", "فرصت", "time", "hour", "هفته"],
    "emotional": ["خسته", "بی‌حال", "بی حال", "ناراحت", "استرس", "دردسر", "حوصله", "کسل", "بد حال", "خواب"],
    "content":   ["ست", "شوت", "عکس", "رنگ", "لباس", "پالت", "نگین", "لاک", "پدیکور", "پا", "ست", "تم"],
    "boundary":  ["محدوده", "حریم", "نمی‌خوام", "حد", "مرز", "نکن"],
    "greeting":  ["سلام", "hi", "hello", "صبح", "عصر", "شب"],
}

SYSTEM_PROMPT = """تو دستیارِ گرمِ استودیوی محتوای یک خالق (Creator) هستی. لحن‌ت صمیمی، حمایت‌گر و کوتاه است.

قواعد (هرگز نقض نکن):
- فقط موضوعِ پا (feet-only) — هرگز چهره/بدن/explicit پیشنهاد نده.
- پرداخت فقط درون‌پلتفرم — هرگز paypal/crypto/بانک/خارج‌پلتفرم را پیشنهاد نده.
- propose-only — هیچ‌چیز خودکار منتشر نمی‌شود؛ فقط ایده و پیشنهاد.
- محدودهٔ خالق مقدم — اگر خسته/ناخوش است، استراحت را اولویت بده و فشار نیاور.
- زبان فارسی — حداکثر ۳ جمله — لحن گرم و واقعی.
- اگر دربارهٔ ظرفیت پرسیدی، عدد بپرس (چند ساعت این هفته داری؟).
- اگر دربارهٔ محتوا گفت، ایدهٔ خلاقانه بده (ترند، رنگ، فصل) و بعد پیشنهادِ ثبت بده.
- هرگز نامِ واقعی، شهر، آدرس، شماره، یا هر اطلاعاتِ شخصی را تکرار نکن.
- هرگز کلمهٔ پلتفرم را به‌صورتِ مستقیم ننویس؛ بگو «پلتفرم» یا «صفحه»."""


# ═══════════════════════════════════════════════════════════════════════════
# GuardLayer — redact PII ورودی + filter خروجی (manifest-compliant)
# ═══════════════════════════════════════════════════════════════════════════
class GuardLayer:
    """لایهٔ محافظ: PII/geo قبل از LLM، forbidden terms بعد از LLM."""

    def __init__(self, config_path: Path | None = None):
        cfg_path = config_path or LANGAR_CONFIG
        self._blocklist: list[str] = []
        self._city_terms: list[str] = []
        self._name_map: dict[str, str] = {}
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            self._blocklist = [str(t) for t in cfg.get("blocklist", []) if t]
            self._city_terms = [str(t) for t in cfg.get("city_terms", []) if t]
            self._name_map = {str(k): str(v) for k, v in cfg.get("name_map", {}).items()}
        except Exception:
            pass  # fail-soft: بدون config، فقط FORBIDDEN_TERMS

    def redact_input(self, text: str) -> str:
        """قبل از ارسال به LLM. PII/geo/names → [REDACTED]."""
        if not text:
            return ""
        out = text
        for term in self._blocklist:
            if term and term in out:
                out = out.replace(term, "[REDACTED]")
        for term in self._city_terms:
            if term and term in out:
                out = out.replace(term, "[LOC]")
        for src, dst in self._name_map.items():
            if src and src in out:
                out = out.replace(src, dst)
        return out

    def filter_output(self, text: str) -> tuple[bool, str]:
        """بعد از دریافت از LLM. (safe, text_or_reason)."""
        if not text:
            return False, "[empty]"
        t = str(text).lower()
        violations = [term for term in FORBIDDEN_TERMS if term in t]
        if violations:
            return False, f"[blocked: {','.join(violations[:3])}]"
        # red-flag پرداختِ خارج‌پلتفرم
        payment_red_flags = ["paypal", "crypto", "bitcoin", "bank transfer",
                             "send me money", "direct transfer"]
        for flag in payment_red_flags:
            if flag in t:
                return False, "[blocked: payment-red-flag]"
        return True, text


# ═══════════════════════════════════════════════════════════════════════════
# MemoryStore — creator_memory.jsonl (append-only، O(1) write)
# ═══════════════════════════════════════════════════════════════════════════
class MemoryStore:
    """حافظهٔ تعاملی. JSONL append-only (الگوی langar_log.jsonl)."""

    def __init__(self, path: Path | None = None, max_entries: int = 500):
        self._path = path or MEMORY_FILE
        self._max = max_entries

    def append(self, role: str, text: str, **extra) -> None:
        """یک entry اضافه می‌کند. fail-soft."""
        entry = {"ts": _now_iso(), "role": role, "text": str(text)[:800]}
        entry.update(extra)
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass  # fail-soft — memory نباید بات را بکُشد

    def recent(self, n: int = 16) -> list[dict]:
        """n ورودیِ آخر را برمی‌گرداند (context window)."""
        try:
            raw = self._path.read_text(encoding="utf-8").strip()
            if not raw:
                return []
            lines = raw.splitlines()
            return [json.loads(l) for l in lines[-n:]]
        except Exception:
            return []

    def stats(self) -> dict:
        """شمارش برای داشبورد."""
        try:
            raw = self._path.read_text(encoding="utf-8").strip()
            if not raw:
                return {"total": 0, "creator": 0, "bot": 0}
            lines = raw.splitlines()
            creator = sum(1 for l in lines
                          if '"role": "creator"' in l or '"role":"creator"' in l
                          or '"role": "saba"' in l or '"role":"saba"' in l)
            bot = sum(1 for l in lines if '"role": "bot"' in l or '"role":"bot"' in l)
            return {"total": len(lines), "creator": creator, "bot": bot}
        except Exception:
            return {"total": 0, "creator": 0, "bot": 0}


# ═══════════════════════════════════════════════════════════════════════════
# LLMClient — Ollama /api/chat (محلی) + Fugu (fallback اختیاری)
# ═══════════════════════════════════════════════════════════════════════════
class LLMClient:
    """کلاینت LLM. پیش‌فرض: Ollama localhost. Fallback: Fugu cloud (با flag)."""

    def __init__(self):
        self._last_call_ts = 0.0
        self._use_cloud = (os.environ.get("STUDIO_LLM_CLOUD")
                           or os.environ.get("SABA_LLM_CLOUD")) == "1"
        self._fugu_key = os.environ.get("FUGU_API_KEY") or os.environ.get("SAKANA_API_KEY")
        self._fugu_available = bool(self._use_cloud and self._fugu_key)

    def chat(self, user_text: str, history: list[dict] | None = None,
             system: str = SYSTEM_PROMPT) -> dict | None:
        """گفت‌و‌گو با messages array. خروجی: {text, source, ms} یا None.
        محلی اول؛ اگر fail شد و cloud فعال بود، cloud تلاش می‌کند."""
        # rate-limit
        gap = time.time() - self._last_call_ts
        if gap < MIN_INTERVAL_S:
            time.sleep(MIN_INTERVAL_S - gap)
        self._last_call_ts = time.time()

        messages = [{"role": "system", "content": system}]
        for h in (history or [])[-12:]:
            role = "user" if h.get("role") in ("creator", "saba") else "assistant"
            t = h.get("text", "").strip()
            if t:
                messages.append({"role": role, "content": t[:400]})
        messages.append({"role": "user", "content": user_text[:800]})

        # محلی اول
        t0 = time.time()
        local = self._ollama_chat(messages)
        if local is not None:
            return {"text": local, "source": "local", "ms": int((time.time() - t0) * 1000)}
        # fallback cloud
        if self._fugu_available:
            t0 = time.time()
            cloud = self._fugu_chat(messages)
            if cloud is not None:
                return {"text": cloud, "source": "cloud", "ms": int((time.time() - t0) * 1000)}
        return None

    def _ollama_chat(self, messages: list[dict]) -> str | None:
        """Ollama /api/chat. stdlib urllib."""
        try:
            payload = json.dumps({
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 200},
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{OLLAMA_URL}/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as r:
                data = json.loads(r.read().decode("utf-8"))
            msg = data.get("message") or {}
            return (msg.get("content") or "").strip() or None
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
            return None  # Ollama خاموش
        except Exception:
            return None

    def _fugu_chat(self, messages: list[dict]) -> str | None:
        """Sakana Fugu (OpenAI-compatible). فقط با FUGU_API_KEY."""
        try:
            payload = json.dumps({
                "model": FUGU_MODEL,
                "messages": messages,
                "max_tokens": 200,
                "temperature": 0.8,
            }).encode("utf-8")
            req = urllib.request.Request(
                FUGU_URL,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._fugu_key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=FUGU_TIMEOUT) as r:
                data = json.loads(r.read().decode("utf-8"))
            choices = data.get("choices") or []
            if not choices:
                return None
            return (choices[0].get("message", {}).get("content") or "").strip() or None
        except Exception:
            return None


# ═══════════════════════════════════════════════════════════════════════════
# intent classifier — heuristic (بدون LLM)
# ═══════════════════════════════════════════════════════════════════════════
def _classify(text: str) -> str:
    """intent از رویِ keyword. خروجی: halt/capacity/emotional/content/boundary/greeting/random."""
    t = str(text).lower()
    for intent, words in _INTENT_KEYWORDS.items():
        for w in words:
            if w in t:
                return intent
    return "random"


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ═══════════════════════════════════════════════════════════════════════════
# CreatorBrain — لایهٔ هوشِ اصلی (compatible با brain= پارامترِ creator_studio.py)
# ═══════════════════════════════════════════════════════════════════════════
class CreatorBrain:
    """مغزِ تعاملیِ C. ‏respond_to_creator(text) نقطهٔ ورودِ اصلی است."""

    def __init__(self):
        self._guard = GuardLayer()
        self._memory = MemoryStore()
        self._llm = LLMClient()
        self._stats = {"calls": 0, "blocked": 0, "fallback": 0}

    # ─── نقاطِ ورود ──────────────────────────────────────────────────────
    def respond_to_creator(self, text: str) -> str | None:
        """متنِ آزادِ C → پاسخِ گرم و هوشمند، یا None (fallback به creator_studio)."""
        if not text or not text.strip():
            return None
        self._stats["calls"] += 1

        # ۱. intent classification (هیوریستیک، $0)
        intent = _classify(text)

        # halt/boundary را به creator_studio بسپار (دستِ خالق بر /halt، /scope)
        if intent in ("halt", "boundary"):
            return None

        # ۲. redact PII قبل از هر چیزی
        clean = self._guard.redact_input(text.strip()[:800])

        # ۳. ذخیره در memory
        self._memory.append(role="creator", text=clean, intent=intent)

        # ۴. ساختنِ context (آخرِ گفت‌و‌گو)
        history = self._memory.recent(n=12)

        # ۵. ساختنِ prompt با توجه به intent
        user_prompt = self._build_user_prompt(clean, intent, history)

        # ۶. LLM call
        result = self._llm.chat(user_prompt, history=history)
        if not result or not result.get("text"):
            self._stats["fallback"] += 1
            return self._heuristic_fallback(intent)  # پاسخِ آماده، $0

        # ۷. filter خروجی
        safe, filtered = self._guard.filter_output(result["text"])
        if not safe:
            self._stats["blocked"] += 1
            return self._heuristic_fallback(intent)

        # ۸. ذخیرهٔ پاسخ
        self._memory.append(
            role="bot", text=filtered, source=result.get("source"),
            ms=result.get("ms"), intent=intent)
        return filtered

    def think_and_communicate(self, draft_title: str = "weekly", **kwargs) -> dict:
        """compat shim برای brief_page (الگوی DualBrainV3).
        خروجیِ کوتاه از آخرین memory + یک پرسشِ باز برای خالق."""
        stats = self._memory.stats()
        if stats["creator"] == 0:
            return {
                "messages": [{
                    "kind": "brief_creator",
                    "text": "هیچ گفت‌و‌گویی هنوز ثبت نشده. اولین سلامِ خالق آغازِ حافظه است.",
                    "tone": "warm",
                }],
                "blocked": False,
            }
        recent = self._memory.recent(n=4)
        last = recent[-1].get("text", "")[:100] if recent else ""
        return {
            "messages": [{
                "kind": "brief_creator",
                "text": (f"آخرین گفت‌و‌گو ({stats['creator']} پیام از خالق): "
                         f"{last}… این هفته چه ستّی می‌خوای بسازی؟"),
                "tone": "warm",
            }],
            "blocked": False,
        }

    # ─── helperهای داخلی ─────────────────────────────────────────────────
    def _build_user_prompt(self, clean: str, intent: str,
                           history: list[dict]) -> str:
        """prompt با توجه به intent."""
        base = f"پیامِ خالق: {clean}"
        if intent == "capacity":
            return base + "\n\n(خالق دربارهٔ ظرفیت/وقت صحبت می‌کند. عدد بپرس: چند ساعت این هفته داری؟)"
        if intent == "emotional":
            return base + "\n\n(خالق خسته/بی‌حال است. همدلی کن، استراحت پیشنهاد بده، و ظرفیتش را بپرس. هرگز فشار نیاور.)"
        if intent == "content":
            return base + "\n\n(خالق دربارهٔ محتوا/ایده صحبت می‌کند. یک ایدهٔ خلاقانهٔ feet-only بده و بعد پیشنهادِ ثبتِ درفت بده.)"
        if intent == "greeting":
            return base + "\n\n(خالق سلام کرده. گرم خوش‌آمد بگو و حالش را بپرس.)"
        return base + "\n\n(پاسخِ کوتاه و گرم بده. اگر موضوع روشن نیست، یک سوالِ باز بپرس.)"

    def _heuristic_fallback(self, intent: str) -> str:
        """وقتی LLM در دسترس نیست — پاسخِ آماده با intent."""
        fallbacks = {
            "capacity":  "چند ساعت این هفته وقت داری؟ برنامه با همون تنظیم می‌شه. 🌸",
            "emotional": "می‌فهمم. استراحت مهمه. هیچ عجله‌ای نیست — هر وقت آماده‌ای، اینجام. 💛",
            "content":   "ایده‌ت خوبه! برای شروع «📤 ثبت ایده» رو بزن تا با هم بسازیمش. 🌟",
            "greeting":  "سلامِ گرم! 🌸 حالت چطوره؟ امروز چی می‌خوای بسازی؟",
        }
        return fallbacks.get(intent,
            "نفهمیدم دقیقاً 🌸 از منوی پایین یه دکمه بزن، یا بگو چی می‌خوای.")

    def stats(self) -> dict:
        """برای observability."""
        s = dict(self._stats)
        s["memory"] = self._memory.stats()
        s["cloud_enabled"] = self._llm._fugu_available
        s["model"] = OLLAMA_MODEL
        return s


# ═══════════════════════════════════════════════════════════════════════════
# self-test (آفلاین، $0)
# ═══════════════════════════════════════════════════════════════════════════
def _selftest() -> int:
    """تستِ آفلاین: guard + memory + classify (بدون LLM).

    2026-07-20: قبلاً این تست نام/شهرِ واقعی را hardcode داشت (نقض PII در سورس)؛
    حالا با configِ موقتِ placeholder-only مکانیزم را می‌سنجد — صفر PII."""
    import tempfile as _tf
    fails = 0
    _cfg = {"blocklist": ["PLACEHOLDER FULLNAME", "0000000000"],
            "city_terms": ["Testville", "تست‌ویل"], "name_map": {}}
    with _tf.NamedTemporaryFile(suffix=".json", delete=False, mode="w",
                                encoding="utf-8") as _cf:
        json.dump(_cfg, _cf, ensure_ascii=False)
        _cfg_path = Path(_cf.name)
    try:
        g = GuardLayer(config_path=_cfg_path)
        # redact باید termهای پیکربندی‌شده را پاک کند
        r = g.redact_input("PLACEHOLDER FULLNAME از Testville زنگ زد")
        if "PLACEHOLDER FULLNAME" in r or "Testville" in r:
            print(f"FAIL redact: {r}"); fails += 1
    finally:
        try: _cfg_path.unlink()
        except Exception: pass
    g = GuardLayer(config_path=Path("NONEXISTENT-cfg.json"))
    # filter باید forbidden را بگیرد
    ok, _ = g.filter_output("come to sydney for paypal")
    if ok:
        print("FAIL filter: sydney/paypal عبور کرد"); fails += 1
    ok2, _ = g.filter_output("ایدهٔ پاییزی با لاکِ نارنجی")
    if not ok2:
        print("FAIL filter: پاسخِ تمیز را بلاک کرد"); fails += 1
    # classify
    if _classify("امروز خیلی خسته‌ام") != "emotional":
        print("FAIL classify: خسته → emotional نبود"); fails += 1
    if _classify("می‌خوام یه ست بسازم") != "content":
        print("FAIL classify: ست → content نبود"); fails += 1
    # memory roundtrip (tmp file)
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as tf:
        tmp = Path(tf.name)
    try:
        m = MemoryStore(path=tmp)
        m.append("creator", "hello"); m.append("bot", "hi")
        rec = m.recent(5)
        if len(rec) != 2 or rec[0]["role"] != "creator":
            print(f"FAIL memory: {rec}"); fails += 1
        st = m.stats()
        if st["total"] != 2:
            print(f"FAIL stats: {st}"); fails += 1
    finally:
        try: tmp.unlink()
        except Exception: pass
    print(f"creator_brain self-test: {3 - fails}/3 pass" if fails
          else "creator_brain self-test: ALL PASS")
    return fails


# سازگاری عقب‌رو (C1 rename 2026-07-20): نام‌های قدیمی هنوز کار می‌کنند.
CreatorBrain.respond_to_saba = CreatorBrain.respond_to_creator
SabaBrain = CreatorBrain


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    # shadow-mode conversation loop (بدون Telegram، stdin/stdout)
    print("=" * 60)
    print("🎬 creator_brain — shadow-mode (تست آفلاین)")
    print("    خروج بزن: Ctrl-C یا /quit")
    print("    LLM source:", "cloud+local"
          if (os.environ.get("STUDIO_LLM_CLOUD") or os.environ.get("SABA_LLM_CLOUD")) == "1"
          else "local-only")
    print("=" * 60)
    brain = CreatorBrain()
    print(brain._heuristic_fallback("greeting"))
    while True:
        try:
            msg = input("\nخالق> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nخروج."); break
        if not msg or msg in ("/quit", "exit", "خروج"):
            break
        if msg == "/stats":
            print(json.dumps(brain.stats(), ensure_ascii=False, indent=2)); continue
        resp = brain.respond_to_creator(msg)
        print(f"\n🤖 {resp or '(بدون پاسخ — LLM خاموش)'}")
