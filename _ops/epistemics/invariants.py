"""invariants.py — ۱۰ invariantِ معرفتیِ صریح و قابل‌تست (ADR-039 §7, Phase 2.5).

بازبینیِ Hypothesis-Ledger (2026-08-13) چهار invariantِ تلقینیِ ما را به ده تا گسترش داد.
این فایل آن‌ها را به‌صورتِ یک رجیستریِ صریح و قابلِ enumerate نگه می‌دارد تا:

  (الف) هر invariant یک نام، یک صورتِ صریح، و یک نقطهٔ enforcement داشته باشد؛
  (ب) تست‌ها بتوانند همهٔ ۱۰ را assert کنند (نه فقط باورِ تلقینی)؛
  (پ) آن‌هایی که «structural» هستند واقعاً توسط schema/validator enforce شوند.

قانونِ کابینِ epistemics: این فایل stdlib-only است (Pydantic فقط در schemas.py).
نقاطِ enforcement با ارجاعِ رشته‌ای به فایل/کلاس مشخص می‌شوند، نه import.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Invariant:
    """یک invariantِ معرفتی.

    enforcement_point:
      - "schema"     → توسط Pydantic در زمانِ ساخت enforce می‌شود (سخت‌ترین)
      - "validator"  → توسط validator.py به‌صورتِ defense-in-depth
      - "runtime"    → توسط gate/composer در زمانِ اجرا
      - "advisory"   → اصلِ مفهومی؛ باید در prompt/UI افشا شود (هنز enforce‌نشده ساختاری)
    """
    id: int
    name: str          # شناسهٔ کوتاه (مثلاً "possible!=true")
    statement: str     # صورتِ صریح
    enforcement_point: str
    enforced_by: str   # فایل/کلاس/تابعی که آن را enforce می‌کند


# ترتیب مهم است (تست‌ها به ترتیبِ ۱..۱۰ assert می‌کنند).
ALL_INVARIANTS: Tuple[Invariant, ...] = (
    Invariant(
        1, "possible != true",
        "اینکه چیزی ممکن است معنایش نیست که حقیقت دارد.",
        "schema",
        "GateOutcome فقط SUPPORTED/REFUTED/INCONCLUSIVE/BLOCKED دارد — مقدارِ TRUE وجود ندارد",
    ),
    Invariant(
        2, "useful != true",
        "کارآمد بودنِ یک فرضیه (discovery value) معنایش نیست که درست است.",
        "advisory",
        "pursue_score در hypothesis_brain (EIG) از p_e جدا است — usefulness بر belief اثر ندارد",
    ),
    Invariant(
        3, "predicted != observed",
        "پیش‌بینیِ یک مدل معنایش نیست که آن چیزی واقعاً مشاهده شد — receipt جدا است.",
        "runtime",
        "Prediction (schemas) از EvidenceReceipt (schemas) جدا است؛ gate آن‌ها را مقایسه می‌کند",
    ),
    Invariant(
        4, "simulation != reality",
        "خروجیِ sandbox/شبیه‌سازی واقعیت نیست — labelِ world_mode باید حفظ شود.",
        "schema",
        "WorldMode enum + EpistemicClaim._reality_never_defaulted (REALITY روی claim ممنوع)",
    ),
    Invariant(
        5, "cited != verified",
        "ارجاع به یک منبع معنایش تأییدِ آن نیست — trust_level جدا است.",
        "schema",
        "EvidenceLink.trust_level (verified|derived|untrusted)؛ contracts.EPISTEMIC_LABELS",
    ),
    Invariant(
        6, "generated != sourced",
        "متنی که مدل تولید کرده منبع نیست — باید از receipt تایید‌شده بیاید.",
        "advisory",
        "produced_by فقط producerِ مجاز (validator.unauthorized_producer)؛ generated بدون receipt شاهد نیست",
    ),
    Invariant(
        7, "correlation != causation",
        "همبستگیِ مشاهده‌شده علّت نیست — ادعای CAUSAL نیاز به طراحیِ مداخلهٔ علّی دارد.",
        "schema",
        "ClaimType.CAUSAL متمایز از DESCRIPTIVE؛ TestDesign (ablation/chaos) برای علّت",
    ),
    Invariant(
        8, "prior != posterior",
        "باورِ پیشین معنایش باورِ پسین نیست — belief_delta باید ثبت شود.",
        "schema",
        "belief_delta_log_odds در GateDecision؛ prior در EpistemicClaim",
    ),
    Invariant(
        9, "no-evidence != evidence-of-absence",
        "نبودِ شواهد معنایش شاهدِ نبودن نیست — INCONCLUSIVE نباید باور را تغییر دهد.",
        "schema",
        "GateDecision._fail_closed: INCONCLUSIVE ⇒ belief_delta_log_odds == 0.0",
    ),
    Invariant(
        10, "sandbox-approval != production-authorization",
        "مجوزِ آزمونِ sandbox مجوزِ اثرِ تولیدی نیست — may_execute همیشه False.",
        "schema",
        "GateDecision.may_execute=False hard-coded + ExecutionScope جدا از authority",
    ),
)


BY_ID = {inv.id: inv for inv in ALL_INVARIANTS}
BY_NAME = {inv.name: inv for inv in ALL_INVARIANTS}


def names() -> Tuple[str, ...]:
    """همهٔ نام‌های invariant به‌ترتیب."""
    return tuple(inv.name for inv in ALL_INVARIANTS)


def count() -> int:
    return len(ALL_INVARIANTS)


def structural_invariants() -> Tuple[Invariant, ...]:
    """invariantهایی که توسط schema در زمانِ ساخت enforce می‌شوند (سخت‌ترین)."""
    return tuple(inv for inv in ALL_INVARIANTS if inv.enforcement_point == "schema")
