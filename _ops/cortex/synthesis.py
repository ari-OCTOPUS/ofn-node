#!/usr/bin/env python3
"""synthesis.py — سنتزکنندهٔ فراشناختی (جلسه ۴۶، رأی مالک: «به‌عنوان مغز تحقیق کنه
با Fugu ... پروپوزال ارتقا بسازه و به تو بده»).

ورودی‌ها را جمع می‌کند — یافته‌های وبِ رایگان + نقشهٔ خود (self-model) + گپ‌های
ماتریسِ ممیزی + جهت‌های مالک (GOALS-OCTOPUS.md) — و به مغز می‌دهد
(model_router: primary=fugu → glm → localِ $0، متر و گیتِ پولی داخلِ روتر) تا
پروپوزال‌های ارتقای هم‌راستا با جهت‌های مالک بسازد.

خروجی: `state/cortex/synthesis-latest.json` (schema synthesis.v1) →
improve آن را به‌عنوان سیگنال می‌خواند و در `/upgrades` و پنل بالا می‌آید.

حاکمیت: propose-only مطلق (این ماژول هیچ‌چیز اعمال نمی‌کند)؛ خرجِ پولی فقط از
مسیرِ متردارِ روتر؛ privacy: فقط محتوای عمومی (گپ/عنوانِ یافته/جهت‌های GOALS که
مالک خودش برای مغزِ ابری نوشته) به prompt می‌رود — هیچ secret، هیچ محتوای خصوصی.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS / "budget") not in sys.path:
    sys.path.insert(0, str(_OPS / "budget"))
import opslib  # noqa: E402

STATE = opslib.STATE_DIR
SYNTH_PATH = STATE / "cortex" / "synthesis-latest.json"
GOALS_PATH = _OPS / "GOALS-OCTOPUS.md"
MAX_TOKENS = int(os.environ.get("SYNTHESIS_MAX_TOKENS", "500"))


def _read(p: Path) -> dict:
    try:
        return json.loads(p.read_text("utf-8")) if p.exists() else {}
    except (OSError, ValueError):
        return {}


def read_goals() -> list[str]:
    """جهت‌های مالک از GOALS-OCTOPUS.md (فقط خط‌های bullet — عمومی و مالک‌نوشته)."""
    try:
        text = GOALS_PATH.read_text("utf-8") if GOALS_PATH.exists() else ""
    except OSError:
        return []
    return [ln[2:].strip() for ln in text.splitlines()
            if ln.startswith("- ") and ln[2:].strip()][:12]


def gather_context() -> dict:
    """ورودی‌های عمومیِ سنتز (همه از stateِ خودِ سیستم — sanitized by construction)."""
    research = _read(STATE / "pulse" / "research-latest.json")
    model = _read(STATE / "cortex" / "self-model.json")
    matrix = _read(STATE / "cortex" / "audit-matrix.json")
    gaps = [g.get("item", "") for g in (matrix.get("gaps") or [])
            if g.get("priority") in ("P0", "P1")][:6]
    hits = []
    for f in (research.get("findings") or [])[:4]:
        for h in (f.get("hits") or [])[:2]:
            hits.append(f"{f['topic']}: {h.get('title', '')[:80]} [{h.get('source')}]")
    return {"goals": read_goals(), "gaps": gaps, "web": hits,
            "body": {"n_modules": model.get("n_modules"),
                     "total_lines": model.get("total_lines"),
                     "self_awareness_pct": model.get("self_awareness_pct"),
                     "undocumented": (model.get("undocumented") or [])[:5]}}


def _build_prompt(ctx: dict) -> str:
    parts = ["تو مغزِ تحقیقِ یک ارگانیسمِ نرم‌افزاریِ خودبهبودگر هستی. با ورودی‌های زیر "
             "حداکثر ۳ پروپوزالِ ارتقای مشخص و عملی بساز. هر پروپوزال یک خط: "
             "«عنوان | چرا (به کدام جهت/گپ وصل است) | قدمِ اول». فقط پیشنهاد — هیچ اقدامی.",
             "\n## جهت‌های مالک:"]
    parts += [f"- {g}" for g in ctx["goals"][:8]] or ["- (خالی)"]
    parts.append("\n## گپ‌های ممیزیِ خود:")
    parts += [f"- {g}" for g in ctx["gaps"]] or ["- (خالی)"]
    parts.append("\n## یافته‌های تازهٔ وب:")
    parts += [f"- {h}" for h in ctx["web"]] or ["- (خالی)"]
    b = ctx["body"]
    parts.append(f"\n## بدن: {b.get('n_modules')} ماژول، {b.get('total_lines')} خط، "
                 f"خودآگاهیِ سند {b.get('self_awareness_pct')}%")
    if ctx.get("alarm"):
        parts.append(f"\n## زنگِ خطرِ همین لحظه: {ctx['alarm']}\n"
                     "پروپوزال‌ها را بر تشخیص و رفعِ همین وضعیت متمرکز کن.")
    return "\n".join(parts)


def _parse_proposals(text: str) -> list[dict]:
    """خطوطِ «عنوان | چرا | قدم» → ساختار. fail-soft: متنِ خام هم نگه داشته می‌شود.
    2026-07-18: خطِ echo قالب («عنوان | چرا … | قدم اول») دیگر پروپوزال حساب نمی‌شود —
    مدلِ محلی 07-17 دقیقاً همان header را برگرداند و به‌عنوان پروپوزالِ #1 ثبت شد."""
    out = []
    for ln in (text or "").splitlines():
        ln = re.sub(r"^\s*[-*\d.)\s]+", "", ln).strip("«» \t").strip()
        if "|" in ln and len(ln) > 10:
            bits = [b.strip() for b in ln.split("|")]
            if not bits[0]:
                continue                                   # خطِ بی‌عنوان، ساختاراً بی‌مصرف
            # فقط «برچسبِ لختِ» قالب echo است (تساوی، نه startswith — مدل‌ها اغلب
            # برچسب را پیشوندِ محتوای واقعی نگه می‌دارند: «چرا (…): دلیلِ واقعی»).
            _why = (bits[1].replace("‌", "").rstrip(" :：") if len(bits) > 1 else "")
            if bits[0].rstrip(":：") == "عنوان" or \
                    _why == "چرا (به کدام جهت/گپ وصل است)".replace("‌", ""):
                continue                                   # بازتابِ قالب، نه فکر
            out.append({"title": bits[0][:120],
                        "why": (bits[1] if len(bits) > 1 else "")[:200],
                        "first_step": (bits[2] if len(bits) > 2 else "")[:200]})
        if len(out) >= 3:
            break
    return out


