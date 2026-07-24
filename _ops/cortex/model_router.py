#!/usr/bin/env python3
"""model_router.py — «به همه جا API بده»: یک درِ واحد به سه مغز.

ردهٔ سه‌مغزی (رأی مالک 2026-07-10):
  local     → ollama qwen2.5:1.5b — کارهای ساده/روزمره. $0، همیشه مجاز (rate-limited).
  secondary → GLM (اشتراکِ MAX — نصفِ سهمیه مالِ سیستم) — تحقیق/سنتزِ متوسط.
  primary   → Fugu (اشتراکِ Pro — نصفِ سهمیه مالِ سیستم) — orchestration/عمیق.

انضباطِ paid (I2 + phase −1): هر دو ردهٔ پولی دوقفله‌اند — تاریخ ≥ 2026-07-21 +
`ACTIVATION-CORTEX-PAID.flag` (فقط مالک) — توجه (truth-map 2026-07-17): سپرِ تاریخ با
overrideهای مالک (`ACTIVATION-RESEARCH-EARLY.flag` / `ACTIVATION-GO-LIVE.flag`) دورزدنی
است و از 07-17 گیت عملاً باز است — و هر call به‌صورتِ lazy از
organ_gate.reserve/settle (ارگانِ ARCHITECT_SYS، الگوی allocate_llm) می‌گذرد؛ چون
subscription است، settle با هزینهٔ نقدیِ ۰ ولی استفاده METER می‌شود (سهمیه).
بسته/شکست = fallback به local؛ localِ خاموش = None با دلیل — هرگز کرش.

مصرف: `from cortex.model_router import ask` → ask("classify", "...") یا HTTP POST
/ask روی 127.0.0.1:8772 (کورتکس).
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE))
import opslib  # noqa: E402
import local_llm  # noqa: E402

ACT_CORTEX_PAID = opslib.OPS / "ACTIVATION-CORTEX-PAID.flag"
# اهرمِ مالک (رأی 2026-07-10 «اینترنت هرچه زودتر»): اگر مالک این فایل را بسازد،
# سپرِ تاریخِ فاز-۱ (2026-07-21) برای تحقیقِ پولی دور زده می‌شود — تصمیمِ آگاهانهٔ
# خودِ مالک، نه ایجنت. کلید همچنان لازم است؛ organ_gate/بودجه همچنان حاکم.
ACT_RESEARCH_EARLY = opslib.OPS / "ACTIVATION-RESEARCH-EARLY.flag"

# نگاشتِ نوعِ کار → ردهٔ پیش‌فرض (قابلِ override با tier=)
TASK_TIERS = {
    "daily": "local", "classify": "local", "summarize": "local",
    "think": "local", "triage": "local",
    "research": "secondary", "synthesize": "secondary", "draft": "secondary",
    "orchestrate": "primary", "deep": "primary", "plan": "primary",
    # M2 fugu-everywhere (2026-07-24): explicit tiers for organ work-types that were
    # bespoke or defaulted silently to local. ADDITIVE — existing callers unchanged;
    # unmapped tasks still fall back to "local" via TASK_TIERS.get(task, "local").
    "governor": "primary", "debate_architect": "primary",
    "debate_muse": "secondary", "tg_intent": "local",
    "chord.extract": "local", "heart_setpoint": "local",
}
_TIER_ROLE = {"secondary": "glm", "primary": "orchestr"}   # roleهای واقعیِ budgets.yaml

# نرمال‌سازی برای سنجشِ echo: اعراب/ZWNJ/RLM/گیومه حذف، فاصله فشرده — تا «قدمِ اول»
# با «قدم اول» یکی دیده شود (مدلِ محلی موقعِ بازتاب، اعراب را می‌اندازد).
_ECHO_STRIP = re.compile("[\\u064b-\\u0652\\u0670\\u200c\\u200f\\u00ab\\u00bb]")


def _norm_echo(s: str) -> str:
    return " ".join(_ECHO_STRIP.sub("", s or "").split())


def _local_quality_ok(text: str, prompt: str, min_chars: int) -> bool:
    """گیتِ کیفیتِ محلی-اول (رأی مالک 2026-07-18 «هوشمندتر»): طول به‌تنهایی کافی نیست.
    جوابی که عمدتاً بازتابِ (echo) خودِ prompt/قالب یا خط‌های تکراری باشد رد می‌شود تا
    نوبت واقعاً به ردهٔ پولی برسد — پیش از این، جوابِ آشغالِ بلندِ qwen گیتِ length-only
    را پاس می‌کرد و Fugu ساختاراً هرگز صدا نمی‌خورد (synthesis 2026-07-17).
    رد یا خطای گیت = همان مسیرِ پولیِ امروز (fail توی جهتِ کیفیت، نه سکوت)."""
    t = (text or "").strip()
    if len(t) < min_chars:
        return False
    p_norm = _norm_echo(prompt)
    lines = [_norm_echo(ln) for ln in t.splitlines() if len(ln.strip()) >= 12]
    if lines:
        echo = sum(1 for ln in lines if ln and ln in p_norm)
        if echo * 2 >= len(lines):        # ≥۵۰٪ خط‌ها بازتابِ خودِ prompt → طوطی، نه فکر
            return False
        if len(set(lines)) * 2 <= len(lines):   # اکثریتِ خط‌ها تکراری → degenerate
            return False
    # سقفِ هم‌پوشانیِ توکنی با prompt (مشخصهٔ مالک ~۰.۷): جوابی که تقریباً چیزی جز
    # واژگانِ خودِ prompt ندارد، فکر نیست — حتی اگر خطی «عیناً» echo نباشد.
    # کفِ واژگانِ یکتا: متنِ بلندِ کم‌واژه («بله بله بله…») degenerate است، نه جواب.
    toks = {w for w in _norm_echo(t).split() if len(w) >= 2}
    if len(toks) < 8:
        return False
    p_toks = {w for w in p_norm.split() if len(w) >= 2}
    if len(toks & p_toks) / len(toks) > 0.7:
        return False
    return True


def keys_present() -> dict:
    """حضورِ کلیدها (فقط bool — هرگز مقدار). env_loader مسیرِ رسمیِ لودِ .env است."""
    try:
        sys.path.insert(0, str(_HERE.parent / "budget"))
        import env_loader
        env_loader.load_env()
    except Exception:  # noqa: BLE001
        pass
    return {"fugu": bool(os.environ.get("FUGU_API_KEY")),
            "glm": bool(os.environ.get("GLM_API_KEY")),
            "deepseek": bool(os.environ.get("DEEPSEEK_API_KEY"))}


def paid_gate() -> tuple[bool, str]:
    """دوقفلهٔ ردهٔ پولی: تاریخِ phase−1 + پرچمِ مالک.
    اهرمِ زودهنگام: اگر ACTIVATION-RESEARCH-EARLY.flag باشد (فقط مالک می‌سازد)، سپرِ
    تاریخ دور زده می‌شود ولی پرچمِ فعال‌سازی همچنان لازم است (تصمیمِ آگاهانهٔ مالک)."""
    if ACT_RESEARCH_EARLY.exists():
        if ACT_CORTEX_PAID.exists():
            return True, "open (owner research-early override — سپرِ تاریخ دور زده شد)"
        return False, "research-early فعال ولی ACTIVATION-CORTEX-PAID.flag نیست"
    return opslib.live_gate_open(ACT_CORTEX_PAID)


def _ask_paid(tier: str, prompt: str, system: str, max_tokens: int) -> dict | None:
    """مسیرِ پولی — فقط پشتِ گیتِ باز. lazy organ_gate (I2)؛ metering سهمیه‌ای:
    settle(actual=0.0) چون subscription؛ خودِ reserve/settle مصرف را ثبت می‌کند."""
    ok, why = paid_gate()
    if not ok:
        return None
    role = _TIER_ROLE.get(tier)
    if not role:
        return None
    try:
        sys.path.insert(0, str(opslib.DEBATE_DIR))
        from client import MultiProviderClient  # noqa: E402
        import organ_gate                       # noqa: E402
        cli = MultiProviderClient(role=role)
        est = cli.est_worst_case(len(system) + len(prompt), max_tokens=max_tokens) \
            if hasattr(cli, "est_worst_case") else 0.05
        r = organ_gate.reserve("ARCHITECT_SYS", est, task=f"cortex-{tier}")
        if not r.get("allow"):
            return None
        try:
            out = cli.complete(system, prompt, max_tokens=max_tokens)
        except Exception:
            organ_gate.release("ARCHITECT_SYS", est, task=f"cortex-{tier}")
            raise
        # subscription: هزینهٔ نقدی ~۰ ولی استفاده متر می‌شود (سهمیهٔ نصفِ اشتراک)
        organ_gate.settle("ARCHITECT_SYS", est,
                          float(out.get("cost_usd", 0.0) or 0.0),
                          task=f"cortex-{tier}")
        return {"text": out.get("text", ""), "tier": tier,
                "model": out.get("model"), "cost_usd": out.get("cost_usd", 0.0)}
    except Exception as e:  # noqa: BLE001 — پولی شکست → fallback
        opslib.alert([f"cortex router {tier} failed (fallback local): "
                      f"{type(e).__name__}: {e}"])
        return None


def _scored_tier(task: str) -> str | None:
    """مشاورِ route_scorer پشتِ پرچمِ CORTEX_ROUTE_SCORER (CORTEX-02).

    فقط وقتی صدا زده می‌شود که پرچم روشن باشد و tier صریح داده نشده باشد. خالص و
    $۰ (route_scorer فقط امتیاز می‌دهد، هیچ callِ LLM ندارد). هر خطا/خروجیِ نامعتبر
    → None تا مسیرِ ایستای TASK_TIERS دقیقاً مثلِ امروز جاری شود (fail-soft)."""
    try:
        import route_scorer  # noqa: E402 — هم‌ماژول در cortex؛ در sys.path هست
        out = route_scorer.score_route(task, None)
        tier = out.get("tier") if isinstance(out, dict) else None
        if tier in ("local", "secondary", "primary"):
            return tier
    except Exception as e:  # noqa: BLE001 — مشاور هرگز صداکننده را نکشد
        try:
            opslib.alert([f"cortex route_scorer consult failed (static fallback): "
                          f"{type(e).__name__}: {e}"])
        except Exception:  # noqa: BLE001
            pass
    return None


def _ask_impl(task: str, prompt: str, system: str = "", max_tokens: int = 400,
              tier: str | None = None, opener=None, quality=None) -> dict:
    """درِ واحد. خروجی همیشه dict: {ok, tier?, text?, reason?}.
    ردهٔ پولی بسته/ناموفق → local؛ local خاموش → ok=False با دلیلِ صادق.

    CORTEX-02: اگر پرچمِ CORTEX_ROUTE_SCORER روشن باشد و tier صریح نداده شده باشد،
    route_scorer.score_route مشورت می‌شود (fail-soft)؛ خطا/خالی → نگاشتِ ایستای
    TASK_TIERS. پرچمِ خاموش (پیش‌فرض) = رفتار byte-identical با امروز.

    quality (اختیاری): callable(text)->bool که فقط گیتِ محلی-اولِ ردهٔ secondary را
    سخت‌گیرتر می‌کند (مثلاً synthesis حداقل ۲ پروپوزالِ واقعی می‌خواهد). None =
    گیتِ عمومیِ _local_quality_ok. روی مسیرِ پولی/tierهای دیگر هیچ اثری ندارد."""
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return {"ok": False, "reason": "kill-switch"}
    # CONTEXT-FENCE (پشتِ OCTOPUS_WIRE_CONTEXT_FENCE): promptِ ورودی ممکن است دادهٔ نامعتمد
    # (لیدِ خام/وب/ایمیل) داشته باشد؛ برای الگوهای prompt-injection غربالش کن. flag خاموش →
    # passthroughِ بایت‌به‌بایت. observe-only در v1: تشخیص → alert (side-effect واقعی)، هرگز
    # prompt را تغییر/بلاک نمی‌کند (امنِ مسیرِ داغِ LLM). §۴ fail-soft — غربال tick را نمی‌کشد.
    try:
        import os as _os3
        _cd = _os3.path.dirname(_os3.path.abspath(__file__))
        if _cd not in sys.path:
            sys.path.insert(0, _cd)
        import context_fence as _fence   # noqa: WPS433 — همسایهٔ همین ماژول
        if _fence.enabled():
            _scr = _fence.screen(prompt)
            if not _scr.get("clean", True):
                opslib.alert([f"context_fence: ورودیِ مشکوک به prompt-injection در "
                              f"task={str(task)[:32]!r} — کدها: {_scr.get('findings')}"])
    except Exception:  # noqa: BLE001 — غربال هرگز مسیرِ LLM را نمی‌کشد
        pass
    want = tier
    if not want and os.environ.get("CORTEX_ROUTE_SCORER"):
        want = _scored_tier(task)
    want = want or TASK_TIERS.get(task, "local")
    _lo_rejected = None      # جوابِ محلیِ رد-کیفیت — اگر پولی هم شکست، بهتر از هیچ
    if want in ("secondary", "primary"):
        # 2026-07-16 محلی-اول (اقتصادِ مغز، رأی مالک «محلی رایگان، پولی فقط برای کارِ بزرگ»):
        # پشتِ CORTEX_LOCAL_FIRST، ردهٔ میانی (secondary: research/synthesize/draft) اول از
        # مغزِ محلیِ $0 می‌پرسد؛ یک گیتِ کیفیتِ قطعی (متنِ ناخالی با طولِ حداقلی) خروجی را
        # می‌سنجد — پاس = همان جواب، رد/در دسترس نبودن = مسیرِ پولیِ امروز، بایت‌به‌بایت.
        # ردهٔ سنگین (primary: plan/deep/orchestrate) هرگز محلی-اول نمی‌شود — کارِ بزرگ = API.
        if want == "secondary" and os.environ.get("CORTEX_LOCAL_FIRST") == "1":
            try:
                _min_chars = int(os.environ.get("LOCAL_FIRST_MIN_CHARS", "80"))
                _lo = local_llm.ask(prompt, system=system, max_tokens=max_tokens,
                                    opener=opener)
                # 2026-07-18 (رأی مالک «هوشمندتر»): گیتِ length-only جوابِ طوطی‌وار را
                # پاس می‌کرد و Fugu گرسنه می‌ماند — حالا کیفیت (یا چکِ اختصاصیِ صداکننده).
                _gate = quality or (lambda _t: _local_quality_ok(_t, prompt, _min_chars))
                if _lo and _gate(str(_lo.get("text", ""))):
                    return {"ok": True, **_lo, "local_first": True}
                _lo_rejected = _lo
            except Exception:  # noqa: BLE001 — محلی-اول هرگز مسیرِ پولی را نکشد
                pass
        # 2026-07-15 key-aware: tierِ خواسته اول، بعد tierِ پولیِ دیگر — ولی فقط آن‌هایی که کلید
        # دارند (وگرنه یک failِ الکی می‌سوزانیم و به محلیِ آشغال می‌افتیم). این کاری می‌کند که
        # اشتراکِ Fuguِ مالک واقعاً استفاده شود حتی وقتی tierِ خواسته GLMِ بی‌کلید بود (باگِ اصلی).
        kp = keys_present()
        _has = {"secondary": bool(kp.get("glm")), "primary": bool(kp.get("fugu"))}
        order = [want] + [t for t in ("primary", "secondary") if t != want]
        tried = []
        for _t in order:
            if not _has.get(_t):
                continue
            out = _ask_paid(_t, prompt, system, max_tokens)
            tried.append(_t)
            if out:
                return {"ok": True, **out}
        gate_ok, gate_why = paid_gate()
        if not gate_ok:
            fallback_reason = gate_why
        elif not any(_has.values()):
            fallback_reason = "no-paid-key"
            try:
                opslib.alert(["cortex: هیچ کلیدِ پولی (Fugu/GLM) در دسترس نیست — مغز روی محلیِ $0"])
            except Exception:  # noqa: BLE001
                pass
        else:
            fallback_reason = "paid-call-failed"
            try:
                opslib.alert([f"🔴 cortex: مغزِ پولی روی {tried or order} شکست خورد → "
                              f"محلیِ آشغال. paid brain broken (کلید/شبکه/quota؟)"])
            except Exception:  # noqa: BLE001
                pass
    else:
        fallback_reason = None
    out = local_llm.ask(prompt, system=system, max_tokens=max_tokens,
                        opener=opener)
    if not out and _lo_rejected:
        # rate-limit ۱۰ثانیه‌ای، callِ دومِ محلی را می‌بُرد — جوابِ رد-کیفیتِ همین چند
        # ثانیه پیش صادقانه‌تر از «local-llm-unavailable» است (fallback_from می‌گوید چرا).
        out = _lo_rejected
    if out:
        res = {"ok": True, **out}
        if fallback_reason:
            res["fallback_from"] = f"{want}: {fallback_reason}"
        return res
    return {"ok": False,
            "reason": "local-llm-unavailable"
                      + (f" · {want} بسته: {fallback_reason}" if fallback_reason else ""),
            "hint": "ollama serve + مدل qwen2.5:1.5b (HH-P10)"}


def ask(task: str, prompt: str, system: str = "", max_tokens: int = 400,
        tier: str | None = None, opener=None, quality=None) -> dict:
    """درِ واحدِ LLM (wrapper). رفتار = `_ask_impl` بایت‌به‌بایت + یک side-effectِ observability:
    هر call واقعیِ LLM را در استریمِ «سوختِ» قلب ثبت می‌کند (fuel_meter) تا producers.velocity_meter
    دادهٔ واقعی بخواند — بستنِ orphanِ کانالِ خون (HH-fuel، 2026-07-21).

    flag `OCTOPUS_WIRE_HEART_FUEL` خاموش (پیش‌فرض) → fuel_meter.record خودش no-op است، پس این
    wrapper بایت‌به‌بایتِ امروز است. ثبت در try/except و هرگز محتوا/prompt ثبت نمی‌شود (فقط
    tier/model/cost/latency) — مسیرِ داغِ LLM هرگز کشته نمی‌شود."""
    import time as _t
    _t0 = _t.time()
    res = _ask_impl(task, prompt, system, max_tokens, tier=tier, opener=opener, quality=quality)
    try:
        if isinstance(res, dict) and res.get("ok") and res.get("reason") != "kill-switch":
            _hp = str(_HERE.parent / "heart") if "_HERE" in globals() else \
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "heart")
            if _hp not in sys.path:
                sys.path.insert(0, _hp)
            import fuel_meter as _fm   # noqa: WPS433 — lazy؛ خودش flag/kill را چک می‌کند
            _fm.record(str(res.get("tier") or "local"), str(res.get("model") or ""),
                       cost_usd=float(res.get("cost_usd") or 0.0),
                       ms=int((_t.time() - _t0) * 1000), ok=True)
    except Exception:  # noqa: BLE001 — observability هرگز مسیرِ LLM را نمی‌کشد
        pass
    return res


if __name__ == "__main__":
    print(json.dumps({"keys": keys_present(), "paid_gate": paid_gate(),
                      "sample": ask("think", "وضعیتِ یک ارگانیسمِ در حالِ یادگیری را در یک جمله توصیف کن.")},
                     ensure_ascii=False, indent=2))
