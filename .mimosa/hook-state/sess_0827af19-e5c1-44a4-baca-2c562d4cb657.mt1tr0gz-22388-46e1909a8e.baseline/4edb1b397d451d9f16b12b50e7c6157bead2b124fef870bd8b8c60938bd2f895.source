#!/usr/bin/env python3
"""classifier — «این عمل چقدر خطرناک است؟» تابعِ خالص، همیشه رو به بالا.

هستهٔ امنیتیِ پل. سه قاعده که هیچ‌کدام قابلِ مذاکره نیستند:

  ۱) **ناشناخته = A6.** نوعِ عملی که در جدول نیست، رد می‌شود — نه A0. اگر
     پیش‌فرضْ امن می‌بود، هر تایپو یا هر نامِ نوی مولد یک درِ باز می‌شد.
  ۲) **فقط بالا، هرگز پایین.** هر سیگنال می‌تواند کلاس را **بالا** ببرد؛ هیچ
     سیگنالی نمی‌تواند پایینش بیاورد. `escalate()` این را ساختاراً تضمین می‌کند.
  ۳) **متن مجوز نیست.** `intent`، `expected_effect`، `source_component` و هر
     رشتهٔ آزادِ دیگری فقط می‌توانند کلاس را **بالا** ببرند (اگر نشانهٔ خطر
     داشته باشند). هیچ‌کدام نمی‌توانند کلاس را پایین بیاورند یا جدول را override
     کنند — وگرنه یک prompt-injection در متنِ یک منبعِ وب می‌توانست خودش را
     «فقط خواندنی» اعلام کند.

قاعدهٔ ۳ دلیلِ وجودیِ این فایل است: `world_discovery` قرار است از **وب عمومی**
تغذیه شود، یعنی متنِ کنترل‌نشدهٔ دشمن‌محتمل واردِ `intent` می‌شود. پس طبقه‌بندی
باید از میدان‌های **ساختاری** (نوع، مقصد، فلگ، هزینه) بیاید، نه از روایت.

$0 · stdlib · تابعِ خالص · صفر I/O.
"""
from __future__ import annotations

import re

from contracts import escalate  # noqa: E402  (هم‌پوشه؛ مسیر را صداکننده ست می‌کند)
from scope_guard import hits_forbidden  # noqa: E402

# ── جدولِ پایه: نوعِ عمل → کلاسِ کمینه ───────────────────────────────────────
# «کمینه» یعنی سیگنال‌های دیگر فقط می‌توانند بالاترش ببرند.
BASE = {
    # A0 — مشاهده
    "read_public": "A0", "read_local_file": "A0", "observe_metric": "A0",
    "list_directory": "A0", "parse_artifact": "A0", "search_index": "A0",
    # A1 — artifact در sandbox
    "write_sandbox_artifact": "A1", "render_report": "A1",
    "write_scratch_json": "A1", "build_plan_document": "A1",
    # A2 — تغییرِ برگشت‌پذیرِ داخلی (فعلاً بی‌مجوز)
    "edit_allowlisted_code": "A2", "write_allowlisted_state": "A2",
    "rotate_allowlisted_log": "A2",
    # A3 — کاری که مالک باید بکند/تأیید کند
    "draft_message": "A3", "owner_action_card": "A3", "request_owner_decision": "A3",
    # A4 — اثرِ بیرونی
    "send_message": "A4", "post_public": "A4", "submit_web_form": "A4",
    "http_side_effect": "A4", "deploy": "A4", "git_push": "A4",
    "merge_to_master": "A4", "restart_process": "A4", "send_email": "A4",
    # A5 — پول و تعهد
    "paid_api_call": "A5", "purchase": "A5", "sign_contract": "A5",
    "create_account": "A5", "transfer_funds": "A5",
    # A6 — همیشه ممنوع
    "edit_governance": "A6", "edit_evaluator": "A6", "edit_test": "A6",
    "disable_kill_switch": "A6", "rewrite_evidence": "A6",
    "delete_evidence": "A6", "fabricate_claim": "A6", "arm_flag": "A6",
    "acquire_credentials": "A6", "replicate": "A6",
}

# نوشتن‌هایی که اگر مقصدشان شاهد/پول/حاکمیت باشد، جعل‌اند نه کار.
_WRITE_LIKE = frozenset({
    "write_sandbox_artifact", "write_scratch_json", "render_report",
    "edit_allowlisted_code", "write_allowlisted_state", "rotate_allowlisted_log",
    "build_plan_document",
})

# ── نشانه‌های جعل در **متن** — دو-بخشی، نه یک رگکسِ بلند ────────────────────
# چرا دو-بخشی: نسخهٔ اول یک رگکسِ طولانیِ تک‌تکه بود و «یک lead ساختگی بساز» را
# **نگرفت**، چون فقط «ادعای ساختگی»/«درآمدِ ساختگی» را می‌شناخت. صرفِ فارسی و
# ترتیبِ آزادِ کلمات یعنی الگوی جفت‌شده شکننده است. حالا: یک فعلِ ساختن **و** یک
# اسمِ شاهد، در هر ترتیبی و با هر فاصله‌ای.
#
# عمداً هر دو لازم‌اند: «claim» به‌تنهایی کافی نیست (خواندنِ `attribution.claimed`
# یک A0 ِ کاملاً مشروع است) و «بساز» به‌تنهایی هم نه (ساختنِ گزارش A1 است).
_FAB_VERB = re.compile(
    r"(جعل|ساختگی|جعلی|قلابی|صوری|بک[‌\s]*دیت|"
    r"fabricat|forge|fake|synthetic|synthes\w*|invent\w*|backdate|"
    r"make\s+up|made[\s-]?up|بساز(م|یم)?|بسازد)", re.I)
