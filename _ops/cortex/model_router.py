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
sys.path.insert(0, str(_HERE.parent))
import opslib  # noqa: E402
import local_llm  # noqa: E402
import circuit_breaker as _cb  # noqa: E402  # per-provider breaker (2026-07-25): Fugu timeoutlarını fail-fast کند

ACT_CORTEX_PAID = opslib.OPS / "ACTIVATION-CORTEX-PAID.flag"
# اهرمِ مالک (رأی 2026-07-10 «اینترنت هرچه زودتر»): اگر مالک این فایل را بسازد،
# سپرِ تاریخِ فاز-۱ (2026-07-21) برای تحقیقِ پولی دور زده می‌شود — تصمیمِ آگاهانهٔ
# خودِ مالک، نه ایجنت. کلید همچنان لازم است؛ organ_gate/بودجه همچنان حاکم.
ACT_RESEARCH_EARLY = opslib.OPS / "ACTIVATION-RESEARCH-EARLY.flag"

# ── ردِ append-only هر تماسِ پولی (B4) ────────────────────────────────────────
# تنها فایلی که به سؤالِ «آیا مغزِ پولی واقعاً کار کرد؟» جواب می‌دهد.
# عمداً پشتِ فلگ نیست: فلگ restart می‌خواهد و می‌تواند بی‌صدا خاموش بماند، و آن‌وقت
# «فایلِ خالی» با «کار نکرد» یکی می‌شود. $۰، بدونِ شبکه، fail-soft، هرگز prompt/کلید.
# subscription=max ⇒ cost_usd ساختاراً 0.0 است — شاهدِ مصرف این‌جا tokens/attempt است، نه دلار.
PAID_LOG = opslib.STATE_DIR / "paid-calls.jsonl"

_SECRET_RE = re.compile(r'(?i)\b(bearer|api[_-]?key|authorization)\b\s*[:=]?\s*[A-Za-z0-9_\-\.]{10,}')


def _receipt_ids(task: str) -> tuple[str | None, str | None]:
    """Caller/context only. Never invent task_id from pid/time/model."""
    try:
        from nervous_recovery.task_context import resolve  # noqa: WPS433
        r = resolve(caller_task=task, run_id=os.environ.get("OCTOPUS_RUN_ID"))
        tid = r.get("task_id")
        rid = r.get("run_id")
        return (str(tid)[:64] if tid else None,
                str(rid)[:64] if rid else None)
    except Exception:  # noqa: BLE001 — attribution helper must not kill the brain
        t = str(task or "").strip()[:64] or None
        r = str(os.environ.get("OCTOPUS_RUN_ID") or "").strip()[:64] or None
        return t, r


def _error_detail(exc: Exception, limit: int = 300) -> str:
    """۲۰۲۶-۰۸-۰۹ (پیشرفتِ واقعی، فازِ ۱): جزئیاتِ خطا برایِ paid-calls.jsonl —
    نه فقط اسمِ کلاس. امروز دقیقاً همینِ نبودنش باعث شد نتوانم بفهمم HTTPError
    یعنی چه — کلیدِ خراب، ۴۲۹، یا ۵۰۰؟ فقط از داشبوردِ Sakana فهمیدیم (سقفِ
    هفتگی، نه کلید). برای دفعهٔ بعد، status/reason/بدنهٔ پاسخ همین‌جا می‌ماند.

    فقط پیام/بدنهٔ خطا را می‌بیند، هرگز کلید را — secretها هم یک لایهٔ دومِ
    دفاعی این‌جا حذف می‌شوند (لایهٔ اولِ واقعی این است که کلید هرگز در exception
    args ننشیند، چون client.py آن را در body/header می‌گذارد نه پیام‌خطا)."""
    import urllib.error as _ue
    parts = [f"{type(exc).__name__}: {exc}"]
    if isinstance(exc, _ue.HTTPError):
        try:
            body = exc.read().decode("utf-8", "replace").strip()
            if body:
                parts.append(body)
        except Exception:  # noqa: BLE001
            pass
    text = " | ".join(parts)
    text = _SECRET_RE.sub(r'\1 <REDACTED>', text)
    return text[:limit]


def _error_http_code(exc: Exception) -> "int | None":
    """HTTP status code به‌صورت ساختاری — ۲۰۲۶-۰۸-۱۰ (soak): قبلاً فقط متنِ
    'HTTP Error 400: Bad Request' در error_detail می‌نشست و استخراجِ status
    از روی متن حدس‌زنی بود. حالا e.code جدا ذخیره می‌شود تا کارتِ امتیازِ
    soak بتواند 401/429/5xx را بدون parse تشخیص دهد."""
    import urllib.error as _ue
    if isinstance(exc, _ue.HTTPError):
        return int(getattr(exc, "code", 0) or 0) or None
    return None


