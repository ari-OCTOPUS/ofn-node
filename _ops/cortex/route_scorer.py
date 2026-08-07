#!/usr/bin/env python3
"""route_scorer.py — امتیازدهِ خالصِ ردهٔ مسیریابی (پیشنهاد، نه اجرا).

نقش: از یک توصیفِ کار (task + ctx) شش سیگنالِ ۰..۱ می‌سنجد
(complexity/risk/privacy/impact/cost/urgency) و **پیشنهادِ** یک رده می‌دهد:
  local     → کم‌عمق/روتین/کم‌اثر/برگشت‌پذیر/خصوصی (qwen محلی، $0).
  secondary → متوسط (GLM).
  primary   → عمیق/صحت‌بحرانی/معماری/چندفایل (Fugu).
  حساس      → ترجیحِ محلی (redact-first: پیش از هر مسیرِ بیرونی، حذفِ دادهٔ حساس).

مرزها (سختگیرانه، مثلِ کلِ لایهٔ کورتکس):
  * این ماژول **model_router را تغییر نمی‌دهد** (پیشنهاد است، نه اجرا). ادعای قبلیِ
    این خط («توسطِ model_router صدا زده نمی‌شود») کهنه بود — به‌روز شد در راستی‌آزماییِ
    ۲۰۲۶-۰۸-۰۷ (فازِ ۱): model_router.py:283-284 پشتِ پرچمِ CORTEX_ROUTE_SCORER واقعاً
    `score_route(task, None)` را صدا می‌زند (فقط اگر tier صریح نداده شده و مسیرِ
    نگاشتِ ایستا هم tier ندهد). **مهم: ctx همیشه None است در این مسیرِ زنده** —
    یعنی سیگنال‌هایِ context-rich (n_files/architecture/reversible/privacy/...) در
    عمل هرگز از caller نمی‌رسند؛ فقط طبقه‌بندیِ واژگانیِ خودِ task اثر دارد.
  * decision_record در حافظه ساخته می‌شود؛ نوشتن روی دیسک **فقط** پشتِ پرچمِ
    CORTEX_ROUTE_SCORER (env). پرچم خاموش = صفر اثرِ جانبی، صفر نوشتن.
  * fail-soft: هر خطا → پیش‌فرضِ امنِ local؛ هرگز کرشِ صداکننده.
  * $0 · فقط stdlib + opslib.

هم‌ترازِ آموزهٔ model_router (TASK_TIERS، سه‌ردهٔ local-first، قفلِ دوگانهٔ پولی) —
ولی آن‌جا را import نمی‌کند تا خالص و standalone بماند (بدونِ اثرِ جانبیِ local_llm).
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

# پرچمِ فعال‌سازیِ نوشتنِ روی دیسک (فقط env؛ وجود = روشن). خاموش = فقط-حافظه.
FLAG = "CORTEX_ROUTE_SCORER"
DECISIONS_LOG = opslib.STATE_DIR / "cortex" / "route-decisions.jsonl"

# آستانه‌های رده روی عمقِ ترکیبی (depth).
PRIMARY_T = 0.64
SECONDARY_T = 0.38
PRIVACY_LOCAL = 0.60      # حریمِ ≥ این = override به محلی (redact-first)

# ── واژگانِ سیگنال (کوچک‌شده؛ substring + توکن) ──────────────────────────────────
# containment: هیچ اشاره‌ای به هویتِ Project-F این‌جا نیست — فقط جنسِ کار.
_SHALLOW = {"classify", "summarize", "summarise", "triage", "daily", "think",
            "format", "lint", "rename", "tag", "list", "fetch", "read", "extract",
            "label", "sort", "note", "log", "count", "lookup"}
_MEDIUM = {"research", "synthesize", "synthesise", "draft", "analyze", "analyse",
           "compare", "review", "translate", "outline", "explain", "summarize-long"}
_DEEP = {"orchestrate", "deep", "plan", "architect", "architecture", "design",
         "refactor", "migrate", "redesign", "strategize", "coordinate", "audit"}
_RISKY = {"money", "payment", "pay", "delete", "drop", "migrate", "schema",
          "deploy", "prod", "production", "security", "transfer", "irreversible",
          "overwrite", "wipe", "purge"}
_SENSITIVE_TOK = {"password", "secret", "credential", "token", "personal",
                  "private", "sensitive", "seed", "wallet", "ssn", "passport",
                  "bank", "apikey"}
_SENSITIVE_SUB = ("api key", "api-key", "private key", "credit card")

_CLASS_COMPLEXITY = {"shallow": 0.15, "medium": 0.50, "deep": 0.85, "unknown": 0.40}
_CLASS_IMPACT = {"shallow": 0.15, "medium": 0.45, "deep": 0.70, "unknown": 0.35}


def _clamp(x: float) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except (TypeError, ValueError):
        return 0.0


def _tokens(task: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", (task or "").lower()))


def _num(ctx: dict, *keys, default=None):
    """اولین کلیدِ عددیِ موجود در ctx (fail-soft)."""
    for k in keys:
        if k in ctx:
            try:
                return float(ctx[k])
            except (TypeError, ValueError):
                continue
    return default


def _flag_hint(ctx: dict, *keys):
    """سه‌حالته: True/False اگر صریح بود، وگرنه None (نامشخص).

    باگِ ۲۰۲۶-۰۸-۰۷: `bool(ctx[k])` رویِ رشته کار نمی‌کند طبقِ انتظار — `bool("false")`
    در پایتون `True` است (هر رشتهٔ غیرِخالی truthy است)، پس `{"reversible": "false"}`
    را به‌جایِ False به True تبدیل می‌کرد و risk را به‌غلط پایین می‌آورد. امروز در
    مسیرِ زنده اثری ندارد (model_router همیشه ctx=None می‌فرستد) ولی برایِ هر caller
    آیندهٔ context-rich یک تلهٔ خاموش بود."""
    for k in keys:
        if k in ctx and ctx[k] is not None:
            v = ctx[k]
            if isinstance(v, str):
                return v.strip().lower() not in ("", "false", "0", "no", "off", "none")
            return bool(v)
    return None


def _level(ctx: dict, key: str):
    """low/medium/high یا عدد → 0..1 یا None."""
    if key not in ctx or ctx[key] is None:
        return None
    v = ctx[key]
    if isinstance(v, (int, float)):
        return _clamp(v)
    return {"low": 0.15, "medium": 0.5, "med": 0.5, "high": 0.85,
            "critical": 0.95}.get(str(v).strip().lower())


# ── سنجشِ شش سیگنال ─────────────────────────────────────────────────────────────
def _classify(task_lower: str, toks: set[str]) -> str:
    if toks & _DEEP or "many files" in task_lower:
        return "deep"
    if toks & _MEDIUM:
        return "medium"
    if toks & _SHALLOW:
        return "shallow"
    return "unknown"


def _n_files(ctx: dict) -> float:
    n = _num(ctx, "n_files", "files_touched", "num_files")
    if n is None:
        f = ctx.get("files")
        if isinstance(f, (list, tuple, set)):
            n = float(len(f))
    return n or 0.0


def _score(task: str, ctx: dict) -> tuple[dict, str, list[str]]:
    task_lower = (task or "").lower()
    toks = _tokens(task)
    cls = _classify(task_lower, toks)
    files = _n_files(ctx)
    reasons: list[str] = []

    # complexity: جنسِ کار + شمارِ فایل + پرچمِ معماری
    complexity = _CLASS_COMPLEXITY[cls]
    if _flag_hint(ctx, "architecture", "is_architecture"):
        complexity = max(complexity, 0.85)
    complexity = _clamp(complexity + min(files, 10.0) / 10.0 * 0.30)

    # impact: کم‌اثر↔پراثر
    lvl = _level(ctx, "impact")
    impact = lvl if lvl is not None else _CLASS_IMPACT[cls]
    if _flag_hint(ctx, "architecture", "is_architecture"):
        impact = max(impact, 0.85)
    if _flag_hint(ctx, "low_impact"):
        impact = min(impact, 0.15)
    if files > 5:
        impact = max(impact, 0.60)
    impact = _clamp(impact)

    # risk: برگشت‌ناپذیری + صحت‌بحرانی
    risk = 0.20
    rev = _flag_hint(ctx, "reversible")
    if rev is False:
        risk += 0.40
    elif rev is True:
        risk -= 0.10
    if toks & _RISKY:
        risk = max(risk, 0.70)
    if _flag_hint(ctx, "high_correctness", "correctness", "critical"):
        risk = max(risk, 0.75)
    risk = _clamp(risk)

    # privacy: حساسیت/خصوصی‌بودن (بالا = نیازِ ماندن در محلی)
    privacy = 0.10
    if _flag_hint(ctx, "sensitive"):
        privacy = max(privacy, 0.90)
    if _flag_hint(ctx, "private"):
        privacy = max(privacy, 0.70)
    if toks & _SENSITIVE_TOK or any(s in task_lower for s in _SENSITIVE_SUB):
        privacy = max(privacy, 0.85)
    privacy = _clamp(privacy)

    # urgency: مهلت/واژه‌های فوریت
    ulvl = _level(ctx, "urgency")
    urgency = ulvl if ulvl is not None else 0.30
    if toks & {"urgent", "asap", "now", "immediately"}:
        urgency = max(urgency, 0.90)
    urgency = _clamp(urgency)

    # cost: هزینهٔ نسبیِ اجرا روی مدلِ بزرگ‌تر (مشاورِ انضباطِ $0)
    cost = _clamp(0.10 + 0.70 * complexity)

    scores = {"complexity": round(complexity, 3), "risk": round(risk, 3),
              "privacy": round(privacy, 3), "impact": round(impact, 3),
              "cost": round(cost, 3), "urgency": round(urgency, 3)}
    return scores, cls, reasons


def _decide(scores: dict, cls: str, reasons: list[str]) -> str:
    complexity = scores["complexity"]
    impact = scores["impact"]
    risk = scores["risk"]
    privacy = scores["privacy"]
    urgency = scores["urgency"]

    # override: حساس → ترجیحِ محلی (redact-first). آموزهٔ صریحِ مالک.
    if privacy >= PRIVACY_LOCAL:
        reasons.append("حساس/خصوصی → ترجیحِ محلی (redact-first: پیش از هر مسیرِ "
                       "بیرونی، دادهٔ حساس حذف/ماسک شود)")
        return "local"

    # عمقِ ترکیبی
    depth = _clamp(0.42 * complexity + 0.33 * impact + 0.25 * risk)
    if urgency >= 0.70 and depth >= 0.50:
        depth = _clamp(depth + 0.05)   # فوریِ سنگین → مدلِ قوی‌تر موجه است

    if depth >= PRIMARY_T:
        tier = "primary"
        # انضباطِ $0: درست روی مرز، اگر برگشت‌پذیر و کم‌ریسک و بی‌فوریت → ردهٔ ارزان‌تر
        if depth < PRIMARY_T + 0.05 and risk < 0.50 and urgency < 0.50:
            tier = "secondary"
            reasons.append("درست روی مرزِ primary ولی برگشت‌پذیر/کم‌ریسک → "
                           "secondary برای انضباطِ هزینه ($0)")
        else:
            reasons.append("عمیق/صحت‌بحرانی/معماری/چندفایل → primary")
    elif depth >= SECONDARY_T:
        tier = "secondary"
        reasons.append("عمقِ متوسط → secondary")
    else:
        tier = "local"
        reasons.append("کم‌عمق/روتین/کم‌اثر → محلی ($0)")

    if risk >= 0.70 and tier != "primary":
        reasons.append("توجه: صحت‌بحرانی/برگشت‌ناپذیر — بازبینیِ انسانی توصیه می‌شود")
    return tier


def _est_cost(tier: str, complexity: float) -> float:
    """برآوردِ برنامه‌ریزیِ هزینه (USD). محلی $0؛ پولی‌ها نامی/سهمیه‌ای."""
    if tier == "primary":
        return round(0.02 + 0.08 * complexity, 4)
    if tier == "secondary":
        return round(0.01 + 0.04 * complexity, 4)
    return 0.0


def _fallback(tier: str) -> str:
    # هم‌ترازِ ask(): پولی بسته/ناموفق → local؛ محلیِ خاموش → escalate به مالک.
    return "local" if tier in ("secondary", "primary") else "owner"


def _task_id(task: str, ctx: dict) -> str:
    try:
        raw = json.dumps({"t": task, "c": ctx}, ensure_ascii=False, sort_keys=True,
                         default=str)
    except (TypeError, ValueError):
        raw = str(task)
    h = hashlib.sha1(raw.encode("utf-8", "replace")).hexdigest()[:8]
    return f"rt-{h}"


def _maybe_persist(record: dict) -> None:
    """نوشتنِ append-only فقط پشتِ پرچم. خاموش = no-op. fail-soft."""
    import os
    if not os.environ.get(FLAG):
        return
    try:
        opslib.append_jsonl(DECISIONS_LOG, record)
    except Exception as e:  # noqa: BLE001 — نوشتنِ سایه هرگز صداکننده را نکشد
        try:
            opslib.alert([f"route_scorer persist failed: {e}"])
        except Exception:  # noqa: BLE001
            pass


def _safe_default(task: str) -> dict:
    """پیش‌فرضِ امن هنگامِ هر خطا: محلی، صفرِ سیگنال، دلیلِ صادق."""
    scores = {k: 0.0 for k in ("complexity", "risk", "privacy",
                               "impact", "cost", "urgency")}
    return {"tier": "local", "scores": scores,
            "reasons": ["fail-soft: خطا در سنجش → پیش‌فرضِ امنِ محلی"],
            "decision_record": {"task_id": _task_id(task, {}), "scores": scores,
                                "tier": "local", "why": "fail-soft default",
                                "est_cost": 0.0, "fallback": "owner"}}


def score_route(task: str, ctx: dict | None = None) -> dict:
    """پیشنهادِ ردهٔ مسیریابی از توصیفِ کار — خالص، بی‌اثر (مگر پرچمِ نوشتن).

    خروجی: {tier, scores{complexity,risk,privacy,impact,cost,urgency},
             reasons[...], decision_record{task_id,scores,tier,why,est_cost,fallback}}
    هرگز کرش نمی‌کند: هر خطا → پیش‌فرضِ امنِ محلی.
    """
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        scores, cls, reasons = _score(task, ctx)
        tier = _decide(scores, cls, reasons)
        record = {
            "task_id": _task_id(task, ctx),
            "ts": opslib.now_iso(),
            "task": (task or "")[:120],
            "scores": scores,
            "tier": tier,
            "why": " · ".join(reasons),
            "est_cost": _est_cost(tier, scores["complexity"]),
            "fallback": _fallback(tier),
        }
        _maybe_persist(record)
        return {"tier": tier, "scores": scores, "reasons": reasons,
                "decision_record": record}
    except Exception as e:  # noqa: BLE001 — قرارِ fail-soft: هرگز صداکننده را نکش
        try:
            opslib.alert([f"route_scorer score_route failed: "
                          f"{type(e).__name__}: {e}"])
        except Exception:  # noqa: BLE001
            pass
        return _safe_default(task)


if __name__ == "__main__":
    samples = [
        ("classify", None),
        ("orchestrate a deep architecture refactor", {"n_files": 12,
                                                      "reversible": False}),
        ("summarize", {"sensitive": True}),
    ]
    for t, c in samples:
        r = score_route(t, c)
        print(json.dumps({"task": t, "tier": r["tier"], "scores": r["scores"],
                          "reasons": r["reasons"]}, ensure_ascii=False, indent=2))