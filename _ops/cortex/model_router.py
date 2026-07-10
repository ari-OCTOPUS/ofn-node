#!/usr/bin/env python3
"""model_router.py — «به همه جا API بده»: یک درِ واحد به سه مغز.

ردهٔ سه‌مغزی (رأی مالک 2026-07-10):
  local     → ollama qwen2.5:1.5b — کارهای ساده/روزمره. $0، همیشه مجاز (rate-limited).
  secondary → GLM (اشتراکِ MAX — نصفِ سهمیه مالِ سیستم) — تحقیق/سنتزِ متوسط.
  primary   → Fugu (اشتراکِ Pro — نصفِ سهمیه مالِ سیستم) — orchestration/عمیق.

انضباطِ paid (I2 + phase −1): هر دو ردهٔ پولی دوقفله‌اند — تاریخ ≥ 2026-07-21 +
`ACTIVATION-CORTEX-PAID.flag` (فقط مالک) — و هر call به‌صورتِ lazy از
organ_gate.reserve/settle (ارگانِ ARCHITECT_SYS، الگوی allocate_llm) می‌گذرد؛ چون
subscription است، settle با هزینهٔ نقدیِ ۰ ولی استفاده METER می‌شود (سهمیه).
بسته/شکست = fallback به local؛ localِ خاموش = None با دلیل — هرگز کرش.

مصرف: `from cortex.model_router import ask` → ask("classify", "...") یا HTTP POST
/ask روی 127.0.0.1:8772 (کورتکس).
"""
from __future__ import annotations

import json
import os
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
}
_TIER_ROLE = {"secondary": "glm", "primary": "orchestr"}   # roleهای واقعیِ budgets.yaml


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


def ask(task: str, prompt: str, system: str = "", max_tokens: int = 400,
        tier: str | None = None, opener=None) -> dict:
    """درِ واحد. خروجی همیشه dict: {ok, tier?, text?, reason?}.
    ردهٔ پولی بسته/ناموفق → local؛ local خاموش → ok=False با دلیلِ صادق."""
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return {"ok": False, "reason": "kill-switch"}
    want = tier or TASK_TIERS.get(task, "local")
    if want in ("secondary", "primary"):
        out = _ask_paid(want, prompt, system, max_tokens)
        if out:
            return {"ok": True, **out}
        gate_ok, gate_why = paid_gate()
        # صادق: چرا پولی نشد + ادامه با local
        fallback_reason = gate_why if not gate_ok else "paid-call-failed"
    else:
        fallback_reason = None
    out = local_llm.ask(prompt, system=system, max_tokens=max_tokens,
                        opener=opener)
    if out:
        res = {"ok": True, **out}
        if fallback_reason:
            res["fallback_from"] = f"{want}: {fallback_reason}"
        return res
    return {"ok": False,
            "reason": "local-llm-unavailable"
                      + (f" · {want} بسته: {fallback_reason}" if fallback_reason else ""),
            "hint": "ollama serve + مدل qwen2.5:1.5b (HH-P10)"}


if __name__ == "__main__":
    print(json.dumps({"keys": keys_present(), "paid_gate": paid_gate(),
                      "sample": ask("think", "وضعیتِ یک ارگانیسمِ در حالِ یادگیری را در یک جمله توصیف کن.")},
                     ensure_ascii=False, indent=2))