def _log_provider_usage_safe(*, model: str, task: str, tier: str,
                             usage: dict | None = None, latency_ms: int = 0,
                             status: str = "ok", error: str = "") -> None:
    """۲۰۲۶-۰۸-۰۹ (پیشرفتِ واقعی، فازِ ۲): پلِ گم‌شده به ledger ِ owner_cockpit.

    یافتهٔ امروز: model_router._ask_paid هرگز از fugu_proxy.py رد نمی‌شود —
    مستقیم به sakana.ai می‌زند. یعنی تبِ Fugu در owner_cockpit صفر ترافیکِ
    واقعی می‌بیند، هرچند خودِ پراکسی ساخته و تست شده. به‌جایِ اجبارِ ترافیک از
    یک پروسهٔ پراکسیِ همیشه-روشنِ تازه (هزینهٔ زیرساخت)، همان تابعِ نوشتنِ
    آمادهٔ db.py مستقیم از این‌جا صدا زده می‌شود — دو نویسنده نیست، یک
    نویسنده از دو نقطهٔ صدا (fail-soft، پشتِ فلگِ خودِ OCTOPUS_WIRE_OWNER_DB،
    پیش‌فرض خاموش — این تابع تا فلگ روشن نشود کاملاً no-op است)."""
    try:
        _oc = str(_HERE.parent / "owner_cockpit")
        if _oc not in sys.path:
            sys.path.insert(0, _oc)
        import db as _ocdb  # noqa: WPS433 — owner_cockpit/db.py
        _ocdb.log_provider_usage(
            model=model, task=task, tier=tier, usage=usage or {},
            latency_ms=int(latency_ms), status=status, error=error[:300])
    except Exception:  # noqa: BLE001 — ledger هرگز نباید مسیرِ اصلیِ مغز را بشکند
        pass


def _paid_log(**rec) -> None:
    try:
        opslib.append_jsonl(PAID_LOG, {"ts": opslib.now_iso(), **rec})
    except Exception:  # noqa: BLE001 — لاگ هرگز مسیرِ مغز را نمی‌کشد
        pass

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
    # Talk Discovery: collaborator → DeepSeek (role=reason / secondary).
    # 2026-08-12 owner: «با DeepSeek حرف بزن» — local/ollama عمداً نه (hang).
    # Soft call-cap = OCTOPUS_COLLAB_MODEL_DAILY_CAP. Rollback: "local".
    "collab_chat": "secondary",
}
_TIER_ROLE = {"secondary": "reason", "primary": "reason"}   # roleهای واقعیِ budgets.yaml
# 2026-08-15 (شب — رأی مالک: «فوگو گرونه، فعلا با دیپ‌سیک»): primary از orchestr
# (sakana/fugu) به reason (deepseek-v4-flash, thinking) برگشت. rollback: همین
# خط به "orchestr" برگردد + ری‌استارت. قیمت/بودجه خودکار از budgets.yaml
# (role reason: in $0.14 / out $0.28 per 1M — قفل‌شده و VERIFIED).
# 2026-08-10 (Deployment): secondary از glm به reason (deepseek-v4-flash) عوض شد —
# طبق مگاپرامپتِ تعویضِ نقشهٔ مدل‌ها. rollback: کامنتِ یک خط به glm برمی‌گردد.

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


def is_useless_truncation(text: str, finish_reason) -> bool:
    """پاسخِ بریده‌ای که متنِ مرئیِ قابلِ‌استفاده ندارد → شکست، نه موفقیت.

    عمداً **باریک**؛ هر دو شرط لازم است:
      · `finish_reason == "length"` — تولید قطع شده (خودِ این از `client._infer_finish`
        می‌آید که وقتی provider ساکت است از `tokens_out >= max_tokens` استنتاجش می‌کند).
      · و متنِ مرئی زیرِ `PAID_MIN_USEFUL_CHARS` (پیش‌فرض ۴۰) باشد.

    پس این‌ها **عبور می‌کنند** و باید عبور کنند:
      · پاسخِ کوتاهِ سالم که به سقف نخورده («بله») — جوابِ درستِ کوتاه است.
      · پاسخِ بریدهٔ طولانی — ناقص ولی مفید؛ صاحبِ فراخوان خودش تصمیم بگیرد.

    شاهدی که این را لازم کرد (`state/paid-calls.jsonl`، ۲۰۲۶-۰۷-۲۹T۱۷:۳۳:۰۸):
    `tokens_out=500` (=سقفِ آن‌روزِ سنتز) با `chars_out=3` → سنتز صفر پیشنهاد ثبت
    کرد و هیچ آلارمی نزد. تابعِ خالص است تا گاردش بتواند خودِ همین منطق را بسنجد،
    نه وجودِ یک رشته در سورس."""
    try:
        min_useful = int(os.environ.get("PAID_MIN_USEFUL_CHARS", "40"))
    except (TypeError, ValueError):
        min_useful = 40
    return finish_reason == "length" and len(str(text or "").strip()) < min_useful


