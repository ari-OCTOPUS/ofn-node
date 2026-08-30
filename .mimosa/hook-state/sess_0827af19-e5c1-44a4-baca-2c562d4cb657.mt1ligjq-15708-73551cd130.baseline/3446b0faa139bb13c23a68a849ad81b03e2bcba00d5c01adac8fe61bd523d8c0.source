#!/usr/bin/env python3
"""policy — سطحِ **واقعیِ** آزمایش را استنتاج کن، نه سطحِ اعلام‌شده را باور کن.

قاعدهٔ مرکزی این فایل:

    سطحِ اعلام‌شدهٔ منبع کفِ کلاس را می‌دهد، نه سقفش.

اگر یک آزمایشِ «E0 — فقط‌خواندنی» در جزئیاتش `send` داشته باشد، E0 نیست؛
A4 است. این‌جا همان تفاوتی است که «برچسب» را از «رفتار» جدا می‌کند — و همان
جایی که یک مولدِ آلوده (یا یک صفحهٔ وبِ دشمن که واردِ متنِ کشف شده) می‌تواند
سعی کند خودش را بی‌خطر اعلام کند.

سه ورودیِ استنتاج، به ترتیبِ قابلِ اعتماد بودن:
  ۱ **میدان‌های ساختاری** — `external_effect`, `cost`, `target`, `capabilities`
  ۲ **افعالِ عملیاتی** در گام‌های آزمایش — send/submit/register/purchase/…
  ۳ متنِ آزاد — فقط بالابرنده، هرگز پایین‌آورنده

$0 · stdlib · تابعِ خالص · صفر I/O.
"""
from __future__ import annotations

import re

from .contracts import LEVEL_TO_CLASS

_LADDER = ("A0", "A1", "A2", "A3", "A4", "A5", "A6")
_RANK = {c: i for i, c in enumerate(_LADDER)}
_LEVEL_RANK = {"E0": 0, "E1": 1, "E2": 2, "E3": 3, "E4": 4}


def escalate(*classes: str) -> str:
    best = "A0"
    for c in classes:
        if c not in _RANK:
            return "A6"
        if _RANK[c] > _RANK[best]:
            best = c
    return best


# ── افعالی که سطح را بالا می‌برند، هرچه روی برچسب نوشته باشد ────────────────
_SEND = re.compile(
    r"\b(send|post|publish|submit|email|dm|message|tweet|comment|reply|"
    r"deploy|push|upload|notify)\b|ارسال|انتشار|ثبتِ?\s*فرم|پیام\s*بده", re.I)
_ACCOUNT = re.compile(
    r"\b(sign[\s-]?up|register|create\s+(an?\s+)?account|onboard|kyc|"
    r"subscribe|trial)\b|ساختِ?\s*حساب|ثبت[\s‌]*نام", re.I)
_MONEY = re.compile(
    r"\b(pay|purchase|buy|checkout|invoice|billing|paid\s+api|credit\s+card|"
    r"subscription\s+fee)\b|خرید|پرداخت|هزینه‌?ی?\s*دلاری|قرارداد", re.I)
_PII = re.compile(
    r"\b(email\s+address|phone\s+number|passport|ssn|tax\s+file|address\s+of|"
    r"date\s+of\s+birth)\b|شمارهٔ?\s*تماس|کدِ?\s*ملی|آدرسِ?\s*منزل", re.I)
_WRITE = re.compile(
    r"\b(write|mutate|patch|edit|modify|delete|truncate|drop)\b|"
    r"نوشتن\s+در|ویرایشِ?\s*فایل", re.I)

# مقصدهای تخطی‌ناپذیر — هرکدام A6، صرفِ‌نظر از سطحِ اعلام‌شده.
_FORBIDDEN_TARGET = (
    "pre-0/", "governance", "constitution", "run_all", "tests/",
    "held_out_evaluator", "cycle_evaluator", "prereg",
    "power.py", "tg_api", "code_autonomy", "code_brain", "kill", "stop-",
    ".env", "secret", "credential", "token", "wallet", "seed",
    ".git", "genome", "ledger", "germline",
    "fitness-latest", "attribution", "revenue", "money", "budget/",
    "_ops/state/", "organism.py", "wiring.py", "octopus-flags",
)


def _blob(experiment: dict) -> str:
    """همهٔ متنِ آزمایش، یکجا — شاملِ گام‌ها که معمولاً رفتارِ واقعی آن‌جاست."""
    if not isinstance(experiment, dict):
        return ""
    parts = [str(experiment.get(k) or "") for k in
             ("title", "description", "method", "hypothesis", "falsifier",
              "action_type", "target", "notes")]
    steps = experiment.get("steps")
    if isinstance(steps, list):
        for s in steps:
            parts.append(canonical_step(s))
    return " ".join(parts)


def canonical_step(s) -> str:
    if isinstance(s, dict):
        return " ".join(f"{k}={v}" for k, v in s.items())
    return str(s or "")


def hits_forbidden_target(experiment: dict) -> "str | None":
    if not isinstance(experiment, dict):
        return None
    blob = " ".join(str(experiment.get(k) or "") for k in
                    ("target", "output_path", "artifact_path", "path")).lower()
    blob = blob.replace("\\", "/")
    return next((m for m in _FORBIDDEN_TARGET if m in blob), None)


