#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_provider_router.py — فاز ۵ دستورالعمل ۲۰۲۶-۰۸-۱۶: Provider Router + fallback پله‌ای.

قیودِ اثبات‌شده (D5/D6):
  · ترتیبِ fallback: fugu → deepseek → glm → ollama؛ همه خراب → None (fail-closed)
  · خودمختاری پله‌ای: fugu/deepseek=execute · glm/ollama=propose → A2 باید propose شود
  · ask() به model_router واگذار می‌شود (delegation — ارگانیسم provider را نمی‌بیند)
  · هر fallback در events.jsonl ثبت می‌شود (trace_id)؛ اعلانِ مالک پشتِ فلگ
  · hookِ model_router فقط fallback واقعی را گزارش می‌کند (flag-off = بی‌اثر)
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "cortex"),
           str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness      # noqa: E402
harness.setup("provider-router")

import provider_adapter as pa   # noqa: E402
from provider_adapter import ProviderRouter, ProviderResponse   # noqa: E402


# ── D5: زنجیرهٔ fallback ─────────────────────────────────────────────────────

def test_fallback_chain_d5_order():
    r = ProviderRouter(health={"fugu": False, "deepseek": True, "glm": True, "ollama": True})
    assert r.select() == "deepseek"
    r2 = ProviderRouter(health={"fugu": False, "deepseek": False, "glm": False, "ollama": True})
    assert r2.select() == "ollama"
    r3 = ProviderRouter(health={p: False for p in pa.FALLBACK_ORDER})
    assert r3.select() is None   # همه خراب → None، نه ادامه با حدس


def test_all_providers_failed_response():
    r = ProviderRouter(health={p: False for p in pa.FALLBACK_ORDER})
    res = r.ask("test prompt", trace_id="t-1")
    assert isinstance(res, ProviderResponse)
    assert res.success is False and res.error == "all_providers_failed"
    assert res.provider == "none" and res.trace_id == "t-1"


def test_check_health_by_keys(monkeypatch):
    import model_router as mr
    monkeypatch.setattr(mr, "keys_present",
                        lambda: {"fugu": True, "deepseek": False, "glm": False})
    r = ProviderRouter()
    assert r.check_health("fugu") is True
    assert r.check_health("deepseek") is False
    assert r.check_health("ollama") is True   # passive: همیشه سالم (fail-soft در local_llm)


# ── D6: کاهش پله‌ای خودمختاری ────────────────────────────────────────────────

def test_stepped_autonomy_d6():
    r = ProviderRouter(health={"fugu": True, "deepseek": True, "glm": True, "ollama": True})
    assert r.autonomy_for("fugu") == "execute"
    assert r.autonomy_for("deepseek") == "execute"
    assert r.autonomy_for("glm") == "propose"
    assert r.autonomy_for("ollama") == "propose"
    assert r.should_downgrade_a2() is False   # fugu زنده → execute
    r.current = "glm"
    assert r.should_downgrade_a2() is True    # GLM → A2 باید propose شود
    r.current = "ollama"
    assert r.should_downgrade_a2() is True


def test_unknown_provider_is_conservative():
    r = ProviderRouter()
    assert r.autonomy_for("unknown-llm") == "propose"   # ناشناخته = محافظه‌کارانه


# ── ثبتِ fallback (NO_SILENT_DOWNGRADE) ──────────────────────────────────────

def test_record_fallback_logs_with_trace_id(monkeypatch):
    monkeypatch.setenv(pa.FLAG, "0")   # اعلانِ مالک خاموش — فقط رکوردِ داخلی
    ev = pa.record_fallback("switch fugu→deepseek (D5 order)",
                            from_provider="fugu", to_provider="deepseek")
    assert ev["trace_id"] and ev["event_type"] == "provider.fallback"
    import events
    lines = [json.loads(x) for x in
             events.LOG.read_text("utf-8").splitlines()[-12:] if x.strip()]
    hit = [x for x in lines if x.get("agent_id") == "provider_router"
           and x.get("status") == "fallback"]
    assert hit and all(x.get("trace_id") for x in hit)


def test_ask_delegates_to_model_router(monkeypatch):
    import model_router as mr
    monkeypatch.setattr(
        mr, "ask",
        lambda task, prompt, max_tokens=400, tier=None, **kw: {
            "ok": True, "text": "پاسخِ آزمایشی", "tier": tier or "local"})
    r = ProviderRouter(health={"fugu": True, "deepseek": True, "glm": True, "ollama": True})
    res = r.ask("سؤال", task="think", trace_id="t-2")
    assert res.success is True and res.provider == "fugu"
    assert res.content == "پاسخِ آزمایشی" and res.tokens_used > 0


def test_tick_never_raises_and_reports_downgrade(monkeypatch):
    def _fake_refresh(self):
        self.health = {"fugu": False, "deepseek": False, "glm": True, "ollama": True}
        return dict(self.health)
    monkeypatch.setattr(ProviderRouter, "refresh_health", _fake_refresh)
    out = pa.tick(77)
    assert out.get("selected") == "glm" and out.get("downgrade_a2") is True
    assert pa.tick(0).get("beat") == 0


def test_model_router_hook_reports_real_fallback(monkeypatch):
    """hookِ ask(): فقط وقتی fallback_from واقعی در نتیجه هست گزارش می‌دهد."""
    import importlib
    import model_router as mr
    monkeypatch.setattr(mr, "_ask_impl",
                        lambda *a, **kw: {"ok": True, "text": "x", "local_first": True,
                                          "fallback_from": "secondary: paid-call-failed",
                                          "tier": "local"})
    recorded = []
    monkeypatch.setattr(pa, "record_fallback",
                        lambda reason, **kw: recorded.append(reason) or {"trace_id": "t"})
    out = mr.ask("think", "prompt")
    assert out["ok"] is True
    assert len(recorded) == 1 and "paid-call-failed" in recorded[0]
    # بدونِ fallback_from → هیچ گزارشی
    monkeypatch.setattr(mr, "_ask_impl", lambda *a, **kw: {"ok": True, "text": "y"})
    mr.ask("think", "prompt")
    assert len(recorded) == 1


def test_owner_verdict_registered():
    assert "OCTOPUS_WIRE_PROVIDER_ROUTER" in \
        (_HERE.parent / "owner-verdicts.yaml").read_text("utf-8")


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