def _synth_quality_ok(text: str) -> bool:
    """گیتِ کیفیتِ اختصاصیِ سنتز برای محلی-اولِ روتر (مشخصهٔ مالک 2026-07-18): جوابِ
    محلی فقط وقتی قبول است که ≥۲ پروپوزالِ ساختاراً کامل داشته باشد — عنوانِ
    غیرتکراری + «چرا»ی ناخالی + قدمِ اولِ عملی (چندواژه‌ای). وگرنه نوبتِ مغزِ
    پولی است — Fugu دیگر پشتِ جوابِ بلندِ بی‌محتوا گرسنه نمی‌ماند."""
    good = [p for p in _parse_proposals(text or "")
            if p["title"] and p["why"]
            and len(p["first_step"]) >= 6 and " " in p["first_step"]]
    return len(good) >= 2 and len({p["title"] for p in good}) >= 2


def _input_sig(ctx: dict) -> str:
    """امضای کوتاهِ ورودی‌های سنتز — برای گیتِ رویدادمحور (Fugu کورتیزولی)."""
    import hashlib
    blob = json.dumps(ctx, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def synthesize(ask=None, extra: dict | None = None, tier: str | None = None) -> dict:
    """یک دورِ سنتز: context → مغز (fugu→glm→local) → پروپوزال‌ها. ask تزریق‌پذیر (تست).

    extra (OCT-CORTISOL 2026-07-18): زمینهٔ رویدادِ ماشه — مثلاً {"alarm": "ورود به
    ترس: legs"}. واردِ ctx می‌شود ⇒ هم prompt جهت‌دار می‌شود («روی رفعِ همین وضعیت
    متمرکز شو») و هم input_sig عوض می‌شود تا dedupِ رویدادمحور شلیکِ کورتیزولی را
    خفه نکند (استرس جزوِ ctx معمولی نیست)."""
    if ask is None:
        from model_router import ask as _router_ask
        ask = _router_ask
    ctx = gather_context()
    if extra and extra.get("alarm"):
        ctx["alarm"] = str(extra["alarm"])[:200]
    # sig همیشه بدونِ alarm (بازبینی 2026-07-18): دو نویسندهٔ synthesis-latest داریم
    # (پمپِ تایمری بدونِ alarm + کورتیزولِ کورتکس با alarm)؛ اگر alarm واردِ sig شود
    # سیگ‌هایشان هرگز با هم نمی‌خواند و بعد از هر شلیک، پمپ یک تماسِ پولیِ بی‌سیگنالِ
    # تازه می‌زند. رویدادِ کورتیزولی به‌جای sig، صریحاً dedup را دور می‌زند (پایین).
    sig = _input_sig({k: v for k, v in ctx.items() if k != "alarm"})
    # OCT-CORTISOL: پشتِ OCTOPUS_SYNTH_EVENT_DRIVEN، اگر ورودی‌ها از سنتزِ قبل تغییر
    # نکرده و پروپوزال داریم → مغزِ پولی را صدا نزن (رد کردنِ کارِ پولی همیشه امن).
    # alarm = رویدادِ به‌تعریف-تازه → هرگز dedup نمی‌شود.
    if not ctx.get("alarm") and os.environ.get("OCTOPUS_SYNTH_EVENT_DRIVEN") == "1":
        prev = _read(SYNTH_PATH)
        if prev.get("input_sig") == sig and prev.get("proposals"):
            return {"ok": True, "skipped": "no-new-signal", "tier": "skip",
                    "input_sig": sig}
    prompt = _build_prompt(ctx)
    # گیتِ کیفیتِ اختصاصی فقط اگر روترِ واقعی (یا fakeِ هم‌امضا) پارامترش را بشناسد —
    # askهای تزریقیِ قدیمیِ تست‌ها بدونِ quality همچنان کار می‌کنند.
    kw = {}
    try:
        import inspect
        if "quality" in inspect.signature(ask).parameters:
            kw["quality"] = _synth_quality_ok
    except (TypeError, ValueError):
        pass
    # کورتیزول = لحظهٔ مهم (رأی مالک «Fugu = کورتیزول») → مستقیم ردهٔ primary؛
    # سنتزِ تایمریِ بی‌alarm مثلِ قبل tier=None (محلی-اولِ ارزان، بعد پولی).
    res = ask("research", prompt, system="پاسخ فقط فارسی، فشرده، بدونِ مقدمه.",
              max_tokens=MAX_TOKENS,
              tier=(tier or ("primary" if ctx.get("alarm") else None)), **kw)
    if not res.get("ok"):
        return {"ok": False, "reason": res.get("reason", "brain-unavailable"),
                "ctx_sizes": {k: len(v) if isinstance(v, list) else 1
                              for k, v in ctx.items()}}
    proposals = _parse_proposals(res.get("text", ""))
    digest = {
        "ts": opslib.now_iso(), "schema": "synthesis.v1",
        "input_sig": sig,
        "tier": res.get("tier"), "model": res.get("model"),
        "cost_usd": res.get("cost_usd", 0.0),
        "fallback_from": res.get("fallback_from"),
        "n_inputs": {"goals": len(ctx["goals"]), "gaps": len(ctx["gaps"]),
                     "web": len(ctx["web"])},
        **({"alarm": ctx["alarm"]} if ctx.get("alarm") else {}),
        "proposals": proposals,
        "raw_text": (res.get("text") or "")[:1500],
    }
    return {"ok": True, "digest": digest}


def run_and_persist(ask=None, extra: dict | None = None, tier: str | None = None) -> dict:
    """سنتز + نوشتنِ اتمیک + NOTE در ledger (شفافیتِ خرج/مسیرِ مغز)."""
    r = synthesize(ask=ask, extra=extra, tier=tier)
    if not r.get("ok"):
        return r
    if r.get("skipped"):
        return r
    digest = r["digest"]
    try:
        SYNTH_PATH.parent.mkdir(parents=True, exist_ok=True)
        with opslib.LockedJson(SYNTH_PATH) as lj:
            lj.write(digest)
        opslib.ledger_note("SYNTHESIS", {"tier": digest["tier"],
                                         "n_proposals": len(digest["proposals"]),
                                         "cost_usd": digest["cost_usd"]},
                           actor="cortex-synthesis")
        # کشف را دیدنی کن (رأی مالک): اولین ایدهٔ مغز به‌صورتِ جملهٔ ساده
        try:
            import discoveries
            props = digest.get("proposals") or []
            if props:
                discoveries.record("idea", f"یه ایده برای بهترشدن: {props[0].get('title', '')[:80]}")
        except Exception:  # noqa: BLE001
            pass
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}
    return {"ok": True, "tier": digest["tier"],
            "n_proposals": len(digest["proposals"]),
            "cost_usd": digest["cost_usd"]}


if __name__ == "__main__":
    print(json.dumps(run_and_persist(), ensure_ascii=False, indent=2))
