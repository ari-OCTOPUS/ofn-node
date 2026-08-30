#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""provider_adapter.py — ارکستراسیون مستقل از Provider (فاز ۵ دستورالعمل ۲۰۲۶-۰۸-۱۶، D5/D6).

Fugu → DeepSeek → GLM → Ollama (D5) با کاهشِ پله‌ایِ خودمختاری (D6):
fugu/deepseek = execute (A0-A2 auto) · glm/ollama = propose (A2 → propose).

چرا این ماژول مسیرِ paid را بازنویسی نمی‌کند
──────────────────────────────────────────────
`model_router._ask_impl` از قبل رده‌محور و key-aware است (primary=fugu ·
secondary=deepseek/glm · local=ollama/qwen) و fallbackِ صادق دارد. این ماژول
لایهٔ **قراردادِ ارکستراسیون** روی همان درِ واحد است: انتخابِ provider بر اساسِ
ترتیبِ D5 + سلامت، سیگنالِ کاهشِ خودمختاری (PROPOSE_ON_FALLBACK)، و ثبتِ
هر fallback (NO_SILENT_DOWNGRADE — سند §۵). ارگانیسم نمی‌داند کدام provider
جواب داد؛ فقط ProviderResponse می‌بیند.

خطوطِ داغ:
  · `ask()` به model_router.ask واگذار می‌کند (صفر HTTP جدید، صفر کلید جدید).
  · `record_fallback()` همیشه در events.jsonl می‌نویسد (ارزان، داخلی)؛ push به
    مالک از مسیرِ موجودِ opslib.alert → governor-alerts → event_bridge (با
    dedupِ ۲۴ساعته و vocabulary-filterِ خودش) — نه کانالِ تلگرامِ جدید.
  · سلامتِ passive (حضورِ کلید)؛ هیچ network-call در select/check_health.
  · همهٔ توابع total/fail-soft؛ A6 هرگز از این‌جا پاس نمی‌شود.
