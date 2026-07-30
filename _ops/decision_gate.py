"""decision_gate — WAVE W2: گیتِ ۵۱/۴۹ با شواهد و ردهٔ نابودی.

قراردادِ حاکم: GENOME LOCK v2026-07-27، LOCK-A.
    AI (مغز + قاضیِ ریاضی) = ۵۱٪ · مالک در تلگرام = ۴۹٪
    AI فقط وقتی propose+execute می‌کند که **هر سه** برقرار باشد:
      ۱) evidence_score ≥ θ
      ۲) destruction_risk = false
      ۳) risk_class ≤ AI_MAX_CLASS
    و مالک **همیشه** حقِ وتو روی برگشت‌ناپذیر دارد.
    HARD-STOP ۱۰۰٪ انسانی — هیچ ۵۱٪ ای اینها را باز نمی‌کند.

چرا ۵۱٪ اینجا «قدرت» نیست
─────────────────────────
عددِ ۵۱ فقط یعنی «وقتی مدرک کامل است و نابودی در کار نیست، منتظرِ تپ نمان».
هر مسیرِ نابودی‌ساز — پول، راز، دیپلوی، تکثیر، حذفِ انبوه — **بی‌قید** انسانی
است. یعنی این ماژول اختیار نمی‌دهد؛ اختیارِ موجود را **مشروط** می‌کند.

سوراخی که این ماژول می‌بندد (نقطهٔ کورِ ۱۳۸)
──────────────────────────────────────────
`autonomy_matrix.is_important` فقط سه کلیدِ سطحِ بالا را می‌خواند
(`title`/`action`/`suggested_action`). پس `{"params": {"amount_aud": 500}}`
رشتهٔ خالی می‌داد و «مهم» شمرده نمی‌شد → autonomous. این‌جا کلِ payload
**بازگشتی** تخت می‌شود، شاملِ کلیدها و مقادیرِ تودرتو و داخلِ لیست.

مرزها
─────
· توابعِ خالص + fail-closed. هر ابهام → `owner_required`.
· این ماژول هیچ‌چیز اجرا نمی‌کند؛ فقط قضاوت و کارت.
· flag پیش‌فرض خاموش (`OCTOPUS_WIRE_DECISION_GATE`) — خاموش یعنی همان
  رفتارِ امروز: همه‌چیز propose-only.
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget"), str(_HERE / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

FLAG = "OCTOPUS_WIRE_DECISION_GATE"
SCHEMA = "decision-record.v1"
LEDGER = opslib.STATE_DIR / "decisions" / "decision-record.jsonl"

AI_WEIGHT = 0.51
OWNER_WEIGHT = 0.49
THETA = 0.70              # آستانهٔ شواهد
AI_MAX_CLASS = 2          # AI حداکثر تا L2؛ L3/L4 همیشه مالک

# وزن‌های فرمولِ §۶. جمعِ مثبت‌ها = ۱ تا نمره در [0,1] بماند.
W_COMPLETENESS, W_VERIFIER, W_CONSISTENCY, W_STUB_PENALTY = 0.35, 0.40, 0.25, 0.50

# ── HARD-STOP (LOCK-A) — هرگز، حتی با ۱۰۰٪ شواهد ──────────────────────────
# فارسی و لاتین با هم: الگویی که نصفِ زبانِ ورودی را نشناسد، امنیت نیست.
_DENY_RULES = {
    # ⚠️ فعل **و** نامِ فیلد. نسخهٔ اول فقط فعل داشت (`payment`, `پرداخت`) و
    # تستِ خودش `{"params": {"amount_aud": 500}}` را رد کرد — یعنی دقیقاً همان
    # نقطهٔ کورِ ۱۳۸ که می‌خواستم ببندم، نیمه‌باز مانده بود. پولِ واقعی معمولاً
    # به‌شکلِ **نامِ فیلد** می‌آید نه فعل.
    "پول/پرداخت": r"(spend|payment|pay\b|invoice|pocketsmith|transfer|withdraw|"
                  r"amount|_aud\b|_usd\b|\bcost\b|price|budget|\bfee\b|balance|"
                  r"پرداخت|واریز|برداشت|فاکتور|خرید|پول|مبلغ|هزینه|قیمت)",
    "راز/کلید": r"(secret|token|api[_-]?key|credential|\.env|rotate[_-]?key|"
                r"راز|رمز|کلید|توکن|اعتبارنامه)",
    "دیپلوی/کد": r"(deploy|git\s+push|force[_-]?push|restart\s+organism|"
                 r"self[_-]?deploy|merge\s+to\s+master|دیپلوی|ری‌?استارتِ?\s*ارگانیسم)",
    "تکثیر": r"(replicat|spawn|clone|fork\s+organism|تکثیر|همتاسازی)",
    "ژنوم/کیل‌سوییچ": r"(ring[_-]?0|genome\s+write|kill[_-]?switch|disable\s+stop|"
                      r"effectorgate\s+bypass|ژنوم|کیل‌?سوییچ)",
    "حذفِ انبوه": r"(mass\s+delete|rm\s+-rf|wipe|truncate|drop\s+table|purge|"
                  r"حذفِ?\s*انبوه|پاک‌?سازیِ?\s*کامل)",
    "خروجِ داده": r"(exfil|upload\s+to|external\s+post|send\s+to\s+customer|"
                  r"ارسالِ?\s*بیرونی|به\s*مشتری)",
}
_DENY_RE = {k: re.compile(v, re.I) for k, v in _DENY_RULES.items()}


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


# ── تخت‌کردنِ بازگشتی — قلبِ فیکسِ نقطهٔ کورِ ۱۳۸ ───────────────────────────
def flatten(obj, _depth: int = 0) -> str:
    """هر ساختار → یک رشتهٔ قابلِ اسکن، شاملِ **کلیدها و مقادیرِ تودرتو**.

    نسخهٔ سطحی همان چیزی بود که `params.amount_aud` را نامرئی می‌کرد. عمقِ
    محدود تا ساختارِ حلقوی/عمیق قضاوت را نکشد؛ رسیدن به سقف = هشدارِ صریح
    در رشته تا fail-closed پایین‌دست شلیک کند."""
    if _depth > 8:
        return " __DEPTH_LIMIT__ "
    if obj is None:
        return ""
    if isinstance(obj, dict):
        return " ".join(f"{k} {flatten(v, _depth + 1)}" for k, v in obj.items())
    if isinstance(obj, (list, tuple, set)):
        return " ".join(flatten(v, _depth + 1) for v in obj)
    return str(obj)


def destruction_risk(payload) -> tuple:
    """آیا این اقدام ردهٔ نابودی است؟ → (bool, دلیل).

    fail-CLOSED: ورودیِ غیرقابلِ اسکن یا عمقِ بیش از حد → True."""
    try:
        blob = flatten(payload)
    except Exception:  # noqa: BLE001
        return True, "payload ناخوانا — fail-closed"
    if "__DEPTH_LIMIT__" in blob:
        return True, "ساختارِ بیش از حد عمیق — قابلِ بازرسی نیست"
    for name, rx in _DENY_RE.items():
        m = rx.search(blob)
        if m:
            return True, f"{name} — «{m.group(0)[:40]}»"
    return False, ""


def _f(v, d=0.0) -> float:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return d
    return x if math.isfinite(x) else d


def clamp01(v) -> float:
    x = _f(v, 0.0)
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def evidence_score(evidence) -> tuple:
    """نمرهٔ شواهد ∈ [0,1] + دلایل. فرمولِ §۶.

    نبودِ شواهد = **صفر**، نه پیش‌فرضِ خوش‌بینانه. `stub=True` جریمه می‌خورد
    چون شواهدِ آلوده‌به‌stub اصلاً شواهد نیست."""
    e = evidence if isinstance(evidence, dict) else {}
    completeness = clamp01(e.get("completeness"))
    verifier = 1.0 if e.get("verifier_pass") is True else 0.0
    consistency = clamp01(e.get("consistency"))
    stub = 1.0 if e.get("stub") is True else 0.0
    score = (W_COMPLETENESS * completeness + W_VERIFIER * verifier
             + W_CONSISTENCY * consistency - W_STUB_PENALTY * stub)
    why = []
    if not e:
        why.append("هیچ شواهدی داده نشد")
    if stub:
        why.append("شواهد آلوده به stub — جریمه خورد")
    if verifier == 0.0:
        why.append("verifier پاس نشده")
    return clamp01(score), why


def decide(*, action: str, payload=None, evidence=None, risk_class: int = 3,
           trace_id: str = "") -> dict:
    """DecisionRecord v1. هرگز اجرا نمی‌کند — فقط می‌گوید چه کسی مجاز است."""
    payload = payload if payload is not None else {}
    blob = {"action": action, "payload": payload}
    destroy, d_why = destruction_risk(blob)
    score, e_why = evidence_score(evidence)
    try:
        rc = int(risk_class)
    except (TypeError, ValueError):
        rc = 4                                  # نامعلوم = بالاترین رده
    reasons = list(e_why)
    if destroy:
        reasons.append(f"ردهٔ نابودی: {d_why}")
    if rc > AI_MAX_CLASS:
        reasons.append(f"ردهٔ ریسک {rc} > سقفِ AI ({AI_MAX_CLASS})")
    if score < THETA:
        reasons.append(f"شواهد {score:.2f} < آستانهٔ {THETA}")

    gate_on = enabled()
    ai_may = bool(gate_on and score >= THETA and not destroy and rc <= AI_MAX_CLASS)
    if not gate_on:
        reasons.append("گیت خاموش — همه‌چیز propose-only")
    return {
        "schema": SCHEMA,
        "ts": opslib.now_iso(),
        "trace_id": str(trace_id or "")[:64],
        "action": str(action or "")[:120],
        "ai_weight": AI_WEIGHT,
        "owner_weight": OWNER_WEIGHT,
        "evidence_score": round(score, 4),
        "threshold": THETA,
        "destruction_risk": destroy,
        "destruction_reason": d_why,
        "risk_class": rc,
        "executor": "ai" if ai_may else "owner_required",
        "needs_evidence": bool(score < THETA and not destroy),
        "reasons": reasons,
    }


def record(rec: dict) -> bool:
    """ثبتِ تصمیم — append-only. خاموش هم ثبت می‌شود (سنجشِ سایه)."""
    try:
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False


def card(rec: dict) -> tuple:
    """کارتِ ۵۱/۴۹ — چهار دکمه طبقِ قراردادِ UI."""
    import html
    r = rec if isinstance(rec, dict) else {}
    tid = str(r.get("trace_id") or "")[:16]
    who = ("🤖 من می‌توانم انجام دهم" if r.get("executor") == "ai"
           else "🙋 منتظرِ توام")
    lines = [f"⚖️ <b>{html.escape(str(r.get('action') or '؟'))}</b>",
             f"▸ {who}",
             f"▸ شواهد: <code>{r.get('evidence_score')}</code> "
             f"(آستانه {r.get('threshold')})",
             f"▸ ردهٔ ریسک: {r.get('risk_class')}"]
    if r.get("destruction_risk"):
        lines.append(f"▸ 🛑 <b>ردهٔ نابودی</b> — {html.escape(str(r.get('destruction_reason')))}")
        lines.append("▸ این یکی هرگز خودکار نمی‌شود، هر چقدر هم مدرک باشد.")
    for w in (r.get("reasons") or [])[:3]:
        lines.append(f"   · {html.escape(str(w))[:110]}")
    lines.append("")
    lines.append("▸ نکنی: هیچ اتفاقی نمی‌افتد — این کارت خودش اجرا نیست.")
    kb = [[{"text": "✅ آره", "callback_data": f"ok:{tid}"},
           {"text": "❌ نه", "callback_data": f"no:{tid}"}],
          [{"text": "⏳ بعداً", "callback_data": f"later:{tid}"},
           {"text": "🔍 مدرک کم است", "callback_data": f"dg:e:{tid}"}]]
    return "\n".join(lines)[:3500], kb


def explain(trace_id: str) -> str:
    """پشتِ دکمهٔ «🔍 مدرک کم است» — **چه** مدرکی کم بود، نه اینکه کم بود.

    دکمه‌ای که فقط بگوید «کم است» همان توضیحِ بی‌فایده‌ای است که کارت خودش داد.
    آنچه مالک لازم دارد این است که بداند اگر یک چیز را بیاورد، تصمیم آزاد می‌شود
    یا نه — پس این‌جا **فاصله تا آستانه** و «آیا اصلاً قابلِ آزادشدن هست» را
    می‌گوییم. برای ردهٔ نابودی جواب همیشه «نه» است و صریح گفته می‌شود.
    """
    import html
    tid = str(trace_id or "")[:64]
    rec = None
    try:
        for line in reversed(LEDGER.read_text("utf-8").splitlines()):
            if not line.strip():
                continue
            row = json.loads(line)
            if str(row.get("trace_id") or "") == tid:
                rec = row
                break
    except (OSError, ValueError):
        pass
    if not rec:
        return ("🔍 <b>این تصمیم در دفتر نیست</b>\n"
                "▸ کارت‌های قدیمی بعد از چرخشِ دفتر رد می‌شوند.\n"
                "▸ نکنی: هیچ — تصمیم همچنان اجرا نشده.")

    score = rec.get("evidence_score")
    lines = [f"🔍 <b>{html.escape(str(rec.get('action') or '؟'))}</b>"]
    if rec.get("destruction_risk"):
        lines += [f"▸ ردهٔ نابودی: {html.escape(str(rec.get('destruction_reason')))}",
                  "▸ <b>هیچ مقدار مدرکی این را آزاد نمی‌کند.</b> "
                  "این‌جا مدرک مسئله نیست، اجازه مسئله است.",
                  "", "▸ فقط تپِ تو بازش می‌کند."]
        return "\n".join(lines)[:3500]

    try:
        gap = max(0.0, THETA - float(score))
    except (TypeError, ValueError):
        gap = THETA
    lines += [f"▸ شواهد <code>{score}</code> — {gap:.2f} کم دارد تا {THETA}",
              "▸ چه چیزی نمرهٔ آن را پایین آورد:"]
    for w in (rec.get("reasons") or [])[:5]:
        lines.append(f"   · {html.escape(str(w))[:110]}")
    lines += ["",
              "▸ سه چیز نمره می‌سازد: کاملبودنِ داده، پاس‌شدنِ verifier، "
              "و سازگاری با آنچه از قبل می‌دانم.",
              "▸ نکنی: هیچ — منتظر می‌ماند."]
    return "\n".join(lines)[:3500]


if __name__ == "__main__":   # pragma: no cover
    demos = [
        ("اسکنِ کد", {}, {"completeness": 1, "verifier_pass": True, "consistency": 1}, 1),
        ("پرداختِ فاکتور", {"params": {"amount_aud": 500}},
         {"completeness": 1, "verifier_pass": True, "consistency": 1}, 1),
        ("بازآراییِ لاگ", {}, {"completeness": 0.5}, 1),
    ]
    print(json.dumps([decide(action=a, payload=p, evidence=e, risk_class=c)
                      for a, p, e, c in demos], ensure_ascii=False, indent=1))
