"""experiment_designer.py — طراحی آزمایش کم‌خطر و ابطال‌پذیر.

بند ۱۲: همیشه کوچک‌ترین سطحی را انتخاب کن که فرضیه را ابطال کند.
سطوح:
  E0 — فقط داده عمومی
  E1 — artifact واقعی بدون ارسال
  E2 — draft تعامل، ارسال با رأی
  E3 — تعامل واقعی، فقط با رأی تازه
  E4 — خرج/قرارداد، بدون رأی ممنوع
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from .contracts import (
    ALLOWED_EXP_LEVELS,
    EXP_E0,
    EXP_E1,
    EXP_E2,
    Experiment,
    Opportunity,
)


def _exp_id(discovery_id: str, hypothesis: str) -> str:
    return "exp-" + hashlib.sha256(
        f"{discovery_id}|{hypothesis}".encode()
    ).hexdigest()[:12]


def choose_minimal_level(opp: Opportunity, *, action_level: str) -> str:
    """کوچک‌ترین سطح آزمایش که فرضیه را ابطال می‌کند + در محدودهٔ مجاز باشد."""
    # مأموریت ما L3 است، ولی آزمایش باید حداقل سطح را انتخاب کند
    # ابتدا E0 پیشنهاد می‌شود (داده عمومی)
    # اگر reversal نیاز به artifact دارد → E1
    if opp.type in ("ai-architecture-insight", "competitor-weakness",
                    "pricing-anomaly", "distribution-gap"):
        return EXP_E0  # با دادهٔ عمومی قابل ابطال
    if opp.type in ("tool-opportunity", "capability-composition", "workflow-inefficiency"):
        return EXP_E1  # artifact لازم است (benchmark/draft)
    return EXP_E0


def design_experiment(
    discovery: dict,
    opp: Opportunity,
    *,
    action_level: str = "L3",
    horizon_days: int = 7,
    now: Optional[datetime] = None,
) -> Experiment:
    """طراحی یک آزمایش E0/E1 برای discovery + opportunity.

    هر آزمایش:
    - hypothesis و falsifier صریح دارد.
    - baseline و observable_metric دارد.
    - owner_gate دارد (L3 → ارسال با رأی).
    - cost_ceiling = 0 AUD.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    deadline = (now + timedelta(days=horizon_days)).strftime("%Y-%m-%d")

    claim = discovery.get("claim", opp.claim)
    level = choose_minimal_level(opp, action_level=action_level)

    hypothesis = (
        f"اگر فرضیهٔ «{claim[:140]}» درست باشد، با {level} قابل مشاهده است."
    )
    baseline = "وضعیت فعلی پیش از آزمایش (ثبت‌شده قبل از نتیجه)."
    metric = _derive_metric(opp, level)
    target = _derive_target(opp, level)
    falsifier = _derive_falsifier(claim, opp)

    allowed = ["read-public-data", "compute-metric", "build-artifact"] if level == EXP_E1 \
        else ["read-public-data", "compute-metric"]
    forbidden = [
        "send-telegram", "send-email", "create-account", "spend",
        "call-customer", "register-form", "bypass-paywall", "scrape-tos-violation",
    ]
    if level in (EXP_E0, EXP_E1):
        forbidden.append("any-external-send")

    return Experiment(
        experiment_id=_exp_id(discovery.get("discovery_id", ""), hypothesis),
        discovery_id=discovery.get("discovery_id", ""),
        level=level,
        hypothesis=hypothesis,
        baseline=baseline,
        observable_metric=metric,
        target=target,
        deadline=deadline,
        public_data_required=_public_data_required(opp),
        allowed_actions=allowed,
        forbidden_actions=forbidden,
        owner_gate=(
            "L3: نتیجهٔ آزمایش به‌صورت report تحویل داده می‌شود؛ "
            "هیچ ارسالی بدون رأی تازهٔ مالک انجام نمی‌شود."
        ),
        expected_evidence=_expected_evidence(level),
        falsifier=falsifier,
        stop_condition=(
            "اگر دادهٔ عمومی کافی برای محاسبهٔ metric یافت نشد → توقف و گزارش NO_DATA."
        ),
        cost_ceiling="0 AUD",
        privacy_boundary="no-personal-data; read-only public sources",
        rollback=(
            "آزمایش فقط خواندن/محاسبه است؛ هیچ state ای تغییر نمی‌کند. "
            "rollback = حذف artifact محلی."
        ),
    )


def _derive_metric(opp: Opportunity, level: str) -> str:
    """یک metric قابل مشاهده."""
    t = opp.type
    if t == "pricing-anomaly":
        return "اختلاف قیمت عمومی منتشرشدهٔ رقبا (دلار) به‌ازای واحد قابلیت."
    if t == "competitor-weakness":
        return "تعداد منابع مستقل تأییدکنندهٔ ضعف ساختاری رقیب."
    if t == "distribution-gap":
        return "تعداد کانال/پلتفرمی که رقیب حضور ندارد ولی demand موجود است."
    if t == "ai-architecture-insight":
        return "وجود/عدم‌وجود قابلیت ادعا‌شده در مستندات رسمی رقیب (بله/خیر)."
    if t == "tool-opportunity":
        return "هزینه/زمان یک workflow خاص با ابزار موجود در برابر جایگزین."
    return "یک سنجهٔ قابل مشاهدهٔ عمومی مرتبط با ادعا."


def _derive_target(opp: Opportunity, level: str) -> str:
    if opp.time_to_test_days:
        return f"دریافت شاهد اولیه در ≤{opp.time_to_test_days} روز."
    return "دریافت شاهد اولیه در ≤۷ روز."


def _derive_falsifier(claim: str, opp: Opportunity) -> str:
    return (
        f"اگر دادهٔ عمومی نشان دهد که «{claim[:120]}» برعکس است "
        f"(یا رقیب آن را پر کرده، یا demand وجود ندارد)، فرضیه باطل می‌شود."
    )


def _expected_evidence(level: str) -> str:
    if level == EXP_E0:
        return "یک جدول/metric محاسبه‌شده از دادهٔ عمومی + منابع."
    return "یک artifact (benchmark/draft) + metric + منابع."


def _public_data_required(opp: Opportunity) -> list[str]:
    t = opp.type
    reqs = ["official-pricing-pages", "changelog-or-release-notes"]
    if t in ("competitor-weakness", "ai-architecture-insight"):
        reqs.append("official-product-documentation")
    if t == "pricing-anomaly":
        reqs.append("public-feature-comparison")
    if t == "distribution-gap":
        reqs.append("channel/platform-presence-data")
    return reqs