"""
from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE.parent), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

FLAG = "OCTOPUS_WIRE_PROVIDER_ROUTER"   # فقط گیتِ اعلانِ fallback در model_router

# D5 — ترتیبِ fallback
FALLBACK_ORDER = ["fugu", "deepseek", "glm", "ollama"]

# D5/D6 — نرخ، رده، خودمختاری (سندِ LIFE-CURRENCY §۲)
PROVIDER_CONFIG = {
    "fugu":     {"rate": 1.0, "tier": 1, "autonomy": "execute"},
    "deepseek": {"rate": 0.8, "tier": 2, "autonomy": "execute"},
    "glm":      {"rate": 0.9, "tier": 2, "autonomy": "propose"},
    "ollama":   {"rate": 0.1, "tier": 3, "autonomy": "propose"},
}

# نگاشتِ provider → tierِ model_router (درِ واحدِ موجود)
_PROVIDER_TIER = {"fugu": "primary", "deepseek": "secondary",
                  "glm": "secondary", "ollama": "local"}

_TRUTHY = ("1", "true", "yes", "on")


@dataclass
class ProviderResponse:
    """پاسخِ یکپارچه — ارگانیسم provider را نمی‌بیند، فقط این را می‌بیند."""
    provider: str
    content: str
    tokens_used: int
    latency_ms: int
    trace_id: str
    success: bool
    error: Optional[str] = None

    def as_dict(self) -> dict:
        return {"provider": self.provider, "success": self.success,
                "tokens_used": self.tokens_used, "latency_ms": self.latency_ms,
                "trace_id": self.trace_id,
                **({"content": self.content} if self.success
                   else {"error": self.error or "unknown"})}


def enabled() -> bool:
    """گیتِ اعلانِ fallback در مسیرِ model_router (پیش‌فرض: رأیِ tracked، env برنده)."""
    if FLAG in os.environ:
        return str(os.environ[FLAG]).strip().lower() in _TRUTHY
    try:
        import owner_verdicts as _ov   # noqa: WPS433 — lazy
        return str(_ov.get(FLAG) or "0").strip().lower() in _TRUTHY
    except Exception:  # noqa: BLE001
        return False


class ProviderRouter:
    """انتخابِ provider بر اساسِ ترتیبِ D5 و سلامتِ passive."""

    def __init__(self, health: "dict | None" = None):
        self.current = "fugu"
        self.health: dict = health if isinstance(health, dict) else {p: True for p in FALLBACK_ORDER}
        # سلامتِ تزریقی (تست/فراخوانِ صریح) معتبر است — ask دیگر آن را بازنویسی
        # نمی‌کند؛ فقط روترِ پیش‌فرض هر ask خودش را تازه می‌کند.
        self._seeded = isinstance(health, dict)

    # ── سلامت (passive — هیچ network-call) ──────────────────────────────────
    def check_health(self, provider: str) -> bool:
        """fugu/deepseek/glm: حضورِ کلید (model_router.keys_present — فقط bool).
        ollama: همیشه True در passive (local_llm خودش fail-soft است؛ نبودش
        ask را None می‌کند، نه کرش)."""
        try:
            p = str(provider or "").strip().lower()
            if p == "ollama":
                return True
            import model_router as _mr   # noqa: WPS433 — همان‌جا در cortex
            kp = _mr.keys_present()
            return bool(kp.get(p))
        except Exception:  # noqa: BLE001 — سلامتِ نامعلوم = ناسالم (fail-closed)
            return False

    def refresh_health(self) -> dict:
        self.health = {p: self.check_health(p) for p in FALLBACK_ORDER}
        return dict(self.health)

    # ── انتخاب ───────────────────────────────────────────────────────────────
    def select(self) -> "str | None":
        """اولین providerِ سالم در ترتیبِ D5 — فقط از رویِ وضعیتِ شناخته‌شده
        (`self.health`؛ tick/refresh_health آن را تازه می‌کنند). این‌جا دوباره
        کلید نمی‌خوانیم: select باید خالص و ارزان باشد و وضعیتِ تزریقیِ تست را
        بشنود. همه خراب → None (یعنی LLM ها باید بایستند — fail-closed)."""
        for p in FALLBACK_ORDER:
            if self.health.get(p, False):
                if self.current != p:
                    prev = self.current
                    self.current = p
                    record_fallback(f"switch {prev}→{p} (D5 order)",
                                    from_provider=prev, to_provider=p)
                return p
        return None

    # ── خودمختاری (D6) ───────────────────────────────────────────────────────
    def autonomy_for(self, provider: str) -> str:
        return PROVIDER_CONFIG.get(str(provider).lower(), {}).get("autonomy", "propose")

    def should_downgrade_a2(self) -> bool:
        """providerِ جاری GLM/Ollama است؟ → A2 باید propose شود (PROPOSE_ON_FALLBACK)."""
        return self.autonomy_for(self.current) == "propose"

    # ── درِ واحدِ پرسش (delegation — صفر HTTP جدید) ──────────────────────────
    def ask(self, prompt: str, schema: str = "", max_tokens: int = 400,
            temperature: float = 0.0, trace_id: str = "", task: str = "think") -> "ProviderResponse":
        """پرسش از providerِ انتخابی از طریقِ model_router.ask (درِ واحدِ موجود).
        نبودِ provider سالم → success=False با error=all_providers_failed."""
        t0 = time.time()
        if not self._seeded:
            self.refresh_health()   # passive و ارزان (حضورِ کلید) — بدونِ این،
        provider = self.select()    # روترِ تازه با پیش‌فرضِ خوش‌بینانه می‌پرسد
        if provider is None:
            return ProviderResponse(provider="none", content="", tokens_used=0,
                                    latency_ms=0, trace_id=trace_id, success=False,
                                    error="all_providers_failed")
        try:
            import model_router as _mr   # noqa: WPS433
            out = _mr.ask(task, prompt, max_tokens=int(max_tokens),
                          tier=_PROVIDER_TIER.get(provider))
            ok = bool(isinstance(out, dict) and out.get("ok"))
            content = str(out.get("text") or "") if ok else ""
            return ProviderResponse(
                provider=provider, content=content,
                tokens_used=int(len(content) // 4),   # تقریبِ ~۴ کاراکتر/توکن
                latency_ms=int((time.time() - t0) * 1000),
                trace_id=trace_id or "", success=ok,
                error=None if ok else str(out.get("reason") or "provider-error"))
        except Exception as e:   # noqa: BLE001 — درِ واحد هرگز کرش نمی‌کند
            return ProviderResponse(provider=provider, content="", tokens_used=0,
                                    latency_ms=int((time.time() - t0) * 1000),
                                    trace_id=trace_id, success=False,
                                    error=f"{type(e).__name__}: {e}"[:200])


# ── ثبتِ fallback (NO_SILENT_DOWNGRADE) ──────────────────────────────────────

def record_fallback(reason: str, *, from_provider: str = "", to_provider: str = "",
                    trace_id: str = "") -> dict:
    """هر fallback باید دیده شود: events.jsonl همیشه + spine (اگر wired) +
    اعلانِ مالک از مسیرِ alert→event_bridge (فقط با فلگِ notify). هرگز raise نمی‌کند."""
    tid = trace_id or f"pf-{time.strftime('%Y%m%d%H%M%S')}-{os.getpid()}"
    ev = {"event_type": "provider.fallback", "trace_id": tid,
          "from": from_provider, "to": to_provider, "reason": str(reason)[:160],
          "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    try:
        import events as _ev   # noqa: WPS433
        _ev.emit("system.heartbeat", "provider_router", status="fallback",
                 summary=f"provider fallback {from_provider or '?'}→"
                         f"{to_provider or '?'} — {reason}"[:200],
                 next_action="autonomy downgraded per D6 if glm/ollama",
                 trace_id=tid, correlation_id=tid, approval_state="none")
    except Exception:  # noqa: BLE001
        pass
    try:   # spine — پشتِ فلگِ spine خودش؛ بی‌اثر اگر خاموش باشد
        import spine_adapters as _sa   # noqa: WPS433
        _sa.emit_event(event_type="failed", domain="provider",
                       correlation_id=tid, subject=from_provider or "unknown",
                       producer="provider_adapter", trust="DETERMINISTIC",
                       payload={"from": from_provider[:32], "to": to_provider[:32]},
                       idempotency_key=f"{tid}|provider-fallback")
    except Exception:  # noqa: BLE001
        pass
    if enabled():   # اعلانِ مالک — فقط پشتِ فلگ (پیش‌فرض رأیِ tracked)
        try:
            import opslib   # noqa: WPS433
            opslib.alert([f"provider fail → fallback {from_provider}→{to_provider}: "
                          f"{reason} — خودمختاری طبق D6 پله‌ای کم شد "
                          f"(glm/ollama = propose)"])
        except Exception:  # noqa: BLE001
            pass
    return ev


# ── singleton + tick ─────────────────────────────────────────────────────────
_ROUTER: "ProviderRouter | None" = None


def router() -> ProviderRouter:
    global _ROUTER
    if _ROUTER is None:
        _ROUTER = ProviderRouter()
    return _ROUTER


def downgrade_a2_now() -> bool:
    """سیگنالِ PROPOSE_ON_FALLBACK برای مصرف‌کننده‌ها (action_bridge، فاز ۸e)."""
    try:
        return router().should_downgrade_a2()
    except Exception:  # noqa: BLE001 — نبودِ سیگنال = محافظه‌کارانه propose
        return True


def tick(beat: int = 0) -> dict:
    """هر beat: سلامت را تازه کن و providerِ جاری را در ترتیبِ D5 نگه دار.
    هرگز raise نمی‌کند؛ خروجی = snapshotِ سلامت/انتخاب."""
    try:
        r = router()
        health = r.refresh_health()
        selected = r.select()
        return {"beat": int(beat or 0), "health": health,
                "current": r.current, "selected": selected,
                "downgrade_a2": r.should_downgrade_a2()}
    except Exception:  # noqa: BLE001
        return {"beat": int(beat or 0), "error": "failsoft"}


if __name__ == "__main__":   # pragma: no cover
    import json
    print(json.dumps(tick(), ensure_ascii=False, indent=1))