def _ask_paid(tier: str, prompt: str, system: str, max_tokens: int,
              task: str = "", temperature: float | None = None, seed: int | None = None) -> dict | None:
    """مسیرِ پولی — فقط پشتِ گیتِ باز. lazy organ_gate (I2)؛ metering سهمیه‌ای:
    settle(actual=0.0) چون subscription؛ خودِ reserve/settle مصرف را ثبت می‌کند."""
    ok, why = paid_gate()
    if not ok:
        return None
    role = _TIER_ROLE.get(tier)
    if not role:
        return None
    # ── RCPT-2 (2026-08-19, CORE-AUTO-DEBUG): COST_UNOBSERVABLE یا نقضِ سقفِ
    # فراخوانی در رسیدهایِ امروز ⇒ مسیرِ پولی بسته می‌ماند — همان fail-closedِ
    # وعده‌داده‌شده در کامنتِ COST-OBS-1 که تا امروز خوانده نمی‌شد.
    try:
        from cost_receipt import paid_blocked_today  # noqa: E402 — هم‌پوشه
        if paid_blocked_today():
            _paid_log(task=task, tier=tier, role=role, ok=False,
                      error="paid_blocked_cost_unobservable", ms=0,
                      note="RCPT-2: receipt-visible block; manual/owner reset required")
            return None
    except Exception:  # noqa: BLE001 — گارد هرگز مسیر را نمی‌کشد
        pass
    # ── FX-EXP (F18, 2026-08-19): حسابداریِ AUD به FXِ پین‌شدهٔ تازه نیاز دارد —
    # stale/missing ⇒ مسیرِ پولی بسته (fail-closed، هم‌ترازِ validate_fx در Live-4).
    try:
        from cost_receipt import fx_pinned_fresh  # noqa: E402 — هم‌پوشه
        _okfx, _whyfx = fx_pinned_fresh()
        if not _okfx:
            _paid_log(task=task, tier=tier, role=role, ok=False,
                      error=f"fx_{_whyfx}", ms=0,
                      note="F18: paid path blocked until fresh FX pin (pricing_pinned.json)")
            return None
    except Exception:  # noqa: BLE001
        pass
    # ── circuit breaker (per-provider، auto half-open recovery) ────────────────
    # 2026-07-25: fugu_quota global بود (موفقیتِ GLM consecutive_failures را ریست
    # می‌کرد) و recovery دستی بود (فایلِ STOP-FUGU). در زنده، fugu ۳ ساعتِ پشتِ هم
    # timeout شد چون هیچ fail-fast per-providerای وجود نداشت. این breaker:
    #   · target = role ("orchestr"/"glm") → per-provider نه global
    #   · بعد از N شکست (پیش‌فرض ۵) OPEN → فراخوانیِ بعدی بی‌شبکه None برمی‌گرداند
    #   · بعد از cooldown (۶۰s) خودکار HALF_OPEN → یک probe → موفقیت → CLOSED
    # با fugu_quota complementary است (breaker=per-provider/خودکار، quota=daily-cap/دستی).
    _ccb = _cb.check(role)
    if not _ccb.get("allow"):
        _paid_log(task=task, tier=tier, role=role, ok=False,
                  error=f"circuit_{_ccb.get('state')}",
                  ms=0, note=_ccb.get("reason", ""))
        return None
    try:
        sys.path.insert(0, str(opslib.DEBATE_DIR))
        from client import MultiProviderClient  # noqa: E402
        import organ_gate                       # noqa: E402
        cli = MultiProviderClient(role=role)
        est = cli.est_worst_case(len(system) + len(prompt), max_tokens=max_tokens) \
            if hasattr(cli, "est_worst_case") else 0.05
        # A3 (2026-08-20): attribution + bucket cap BEFORE reserve/network.
        try:
            sys.path.insert(0, str(_HERE.parent))
            from cognition_quota import gate_paid_intent  # noqa: WPS433
            _gq = gate_paid_intent(
                task=task,
                run_id=str(os.environ.get("OCTOPUS_RUN_ID") or ""),
                bucket=str(os.environ.get("OCTOPUS_COGNITION_BUCKET") or "telegram_normal"))
            if not _gq.get("allow"):
                _paid_log(task=task, tier=tier, role=role, ok=False,
                          error=f"cognition_quota_{_gq.get('reason')}", ms=0,
                          note=_gq.get("mode"))
                return None
        except Exception:  # noqa: BLE001
            if os.environ.get("OCTOPUS_PAID_COGNITION", "0") != "1":
                _paid_log(task=task, tier=tier, role=role, ok=False,
                          error="cognition_quota_guard_error", ms=0)
                return None
        r = organ_gate.reserve("ARCHITECT_SYS", est, task=f"cortex-{tier}")
        if not r.get("allow"):
            return None
        # ── گاردِ فوگو (روزِ اول): شمارندهٔ attempt-counted + STOP-FUGU ──────────
        import fugu_quota  # noqa: E402
        _q = fugu_quota.reserve(tier, "ARCHITECT_SYS")
        if not _q.get("allow"):
            organ_gate.release("ARCHITECT_SYS", est, task=f"cortex-{tier}")
            _paid_log(task=task, tier=tier, role=role, ok=False,
                      error=f"quota_{_q.get('reason')}", ms=0,
                      quota_used=_q.get("used"))
            return None
        import time as _pt
        _t0 = _pt.time()
        try:
            # OVN-5: temperature قابل‌عبور — پیش‌فرض None = رفتار قبلی؛ پروب‌ها 0 می‌دهند
            out = cli.complete(system, prompt, max_tokens=max_tokens,
                               temperature=temperature if temperature is not None else 0.7,
                               seed=seed)
            fugu_quota.ok(tier)
            _cb.record_success(role)   # provider سالم است → breaker را reset/بهبود بده
        except Exception as _ce:
            fugu_quota.fail(tier, error=_ce)
            _cb.record_failure(role, f"{type(_ce).__name__}: {_ce}")   # provider ناسالم
            _detail = _error_detail(_ce)
            _http = _error_http_code(_ce)
            _elapsed_ms = int((_pt.time() - _t0) * 1000)
            _paid_log(task=task, tier=tier, role=role,
                      provider=getattr(cli, "provider", ""),
                      model=getattr(cli, "model", ""),
                      via_gateway=bool(getattr(cli, "use_gateway", False)),
                      subscription=getattr(cli, "subscription", None) or "metered",
                      ok=False, error=type(_ce).__name__, error_detail=_detail,
                      http_code=_http,
                      ms=_elapsed_ms,
                      quota_used=_q.get("used"))
            _log_provider_usage_safe(model=getattr(cli, "model", "") or role,
                                     task=task, tier=tier, latency_ms=_elapsed_ms,
                                     status="error", error=_detail)
            organ_gate.release("ARCHITECT_SYS", est, task=f"cortex-{tier}")
            raise
        # subscription: هزینهٔ نقدی ~۰ ولی استفاده متر می‌شود (سهمیهٔ نصفِ اشتراک)
        organ_gate.settle("ARCHITECT_SYS", est,
                          float(out.get("cost_usd", 0.0) or 0.0),
                          task=f"cortex-{tier}")
        _elapsed_ms = int((_pt.time() - _t0) * 1000)
        # ── COST-OBS-1 (رأی مالک 2026-08-19): رسیدِ هزینهٔ پرداختی در همان
        # لایه‌ای که usage/cost_usd هنوز در دسترس است — fail-soft برای مغز،
        # fail-closed برای پرداخت: COST_UNOBSERVABLE ⇒ فراخوانیِ بعدیِ پرداختی بسته می‌شود.
        try:
            import hashlib as _hl, json as _jn, datetime as _dt
            from datetime import timezone as _tz
            from pathlib import Path as _P
            from cost_receipt import CostReceiptAdapter, remaining_budget_aud  # noqa: WPS433 — هم‌پوشه
            _rp = _P(str(_P(__file__).resolve().parent.parent / "state" / "cortex" / "cost-receipts.jsonl"))
            _tid, _rid = _receipt_ids(task)
            _recpt = CostReceiptAdapter().build(
                trace_id=f"paid-{tier}-{int(_pt.time()*1000)}",
                provider=str(getattr(cli, "provider", "") or ""),
                model=str(out.get("model") or ""),
                ts_req=_dt.datetime.fromtimestamp(_t0, _tz.utc).isoformat(timespec="seconds"),
                ts_resp=_dt.datetime.now(_tz.utc).isoformat(timespec="seconds"),
                # RCPT-1 (2026-08-19): مبنای بودجه = باقی‌ماندهٔ روز از رسیدهای خودِ
                # امروز — نه هزینهٔ خودِ فراخوانی (باگِ budget_afterِ منفی).
                budget_before_aud=remaining_budget_aud(_rp),
                usage_payload=({"cost_usd": out.get("cost_usd"),
                                "prompt_tokens": out.get("tokens_in"),
                                "completion_tokens": out.get("tokens_out")}
                               if out.get("cost_usd") is not None else None),
                tokens_in=out.get("tokens_in"), tokens_out=out.get("tokens_out"),
                input_sha256=_hl.sha256(str(prompt).encode("utf-8", "replace")).hexdigest(),
                # T50 + Wave0 plumbing: task from caller/context resolver; never inferred.
                task_id=_tid,
                run_id=_rid)
            _rp.parent.mkdir(parents=True, exist_ok=True)
            _rp.open("a", encoding="utf-8").write(_jn.dumps(_recpt, ensure_ascii=False, default=str) + "\n")
        except Exception:  # noqa: BLE001 — رسید هرگز مغز را نمی‌کشد
            pass
        # ── T48 producer_1 (دستور #۸ §۳ + اصلاح T52 دستور #۱۰ §۲) ─────────
        # occurred_at اولویت با «زمان سرورِ provider» است (فیلد created، unix
        # seconds — ساعتِ مستقلِ بیرونی)؛ در نبودش fallback به router_request_ts
        # (DELAY_BEARING_SAME_CLOCK — همان ساعت ماشین، فقط تأخیر می‌سازد).
        # انحراف ساعت (server − local) در payload ثبت می‌شود؛
        # occurred>recorded خودکار در spine ⇒ CLOCK_SKEW_SUSPECTED.
        if str(os.environ.get("OCTOPUS_T48_EVENT_TIME", "1")).strip().lower() in ("1", "true", "yes", "on"):
            try:
                import spine_adapters as _sat48  # noqa: WPS433 — همان path زندهٔ provider_adapter
                _t48_occ = None
                _t48_src = None
                _t48_prec = None
                try:
                    _sc = out.get("server_created")
                    if _sc is not None:
                        from datetime import datetime as _dt52, timezone as _tz52
                        _t48_occ = _dt52.fromtimestamp(int(_sc), tz=_tz52.utc).isoformat(timespec="seconds")
                        _t48_src = "provider_server_created"
                        _t48_prec = "1s"
                except Exception:  # noqa: BLE001 — پارس نشد → fallback
                    _t48_occ = None
                if _t48_occ is None:
                    _t48_occ = _dt.datetime.fromtimestamp(_t0, _tz.utc).isoformat(timespec="milliseconds")
                    _t48_src = "router_request_ts"
                    _t48_prec = "ms"
                _sat48.emit_event(
                    event_type="accepted-measurement", domain="provider",
                    correlation_id=str(_recpt.get("trace_id") or f"paid-{tier}-{int(_pt.time()*1000)}"),
                    subject=str(task or "unknown")[:64],
                    producer="model_router_t48", trust="DETERMINISTIC",
                    occurred_at=_t48_occ,
                    event_time_source=_t48_src, time_precision=_t48_prec,
                    payload={"tier": str(tier)[:16], "task": str(task or "")[:40],
                             "receipt_trace": str(_recpt.get("trace_id") or "")[:48],
                             "router_request_ts": _dt.datetime.fromtimestamp(
                                 _t0, _tz.utc).isoformat(timespec="milliseconds")},
                    idempotency_key=f"{_recpt.get('trace_id')}|t48-provider-call")
            except Exception:  # noqa: BLE001 — instrumentation هرگز مسیر پولی را نمی‌کشد
                pass
        _paid_log(task=task, tier=tier, role=role,
                  provider=getattr(cli, "provider", ""),
                  model=out.get("model"),
                  via_gateway=bool(out.get("via_gateway")),
                  subscription=out.get("subscription"),
                  ok=True,
                  tokens_in=out.get("tokens_in"), tokens_out=out.get("tokens_out"),
                  cost_usd=float(out.get("cost_usd", 0.0) or 0.0),
                  chars_out=len(out.get("text") or ""),
                  ms=_elapsed_ms,
                  quota_used=_q.get("used"))
        # ۲۰۲۶-۰۸-۰۹ (پیشرفتِ واقعی، فازِ ۲): همان رکورد به ledger ِ owner_cockpit
        # هم می‌رود — تبِ Fugu در کاکپیت اولین‌بار ترافیکِ واقعی می‌بیند.
        _log_provider_usage_safe(
            model=out.get("model") or role, task=task, tier=tier,
            usage={"input_tokens": out.get("tokens_in") or 0,
                   "output_tokens": out.get("tokens_out") or 0,
                   "total_tokens": (out.get("tokens_in") or 0) + (out.get("tokens_out") or 0),
                   "total_cost_usd": float(out.get("cost_usd", 0.0) or 0.0)},
            latency_ms=_elapsed_ms, status="ok")
        # ── سایهٔ output_critic (کارت ۲ کاشف، رأی مالک 2026-08-16): امتیازِ
        # کیفیتِ چهاربعدی، صفر اثر — فقط log-only. fail-soft: خطا هرگز مغز را نمی‌کشد.
        try:
            _critic = __import__("output_critic").grade(
                [{"ts": _pt.time(), "text": str(out.get("text") or ""), "stream": task}])
            _paid_log(kind="critic_shadow", task=task, tier=tier, role=role,
                      scores=_critic.get("scores", {}))
        except Exception:
            pass
        # ── پاسخِ بریدهٔ بی‌متن = شکست، نه موفقیت (۲۰۲۶-۰۷-۳۰) ──────────────────
        # ۰۷-۲۷ `finish_reason` را عبور دادند تا صاحبِ فراخوان بریدگی را ببیند، ولی
        # **هیچ‌کس نمی‌خواندش** و sakana هم هرگز پرش نمی‌کرد (۲۰۶/۲۰۶ تماسِ موفق
        # `None`). نتیجه: مدلِ استدلالی کلِ بودجه را صرفِ تفکر می‌کرد، سه کاراکتر
        # بیرون می‌داد، و این تابع همان را با `ok=True` تحویل می‌داد. شاهدِ زنده:
        # `2026-07-29T17:33:08 tokens_out=500 (=سقف) chars_out=3` → سنتز صفر
        # پیشنهاد ثبت کرد و هیچ آلارمی نزد.
        #
        # حالا این حالت مثلِ هر شکستِ دیگرِ tier رفتار می‌کند: `None` برگردان تا
        # صداکننده ردهٔ پولیِ بعدی یا محلی را امتحان کند. استابِ بی‌مصرف بدتر از
        # نبودِ جواب است، چون خودش را جوابِ معتبر جا می‌زند.
        # عمداً باریک: فقط وقتی **هم** بریده باشد **و هم** متنِ مرئی بی‌مصرف. پاسخِ
        # کوتاهِ سالم (که به سقف نخورده) و پاسخِ بریدهٔ طولانی (که ناقص ولی مفید
        # است) هر دو دست‌نخورده عبور می‌کنند.
        _txt = str(out.get("text") or "").strip()
        if is_useless_truncation(_txt, out.get("finish_reason")):
            opslib.alert([
                f"cortex router {tier}: پاسخِ بریدهٔ بی‌متن — "
                f"tokens_out={out.get('tokens_out')} به سقفِ max_tokens={max_tokens} "
                f"خورد و فقط {len(_txt)} کاراکترِ مرئی برگشت. مدلِ استدلالی بودجه را "
                f"صرفِ تفکر کرده؛ سقف را بالا ببر. این tier کنار رفت."])
            return None
        # finish_reason را عبور بده (۲۰۲۶-۰۷-۲۷): بدونِ آن یک پاسخِ **بریده** از
        # درِ واحدِ مغز به‌عنوانِ موفقیت بیرون می‌آید و صاحبِ فراخوان فقط بعداً
        # می‌فهمد که parse شکست — همان کوری که مسیرِ گاورنر را ۲۴+ ساعت مرده نگه داشت.
        return {"text": out.get("text", ""), "tier": tier,
                "model": out.get("model"), "cost_usd": out.get("cost_usd", 0.0),
                "finish_reason": out.get("finish_reason")}
    except Exception as e:  # noqa: BLE001 — پولی شکست → fallback
        # صداقتِ متن (2026-07-25): این تابع نمی‌داند بعدش چه می‌شود — caller اول
        # tierهای پولیِ بعدی را امتحان می‌کند و فقط اگر همه شکست خوردند به محلی می‌افتد.
        # متنِ قبلی «fallback local» بود و مالک را گمراه می‌کرد: در شاهدِ زنده primary
        # (fugu) تایم‌اوت شد، آلارم گفت «محلی»، ولی درجا secondary (glm) پولی جواب داد.
        opslib.alert([f"cortex router {tier} failed (این tier کنار رفت؛ انتخابِ "
                      f"tierِ بعدی یا محلی دستِ caller است): {type(e).__name__}: {e}"])
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
              temperature: float | None = None, seed: int | None = None,
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
                # ثبت همیشه، گیت فقط روی تحویل (۲۰۲۶-۰۸-۰۱): alertِ زیر throttle
                # دارد و dedupِ `opslib.alert` هم بعد از ۳ تکرار دیگر چیزی نمی‌نویسد،
                # پس زیرِ سیلِ تزریق ردِ اکثرِ شلیک‌ها پاک می‌شد و مالک نمی‌توانست
                # بپرسد «چند بار؟». شمارش **قبل** از تحویل و مستقل از آن. content-free.
                try:
                    import fence_ledger as _fl   # noqa: WPS433 — همسایهٔ همین ماژول
                    _fl.record(f"model_router.{str(task)[:24]}", _scr.get("findings"),
                               provenance="external")
                except Exception:  # noqa: BLE001 — دفتر هرگز مسیرِ LLM را نمی‌کشد
                    pass
                # throttled (2026-07-25): این تنها اقدامِ screen است و روی **مسیرِ داغِ
                # LLM** می‌نشیند. با سه مسیرِ مسلح، یک payloadِ regex-تریگر در هر epoch
                # سیلِ آلارم می‌سازد و آلارم به تلگرامِ مالک می‌رود → اعلانِ واقعیِ halt
                # زیر نویز می‌رود. کلید per-task تا یک taskِ نو هرگز خفه نشود؛ متنِ نو
                # (findingsِ متفاوت) هم فوراً عبور می‌کند. fail-open در هر خطای I/O.
                _msg = (f"context_fence: ورودیِ مشکوک به prompt-injection در "
                        f"task={str(task)[:32]!r} — کدها: {_scr.get('findings')}")
                _thr = getattr(opslib, "alert_throttled", None)
                if callable(_thr):
                    _thr([_msg], key=f"context_fence:{str(task)[:32]}", window_s=1800.0)
                else:                      # opslibِ قدیمی → رفتارِ قبلی
                    opslib.alert([_msg])
    except Exception:  # noqa: BLE001 — غربال هرگز مسیرِ LLM را نمی‌کشد
        pass
    want = tier
    # 2026-08-13 (fix): collab_chat is owner-pinned to DeepSeek (secondary) in
    # TASK_TIERS and must never be overridden by route_scorer's generic heuristic,
    # which classifies it "low-depth → local". Local qwen is explicitly disabled
    # for collab_chat, so route_scorer's local vote made the chat return
    # "deepseek-unavailable" even though DeepSeek was healthy. Pin before the
    # route_scorer consult so the explicit owner mapping wins.
    if str(task or "") == "collab_chat":
        want = "secondary"
    elif not want and os.environ.get("CORTEX_ROUTE_SCORER"):
        want = _scored_tier(task)
    want = want or TASK_TIERS.get(task, "local")
    if __import__("os").environ.get("OCTOPUS_WIRE_ROUTE_SHADOW") == "1": __import__("now_moves.route_scorer_shadow_log", fromlist=["log_decision"]).log_decision(task, want)  # M7 (now_moves): flag-gated shadow log — default OFF; rollback = delete this line
    _lo_rejected = None      # جوابِ محلیِ رد-کیفیت — اگر پولی هم شکست، بهتر از هیچ
    if want in ("secondary", "primary"):
        # 2026-07-16 محلی-اول (اقتصادِ مغز، رأی مالک «محلی رایگان، پولی فقط برای کارِ بزرگ»):
        # پشتِ CORTEX_LOCAL_FIRST، ردهٔ میانی (secondary: research/synthesize/draft) اول از
        # مغزِ محلیِ $0 می‌پرسد؛ یک گیتِ کیفیتِ قطعی (متنِ ناخالی با طولِ حداقلی) خروجی را
        # می‌سنجد — پاس = همان جواب، رد/در دسترس نبودن = مسیرِ پولیِ امروز، بایت‌به‌بایت.
        # ردهٔ سنگین (primary: plan/deep/orchestrate) هرگز محلی-اول نمی‌شود — کارِ بزرگ = API.
        # ۲۰۲۶-۰۸-۱۲: collab_chat = حرف با مالک روی DeepSeek. LOCAL_FIRST اینجا
        # qwen را قبول می‌کرد و جوابِ بی‌ربط («لید نقاشی/پول») برمی‌گشت.
        _skip_local = str(task or "") == "collab_chat"
        if (want == "secondary" and os.environ.get("CORTEX_LOCAL_FIRST") == "1"
                and not _skip_local):
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
        # secondary → budgets routing.reason (الان deepseek؛ قبلاً glm).
        # کلیدِ همان provider را بسنج، نه فقط GLM.
        # CL01/INC-2 + FREEZE-01 (رأی مالک 2026-08-15 و 2026-08-19): primary = DeepSeek
        # طبق سیاستِ ثبت‌شده؛ fugu فقط مسیرِ سهمیه‌ایِ صریح است، نه نگاشتِ پنهانِ primary.
        _has = {
            "secondary": bool(kp.get("deepseek") or kp.get("glm")),
            "primary": bool(kp.get("deepseek")),
        }
        order = [want] + [t for t in ("primary", "secondary") if t != want]
        tried = []
        # بودجهٔ ساعتِ دیواریِ کلِ تلاشِ پولی در یک ask (env PAID_ASK_BUDGET_S، پیش‌فرض ۹۰s).
        # بدونِ این، دو ردهٔ پولیِ سریالی هرکدام تا timeoutِ سوکت وقت می‌گیرند و نخِ
        # متابولیک همان‌قدر STOP-ORGANISM را نمی‌بیند (چکِ kill سرِ حلقه است).
        import time as _tb
        try:
            _budget_s = float(os.environ.get("PAID_ASK_BUDGET_S", "90"))
        except (TypeError, ValueError):
            _budget_s = 90.0
        _deadline = _tb.time() + max(5.0, _budget_s)
        # CL01/FREEZE-01: یخِ فعال ⇒ حلقهٔ پرداخت اصلاً اجرا نمی‌شود (pre-check قطعی)؛
        # رسید و نشانه‌گذاری در ask() انجام می‌شود — هرگز موفقیتِ localِ بی‌رسید نیست.
        _frozen_pre = None
        try:
            import opslib as _ol0
            _frozen_pre = _ol0.freeze_state()
        except Exception:  # noqa: BLE001
            _frozen_pre = None
        for _t in order:
            if _frozen_pre:
                tried.append(f"{_t}:skipped-frozen")
                break
            if not _has.get(_t):
                continue
            if _tb.time() >= _deadline:
                tried.append(f"{_t}:skipped-deadline")
                break
            out = _ask_paid(_t, prompt, system, max_tokens, task=task,
                               temperature=temperature, seed=seed)
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
                # ۲۰۲۶-۰۸-۰۶: این هشدار قبلِ فیکس هر بار «broken (کلید/شبکه/quota؟)»
                # می‌زد — حتی وقتی علتِ دقیق سقفِ روزانهٔ عادیِ فوگو بود (کد خودش
                # reason را در fugu_quota.reserve می‌دانست، فقط اینجا خوانده نمی‌شد).
                # زنده: سه هشدارِ 🔴 در یک ساعت (۱۳:۳۹/۱۳:۴۱/۱۳:۵۰)، هر سه دقیقاً
                # وقتی quota_used=۶۰=FUGU_DAILY_CALL_CAP — نه شکستِ کلید/شبکه، بودجه‌
                # محافظتِ طراحی‌شده. تشخیص خودش را از fugu_quota.status() می‌گیرد،
                # نه از حدسِ درجا — همان الگوی «حدس نزن، بسنج».
                import fugu_quota as _fq_status
                _fqs = _fq_status.status()
                if int(_fqs.get("remaining", 1) or 0) <= 0:
                    opslib.alert([f"ℹ️ cortex: سقفِ روزانهٔ فوگو پر شد "
                                  f"({_fqs.get('used_total')}/{_fqs.get('cap')}) → مغز "
                                  f"موقتاً محلی — فردا خودکار ریست می‌شود (بودجه‌محافظتِ "
                                  f"طراحی‌شده، نه خرابی)."])
                else:
                    opslib.alert([f"🔴 cortex: مغزِ پولی روی {tried or order} شکست خورد → "
                                  f"محلیِ آشغال. paid brain broken (کلید/شبکه/quota؟)"])
            except Exception:  # noqa: BLE001
                pass
    else:
        fallback_reason = None
    # collab_chat: هرگز qwen محلی — یا DeepSeek یا شکستِ صادق.
    if str(task or "") == "collab_chat":
        return {
            "ok": False,
            "reason": fallback_reason or "deepseek-unavailable",
            "hint": "collab_chat forces DeepSeek; local qwen fallback disabled",
        }
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
        tier: str | None = None, opener=None, quality=None, temperature: float | None = None,
        seed: int | None = None) -> dict:
    """درِ واحدِ LLM (wrapper). رفتار = `_ask_impl` بایت‌به‌بایت + یک side-effectِ observability:
    هر call واقعیِ LLM را در استریمِ «سوختِ» قلب ثبت می‌کند (fuel_meter) تا producers.velocity_meter
    دادهٔ واقعی بخواند — بستنِ orphanِ کانالِ خون (HH-fuel، 2026-07-21).

    flag `OCTOPUS_WIRE_HEART_FUEL` خاموش (پیش‌فرض) → fuel_meter.record خودش no-op است، پس این
    wrapper بایت‌به‌بایتِ امروز است. ثبت در try/except و هرگز محتوا/prompt ثبت نمی‌شود (فقط
    tier/model/cost/latency) — مسیرِ داغِ LLM هرگز کشته نمی‌شود."""
    import time as _t
    _t0 = _t.time()
    # CL01/LIVE-4-RESERVATION-01: پنجرهٔ رزرو — درخواستِ پولیِ غیر-Live4 ⇒ DEFERRED رسیددار
    try:
        _want_r = tier or TASK_TIERS.get(task, "local")
        if _want_r in ("primary", "secondary"):
            import live4_reservation as _lr
            _d = _lr.gate_paid(str(task or ""))
            if _d is not None and "DEFERRED_FOR_LIVE4_RESERVATION" in str(_d.get("receipt_status", "")):
                _paid_log(kind="deferred_for_live4", task=task,
                          receipt_status=_d["receipt_status"], provider_actual="none",
                          cost_aud=0, retry_after=_d["retry_after"],
                          evaluation_eligible=False, code=_d["code"])
                return {"ok": False, "reason": _d["receipt_status"],
                        "retry_after": _d["retry_after"], "provider_actual": "none",
                        "cost_aud": 0, "evaluation_eligible": False}
    except Exception:  # noqa: BLE001 — رزرو هرگز مسیرِ مغز را نمی‌کشد
        pass
    res = _ask_impl(task, prompt, system, max_tokens, tier=tier, opener=opener, quality=quality,
                      temperature=temperature, seed=seed)
    # CL01/FREEZE-01: درخواستِ ردهٔ پولی در حالتِ freeze ⇒ هرگز موفقیتِ local بی‌رسید نیست
    try:
        _want = tier or TASK_TIERS.get(task, "local")
        if _want in ("primary", "secondary"):
            import opslib as _ol2
            _fz = _ol2.freeze_state()
            if _fz and isinstance(res, dict) and res.get("ok"):
                res.setdefault("fallback_reason", "PAID_PATH_BLOCKED_BY_FREEZE")
                res.setdefault("provider_actual", "local")
                res.setdefault("evaluation_eligible", False)
                _paid_log(kind="paid_path_blocked_by_freeze", task=task,
                          receipt_status="PAID_PATH_BLOCKED_BY_FREEZE",
                          trace_id=f"{task}-{int(_t0*1000)}",
                          freeze_id=_fz["freeze_id"],
                          freeze_created_at=_fz["freeze_created_at"],
                          freeze_reason_code=_fz["freeze_reason_code"],
                          freeze_scope=_fz["freeze_scope"],
                          freeze_expiry_or_review_condition=_fz["freeze_expiry_or_review_condition"])
    except Exception:  # noqa: BLE001 — شفافیت هرگز مسیرِ مغز را نمی‌کشد
        pass
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
    # فاز ۵ دستورالعمل ۲۰۲۶-۰۸-۱۶ (NO_SILENT_DOWNGRADE): اگر این ask واقعاً به
    # fallback رسید (fallback_from)، به provider_adapter گزارش بده تا در
    # events/spine ثبت شود و (پشتِ OCTOPUS_WIRE_PROVIDER_ROUTER) به مالک برسد.
    # flag خاموش → فقط رکوردِ داخلیِ ارزان. هم‌الگویِ fuel_meter بالا: fail-soft،
    # بی‌محتوا، مسیرِ داغ هرگز کشته نمی‌شود.
    try:
        if isinstance(res, dict) and res.get("fallback_from"):
            import provider_adapter as _pa   # noqa: WPS433 — هم‌ماژول در cortex
            _pa.record_fallback(str(res["fallback_from"])[:120],
                                from_provider=str(res.get("tier") or task or "paid"),
                                to_provider="local",
                                trace_id=f"mrf-{int(_t0 * 1000)}")
            # F15 (2026-08-19): پا‌یِ fallbackِ محلی هم رسیدِ دیدنی می‌گیرد —
            # FREE_OR_UNBILLED با fallback_of؛ دیگر fallbackِ半‌ساکت نیست.
            try:
                import time as _tf15
                from datetime import datetime as _dtf15, timezone as _tzf15
                from cost_receipt import (CostReceiptAdapter as _CRA,  # noqa: WPS433
                                          remaining_budget_aud as _rb15)
                _tid15, _rid15 = _receipt_ids(task)
                _fr = _CRA().build(
                    trace_id=f"mrfb-{int(_tf15.time() * 1000)}",
                    provider="local-ollama", model="qwen2.5:1.5b",
                    ts_req=_dtf15.fromtimestamp(_t0, _tzf15.utc).isoformat(timespec="seconds"),
                    ts_resp=_dtf15.now(_tzf15.utc).isoformat(timespec="seconds"),
                    budget_before_aud=_rb15(), tokens_in=None, tokens_out=None,
                    input_sha256="", free_tier=True,
                    task_id=_tid15, run_id=_rid15,
                    fallback_of={"receipt_status": "PAID_UNAVAILABLE",
                                 "provider": str(res.get("fallback_from"))[:60],
                                 "trace": f"mrf-{int(_t0 * 1000)}"})
                import json as _jf15
                from pathlib import Path as _Pf15
                _rfp = _Pf15(str(_Pf15(__file__).resolve().parent.parent / "state" / "cortex" / "cost-receipts.jsonl"))
                _rfp.parent.mkdir(parents=True, exist_ok=True)
                _rfp.open("a", encoding="utf-8").write(_jf15.dumps(_fr, ensure_ascii=False, default=str) + chr(10))
            except Exception:  # noqa: BLE001 — رسیدِ fallback هرگز مسیر را نمی‌کشد
                pass
    except Exception:  # noqa: BLE001 — گزارشِ fallback هرگز مسیرِ LLM را نمی‌کشد
        pass
    return res


if __name__ == "__main__":
    print(json.dumps({"keys": keys_present(), "paid_gate": paid_gate(),
                      "sample": ask("think", "وضعیتِ یک ارگانیسمِ در حالِ یادگیری را در یک جمله توصیف کن.")},
                     ensure_ascii=False, indent=2))