def infer_level(experiment: dict, declared: "str | None") -> dict:
    """سطحِ واقعی + دلیل. خروجی: {level, class, reasons, declared}.

    سطحِ ناشناخته ⇒ `None` و کلاسِ `None` — صداکننده باید BLOCK کند، نه حدس."""
    reasons = []
    dec = declared if declared in _LEVEL_RANK else None
    if declared is not None and dec is None:
        reasons.append(f"unknown-declared-level:{declared!r}")

    base_cls = LEVEL_TO_CLASS.get(dec) if dec else None
    if base_cls:
        reasons.append(f"declared:{dec}→{base_cls}")
    cls = base_cls or "A0"          # کف؛ اگر هیچ سیگنالی نباشد صداکننده BLOCK می‌کند

    if not isinstance(experiment, dict):
        return {"level": dec, "class": None, "declared": declared,
                "reasons": reasons + ["no-experiment-object"]}

    # ۱) میدان‌های ساختاری
    ext = experiment.get("external_effect")
    if ext is True:
        cls = escalate(cls, "A4")
        reasons.append("external_effect=true→A4")
    cost = experiment.get("estimated_cost", experiment.get("cost", 0))
    if isinstance(cost, bool) or not isinstance(cost, (int, float)):
        if cost is not None:
            cls = escalate(cls, "A5")
            reasons.append("cost-unreadable→A5")
    elif float(cost) > 0:
        cls = escalate(cls, "A5")
        reasons.append(f"cost={cost}→A5")

    # ۲) افعالِ عملیاتی در گام‌ها و توضیح
    blob = _blob(experiment)
    if _SEND.search(blob):
        cls = escalate(cls, "A4")
        reasons.append("send-verb→A4")
    if _ACCOUNT.search(blob):
        cls = escalate(cls, "A5")
        reasons.append("account-creation→A5")
    if _MONEY.search(blob):
        cls = escalate(cls, "A5")
        reasons.append("money-verb→A5")
    if _PII.search(blob):
        cls = escalate(cls, "A6")
        reasons.append("pii-collection→A6")
    if _WRITE.search(blob) and dec in ("E0",):
        cls = escalate(cls, "A1")
        reasons.append("write-verb-in-E0→A1")

    # ۳) مقصدِ ممنوع — تخطی‌ناپذیر
    hit = hits_forbidden_target(experiment)
    if hit:
        cls = escalate(cls, "A6")
        reasons.append(f"forbidden-target:{hit}→A6")

    return {"level": dec, "class": (cls if (dec or cls != "A0") else None),
            "declared": declared, "reasons": reasons}


def decide(source_status: str, action_class: "str | None",
           *, has_experiment: bool, falsifier_present: bool) -> dict:
    """تصمیمِ نهاییِ مرز. **این تابع تنها جایی است که NO_ACTION تولید می‌شود.**

    قاعدهٔ اول و مهم‌تر از همه: وضعیتِ غیرقابلِ‌اقدام هرگز عملِ اجرایی نمی‌سازد.
    استثنای تک: یک آزمایشِ **کاملاً اطلاعاتیِ** A0 که برای *رفعِ کمبودِ شاهد*
    طراحی شده — و حتی آن هم کشف را validated اعلام نمی‌کند."""
    if source_status not in [*_NON_ACTIONABLE, *_ACTIONABLE]:
        return {"decision": "BLOCK", "reason": f"unknown-source-status:{source_status!r}"}

    if source_status in _NON_ACTIONABLE:
        if not has_experiment:
            return {"decision": "NO_ACTION",
                    "reason": f"{source_status}: هیچ آزمایشی در artifact نیست"}
        if action_class == "A0" and falsifier_present:
            return {"decision": "DRY_RUN",
                    "reason": (f"{source_status}: آزمایشِ اطلاعاتیِ A0 برای گسترشِ "
                               "شاهد — کشف همچنان validated نیست")}
        return {"decision": "NO_ACTION",
                "reason": (f"{source_status}: آزمایش A0/ابطال‌پذیر نیست "
                           f"(class={action_class}, falsifier={falsifier_present})")}

    # وضعیتِ قابلِ‌اقدام (فقط DISCOVERY_VALIDATED)
    if action_class is None:
        return {"decision": "BLOCK", "reason": "unknown-action-class"}
    if not falsifier_present:
        return {"decision": "NO_ACTION",
                "reason": "کشفِ معتبر ولی بدونِ falsifier — امتیازِ تکمیل نمی‌گیرد"}
    if action_class in ("A0", "A1"):
        return {"decision": "DRY_RUN", "reason": f"validated + {action_class}"}
    if action_class == "A3":
        return {"decision": "OWNER_GATE", "reason": "validated + A3 — کارتِ رأی"}
    if action_class in ("A4", "A5"):
        return {"decision": "BLOCK", "reason": f"{action_class} — BLOCKED_BY_OWNER"}
    return {"decision": "REJECT", "reason": f"{action_class} — ممنوعِ مطلق"}


from .contracts import NON_ACTIONABLE as _NON_ACTIONABLE  # noqa: E402
_ACTIONABLE = frozenset({"DISCOVERY_VALIDATED"})
