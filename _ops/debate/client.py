#!/usr/bin/env python3
"""
client.py — کلاینت LLM حداقلی (stdlib، بدون SDK) برای لوپ مناظره و Governor.

قراردادهای سخت:
  - model و base_url فقط از budgets.yaml (routing.econ / routing.reason) — هرگز هاردکد
    (aliasهای deepseek-chat/reasoner از 2026-07-24 بازنشسته‌اند؛ فایل الان v4-flash دارد).
  - کلید فقط از DEEPSEEK_API_KEY. fallback به ANTHROPIC_API_KEY ممنوع — در استک
    control-brain آن متغیر عمداً حامل کلید DeepSeek برای مسیر anthropic-سازگار است و
    اتکای کور به آن دقیقاً همان تلهٔ نشت است (پک B.1).
  - گارد نشت: base_url باید شامل api.deepseek.com باشد وگرنه RefuseToSend.
  - متر بدون «or 0»: پاسخ بدون usage در مسیر زنده = TelemetryError (نه صفر بی‌صدا).
  - قیمت قفل‌نشده = PriceNotLocked؛ قیمت از کلیدهای price_in/price_out خود budgets.yaml
    (پیشنهاد diff موجود است) — تا مالک بعد از platform.deepseek.com قفل نکند، call زنده نداریم.
  - est همیشه بدترین‌حالت: توکن‌های reasoning هم شارژ می‌شوند (پک B.1).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "budget"))
import opslib  # noqa: E402



# ── R27 (2026-08-16): پاکسازِ پیش‌متنِ استدلال ──────────────────────────────
# شواهد: chat-log.jsonl 2026-08-13T00:57 و 2026-08-15T10:59 — پاسخ با
# «The user is asking me…» / «The user message starts with…» شروع می‌شد و
# جوابِ فارسیِ واقعی چند پاراگراف بعد می‌آمد. قانونِ شواهد‌محور:
#   ۱) فقط وقتی دست می‌زنیم که خطِ اول با نشانگرِ استدلالِ انگلیسی بخورد.
#   ۲) مرزِ پاسخ = اولین پاراگرافِ با محتوای فارسی (≥۳۰٪ حرفِ فارسی).
#   ۳) پاراگرافِ فارسی پیدا نشد ⇒ متن عیناً برمی‌گردد (fail-soft).
_REASONING_OPENERS = (
    "the user", "let me", "the message", "we need to", "okay",
    "first, ", "i need to", "it seems", "looking at", "the assistant",
)
_FA_RANGE = range(0x0600, 0x0700)


def _fa_ratio(par: str) -> float:
    s = par.strip()
    if not s:
        return 0.0
    fa = sum(1 for ch in s if ord(ch) in _FA_RANGE)
    return fa / len(s)


def _strip_reasoning_preamble(text: str) -> str:
    t = str(text or "")
    if not t:
        return t
    head = t.lstrip()[:60].lower()
    if not any(head.startswith(o) for o in _REASONING_OPENERS):
        return t
    sep = chr(10) + chr(10)
    parts = t.split(sep)
    for i, par in enumerate(parts):
        if _fa_ratio(par) >= 0.30:
            return sep.join(parts[i:]).lstrip()
    return t  # fail-soft


class RefuseToSend(RuntimeError):
    """گارد نشت/پیکربندی — عمداً قبل از هر بایت شبکه."""


class PriceNotLocked(RuntimeError):
    """قیمت [EST] هنوز در budgets.yaml قفل نشده (V1) — call زنده ممنوع."""


class TelemetryError(RuntimeError):
    """پاسخ بدون usage — متر کور می‌شود؛ صفرِ بی‌صدا ممنوع."""


def extract_json(text: str) -> dict[str, Any]:
    """JSON را از پاسخ مدل بیرون می‌کشد.

    - حصارِ ```json ... ``` یا ``` ... ``` را حذف می‌کند (Markdown).
    - JSON نامعتبر یا بریده (truncated by max_tokens) → خطای واضح با علت.
    - وقتی آکولادِ پایانی غایب باشد، پیامِ «truncated» می‌دهد نه «no JSON object»
      تا صاحبِ فراخوان بداند علت سقفِ توکن است نه نبودِ JSON.
    """
    s = text.strip()
    # ── strip markdown code fences ──────────────────────────────────────
    # الگو: ```json ... ```  یا  ``` ... ``` — فقط اولین و آخرین حصار را حذف می‌کند
    if s.startswith("```"):
        first_nl = s.find("\n")
        if first_nl != -1:
            # حصارِ شروع: ```json یا ``` (3+ کاراکتر)
            fence_open = first_nl + 1
            # حصارِ پایانی: خطی که فقط ``` دارد
            fence_close = s.rfind("```")
            if fence_close > fence_open:
                s = s[fence_open:fence_close].strip()
            else:
                # حصارِ پایانی غایب — JSON درون حصار شروع شده ولی تمام نشده (truncated)
                s = s[fence_open:]
    # ── find JSON braces ───────────────────────────────────────────────
    i, j = s.find("{"), s.rfind("}")
    if i == -1:
        raise ValueError(f"no JSON object in model reply: {s[:120]!r}")
    if j == -1:
        # بریدگیِ توکن — JSON شروع شده ولی تمام نشده
        raise ValueError(
            f"JSON response truncated (missing closing brace): "
            f"{s[:120]!r}  — likely finish_reason=length; raise max_tokens")
    candidate = s[i:j + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"invalid JSON in model reply (offset {exc.pos}): {exc.msg!r}  "
            f"snippet: {candidate[max(0, exc.pos - 20):exc.pos + 40]!r}") from exc


def _infer_finish(finish, tokens_out, max_tokens) -> "str | None":
    """اگر provider ساکت است، بریدگی را از شمارِ توکن استنتاج کن.

    ۲۰۲۶-۰۷-۳۰ — شاهد: در `state/paid-calls.jsonl` هر ۲۰۶ تماسِ موفق
    `finish_reason=None` داشتند، چون sakana/fugu این میدان را برنمی‌گرداند. پس
    گاردی که ۰۷-۲۷ برای دیدنِ «length» ساخته شده بود **هرگز شلیک نمی‌کرد** —
    میدان لوله‌کشی شده بود ولی همیشه خالی می‌آمد.

    چرا `tokens_out >= max_tokens` استنتاجِ معتبری است: مدلِ استدلالی توکن‌های
    تفکرش را از همان بودجهٔ `max_tokens` می‌خورد. اگر شمارِ خروجی به سقف بخورد،
    تولید **قطع** شده است؛ چه متنِ مرئی داشته باشیم چه نه. نمونهٔ زنده:
    `tokens_out=500 (=سقف) → chars_out=3` — کلِ بودجه صرفِ استدلال شد و سه
    کاراکتر بیرون آمد. بدونِ این استنتاج، آن پاسخ «موفق» شمرده می‌شد.

    محافظه‌کار است: رأیِ صریحِ provider همیشه برنده است، و پاسخِ کوچکی که به سقف
    نخورده (`tokens_out=18` با سقفِ ۷۰۰) دست‌نخورده می‌ماند — آن پاسخِ سالمِ
    کوتاه است، نه بریده."""
    if finish:
        return finish
    try:
        if int(tokens_out or 0) >= int(max_tokens or 0) > 0:
            return "length"
    except (TypeError, ValueError):
        pass
    return finish


class DeepSeekClient:
    """یک client، base_url از فایل. transport تزریقی = تست آفلاین بدون کلید/شبکه ($0)."""

    def __init__(self, role: str = "econ",
                 transport: Callable[[dict], dict] | None = None) -> None:
        routing = opslib.load_budgets().get("routing", {})
        cfg = routing.get(role)
        if not cfg:
            raise RefuseToSend(f"routing.{role} در budgets.yaml نیست")
        self.role = role
        self.model = cfg.get("model")
        self.base_url = str(cfg.get("base_url", "")).rstrip("/")
        self.price_in = cfg.get("price_in")     # USD per 1M — فقط از فایل
        self.price_out = cfg.get("price_out")
        self.transport = transport
        if transport is None:
            if "api.deepseek.com" not in self.base_url:
                raise RefuseToSend(
                    f"leak-guard: base_url «{self.base_url}» deepseek نیست — refusing")
            if not self.model:
                raise RefuseToSend(f"routing.{role}.model خالی است")
            if self.price_in is None or self.price_out is None:
                raise PriceNotLocked(
                    "price_in/price_out در budgets.yaml قفل نشده — اول از platform.deepseek.com "
                    "راستی‌آزمایی و با verdict اضافه کن (پیشنهاد: budgets-proposed-diff.md)")
            self.api_key = os.environ.get("DEEPSEEK_API_KEY")
            if not self.api_key:
                raise RefuseToSend("DEEPSEEK_API_KEY تنظیم نیست (fallback به کلید دیگر ممنوع)")

    def est_worst_case(self, prompt_chars: int, max_tokens: int) -> float:
        """تخمین بدترین‌حالت USD: ورودی ~۳ کاراکتر/توکن + خروجی کامل با سربار reasoning ×۱.۵."""
        pin = float(self.price_in or 0.0)
        pout = float(self.price_out or 0.0)
        return (prompt_chars / 3.0) / 1e6 * pin + (max_tokens * 1.5) / 1e6 * pout

    def complete(self, system: str, user: str, max_tokens: int = 1024,
                 temperature: float = 0.7, seed: int | None = None) -> dict[str, Any]:
        body = {
            "model": self.model or "stub",
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if seed is not None:
            body["seed"] = seed
        # [VERIFIED 2026-07-18 live-probe 3/3] GLM-4.6 بدونِ این پارامتر توکن‌ها را در reasoning_content
        # می‌سوزاند و content خالی برمی‌گردد (ریشهٔ flake در smoke). با disabled: content='PONG' قطعی.
        if "glm" in str(self.model or "").lower() or "api.z.ai" in self.base_url or "bigmodel.cn" in self.base_url:
            body["thinking"] = {"type": "disabled"}
        if self.transport is not None:
            raw = self.transport(body)
        else:
            req = urllib.request.Request(
                self.base_url + "/chat/completions",
                data=json.dumps(body).encode("utf-8"),
                headers={"Authorization": f"Bearer {self.api_key}",
                         "Content-Type": "application/json"})
            with urllib.request.urlopen(
                    req, timeout=_http_timeout(
                        getattr(self, "role", None), max_tokens)) as resp:  # pragma: no cover
                raw = json.loads(resp.read().decode("utf-8"))
        _choice = (raw.get("choices") or [{}])[0]
        # 2026-07-27: `finish_reason` هرگز سطح‌بالا نمی‌آمد، پس یک پاسخِ **بریده** از
        # صدا درنمی‌آمد — فقط بعداً `extract_json` می‌شکست و آلارم «no JSON object»
        # می‌داد. مسیرِ LLM ِ گاورنر ۲۴+ ساعت روی همین کوری مرده ماند و هر epoch یک
        # فراخوانِ ~۳۰ ثانیه‌ای Fugu را دور ریخت. حالا صاحبِ فراخوان می‌تواند «length»
        # را ببیند و سقف را بالا ببرد به‌جای اینکه دنبالِ باگِ parser بگردد.
        _finish = _choice.get("finish_reason")
        _msg = _choice.get("message", {})
        # fallback به reasoning_content — مدل‌های reasoning گاهی content را خالی می‌گذارند (fail-soft، صادق)
        text = _msg.get("content") or ""   # OVN-5 step0: reasoning هرگز به‌جای پاسخ (فقط content)
        # 2026-08-16 (R27): مدل‌های thinking (deepseek-v4-flash) گاهی کلِ زنجیرهٔ
        # استدلالِ انگلیسی را داخلِ content می‌آورند و پاسخِ واقعیِ فارسی بعدش —
        # دو نمونهٔ زندهٔ 2026-08-13/15 در state/chat/chat-log.jsonl. اگر متن با
        # نشانگرِ استدلال شروع شود، از اولین پاراگرافِ فارسی به بعد برگردان؛
        # نشد، متن دست‌نخورده (fail-soft — پاکساز هرگز پاسخ را حذف نمی‌کند).
        text = _strip_reasoning_preamble(text)
        usage = raw.get("usage")
        if self.transport is None and not usage:
            raise TelemetryError("پاسخ بدون usage — متر کور؛ call را شکست‌خورده حساب کن")
        usage = usage or {}
        tin = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
        tout = usage.get("completion_tokens") or usage.get("output_tokens") or 0
        if self.transport is None and (tin + tout) == 0:
            raise TelemetryError("usage صفر/ناقص — صفر بی‌صدا ممنوع (تلهٔ or 0)")
        cost = (tin / 1e6) * float(self.price_in or 0.0) \
            + (tout / 1e6) * float(self.price_out or 0.0)
        # DEFECT-W4: transportِ تزریقی می‌تواند ردهٔ واقعیِ خود را اعلام کند (octopus_tier)
        # تا ledger بینِ stubِ آفلاین و مغزِ محلیِ واقعی فرق بگذارد. نبودِ این کلید =
        # رفتارِ امروز بایت‌به‌بایت (هر transport = stub؛ بدونِ transport = زنده).
        _tier = raw.get("octopus_tier")
        return {"text": text, "reasoning_content": _msg.get("reasoning_content") or "", "model": raw.get("octopus_model") or self.model,
                "tokens_in": tin, "tokens_out": tout, "cost_usd": cost,
                "finish_reason": _infer_finish(_finish, tout, max_tokens),
                "tier": _tier or ("stub" if self.transport is not None else "paid"),
                "stub": self.transport is not None and (_tier or "stub") == "stub"}


# ─── MultiProviderClient (GLM/Fugu/DeepSeek) — تسکِ routing اصلی ──────────────

# ─── GATEWAY (LiteLLM proxy) — مسیرِ اصلی ─────────────────────────────────────
# تو یک پروکسی LiteLLM روی localhost:4000 دارد که مدل‌های مجازی expose می‌کند
# (glm-coder, deepseek-bulk, orchestr, fugu) با cost-cap + audit + fallback.
# کد از طریقِ gateway می‌زند، نه مستقیم. کلید = LITELLM_MASTER_KEY از gateway/.env.
GATEWAY_URL = "http://localhost:4000"


# ── سقفِ مشتق‌شده از اندازهٔ درخواست (یافتهٔ ۲۵ جولای، عدد-به-عدد) ──────────────
# شاهدِ زنده در `state/paid-calls.jsonl`: **هر ۱۵ شکست** از ۳۰ فراخوان دقیقاً روی سقفِ
# سوکتِ خودمان مرد (۶ تا روی ۴۵s، ۹ تا روی ۲۰s). صفر خطای فروشنده، صفر ۴۰۱.
# نرخِ مشاهده‌شدهٔ Fugu از سه موفقیت (out=18→4.3s، 479→12.7s، 488→16.1s):
#     ms ≈ 3811 + 25.2 × out_tokens        (~۴۰ tok/s + ~۳.۸s سرِ ثابت)
# و `governor_epoch.py` با `max_tokens=1200` می‌زد ⇒ ≥۳۴ ثانیه لازم داشت. با سقفِ
# سراسریِ ۲۰ ثانیه آن فراخوان **ریاضیاتاً غیرممکن** بود، نه بعید — و هر شکست به‌عنوان
# «شکستِ فروشنده» شمرده می‌شد تا FUGU_FAIL_CEILING مغزِ پولی را خاموش کند.
#
# ریشهٔ معماری: یک عددِ سراسری نمی‌تواند هم GLMِ ۹ ثانیه‌ای و هم مسیرِ orchestrationِ
# چند-ایجنتی را سرویس کند. پس سقف **مشتق** می‌شود: از max_tokensِ همان درخواست، با
# حاشیهٔ ایمنی، کف‌دار به سقفِ صریح، و **کران‌دار به کسری از PAID_ASK_BUDGET_S** تا
# فراخوانِ اول کلِ بودجهٔ ask را نخورد و fallbackِ tierِ دوم بی‌وقت نماند.
_TOK_PER_S = 25.0          # محافظه‌کارانه‌تر از ۴۰ tok/sِ مشاهده‌شده (حاشیه برای افتِ نرخ)
_OVERHEAD_S = 5.0          # سرِ ثابتِ مشاهده‌شده ۳.۸s، رُند به بالا
_SAFETY = 1.5              # ضریبِ حاشیه
_ASK_BUDGET_SHARE = 0.6    # حداکثر ۶۰٪ بودجهٔ ask برای یک سوکت → ۴۰٪ برای fallback

# ۲۰۲۶-۰۷-۲۷ — بودجهٔ ask هم نمی‌تواند یک عددِ سراسری باشد، به همان دلیلی که سقفِ
# سوکت نمی‌توانست. اندازه‌گیریِ زندهٔ همان روز نشان داد گاورنر با max_tokens=600
# **بریده** می‌شود و فقط با ۲۰۰۰ خروجیِ parseشدنی می‌دهد؛ ولی مشتقِ همین ماژول برای
# ۲۰۰۰ توکن ۱۲۷.۵s می‌خواهد و کرانِ ۶۰٪ از بودجهٔ سراسریِ ۹۰s فقط ۵۴s می‌داد. یعنی
# فراخوان دوباره ریاضیاتاً محکوم بود — همان باگی که یک بار بسته شده بود، از سمتِ
# دیگر برگشت.
#
# چرا سراسری را بالا نمی‌بریم: بودجهٔ ask فقط سقفِ صبر نیست؛ کرانِ زمانی است که نخِ
# متابولیک تا دیدنِ STOP-ORGANISM تحمل می‌کند. بالابردنش برای همه، پاسخ‌گوییِ
# کلیدِ کشتن را برای هر مسیرِ پولی کند می‌کند. پس فقط نقشی که واقعاً سقفِ بزرگ
# لازم دارد بودجهٔ بزرگ می‌گیرد.
_ASK_BUDGET_DEFAULT = 90.0
_ASK_BUDGET_BY_ROLE = {
    # حلقهٔ epochِ گاورنر هر ۲۰ دقیقه در نخِ خودش است؛ ۲۱۵s سقفِ ask یعنی
    # ۱۲۹s سقفِ سوکت — کمی بالای ۱۲۷.۵sِ لازم برای ۲۰۰۰ توکن.
    "ORCHESTR": 215.0,
    # OWNER-CLOSE 2026-08-16 دروازه ۳: reason همان سقف ۲۰۰۰توکن را می‌زند
    # (هشدار زنده: need 127.5s / cap 54s → PAID_ASK_BUDGET_S_REASON ≥212).
    "REASON": 215.0,
}


def _ask_budget(role: "str | None") -> float:
    """بودجهٔ askِ این نقش: envِ per-role → envِ سراسری → جدولِ نقش → پیش‌فرض."""
    import os as _o
    r = str(role or "").strip().upper()
    if r:
        per = _env_float(f"PAID_ASK_BUDGET_S_{r}", 0.0)
        if per > 0:
            return per
    if str(_o.environ.get("PAID_ASK_BUDGET_S", "")).strip():
        return _env_float("PAID_ASK_BUDGET_S", _ASK_BUDGET_DEFAULT)
    return _ASK_BUDGET_BY_ROLE.get(r, _ASK_BUDGET_DEFAULT)


def _env_float(name: str, default: float) -> float:
    import os as _o
    try:
        return float(_o.environ.get(name, "") or default)
    except (TypeError, ValueError):
        return default


_TRUNC_SEEN = set()


def _timeout_truncated(role, max_tokens, need_s: float, cap_s: float) -> None:
    """آلارمِ «سقفِ سوکت زیرِ نیازِ محاسبه‌شده» — یک بار per (نقش، سقف)، fail-soft.

    عمداً بی‌صدا **نیست** ولی پرحرف هم نیست: هر ترکیب یک بار در عمرِ پروسه."""
    key = (str(role or ""), int(max_tokens or 0))
    if key in _TRUNC_SEEN:
        return
    _TRUNC_SEEN.add(key)
    try:
        # ⚠️ مسیر از `opslib.STATE_DIR` می‌آید نه از `__file__`.
        # نسخهٔ اولِ همین تابع (چند ساعت پیش، همین جلسه) مسیر را از `__file__`
        # می‌ساخت — یعنی **مستقل از env**. نتیجه: هر اجرای سوییت روی درختِ
        # **زنده** می‌نوشت و ۹۸ ردیفِ آزمایشی در state واقعی نشست. دقیقاً همان
        # دامِ «مسیر بی‌صدا به درختِ زنده می‌خورد» که در این مخزن ثبت شده است.
        p = opslib.STATE_DIR / "paid-timeout-alerts.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        import json as _j
        import time as _t
        with open(p, "a", encoding="utf-8") as f:
            f.write(_j.dumps({
                "ts": _t.strftime("%Y-%m-%dT%H:%M:%S"),
                "role": str(role or ""), "max_tokens": int(max_tokens or 0),
                "need_s": round(float(need_s), 1), "cap_s": round(float(cap_s), 1),
                "why": "سقفِ سوکت زیرِ نیازِ مشتق‌شده — این فراخوان احتمالاً بریده می‌شود",
                "fix": f"PAID_ASK_BUDGET_S_{str(role or '').upper()} را "
                       f"≥{need_s / _ASK_BUDGET_SHARE:.0f} کن یا max_tokens را کم کن",
            }, ensure_ascii=False) + "\n")
    except (OSError, ValueError, TypeError):
        pass


def _http_timeout(role: "str | None" = None, max_tokens: "int | None" = None) -> float:
    """سقفِ سختِ عملیاتِ سوکت روی مسیرِ پولی.

    ترتیبِ اولویت:
      ۱) `PAID_HTTP_TIMEOUT_S_<ROLE>` (مثلاً `PAID_HTTP_TIMEOUT_S_ORCHESTR`) — صریح، per-role
      ۲) `PAID_HTTP_TIMEOUT_S` — سقفِ سراسری (پیش‌فرض ۴۵s)
      ۳) کفِ مشتق‌شده از max_tokens: (OVERHEAD + tokens/RATE) × SAFETY
    نتیجه = max(صریح، مشتق‌شده) و بعد کران‌دار به `ASK_BUDGET × 0.6` و بازهٔ [1, 300].
    با `max_tokens=None` رفتار **بایت‌به‌بایت** مثلِ قبل است (سازگاریِ عقب‌رو)."""
    base = _env_float("PAID_HTTP_TIMEOUT_S", 45.0)
    if not (1.0 <= base <= 300.0):
        base = 45.0
    if role:
        per = _env_float(f"PAID_HTTP_TIMEOUT_S_{str(role).strip().upper()}", 0.0)
        if 1.0 <= per <= 300.0:
            base = per
    if max_tokens:
        try:
            need = (_OVERHEAD_S + float(max_tokens) / _TOK_PER_S) * _SAFETY
        except (TypeError, ValueError, ZeroDivisionError):
            need = 0.0
        if need > base:
            base = need
        # کرانِ بالا: هرگز از سهمِ مجازِ بودجهٔ askِ بیرونی رد نشو
        ask = _ask_budget(role)
        if ask > 0:
            cap = ask * _ASK_BUDGET_SHARE
            if base > cap:
                # ⚠️ این‌جا داریم تماسی می‌زنیم که خودمان محاسبه کرده‌ایم تمام
                # نمی‌شود. یک بار همین اتفاق افتاد و ۸۷ آلارمِ «no JSON object»
                # داد بدونِ اینکه یک بار بگوید علت ساعتِ خودمان است. سکوت اجازه
                # نیست — بریدن ثبت می‌شود تا دفعهٔ بعد در همان دقیقهٔ اول پیدا شود.
                _timeout_truncated(role, max_tokens, base, cap)
                base = cap
    return min(300.0, max(1.0, base))
GATEWAY_ENV_PATH = Path(__file__).resolve().parent.parent.parent / "survival-gateway" / ".env"

# نگاشتِ role (در budgets.yaml) → نامِ مدلِ مجازیِ gateway
GATEWAY_MODEL_MAP = {
    "glm": "glm-coder",          # GLM (reason)
    "sakana": "fugu",            # Fugu (orchestrator) — مدلِ سبک‌تر
    "deepseek": "deepseek-bulk", # DeepSeek (econ)
}


def _gateway_master_key():
    """LITELLM_MASTER_KEY را از gateway/.env بخوان (هرگز log/commit).
    fail-soft: نبود → None (تست با stub یا transport کار می‌کند)."""
    try:
        if not GATEWAY_ENV_PATH.exists():
            return None
        for line in GATEWAY_ENV_PATH.read_text(encoding="utf-8").splitlines():
            if line.startswith("LITELLM_MASTER_KEY="):
                return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return None


def _gateway_is_up():
    """آیا gateway روی localhost:4000 بالاست؟ fail-soft."""
    try:
        urllib.request.urlopen(GATEWAY_URL + "/health/live", timeout=2)
        return True
    except urllib.error.HTTPError:
        return True   # 404 یعنی سرور بالاست (مسیر نیست)، ولی gateway زنده
    except Exception:
        return False


# نگاشتِ provider → (env-var-name, base_url-allowed-substring, price_in, price_out)
# فقط برای مسیرِ مستقیمِ fallback (اگر gateway down باشد).
_PROVIDER_REGISTRY = {
    "glm": {
        "env_key": "ZAI_API_KEY",
        "env_key_alias": "GLM_API_KEY",   # 2026-07-15: مالک ممکن است GLM_API_KEY بگذارد (نامِ مستندِ budgets)
        "base_url_env": "GLM_BASE_URL",
        # [VERIFIED 2026-07-18 live-probe] z.ai روت‌های کوتاه (/chat/completions و /v1/) را 404 می‌کند؛
        # pay-as-you-go (/api/paas/v4) روی این اکانت 429 (بدون شارژ) است؛ پلنِ اشتراکیِ Coding مسیرِ درست است (200 + choices).
        "base_url_default": "https://api.z.ai/api/coding/paas/v4",
        "allowed_hosts": ("api.z.ai", "bigmodel.cn"),
        "price_in": 0.6,     # $0.6/M [VERIFIED docs.z.ai] — فقط برای telemetry؛ flat اگر subscription=max
        "price_out": 2.2,    # $2.2/M
    },
    "sakana": {
        "env_key": "SAKANA_API_KEY",
        "env_key_alias": "FUGU_API_KEY",   # 2026-07-15: مالک FUGU_API_KEY گذاشته (Fugu = Sakana)
        "base_url_default": "https://api.sakana.ai/v1",
        "allowed_hosts": ("api.sakana.ai",),
        "price_in": 5.0,     # $5/M [VERIFIED]
        "price_out": 30.0,   # $30/M
    },
    "deepseek": {
        "env_key": "DEEPSEEK_API_KEY",
        "base_url_default": "https://api.deepseek.com",
        "allowed_hosts": ("api.deepseek.com",),
        "price_in": 0.14,
        "price_out": 0.28,
    },
}


def _resolve_base_url(cfg: dict, prov: str) -> str:
    """base_url را از config حل کن. اگر ${ENV_VAR} است، از env بخوان."""
    raw = str(cfg.get("base_url", ""))
    if raw.startswith("${") and raw.endswith("}"):
        env_name = raw[2:-1]
        # سعی کن از env_loader (.env) هم بخواند
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "budget"))
            import env_loader
            env_loader.load_env()
        except Exception:  # noqa: BLE001
            pass
        return os.environ.get(env_name, "").rstrip("/") or _PROVIDER_REGISTRY[prov]["base_url_default"]
    return raw.rstrip("/") or _PROVIDER_REGISTRY[prov]["base_url_default"]


class MultiProviderClient:
    """کلاینتِ چند-پروایدر: GLM (reason) / Fugu (orchestr) / DeepSeek (econ).
    transport تزریقی = تست آفلاین بدون کلید/شبکه. leak-guard هر پروایدر.
    قیمت فقط از _PROVIDER_REGISTRY (هرگز hardcode در call). telemetry بدون or-0."""

    def __init__(self, role: str = "reason",
                 transport: Callable[[dict], dict] | None = None,
                 budgets: dict | None = None) -> None:
        # مطمئن شو .env خوانده شد
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "budget"))
            import env_loader
            env_loader.load_env()
        except Exception:  # noqa: BLE001
            pass
        routing = (budgets or opslib.load_budgets()).get("routing", {})
        cfg = routing.get(role)
        if not cfg:
            raise RefuseToSend(f"routing.{role} در budgets.yaml نیست")
        self.role = role
        self.provider = cfg.get("provider", "")
        if self.provider not in _PROVIDER_REGISTRY:
            raise RefuseToSend(f"provider «{self.provider}» ناشناخته (مجاز: glm/sakana/deepseek)")
        reg = _PROVIDER_REGISTRY[self.provider]
        self.subscription = cfg.get("subscription")   # "max" = flat
        self.transport = transport
        # ── مسیرِ اصلی: LiteLLM gateway (localhost:4000) ────────────────────────
        # gateway مدل‌های مجازی expose می‌کند + cost-cap + audit. اولویت با gateway است.
        self.use_gateway = False
        if transport is None and _gateway_is_up():
            gw_key = _gateway_master_key()
            if gw_key and self.provider in GATEWAY_MODEL_MAP:
                self.use_gateway = True
                self.api_key = gw_key
                self.model = GATEWAY_MODEL_MAP[self.provider]
                self.base_url = GATEWAY_URL
        # ── مسیرِ مستقیمِ fallback (اگر gateway down یا بدون کلید) ──────────────
        if not self.use_gateway:
            self.model = cfg.get("model", "")
            self.base_url = _resolve_base_url(cfg, self.provider)
            # leak-guard: host مجاز
            host_ok = any(h in self.base_url for h in reg["allowed_hosts"])
            if transport is None and not host_ok:
                raise RefuseToSend(
                    f"leak-guard: base_url «{self.base_url}» host مجازِ {self.provider} نیست — refusing")
            # کلید فقط از env (هرگز hardcode)
            if transport is None:
                # 2026-07-15: نامِ اصلی، بعد aliasِ مستند (FUGU_API_KEY / GLM_API_KEY) — تا کلیدِ
                # مالک هرچه نامش باشد به provider برسد. هرگز مقدار log/echo نمی‌شود.
                self.api_key = (os.environ.get(reg["env_key"])
                                or os.environ.get(reg.get("env_key_alias", ""), "") or "")
                if not self.api_key:
                    _names = reg["env_key"] + (f"/{reg['env_key_alias']}" if reg.get("env_key_alias") else "")
                    raise RefuseToSend(f"{_names} تنظیم نیست — کلید فقط از env")
            else:
                self.api_key = ""
        # قیمت از registry (برای telemetry). flat subscription → cost محاسبه ولی گزارش می‌شود
        self.price_in = float(cfg.get("price_in", reg["price_in"]))
        self.price_out = float(cfg.get("price_out", reg["price_out"]))

    def est_worst_case(self, prompt_chars: int, max_tokens: int) -> float:
        """تخمین بدترین‌حالت USD. flat subscription → ۰ (سابسکرایب سقف است)."""
        if self.subscription == "max":
            return 0.0
        return (prompt_chars / 3.0) / 1e6 * self.price_in + (max_tokens * 1.5) / 1e6 * self.price_out

    def complete(self, system: str, user: str, max_tokens: int = 1024,
                 temperature: float = 0.7, seed: int | None = None) -> dict[str, Any]:
        body = {
            "model": self.model or "stub",
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if seed is not None:
            body["seed"] = seed
        # [VERIFIED 2026-07-18 live-probe 3/3] GLM-4.6 بدونِ این پارامتر توکن‌ها را در reasoning_content
        # می‌سوزاند و content خالی برمی‌گردد (ریشهٔ flake در smoke). با disabled: content='PONG' قطعی.
        if "glm" in str(self.model or "").lower() or "api.z.ai" in self.base_url or "bigmodel.cn" in self.base_url:
            body["thinking"] = {"type": "disabled"}
        if self.transport is not None:
            raw = self.transport(body)
        elif self.use_gateway:
            # مسیرِ gateway: localhost:4000 + master_key + virtual model name
            req = urllib.request.Request(
                self.base_url + "/v1/chat/completions",
                data=json.dumps(body).encode("utf-8"),
                headers={"Authorization": f"Bearer {self.api_key}",
                         "Content-Type": "application/json"})
            with urllib.request.urlopen(
                    req, timeout=_http_timeout(
                        getattr(self, "role", None), max_tokens)) as resp:  # pragma: no cover
                raw = json.loads(resp.read().decode("utf-8"))
        else:
            req = urllib.request.Request(
                self.base_url + "/chat/completions",
                data=json.dumps(body).encode("utf-8"),
                headers={"Authorization": f"Bearer {self.api_key}",
                         "Content-Type": "application/json"})
            with urllib.request.urlopen(
                    req, timeout=_http_timeout(
                        getattr(self, "role", None), max_tokens)) as resp:  # pragma: no cover
                raw = json.loads(resp.read().decode("utf-8"))
        _choice = (raw.get("choices") or [{}])[0]
        # 2026-07-27: `finish_reason` هرگز سطح‌بالا نمی‌آمد، پس یک پاسخِ **بریده** از
        # صدا درنمی‌آمد — فقط بعداً `extract_json` می‌شکست و آلارم «no JSON object»
        # می‌داد. مسیرِ LLM ِ گاورنر ۲۴+ ساعت روی همین کوری مرده ماند و هر epoch یک
        # فراخوانِ ~۳۰ ثانیه‌ای Fugu را دور ریخت. حالا صاحبِ فراخوان می‌تواند «length»
        # را ببیند و سقف را بالا ببرد به‌جای اینکه دنبالِ باگِ parser بگردد.
        _finish = _choice.get("finish_reason")
        _msg = _choice.get("message", {})
        # fallback به reasoning_content — مدل‌های reasoning گاهی content را خالی می‌گذارند (fail-soft، صادق)
        text = _msg.get("content") or ""   # OVN-5 step0: reasoning هرگز به‌جای پاسخ (فقط content)
        # 2026-08-16 (R27): مدل‌های thinking (deepseek-v4-flash) گاهی کلِ زنجیرهٔ
        # استدلالِ انگلیسی را داخلِ content می‌آورند و پاسخِ واقعیِ فارسی بعدش —
        # دو نمونهٔ زندهٔ 2026-08-13/15 در state/chat/chat-log.jsonl. اگر متن با
        # نشانگرِ استدلال شروع شود، از اولین پاراگرافِ فارسی به بعد برگردان؛
        # نشد، متن دست‌نخورده (fail-soft — پاکساز هرگز پاسخ را حذف نمی‌کند).
        text = _strip_reasoning_preamble(text)
        usage = raw.get("usage")
        if self.transport is None and not usage:
            raise TelemetryError("پاسخ بدون usage — متر کور؛ call را شکست‌خورده حساب کن")
        usage = usage or {}
        tin = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
        tout = usage.get("completion_tokens") or usage.get("output_tokens") or 0
        if self.transport is None and (tin + tout) == 0:
            raise TelemetryError("usage صفر/ناقص — صفر بی‌صدا ممنون (تلهٔ or 0)")
        # flat subscription → cost ۰ (سابسکرایب سقف است)
        if self.subscription == "max":
            cost = 0.0
        else:
            cost = (tin / 1e6) * self.price_in + (tout / 1e6) * self.price_out
        return {"text": text, "reasoning_content": _msg.get("reasoning_content") or "", "model": self.model, "provider": self.provider,
                "tokens_in": tin, "tokens_out": tout, "cost_usd": cost,
                "finish_reason": _infer_finish(_finish, tout, max_tokens),
                "subscription": self.subscription or "metered",
                "via_gateway": self.use_gateway,
                "stub": self.transport is not None}