_FAB_NOUN = re.compile(
    r"(lead|لید|claim|ادعا|revenue|درآمد|receipt|رسید|attribution|"
    r"claimed|فروش|sale)", re.I)


def _looks_like_fabrication(blob: str) -> bool:
    return bool(_FAB_VERB.search(blob) and _FAB_NOUN.search(blob))

# نشانه‌های تلاش برای دور زدنِ خودِ گارد — همیشه A6.
_SCOPE_ESCAPE = re.compile(
    r"(bypass\s+(the\s+)?(guard|gate|check)|disable\s+(the\s+)?(guard|test|gate)|"
    r"ignore\s+(previous|above|prior)\s+instruction|override\s+classification|"
    r"دور\s*زدن|خاموش\s*کردنِ?\s*(گارد|گیت|تست))", re.I)


def _text_blob(req: dict) -> str:
    return " ".join(str(req.get(k) or "") for k in
                    ("intent", "expected_effect", "target", "action_type"))


def classify(req: dict) -> dict:
    """{classification, reasons, base}. هرگز استثنا پرتاب نمی‌کند.

    `reasons` فهرستِ **همهٔ** سیگنال‌های بالابرنده است، نه فقط برنده — تا کارتِ
    رأی بتواند بگوید چه چیزی این عمل را خطرناک کرد."""
    reasons = []
    if not isinstance(req, dict):
        return {"classification": "A6", "reasons": ["not-a-dict"], "base": None}

    atype = str(req.get("action_type") or "").strip()
    base = BASE.get(atype)
    if base is None:
        # قاعدهٔ ۱ — و صریح ثبت می‌شود تا «چرا رد شد؟» جواب داشته باشد.
        return {"classification": "A6", "base": None,
                "reasons": [f"unknown-action-type:{atype or '<empty>'}"]}
    cls = base
    reasons.append(f"base:{atype}={base}")

    # ── سیگنالِ ساختاری ۱: فلگِ اثرِ بیرونی ─────────────────────────────────
    if req.get("external_effect") is True:
        cls = escalate(cls, "A4")
        reasons.append("external_effect=true→A4")
    elif req.get("external_effect") is not False:
        # نه True نه False (None، رشته، عدد) = اعلام‌نشده ⇒ محافظه‌کار
        cls = escalate(cls, "A4")
        reasons.append("external_effect-undeclared→A4")

    # ── سیگنالِ ساختاری ۲: هزینه ────────────────────────────────────────────
    cost = req.get("estimated_cost")
    if isinstance(cost, bool) or not isinstance(cost, (int, float)):
        cls = escalate(cls, "A5")
        reasons.append("cost-unreadable→A5")
    elif float(cost) > 0:
        cls = escalate(cls, "A5")
        reasons.append(f"cost={cost}→A5")

    # ── سیگنالِ ساختاری ۳: مقصدِ ممنوع ──────────────────────────────────────
    hit = hits_forbidden(str(req.get("target") or ""))
    if hit:
        cls = escalate(cls, "A6")
        reasons.append(f"forbidden-target:{hit}→A6")

    # ── سیگنالِ ساختاری ۴: نوشتن روی شاهد/پول = جعل، نه کار ────────────────
    if atype in _WRITE_LIKE and hit:
        reasons.append("write-to-evidence→A6")

    # ── سیگنالِ متنی (فقط بالابرنده — قاعدهٔ ۳) ──────────────────────────────
    blob = _text_blob(req)
    if _looks_like_fabrication(blob):
        cls = escalate(cls, "A6")
        reasons.append("fabrication-language→A6")
    if _SCOPE_ESCAPE.search(blob):
        cls = escalate(cls, "A6")
        reasons.append("scope-escape-language→A6")

    # ── قابلیت‌های درخواستی ────────────────────────────────────────────────
    caps = req.get("required_capabilities")
    if caps is not None and not isinstance(caps, list):
        cls = escalate(cls, "A6")
        reasons.append("bad:required_capabilities→A6")
    for c in (caps or []):
        cl = str(c).lower()
        if any(x in cl for x in ("network.send", "email", "telegram.send",
                                 "http.post", "publish")):
            cls = escalate(cls, "A4")
            reasons.append(f"capability:{c}→A4")
        if any(x in cl for x in ("payment", "billing", "purchase", "paid")):
            cls = escalate(cls, "A5")
            reasons.append(f"capability:{c}→A5")
        if any(x in cl for x in ("secret", "credential", "keyring", "kill")):
            cls = escalate(cls, "A6")
            reasons.append(f"capability:{c}→A6")

    return {"classification": cls, "base": base, "reasons": reasons}


# ── تصمیم از روی کلاس ───────────────────────────────────────────────────────
# این جدول **سیاستِ این دور** است، نه قانونِ ابدی: A2 عمداً BLOCK است چون
# governance هنوز اجازهٔ تغییرِ برگشت‌پذیرِ خودکار نداده (VQ-SELFGOAL-002 چهار
# پیش‌شرطِ مکانیکیِ باز دارد). وقتی آن‌ها بسته شدند، فقط همین یک خط عوض می‌شود.
DECISION_BY_CLASS = {
    "A0": "ALLOW",
    "A1": "ALLOW",
    "A2": "BLOCK",       # BLOCKED_BY_SAFETY تا رأیِ حاکمیتی
    "A3": "OWNER_GATE",
    "A4": "BLOCK",       # BLOCKED_BY_OWNER
    "A5": "BLOCK",       # BLOCKED_BY_OWNER
    "A6": "REJECT",
}


def decide(classification: str) -> str:
    """کلاسِ ناشناخته ⇒ REJECT. هیچ مسیرِ پیش‌فرضِ سخاوتمندانه‌ای نیست."""
    return DECISION_BY_CLASS.get(classification, "REJECT")
