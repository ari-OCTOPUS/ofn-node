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
    return "\n".join(parts)


def _parse_proposals(text: str) -> list[dict]:
    """خطوطِ «عنوان | چرا | قدم» → ساختار. fail-soft: متنِ خام هم نگه داشته می‌شود."""
    out = []
    for ln in (text or "").splitlines():
        ln = re.sub(r"^\s*[-*\d.)\s]+", "", ln).strip()
        if "|" in ln and len(ln) > 10:
            bits = [b.strip() for b in ln.split("|")]
            out.append({"title": bits[0][:120],
                        "why": (bits[1] if len(bits) > 1 else "")[:200],
                        "first_step": (bits[2] if len(bits) > 2 else "")[:200]})
        if len(out) >= 3:
            break
    return out


def synthesize(ask=None) -> dict:
    """یک دورِ سنتز: context → مغز (fugu→glm→local) → پروپوزال‌ها. ask تزریق‌پذیر (تست)."""
    if ask is None:
        from model_router import ask as _router_ask
        ask = _router_ask
    ctx = gather_context()
    prompt = _build_prompt(ctx)
    res = ask("research", prompt, system="پاسخ فقط فارسی، فشرده، بدونِ مقدمه.",
              max_tokens=MAX_TOKENS, tier=None)
    if not res.get("ok"):
        return {"ok": False, "reason": res.get("reason", "brain-unavailable"),
                "ctx_sizes": {k: len(v) if isinstance(v, list) else 1
                              for k, v in ctx.items()}}
    proposals = _parse_proposals(res.get("text", ""))
    digest = {
        "ts": opslib.now_iso(), "schema": "synthesis.v1",
        "tier": res.get("tier"), "model": res.get("model"),
        "cost_usd": res.get("cost_usd", 0.0),
        "fallback_from": res.get("fallback_from"),
        "n_inputs": {"goals": len(ctx["goals"]), "gaps": len(ctx["gaps"]),
                     "web": len(ctx["web"])},
        "proposals": proposals,
        "raw_text": (res.get("text") or "")[:1500],
    }
    return {"ok": True, "digest": digest}


def run_and_persist(ask=None) -> dict:
    """سنتز + نوشتنِ اتمیک + NOTE در ledger (شفافیتِ خرج/مسیرِ مغز)."""
    r = synthesize(ask=ask)
    if not r.get("ok"):
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
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}
    return {"ok": True, "tier": digest["tier"],
            "n_proposals": len(digest["proposals"]),
            "cost_usd": digest["cost_usd"]}


if __name__ == "__main__":
    print(json.dumps(run_and_persist(), ensure_ascii=False, indent=2))
